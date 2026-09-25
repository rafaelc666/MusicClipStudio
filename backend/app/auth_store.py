"""
Autenticação multiusuário do MusicClipStudio WEB.

⚠️ NOVO (23/09/2026) — LOGIN + CHAVES POR USUÁRIO.

Cada usuário tem:
  - nome de usuário + senha (hash PBKDF2-SHA256, 200k iterações, salt único)
  - um token de sessão opaco (guardado no localStorage do navegador)
  - as PRÓPRIAS chaves de API de stock (7 provedores + 2 slots livres),
    criptografadas em repouso com Fernet (cryptography)

As chaves NUNCA voltam abertas para o frontend — só prévia (últimos 4
caracteres) e um booleano "configurada". O backend injeta a chave certa
na StockDatabase no momento da busca (endpoints /api/provedores/*).

Banco: output/usuarios.db (mesmo espírito do projetos.db: junto do
output, backup = copiar a pasta).
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Optional

from cryptography.fernet import Fernet, InvalidToken

# Provedores fixos do produto (na ordem exibida na UI).
PROVEDORES_FIXOS = [
    {"id": "pexels",    "nome": "Pexels",    "tipo": "fotos+videos", "chave_em": "stock_pexels_api_key"},
    {"id": "pixabay",   "nome": "Pixabay",   "tipo": "fotos+videos", "chave_em": "stock_pixabay_api_key"},
    {"id": "unsplash",  "nome": "Unsplash",  "tipo": "fotos",        "chave_em": "stock_unsplash_api_key"},
    {"id": "nasa",      "nome": "NASA",      "tipo": "fotos+videos", "chave_em": "stock_nasa_api_key", "gratuita_sem_chave": True},
    {"id": "coverr",    "nome": "Coverr",    "tipo": "videos",       "chave_em": "stock_coverr_api_key"},
    {"id": "giphy",     "nome": "Giphy",     "tipo": "gifs/videos",  "chave_em": "stock_giphy_api_key"},
    {"id": "openverse", "nome": "Openverse", "tipo": "fotos",        "chave_em": "stock_openverse_api_key", "gratuita_sem_chave": True},
]
# Slots livres: ILIMITADOS — o usuário adiciona quantos bancos próprios
# quiser (⚠️ 23/09/2026: antes eram 2 fixos). Cada slot aponta para a API
# que o banco usa (mesma engine de um provedor fixo), então o motor de
# busca sabe como consultá-lo.
# ⚠️ NOVO (24/09/2026) — CHAVES DE ÁUDIO TAMBÉM POR USUÁRIO.
#
# A trilha (Epidemic Sound) entra no MESMO cofre do
# usuário: criptografada com Fernet em output/usuarios.db, junto do login.
# Antes existiam só no .env (globais) — pedido do dono: "as chaves têm que
# salvar com o usuário no DB". O .env continua valendo como PADRÃO de
# instalação: se o usuário não colou a dele, o backend usa a do .env.
PROVEDORES_AUDIO = [
    {"id": "epidemic",  "nome": "Epidemic Sound", "tipo": "musica",           "chave_em": "epidemic_api_key"},
]

PROV_POR_ID = {p["id"]: p for p in PROVEDORES_FIXOS}
TIPOS_VALIDOS = set(PROV_POR_ID.keys())
AUDIO_POR_ID = {p["id"]: p for p in PROVEDORES_AUDIO}

# Sessões expiram em 30 dias (usuário não fica logando todo dia).
SESSAO_TTL_S = 30 * 24 * 3600

_PBKDF2_ITER = 200_000


def _default_db_path(base_dir: Path) -> Path:
    d = Path(base_dir) / "output"
    d.mkdir(parents=True, exist_ok=True)
    return d / "usuarios.db"


class AuthStore:
    """Contas + sessões + chaves por usuário em SQLite. Thread-safe."""

    def __init__(self, db_path: Optional[Path | str] = None, base_dir: Optional[Path] = None):
        if db_path is None:
            if base_dir is None:
                base_dir = Path(__file__).resolve().parent.parent.parent
            db_path = _default_db_path(Path(base_dir))
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Chave Fernet: derivada de um segredo local (gerado na 1ª execução).
        # Protege as chaves de API "em repouso" no .db — quem só copiar o
        # arquivo não lê as chaves sem o .secret_key.
        self._secret_path = self.db_path.parent / ".mcs_secret_key"
        if not self._secret_path.exists():
            # ⚠️ HARDENING (23/09/2026): segredo criado já com 0600 (só o dono
            # lê). Em multiusuário do SO, outro usuário do sistema não lê.
            self._secret_path.write_bytes(Fernet.generate_key())
            os.chmod(self._secret_path, 0o600)
        else:
            try:
                os.chmod(self._secret_path, 0o600)  # corrige instalações antigas
            except OSError:
                pass
        self._fernet = Fernet(self._secret_path.read_bytes().strip())
        # O banco de usuários também: contém hashes + chaves criptografadas.
        try:
            os.chmod(self.db_path, 0o600)
        except OSError:
            pass

        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._criar_schema()

    # ── schema ──────────────────────────────────────────────────────────

    def _criar_schema(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS usuarios (
                    id            TEXT PRIMARY KEY,
                    username      TEXT UNIQUE NOT NULL,
                    senha_hash    TEXT NOT NULL,
                    salt          TEXT NOT NULL,
                    chaves        TEXT NOT NULL DEFAULT '{}',
                    custom        TEXT NOT NULL DEFAULT '[]',
                    habilitados   TEXT NOT NULL DEFAULT '{}',
                    criado_em     INTEGER NOT NULL
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessoes (
                    token      TEXT PRIMARY KEY,
                    user_id    TEXT NOT NULL REFERENCES usuarios(id),
                    criada_em  INTEGER NOT NULL,
                    expira_em  INTEGER NOT NULL
                )
                """
            )
            self._conn.commit()

    # ── senha ───────────────────────────────────────────────────────────

    @staticmethod
    def _hash_senha(senha: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256", senha.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ITER
        ).hex()

    # ── contas ──────────────────────────────────────────────────────────

    def registrar(self, username: str, senha: str) -> dict[str, Any]:
        username = username.strip()
        if len(username) < 3:
            raise ValueError("Nome de usuário precisa de ao menos 3 caracteres")
        if len(senha) < 8:
            # ⚠️ HARDENING (23/09/2026): era 4. Mesmo local, a conta guarda as
            # chaves de API do dono — mínimo decente.
            raise ValueError("Senha precisa de ao menos 8 caracteres")
        salt = secrets.token_hex(16)
        with self._lock:
            ja = self._conn.execute(
                "SELECT 1 FROM usuarios WHERE username = ? COLLATE NOCASE", (username,)
            ).fetchone()
            if ja:
                raise ValueError("Esse nome de usuário já existe")
            uid = "user_" + secrets.token_hex(8)
            self._conn.execute(
                "INSERT INTO usuarios (id, username, senha_hash, salt, chaves, custom, habilitados, criado_em) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (uid, username, self._hash_senha(senha, salt), salt, "{}", "[]", "{}", int(time.time())),
            )
            self._conn.commit()
        return {"id": uid, "username": username}

    def _usuario_por_username(self, username: str) -> Optional[sqlite3.Row]:
        with self._lock:
            return self._conn.execute(
                "SELECT * FROM usuarios WHERE username = ? COLLATE NOCASE", (username.strip(),)
            ).fetchone()

    def autenticar(self, username: str, senha: str) -> dict[str, Any]:
        """Login com limite de tentativas (anti força bruta).

        ⚠️ HARDENING (23/09/2026): 5 erros = conta bloqueada por 10 min.
        Em app LOCAL o risco é baixo, mas o app roda em 127.0.0.1 e qualquer
        processo da máquina pode reaching a API — o limite custa nada e fecha
        a porta da força bruta offline.
        """
        agora = int(time.time())
        with self._lock:
            estado = self._tentativas.get(username, (0, 0))
            erros, bloqueado_ate = estado
            if agora < bloqueado_ate:
                restante = (bloqueado_ate - agora + 59) // 60
                raise ValueError(
                    "Muitas tentativas — tente de novo em "
                    f"{restante} minuto" + ("s" if restante > 1 else "")
                )
        row = self._usuario_por_username(username)
        if not row:
            self._registrar_falha(username, agora)
            raise ValueError("Usuário ou senha incorretos")
        calc = self._hash_senha(senha, row["salt"])
        if not hmac.compare_digest(calc, row["senha_hash"]):
            self._registrar_falha(username, agora)
            raise ValueError("Usuário ou senha incorretos")
        # Sucesso: zera o contador
        with self._lock:
            self._tentativas.pop(username, None)
        return {"id": row["id"], "username": row["username"]}

    # ⚠️ HARDENING (23/09/2026): limitador de tentativas por usuário, em
    # memória (processo). 5 erros → 10 min de bloqueio.
    MAX_TENTATIVAS = 5
    BLOQUEIO_S = 10 * 60
    _tentativas: dict[str, tuple[int, int]] = {}

    def _registrar_falha(self, username: str, agora: int) -> None:
        with self._lock:
            erros, _ = self._tentativas.get(username, (0, 0))
            erros += 1
            bloqueado_ate = agora + self.BLOQUEIO_S if erros >= self.MAX_TENTATIVAS else 0
            self._tentativas[username] = (erros, bloqueado_ate)

    # ── sessões ─────────────────────────────────────────────────────────

    def criar_sessao(self, user_id: str) -> dict[str, Any]:
        token = secrets.token_urlsafe(32)
        agora = int(time.time())
        with self._lock:
            self._conn.execute(
                "INSERT INTO sessoes (token, user_id, criada_em, expira_em) VALUES (?,?,?,?)",
                (token, user_id, agora, agora + SESSAO_TTL_S),
            )
            self._conn.commit()
        return {"token": token, "expira_em": agora + SESSAO_TTL_S}

    def usuario_do_token(self, token: str) -> Optional[dict[str, Any]]:
        if not token:
            return None
        agora = int(time.time())
        with self._lock:
            row = self._conn.execute(
                """
                SELECT u.id, u.username, u.chaves, u.custom, u.habilitados
                FROM sessoes s JOIN usuarios u ON u.id = s.user_id
                WHERE s.token = ? AND s.expira_em > ?
                """,
                (token, agora),
            ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "username": row["username"],
            "chaves": json.loads(row["chaves"] or "{}"),
            "custom": json.loads(row["custom"] or "[]"),
            "habilitados": json.loads(row["habilitados"] or "{}"),
        }

    def encerrar_sessao(self, token: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM sessoes WHERE token = ?", (token,))
            self._conn.commit()

    # ── chaves de API (sempre criptografadas no disco) ──────────────────

    @staticmethod
    def _normalizar_custom(custom: Any) -> list[dict[str, str]]:
        """Garante lista de dicts {nome, chave, tipo} (migra formato antigo)."""
        if not isinstance(custom, list):
            return []
        out: list[dict[str, str]] = []
        for c in custom:
            if not isinstance(c, dict):
                continue
            out.append({
                "nome": str(c.get("nome") or ""),
                "chave": str(c.get("chave") or ""),
                "tipo": str(c.get("tipo") or ""),
                "url": str(c.get("url") or ""),  # ⚠️ 23/09: endpoint de API do banco
            })
        return out

    @staticmethod
    def _cripto(f: Fernet, valor: str) -> str:
        return f.encrypt(valor.encode("utf-8")).decode("ascii")

    @staticmethod
    def _decripto(f: Fernet, blob: str) -> str:
        try:
            return f.decrypt(blob.encode("ascii")).decode("utf-8")
        except (InvalidToken, ValueError):
            return ""

    def _previa(self, chave: str) -> str:
        return ("…" + chave[-4:]) if len(chave) >= 4 else ""

    # ⚠️ NOVO (23/09/2026): URLs oficiais por banco — exibidas na UI e usadas
    # quando o usuário não define endpoint próprio. Mesma tabela do motor.
    URLS_OFICIAIS = {
        "pexels": "https://api.pexels.com/v1",
        "pixabay": "https://pixabay.com/api/",
        "unsplash": "https://api.unsplash.com",
        "nasa": "https://images-api.nasa.gov",
        "coverr": "https://api.coverr.co",
        "giphy": "https://api.giphy.com/v1",
        "openverse": "https://api.openverse.org/v1",
    }

    @classmethod
    def _url_oficial(cls, banco: str) -> str:
        return cls.URLS_OFICIAIS.get(banco, "")

    def definir_chave(
        self, user_id: str, provedor_id: str,
        chave: str | None = None, url: str | None = None,
    ) -> dict[str, Any]:
        """Salva/atualiza a chave de um provedor (fixo ou slot custom).

        ⚠️ NOVO (23/09/2026): `url` opcional — endpoint de API do banco
        (proxy/endpoint próprio). Vazio = volta para a URL oficial.
        `chave=None` = não mexer na chave salva (salvar só a URL).
        Guardadas criptografadas; entram no config via `stock_urls`.
        """
        chave = chave.strip() if chave is not None else None
        url = (url or "").strip() if url is not None else None
        with self._lock:
            row = self._conn.execute("SELECT chaves, custom FROM usuarios WHERE id = ?", (user_id,)).fetchone()
            if not row:
                raise ValueError("Usuário não encontrado")
            chaves = json.loads(row["chaves"] or "{}")
            custom = self._normalizar_custom(json.loads(row["custom"] or "[]"))
            raw_urls = chaves.get("__urls__") or {}
            try:
                urls = json.loads(raw_urls) if isinstance(raw_urls, str) else dict(raw_urls)
            except (ValueError, TypeError):
                urls = {}

            if provedor_id.startswith("custom_"):
                idx = int(provedor_id.split("_", 1)[1])
                if not (0 <= idx < len(custom)):
                    raise ValueError("Banco próprio não existe (use 'Adicionar banco')")
                custom[idx]["nome"] = custom[idx].get("nome") or f"Banco próprio {idx + 1}"
                if chave is not None:
                    custom[idx]["chave"] = self._cripto(self._fernet, chave) if chave else ""
                if url is not None:
                    # "" remove o endpoint custom (volta para a oficial)
                    if url.strip():
                        custom[idx]["url"] = url.strip()
                    else:
                        custom[idx].pop("url", None)
            else:
                # ⚠️ 24/09: aceita também a chave de ÁUDIO (epidemic),
                # que fica no mesmo campo `chaves` do usuário.
                ids_validos = {p["id"] for p in PROVEDORES_FIXOS} | set(AUDIO_POR_ID.keys())
                if provedor_id not in ids_validos:
                    raise ValueError("Provedor desconhecido")
                if chave is not None:
                    chaves[provedor_id] = self._cripto(self._fernet, chave) if chave else ""
                if url is not None:
                    # "" remove o endpoint custom (volta para a oficial)
                    if url.strip():
                        urls[provedor_id] = url.strip()
                    else:
                        urls.pop(provedor_id, None)

            if url is not None:
                chaves["__urls__"] = urls  # persiste os endpoints custom
            self._conn.execute(
                "UPDATE usuarios SET chaves = ?, custom = ? WHERE id = ?",
                (json.dumps(chaves), json.dumps(custom), user_id),
            )
            self._conn.commit()
        return self.resumo_provedores(user_id)

    def adicionar_custom(self, user_id: str, tipo: str, nome: str = "") -> int:
        """Cria um novo banco próprio apontando para a API `tipo`. Retorna o idx."""
        tipo = tipo.strip().lower()
        if tipo not in TIPOS_VALIDOS:
            raise ValueError("API desconhecida — escolha uma das engines listadas")
        with self._lock:
            row = self._conn.execute("SELECT custom FROM usuarios WHERE id = ?", (user_id,)).fetchone()
            if not row:
                raise ValueError("Usuário não encontrado")
            custom = self._normalizar_custom(json.loads(row["custom"] or "[]"))
            idx = len(custom)
            custom.append({
                "nome": nome.strip()[:60] or f"{PROV_POR_ID[tipo]['nome']} (próprio)",
                "chave": "",
                "tipo": tipo,
            })
            self._conn.execute("UPDATE usuarios SET custom = ? WHERE id = ?", (json.dumps(custom), user_id))
            self._conn.commit()
        return idx

    def remover_custom(self, user_id: str, idx: int) -> None:
        """Remove um banco próprio e reordena os flags de habilitado."""
        with self._lock:
            row = self._conn.execute("SELECT custom, habilitados FROM usuarios WHERE id = ?", (user_id,)).fetchone()
            if not row:
                raise ValueError("Usuário não encontrado")
            custom = self._normalizar_custom(json.loads(row["custom"] or "[]"))
            if not (0 <= idx < len(custom)):
                raise ValueError("Banco próprio não existe")
            custom.pop(idx)
            habilitados = json.loads(row["habilitados"] or "{}")
            # Reordena os flags custom_N depois do pop (N diminui 1 a partir de idx).
            novos: dict[str, bool] = {}
            for k, v in habilitados.items():
                if k.startswith("custom_"):
                    try:
                        n = int(k.split("_", 1)[1])
                    except ValueError:
                        continue
                    if n == idx:
                        continue  # slot removido
                    if n > idx:
                        n -= 1
                    novos[f"custom_{n}"] = bool(v)
                else:
                    novos[k] = bool(v)
            self._conn.execute(
                "UPDATE usuarios SET custom = ?, habilitados = ? WHERE id = ?",
                (json.dumps(custom), json.dumps(novos), user_id),
            )
            self._conn.commit()

    def renomear_custom(self, user_id: str, idx: int, nome: str) -> None:
        nome = nome.strip()[:60]
        with self._lock:
            row = self._conn.execute("SELECT custom FROM usuarios WHERE id = ?", (user_id,)).fetchone()
            if not row:
                raise ValueError("Usuário não encontrado")
            custom = self._normalizar_custom(json.loads(row["custom"] or "[]"))
            if not (0 <= idx < len(custom)):
                raise ValueError("Banco próprio não existe")
            custom[idx]["nome"] = nome
            self._conn.execute("UPDATE usuarios SET custom = ? WHERE id = ?", (json.dumps(custom), user_id))
            self._conn.commit()

    def resumo_provedores(self, user_id: str) -> dict[str, Any]:
        """O que a UI mostra: SEM chaves abertas, só prévia + status."""
        with self._lock:
            row = self._conn.execute(
                "SELECT chaves, custom, habilitados FROM usuarios WHERE id = ?", (user_id,)
            ).fetchone()
        if not row:
            raise ValueError("Usuário não encontrado")
        chaves_blob = json.loads(row["chaves"] or "{}")
        custom = self._normalizar_custom(json.loads(row["custom"] or "[]"))
        habilitados = json.loads(row["habilitados"] or "{}")

        fixos = []
        raw_urls = chaves_blob.get("__urls__") or {}
        try:
            urls_blob = json.loads(raw_urls) if isinstance(raw_urls, str) else dict(raw_urls)
        except (ValueError, TypeError):
            urls_blob = {}
        for p in PROVEDORES_FIXOS:
            blob = chaves_blob.get(p["id"], "")
            chave = self._decripto(self._fernet, blob) if blob else ""
            fixos.append({
                "id": p["id"],
                "nome": p["nome"],
                "tipo": p["tipo"],
                "gratuita_sem_chave": bool(p.get("gratuita_sem_chave")),
                "configurada": bool(chave),
                "previa": self._previa(chave) if chave else "",
                "habilitado": bool(habilitados.get(p["id"], True)),
                "url": str(urls_blob.get(p["id"]) or ""),  # ⚠️ 23/09: endpoint custom
                "url_oficial": self._url_oficial(p["id"]),
            })

        slots = []
        for i, c in enumerate(custom):
            # Slots vazios de sobra (formato antigo, nunca usados) não aparecem.
            if not c.get("chave") and not c.get("nome") and not c.get("tipo"):
                continue
            chave = self._decripto(self._fernet, c.get("chave", "")) if c.get("chave") else ""
            slots.append({
                "id": f"custom_{i}",
                "nome": c.get("nome") or "",
                "tipo": c.get("tipo") or "",
                "configurada": bool(chave),
                "previa": self._previa(chave) if chave else "",
                "habilitado": bool(habilitados.get(f"custom_{i}", True)),
                "url": str(c.get("url") or ""),  # ⚠️ 23/09: endpoint custom do banco
                "url_oficial": self._url_oficial(c.get("tipo") or "pexels"),
            })
        # ⚠️ NOVO (24/09/2026): chaves de ÁUDIO do usuário (trilha/efeitos),
        # no mesmo formato dos fixos — a UI mostra em bloco separado.
        audio = []
        for p in PROVEDORES_AUDIO:
            blob = chaves_blob.get(p["id"], "")
            chave = self._decripto(self._fernet, blob) if blob else ""
            audio.append({
                "id": p["id"],
                "nome": p["nome"],
                "tipo": p["tipo"],
                "configurada": bool(chave),
                "previa": self._previa(chave) if chave else "",
            })

        return {"ok": True, "fixos": fixos, "custom": slots, "audio": audio}

    def chaves_audio(self, user_id: str) -> dict[str, str]:
        """Chaves de áudio do usuário, DECRIPTOGRAFADAS (uso interno).

        Devolve no formato do ClipConfig (`chave_em`): `epidemic_api_key`.
        Vazio = usuário não colou a dele (cai no .env).
        """
        with self._lock:
            row = self._conn.execute("SELECT chaves FROM usuarios WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return {}
        chaves_blob = json.loads(row["chaves"] or "{}")
        saida: dict[str, str] = {}
        for p in PROVEDORES_AUDIO:
            blob = chaves_blob.get(p["id"], "")
            if blob:
                valor = self._decripto(self._fernet, blob)
                if valor:
                    saida[p["chave_em"]] = valor
        return saida

    def chaves_para_busca(self, user_id: str) -> dict[str, str]:
        """Chaves DECRIPTOGRAFADAS — só para uso interno na busca.

        ⚠️ CORRIGIDO (23/09/2026): devolve no formato que o ClipConfig
        entende (`chave_em` de cada provedor — ex. "stock_pexels_api_key"),
        para o main.py poder fazer `dataclasses.replace(cfg, **chaves)`.
        Antes saía por id ("pexels"), chave inexistente no dataclass.
        Agora inclui também `stock_urls` (JSON com os endpoints custom).
        """
        with self._lock:
            row = self._conn.execute("SELECT chaves FROM usuarios WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return {}
        chaves_blob = json.loads(row["chaves"] or "{}")
        mapa = {p["id"]: p["chave_em"] for p in PROVEDORES_FIXOS}
        saida: dict[str, str] = {}
        urls_usuario: dict[str, str] = {}
        raw_urls = chaves_blob.get("__urls__") or {}
        try:
            urls_usuario = json.loads(raw_urls) if isinstance(raw_urls, str) else dict(raw_urls)
        except (ValueError, TypeError):
            urls_usuario = {}
        for pid, blob in chaves_blob.items():
            if blob and pid in mapa:
                saida[mapa[pid]] = self._decripto(self._fernet, blob)
        if urls_usuario:
            saida["stock_urls"] = json.dumps(urls_usuario, ensure_ascii=False)
        # Bancos próprios: a chave entra pela engine que o slot aponta
        # (ex.: slot "Meu banco" com tipo "pexels" alimenta stock_pexels_api_key).
        with self._lock:
            row = self._conn.execute("SELECT custom FROM usuarios WHERE id = ?", (user_id,)).fetchone()
        if row:
            custom = self._normalizar_custom(json.loads(row["custom"] or "[]"))
            for c in custom:
                t = c.get("tipo", "")
                if c.get("chave") and t in mapa:
                    saida[mapa[t]] = self._decripto(self._fernet, c["chave"])
                # ⚠️ 23/09: endpoint custom do banco próprio entra no stock_urls
                if t and c.get("url"):
                    urls_usuario[t] = c["url"]
        if urls_usuario:
            saida["stock_urls"] = json.dumps(urls_usuario, ensure_ascii=False)
        return saida

    def tipo_do_provedor(self, user_id: str, provedor_id: str) -> str:
        """Engine real que atende o provedor: fixo → próprio id; custom_N → tipo salvo."""
        if not provedor_id.startswith("custom_"):
            if provedor_id not in TIPOS_VALIDOS:
                raise ValueError("Provedor desconhecido")
            return provedor_id
        idx = int(provedor_id.split("_", 1)[1])
        with self._lock:
            row = self._conn.execute("SELECT custom FROM usuarios WHERE id = ?", (user_id,)).fetchone()
        custom = self._normalizar_custom(json.loads(row["custom"] or "[]")) if row else []
        if not (0 <= idx < len(custom)):
            raise ValueError("Banco próprio não existe")
        tipo = custom[idx].get("tipo", "")
        if tipo not in TIPOS_VALIDOS:
            raise ValueError("Esse banco próprio não tem API definida — remova e adicione de novo")
        return tipo

    def habilitados_do_usuario(self, user_id: str) -> dict[str, bool]:
        """⚠️ NOVO (23/09/2026): mapa {provedor_id: ligado?} para a busca.
        Ausente = ligado (default do produto)."""
        with self._lock:
            row = self._conn.execute("SELECT habilitados FROM usuarios WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return {}
        return json.loads(row["habilitados"] or "{}")

    def alternar_provedor(self, user_id: str, provedor_id: str, habilitado: bool) -> None:
        with self._lock:
            row = self._conn.execute("SELECT habilitados FROM usuarios WHERE id = ?", (user_id,)).fetchone()
            if not row:
                raise ValueError("Usuário não encontrado")
            habilitados = json.loads(row["habilitados"] or "{}")
            habilitados[provedor_id] = bool(habilitado)
            self._conn.execute("UPDATE usuarios SET habilitados = ? WHERE id = ?", (json.dumps(habilitados), user_id))
            self._conn.commit()
