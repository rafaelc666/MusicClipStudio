"""
Backend FastAPI do MusicClipStudio (versão Web).

Reutiliza TODO o código Python existente (engine, scene_engine, database,
transcricao, audio, agent, etc.) e o expõe via API REST + WebSocket.

Roda com:
    cd d:\\dev-projetos\\MusicClipStudio
    pip install -r requirements-web.txt
    python -m uvicorn backend.app.main:app --reload --port 8300

Portas dedicadas: frontend 3100, backend 8300 (ver `_utils/_portas.py`).
"""

import sys
import asyncio
import dataclasses
import json
import uuid
import threading
import time
from pathlib import Path
from typing import Any, Optional

from fastapi import Request, Response

# Garante que importamos o MusicClipStudio da pasta raiz.
#
# CORRIGIDO (19/09/2026): antes subia só 3 níveis
# (app/ → backend/ → MusicClipStudio/) e caía na pasta DO PROJETO. Mas os
# módulos ficam PLANOS dentro dela (`MusicClipStudio/engine.py`), então
# `import MusicClipStudio.config` exige o PAI no path. Sem isso o backend
# subia com `backbone_ready: false` e todos os endpoints de engine/database
# caíam em stub silencioso — o front parecia funcionar e não gerava nada.
BASE_DIR = Path(__file__).resolve().parent.parent.parent   # ...\MusicClipStudio
PROJETOS_DIR = BASE_DIR.parent                             # ...\dev-projetos
if str(PROJETOS_DIR) not in sys.path:
    sys.path.insert(0, str(PROJETOS_DIR))
# BASE_DIR também entra: o código legado importa `scene_engine.x` de forma plana
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# ⚠️ NOVO (23/09/2026) — .env do projeto é carregado ANTES de qualquer import
# do backbone. Sem isso as chaves de stock e o HF_TOKEN (download do Whisper)
# só existiam se o processo fosse iniciado pelo shell com o .env exportado.
from dotenv import load_dotenv  # noqa: E402
load_dotenv(BASE_DIR / ".env", override=False)
load_dotenv(Path.home() / ".gerador_clipes_config.env", override=False)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Persistência de projetos (SQLite local — sem API externa, ver §14 do STATUS)
from backend.app.projects_store import ProjectsStore

# ⚠️ NOVO (23/09/2026) — LOGIN + CHAVES POR USUÁRIO.
# Usuários (nome+senha) e chaves de API criptografadas por usuário, em SQLite.
# As chaves do .env continuam valendo como fallback global quando o usuário
# não cadastrou a própria.
from backend.app.auth_store import AuthStore
_AUTH = AuthStore(base_dir=BASE_DIR)

# ── Imports do app existente ────────────────────────────────────────
try:
    from MusicClipStudio.config import load_config, save_config, ClipConfig
    from MusicClipStudio.database import StockDatabase, StockMedia
    from MusicClipStudio.agent import ClipAgent
    from MusicClipStudio.engine import MusicClipEngine, ClipProgress
    from MusicClipStudio.schema import MusicBeat, MusicClipProject
    _BACKBONE_IMPORTED = True
except Exception as _e:
    _BACKBONE_IMPORTED = False
    _BACKBONE_ERROR = str(_e)
    # Stubs locais para o backend poder STARTAR mesmo se as classes acima
    # falharem por qualquer motivo (sandbox, engine.py desatualizado, etc.)
    # O health vai reportar backbone_ready=False e todos endpoints caem no
    # fallback de forma graciosa.
    class _ClipConfigStub:
        pass
    ClipConfig = _ClipConfigStub  # type: ignore[misc,assignment]

    class _EngineStub:
        def __init__(self, cfg):
            self.cfg = cfg

        def analyze_lyrics(self, lyrics: str):
            return {"beats": 1, "palavras": len(lyrics.split())}

    MusicClipEngine = _EngineStub  # type: ignore[misc,assignment]

    class _DbStub:
        def __init__(self, cfg):
            self.cfg = cfg

        def search(self, query, provider=None, max_results=20):
            return []

    StockDatabase = _DbStub  # type: ignore[misc,assignment]

    class _AgentStub:
        def __init__(self, cfg):
            self.cfg = cfg

        def generate_image_prompts(self, payload):
            return {"prompts": []}

    ClipAgent = _AgentStub  # type: ignore[misc,assignment]

    def _stub_load_config():
        import json
        p = Path.home() / ".gerador_clipes_config.json"
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"apis": {}}

    def _stub_save_config(cfg):
        p = Path.home() / ".gerador_clipes_config.json"
        p.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

    load_config = _stub_load_config  # type: ignore[assignment]
    save_config = _stub_save_config  # type: ignore[assignment]


# ═══════════════════════════════════════════════════════════════════════
# Pydantic models (pedidos/respostas da API)
# ═══════════════════════════════════════════════════════════════════════

class HealthResponse(BaseModel):
    status: str
    backbone_ready: bool
    backbone_error: Optional[str] = None
    base_dir: str


class ClipProjectPayload(BaseModel):
    """Corpo enviado pelo frontend em várias etapas."""
    lyrics: str = ""
    description: str = ""
    title: str = ""
    artist: str = ""
    music_prompt: str = "epic cinematic orchestral music, powerful, dramatic, no vocals"
    music_duration: int = 30
    images: list[str] = Field(default_factory=list)
    # ⚠️ NOVO (21/09/2026): um efeito por imagem, na MESMA ordem de `images`.
    # Vem do seletor da etapa 05 (ken_burns, zoom_in, zoom_out, pan_left,
    # pan_right, static). Sem ele todas as cenas caem em ken_burns.
    efeitos: list[str] = Field(default_factory=list)
    # ⚠️ NOVO (23/09/2026): tema visual OPCIONAL digitado pelo usuário na
    # etapa 04 ("chuva lenta", "carros antigos", "vôlei de praia"…). Vira
    # qualificador das queries do agente — catalogar todos os temas é
    # impossível; o usuário define o seu.
    theme: str = ""
    format: str = "9/16"
    duration_beat: float = 5.0
    # ⚠️ NOVO (22/09/2026): estilo da legenda queimada (etapa 03).
    # dict livre {cor, corContorno, fonte, tamanho, contorno, posicao, negrito}.
    legenda_estilo: Optional[dict] = None
    mood: str = "epic"
    style: str = "cinematic"
    media_type_pref: str = "Meio a meio"


class SearchMediaPayload(BaseModel):
    query: str
    provider: Optional[str] = None
    max_results: int = 20
    # ⚠️ NOVO (22/09/2026): filtro de tipo na BUSCA (não na escolha).
    # Exclusivos entre si: nenhum marcado traz os dois; um marcado traz só
    # aquele tipo (o StockDB já trata essa combinação — ver CHECKLIST 4.8).
    apenas_fotos: bool = False
    apenas_videos: bool = False


class TranscribePayload(BaseModel):
    audio_path: str  # caminho relativo em output/uploads


class GeneratePayload(BaseModel):
    project: ClipProjectPayload
    subtitle_lines: list[dict] = Field(default_factory=list)
    selected_media: list[dict] = Field(default_factory=list)
    # Música pronta enviada pelo usuário (caminho vindo de /api/upload/audio).
    # É a fonte OFICIAL de trilha: o app não gera música.
    audio_path: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════
# Singletons & estado
# ═══════════════════════════════════════════════════════════════════════

_config: Optional[ClipConfig] = None
_engine: Optional[MusicClipEngine] = None
_db: Optional[StockDatabase] = None
_agent: Optional[ClipAgent] = None
_jobs: dict[str, dict] = {}          # job_id -> {status, progress, events, ...}

# Persistência de projetos. Não depende do "backbone" acima: mesmo que o
# engine falhe ao importar, salvar/listar projetos deve continuar funcionando.
_projects: Optional[ProjectsStore] = None


def _get_projects() -> ProjectsStore:
    """Store de projetos (lazy). Sobrevive a restart do backend."""
    global _projects
    if _projects is None:
        _projects = ProjectsStore(base_dir=BASE_DIR)
    return _projects


def _get_backbone():
    """Retorna (config, engine, db, agent) — inicializa na primeira vez."""
    global _config, _engine, _db, _agent
    if _config is None:
        _config = load_config()
        _engine = MusicClipEngine(_config)
        _db = StockDatabase(_config)
        _agent = ClipAgent(_config)
    return _config, _engine, _db, _agent


# ═══════════════════════════════════════════════════════════════════════
# App FastAPI
# ═══════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="MusicClipStudio API",
    description="Backend web do gerador de clipes musicais",
    version="0.1.0",
)

# CORS — aceita conexão do Next.js e outras portas comuns em dev.
# Portas dedicadas do projeto: frontend 3100, backend 8300 (_utils/_portas.py).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3100",
        "http://127.0.0.1:3100",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3690",
        "http://127.0.0.1:3690",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pastas servidas publicamente
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR = OUTPUT_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CLIPS_DIR = OUTPUT_DIR / "clipes"
CLIPS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")


# ═══════════════════════════════════════════════════════════════════════
# Health & Debug
# ═══════════════════════════════════════════════════════════════════════

@app.get("/api/health", tags=["debug"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        backbone_ready=_BACKBONE_IMPORTED,
        backbone_error=None if _BACKBONE_IMPORTED else _BACKBONE_ERROR,
        base_dir=str(BASE_DIR),
    )


@app.get("/api/config", tags=["config"])
def get_config() -> dict[str, Any]:
    if not _BACKBONE_IMPORTED:
        raise HTTPException(500, detail=f"Backbone não carregado: {_BACKBONE_ERROR}")
    cfg, _, _, _ = _get_backbone()
    return cfg.to_dict()


@app.post("/api/config", tags=["config"])
def post_config(payload: dict) -> dict[str, Any]:
    if not _BACKBONE_IMPORTED:
        raise HTTPException(500, detail=f"Backbone não carregado: {_BACKBONE_ERROR}")
    cfg = ClipConfig.from_dict(payload)
    save_config(cfg)
    return {"ok": True, "saved_at": str(Path.home() / ".gerador_clipes_config.json")}


# ═══════════════════════════════════════════════════════════════════════
# Projetos · Persistência (SQLite local)
# ═══════════════════════════════════════════════════════════════════════
#
# Espelha o `StudioProjectState` do frontend (StudioClientShell.tsx).
# O corpo é livre (dict) porque o estado do wizard evolui; o store guarda
# como JSON. Não exige autenticação — o app roda na máquina do usuário.

class ProjectSavePayload(BaseModel):
    """Projeto enviado pelo frontend. `id` ausente = criar novo."""
    id: Optional[str] = None
    title: str = ""
    createdAt: Optional[int] = None
    status: Optional[str] = None
    # Campos do wizard (opcionais — o frontend manda o que tiver)
    letra: str = ""
    legenda: list[Any] = Field(default_factory=list)
    musica: dict[str, Any] = Field(default_factory=dict)
    imagens: list[Any] = Field(default_factory=list)
    midia: list[Any] = Field(default_factory=list)
    completedSteps: dict[str, Any] = Field(default_factory=dict)
    activeStep: str = "letra"
    # Escape hatch para o frontend evoluir sem mexer no backend
    extras: dict[str, Any] = Field(default_factory=dict)


# ════════════════════════════════════════════════════════════════════
# ⚠️ NOVO (23/09/2026) — LOGIN / SESSÃO + CHAVES DE API POR USUÁRIO
#
# Sessão em cookie httpOnly (imune a XSS no localStorage). A senha é
# PBKDF2 com salt (auth_store). Sem freemium — decisão do usuário:
# multiusuário simples, só plano free.
# ════════════════════════════════════════════════════════════════════

_COOKIE_SESSAO = "mcs_session"


def _usuario_atual(request: Request) -> Optional[dict[str, Any]]:
    token = request.cookies.get(_COOKIE_SESSAO)
    if not token:
        return None
    return _AUTH.usuario_do_token(token)


def _definir_cookie(resp: Response, token: str) -> None:
    resp.set_cookie(
        _COOKIE_SESSAO, token,
        max_age=60 * 60 * 24 * 30,  # 30 dias
        httponly=True, samesite="lax", path="/",
    )


class AuthPayload(BaseModel):
    username: str
    password: str


@app.get("/api/auth/eu", tags=["auth"])
def auth_eu(request: Request) -> dict[str, Any]:
    usuario = _usuario_atual(request)
    if not usuario:
        return {"logado": False}
    return {
        "logado": True,
        "usuario": {"id": usuario["id"], "username": usuario["username"]},
    }


@app.post("/api/auth/registrar", tags=["auth"])
def auth_registrar(payload: AuthPayload, response: Response) -> dict[str, Any]:
    try:
        usuario = _AUTH.registrar(payload.username.strip(), payload.password)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
    sessao = _AUTH.criar_sessao(usuario["id"])
    _definir_cookie(response, sessao["token"])
    return {"ok": True, "usuario": {"id": usuario["id"], "username": usuario["username"]}}


@app.post("/api/auth/login", tags=["auth"])
def auth_login(payload: AuthPayload, response: Response) -> dict[str, Any]:
    usuario = _AUTH.autenticar(payload.username.strip(), payload.password)
    if not usuario:
        raise HTTPException(401, detail="Usuário ou senha incorretos")
    sessao = _AUTH.criar_sessao(usuario["id"])
    _definir_cookie(response, sessao["token"])
    return {"ok": True, "usuario": {"id": usuario["id"], "username": usuario["username"]}}


@app.post("/api/auth/logout", tags=["auth"])
def auth_logout(request: Request, response: Response) -> dict[str, Any]:
    token = request.cookies.get(_COOKIE_SESSAO)
    if token:
        _AUTH.encerrar_sessao(token)
    response.delete_cookie(_COOKIE_SESSAO, path="/")
    return {"ok": True}


class ChavePayload(BaseModel):
    provedor_id: str
    # ⚠️ 23/09: None = não mexer na chave salva; "" = limpar.
    chave: Optional[str] = None
    # ⚠️ 23/09: endpoint de API custom do banco — None = não mexer;
    # "" = limpar (volta para a oficial); valor = definir.
    url: Optional[str] = None


class HabilitarPayload(BaseModel):
    provedor_id: str
    habilitado: bool


class RenomearCustomPayload(BaseModel):
    idx: int
    nome: str = ""


class AdicionarCustomPayload(BaseModel):
    tipo: str
    nome: str = ""


@app.get("/api/provedores", tags=["provedores"])
def listar_provedores(request: Request) -> dict[str, Any]:
    """Os 7 bancos + 2 slots custom, com estado da chave do usuário logado."""
    usuario = _usuario_atual(request)
    if not usuario:
        raise HTTPException(401, detail="Faça login para configurar os provedores")
    return _AUTH.resumo_provedores(usuario["id"])


@app.post("/api/provedores/chave", tags=["provedores"])
def salvar_chave(payload: ChavePayload, request: Request) -> dict[str, Any]:
    usuario = _usuario_atual(request)
    if not usuario:
        raise HTTPException(401, detail="Faça login para configurar os provedores")
    try:
        # ⚠️ 23/09: repassa também a URL de API (endpoint custom do banco);
        # chave None = não mexer na salva (permite salvar só a URL).
        return _AUTH.definir_chave(
            usuario["id"], payload.provedor_id,
            chave=payload.chave.strip() if payload.chave is not None else None,
            url=payload.url,
        )
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


@app.post("/api/provedores/custom/adicionar", tags=["provedores"])
def adicionar_custom(payload: AdicionarCustomPayload, request: Request) -> dict[str, Any]:
    """Adiciona um banco próprio (slots ilimitados) apontando p/ a engine `tipo`."""
    usuario = _usuario_atual(request)
    if not usuario:
        raise HTTPException(401, detail="Faça login para configurar os provedores")
    try:
        _AUTH.adicionar_custom(usuario["id"], payload.tipo, payload.nome)
        return _AUTH.resumo_provedores(usuario["id"])
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


@app.post("/api/provedores/custom/remover", tags=["provedores"])
def remover_custom(payload: RenomearCustomPayload, request: Request) -> dict[str, Any]:
    usuario = _usuario_atual(request)
    if not usuario:
        raise HTTPException(401, detail="Faça login para configurar os provedores")
    try:
        _AUTH.remover_custom(usuario["id"], payload.idx)
        return _AUTH.resumo_provedores(usuario["id"])
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


@app.post("/api/provedores/habilitar", tags=["provedores"])
def habilitar_provedor(payload: HabilitarPayload, request: Request) -> dict[str, Any]:
    usuario = _usuario_atual(request)
    if not usuario:
        raise HTTPException(401, detail="Faça login para configurar os provedores")
    _AUTH.alternar_provedor(usuario["id"], payload.provedor_id, payload.habilitado)
    return {"ok": True}


@app.post("/api/provedores/custom/renomear", tags=["provedores"])
def renomear_custom(payload: RenomearCustomPayload, request: Request) -> dict[str, Any]:
    usuario = _usuario_atual(request)
    if not usuario:
        raise HTTPException(401, detail="Faça login para configurar os provedores")
    _AUTH.renomear_custom(usuario["id"], payload.idx, payload.nome.strip())
    return {"ok": True}


@app.post("/api/provedores/testar", tags=["provedores"])
def testar_provedor(payload: ChavePayload, request: Request) -> dict[str, Any]:
    """Testa a chave (a nova digitada ou a salva) contra a API real."""
    usuario = _usuario_atual(request)
    if not usuario:
        raise HTTPException(401, detail="Faça login para configurar os provedores")
    if not _BACKBONE_IMPORTED:
        raise HTTPException(500, detail=f"Backbone não carregado: {_BACKBONE_ERROR}")
    # ⚠️ CORRIGIDO (23/09/2026): era `_, _, _, cfg = _get_backbone()` — pegava o
    # AGENT (4º elemento), não o config. Por isso o dataclasses.replace explodia.
    cfg, _, _, _ = _get_backbone()
    chaves_usuario = _AUTH.chaves_para_busca(usuario["id"])
    cfg = dataclasses.replace(cfg, **chaves_usuario) if chaves_usuario else cfg
    try:
        # Bancos próprios (custom_N) usam a engine do tipo salvo no slot.
        engine = _AUTH.tipo_do_provedor(usuario["id"], payload.provedor_id)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
    # A chave recém-digitada tem prioridade sobre a salva
    if payload.chave.strip():
        cfg = dataclasses.replace(cfg, **{f"stock_{engine}_api_key": payload.chave.strip()})
    # ⚠️ 23/09: URL recém-digitada também é testada antes de salvar
    if payload.url and payload.url.strip():
        try:
            urls_map = json.loads(getattr(cfg, "stock_urls", "") or "{}")
        except (ValueError, TypeError):
            urls_map = {}
        urls_map[engine] = payload.url.strip()
        cfg = dataclasses.replace(cfg, stock_urls=json.dumps(urls_map))
    db = StockDatabase(cfg)
    try:
        return db.testar_conexao(engine)
    except Exception as e:
        return {"ok": False, "mensagem": f"Erro no teste: {e}"}


@app.get("/api/projetos", tags=["projetos"])
def listar_projetos(limite: int = 50) -> dict[str, Any]:
    """Lista os projetos salvos, mais recentes primeiro."""
    try:
        store = _get_projects()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, detail=f"Falha ao abrir o banco de projetos: {e}")
    itens = store.listar(limite=limite)
    return {"total": len(itens), "projetos": itens}


@app.get("/api/projetos/{project_id}", tags=["projetos"])
def obter_projeto(project_id: str) -> dict[str, Any]:
    store = _get_projects()
    p = store.obter(project_id)
    if p is None:
        raise HTTPException(404, detail=f"Projeto não encontrado: {project_id}")
    return p


@app.post("/api/projetos", tags=["projetos"])
def salvar_projeto(payload: ProjectSavePayload) -> dict[str, Any]:
    """Cria ou atualiza um projeto (upsert por `id`)."""
    store = _get_projects()
    dados = payload.model_dump()
    extras = dados.pop("extras", None) or {}
    # `extras` é mesclado no nível raiz para o estado sobreviver a mudanças
    for k, v in extras.items():
        dados.setdefault(k, v)
    # remove Nones para não sobrescrever título/id com null
    dados = {k: v for k, v in dados.items() if v is not None}
    gravado = store.salvar(dados)
    return {"ok": True, "projeto": gravado}


@app.delete("/api/projetos/{project_id}", tags=["projetos"])
def apagar_projeto(project_id: str) -> dict[str, Any]:
    """Remove um projeto."""
    store = _get_projects()
    removido = store.apagar(project_id)
    if not removido:
        raise HTTPException(404, detail=f"Projeto não encontrado: {project_id}")
    return {"ok": True, "id": project_id}


@app.get("/api/projetos-stats", tags=["projetos"])
def projetos_stats() -> dict[str, Any]:
    """Contagem rápida — usado pelo dashboard."""
    store = _get_projects()
    return {"total": store.contar(), "db": str(store.db_path)}


# ═══════════════════════════════════════════════════════════════════════
# Etapa 01 · Letra
# ═══════════════════════════════════════════════════════════════════════

@app.post("/api/letra/analisar", tags=["letra"])
def analisar_letra(payload: ClipProjectPayload) -> dict[str, Any]:
    """Recebe a letra e devolve beats + estatísticas."""
    if not _BACKBONE_IMPORTED:
        raise HTTPException(500, detail=f"Backbone não carregado: {_BACKBONE_ERROR}")
    _, engine, _, _ = _get_backbone()
    beats = engine.criar_beats(
        lyrics=payload.lyrics,
        description=payload.description,
        duration_beat=payload.duration_beat,
    )
    palavras = (payload.lyrics or "").split()
    return {
        "total_beats": len(beats),
        "total_palavras": len(palavras),
        "duracao_estimada_seg": round(len(beats) * payload.duration_beat, 1),
        "beats": [b.to_dict() if hasattr(b, "to_dict") else {"texto": getattr(b, "texto", ""),
                                                              "duracao": getattr(b, "duracao", 5.0)}
                 for b in beats],
    }


# ═══════════════════════════════════════════════════════════════════════
# Etapa 02 · Legenda / Transcrição
# ═══════════════════════════════════════════════════════════════════════

@app.post("/api/upload/audio", tags=["upload"])
async def upload_audio(file: UploadFile = File(...)) -> dict[str, Any]:
    """
    Recebe a MÚSICA PRONTA do usuário (base da arquitetura Opção A).

    Devolve `path` (relativo a `output/`, usado pelo engine) e `url`
    (pronta para tocar no navegador).

    CORRIGIDO (19/09/2026): o `/static` montado é `/static/output` e serve
    a pasta `output/`. Antes a resposta só trazia `uploads/<arq>`, então
    montar `API_BASE + "/static/" + path` dava 404 — o player do wizard
    quebrava sempre. Agora `url` já vem no formato certo.
    """
    filename = f"{uuid.uuid4().hex}_{file.filename or 'audio.mp3'}"
    destino = UPLOAD_DIR / filename
    contents = await file.read()
    with open(destino, "wb") as f:
        f.write(contents)
    return {
        "ok": True,
        "path": f"uploads/{filename}",
        "url": f"/static/output/uploads/{filename}",
        "absolute": str(destino),
        "size_bytes": len(contents),
    }


@app.get("/api/upload/audio/recente", tags=["upload"])
def listar_uploads_recentes(limite: int = 8) -> dict[str, Any]:
    """
    Lista os uploads de áudio mais recentes em `output/uploads/`.

    ⚠️ NOVO (21/09/2026): a etapa de áudio do wizard perdia a referência do
    arquivo enviado quando o Fast Refresh do Turbopack remontava o shell
    (o disco ficava intacto, mas `state.musica` zerava). Agora o wizard
    oferece reanexar o último arquivo em vez de pedir upload de novo.

    Devolve cada item com `{path, url, nome, size_bytes, mtime}`. Exclui
    arquivos < 1 KB (currais de teste zerados) e ordena do mais novo pro
    mais antigo.
    """
    if not UPLOAD_DIR.exists():
        return {"ok": True, "total": 0, "itens": []}
    itens = []
    for caminho in UPLOAD_DIR.iterdir():
        if not caminho.is_file() or caminho.suffix.lower() not in (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"):
            continue
        try:
            st = caminho.stat()
        except OSError:
            continue
        if st.st_size < 1024:
            continue
        itens.append({
            "path": f"uploads/{caminho.name}",
            "url": f"/static/output/uploads/{caminho.name}",
            "nome": caminho.name.split("_", 1)[-1] if "_" in caminho.name else caminho.name,
            "size_bytes": st.st_size,
            "mtime": st.st_mtime,
        })
    itens.sort(key=lambda it: it["mtime"], reverse=True)
    itens = itens[:max(1, min(limite, 50))]
    return {"ok": True, "total": len(itens), "itens": itens}


@app.post("/api/legenda/transcrever", tags=["legenda"])
def transcrever(payload: TranscribePayload) -> dict[str, Any]:
    """Roda Whisper no áudio. Requer o caminho salvo por /upload/audio."""
    if not _BACKBONE_IMPORTED:
        raise HTTPException(500, detail=f"Backbone não carregado: {_BACKBONE_ERROR}")

    # ⚠️ CORRIGIDO (21/09/2026): o import usava o nome `transcrever_audio`,
    # QUE NÃO EXISTE — a função em MusicClipStudio.transcricao chama-se
    # `transcrever`. O ImportError caía no `except` e o endpoint devolvia
    # 500 "Transcrição indisponível" para 100% das chamadas. O frontend
    # nunca chegava a rodar o Whisper.
    try:
        from MusicClipStudio.transcricao import transcrever
    except Exception as e:
        raise HTTPException(500, detail=f"Transcrição indisponível: {e}")

    caminho = UPLOAD_DIR / Path(payload.audio_path).name
    if not caminho.exists():
        raise HTTPException(404, detail=f"Áudio não encontrado: {caminho}")

    try:
        # `transcrever` devolve um ResultadoTranscricao (não uma lista) e
        # nunca levanta: em falha vem com `erro` preenchido e sem segmentos.
        resultado = transcrever(str(caminho))
    except Exception as e:
        raise HTTPException(500, detail=f"Erro na transcrição: {e}")

    if not resultado.ok:
        # ⚠️ CORRIGIDO (23/09/2026): áudio INSTRUMENTAL não é erro — é caso
        # normal de produto (o Chopin do usuário, trilhas sem voz). Antes
        # devolvia 500 "Nenhuma fala detectada" e a UI mostrava falha.
        # Agora devolve 200 com ok=false e `instrumental=true`; a UI avisa
        # "clipe segue sem legenda" como informação, não como falha.
        sem_fala = "fala" in (resultado.erro or "").lower()
        if sem_fala:
            return {
                "ok": False,
                "instrumental": True,
                "total_linhas": 0,
                "linhas": [],
                "texto_completo": "",
                "mensagem": resultado.erro or "Nenhuma fala detectada — o clipe segue sem legenda.",
            }
        raise HTTPException(
            500,
            detail=resultado.erro or "A transcrição não produziu nenhum segmento.",
        )

    # O frontend espera {indice, inicio, fim, texto} por linha.
    linhas = [s.para_dict() for s in resultado.segmentos]

    return {
        "ok": True,
        "total_linhas": len(linhas),
        "linhas": linhas,
        "texto_completo": resultado.texto_completo,
        "idioma": resultado.idioma,
        "duracao_audio": resultado.duracao_audio,
        "modelo": resultado.modelo,
    }


# ═══════════════════════════════════════════════════════════════════════
# Etapa 03 · Áudio — ARQUITETURA: o app NÃO gera música
# ═══════════════════════════════════════════════════════════════════════
#
# ┌───────────────────────────────────────────────────────────────────┐
# │  DECISÃO DE PRODUTO (Opção A) — não reverter sem o usuário pedir   │
# │                                                                   │
# │  O MusicClipStudio RECEBE A MÚSICA PRONTA (upload do usuário) e    │
# │  monta o vídeo-clipe em cima dela, usando bancos de imagem         │
# │  gratuitos da internet (Pexels, Pixabay, ...).                     │
# │                                                                   │
# │  O app NÃO gera música. Nunca.                                     │
# │  - O usuário não tem servidor/VM para rodar IA musical.            │
# │  - O ACE-Step (legado) trava acima de ~1 min — inviável para um    │
# │    programa de clipes, onde a música tem 3+ minutos.               │
# │                                                                   │
# │  A geração de música era um resto do produto desktop antigo.       │
# │  As rotas foram neutralizadas em 19/09/2026.                       │
# │  Para trilha: use POST /api/upload/audio.                          │
# └───────────────────────────────────────────────────────────────────┘

@app.post("/api/audio/gerar-trilha", tags=["audio"], deprecated=True)
def gerar_trilha_desativada(payload: ClipProjectPayload) -> dict[str, Any]:
    """
    DESATIVADO. O MusicClipStudio não gera música (arquitetura Opção A).

    Esta rota existia para chamar o ACE-Step e gerar trilha por IA. Foi
    neutralizada porque contraria a arquitetura do produto: a música é
    PRONTA, enviada pelo usuário via POST /api/upload/audio.

    Mantida apenas para devolver um erro explicativo (410 Gone) em vez de
    um 404 seco — assim quem chamar entende o porquê.
    """
    raise HTTPException(
        status_code=410,
        detail=(
            "O MusicClipStudio não gera música. Envie a música pronta em "
            "POST /api/upload/audio — o app monta o clipe em cima dela."
        ),
    )


# ═══════════════════════════════════════════════════════════════════════
# Etapa 04 · Imagens (agente IA prompts)
# ═══════════════════════════════════════════════════════════════════════

@app.post("/api/imagens/gerar-prompts", tags=["imagens"])
def gerar_prompts_imagens(payload: ClipProjectPayload) -> dict[str, Any]:
    """Pede ao agente IA para gerar prompts de busca por beat."""
    if not _BACKBONE_IMPORTED:
        raise HTTPException(500, detail=f"Backbone não carregado: {_BACKBONE_ERROR}")
    _, _, _, agent = _get_backbone()
    try:
        # CORRIGIDO (19/09/2026): era agent.gerar_prompts_busca() — método que
        # NÃO EXISTE. O real é analisar(), que devolve um AgentPlan com uma
        # AgentDecision por beat; cada decisão traz photo_query, que é
        # justamente o prompt de busca visual que esta rota entrega.
        # ⚠️ NOVO (23/09/2026): tema livre digitado pelo usuário vira
        # qualificador de TODAS as queries — "chuva lenta" devolve
        # "rain window (slow motion video)" etc.
        tema_livre = (payload.theme or "").strip()
        if tema_livre:
            agent._tema_livre = tema_livre
        plan = agent.analisar(
            lyrics=payload.lyrics,
            description=payload.description,
            music_prompt=payload.music_prompt,
        )
    except Exception as e:
        raise HTTPException(500, detail=f"Agente IA falhou: {e}")

    prompts = [
        {
            "beat_id": getattr(d, "beat_id", i),
            "prompt": getattr(d, "photo_query", ""),
            "categoria": getattr(d, "image_category", ""),
            "efeito": getattr(d, "effect", ""),
            "animacao": getattr(d, "animation", ""),
            "cor_destaque": getattr(d, "accent_color", ""),
            "cor_fundo": getattr(d, "bg_color", ""),
            "confianca": round(float(getattr(d, "confidence", 0.0)), 3),
        }
        for i, d in enumerate(getattr(plan, "beats", []) or [])
    ]

    # ⚠️ NOVO (23/09/2026): o tema musical detectado (temas_musicais) volta
    # para a UI mostrar o que guiou as cenas (ex.: "Gospel / Worship").
    tema_id = getattr(getattr(agent, "_tema", None), "id", None)
    tema_nome = getattr(getattr(agent, "_tema", None), "nome", None)

    return {
        "ok": True,
        "mood": getattr(getattr(plan, "mood", None), "value", str(getattr(plan, "mood", ""))),
        "estilo": getattr(getattr(plan, "style", None), "value", str(getattr(plan, "style", ""))),
        "tema": tema_id,
        "tema_nome": tema_nome,
        "paleta": getattr(plan, "color_palette", {}) or {},
        "total": len(prompts),
        "prompts": prompts,
    }


# ═══════════════════════════════════════════════════════════════════════
# Etapa 05 · Mídia (busca no banco stock)
# ═══════════════════════════════════════════════════════════════════════

def _config_do_usuario(request: Request) -> Any:
    """Config de stock do usuário logado (sessão no cookie), ou None.

    ⚠️ NOVO (23/09/2026): as chaves por usuário moram no AuthStore
    (criptografadas). Aqui elas são clonadas por cima do config global
    (dataclass → replace), então a busca usa a chave do usuário SEM tocar
    no singleton compartilhado entre requests.
    """
    token = request.cookies.get("mcs_session")
    if not token:
        return None
    usuario = _AUTH.usuario_do_token(token)
    if not usuario:
        return None
    chaves = _AUTH.chaves_para_busca(usuario["id"])
    if not chaves:
        return None
    cfg = load_config()
    # ⚠️ NOVO (23/09/2026): os toggles liga/desliga do diálogo controlam de
    # verdade a busca — sem isso, banco desligado continuava sendo consultado.
    habilitados = _AUTH.habilitados_do_usuario(usuario["id"])
    overrides: dict[str, Any] = dict(chaves)
    for pid, ligado in habilitados.items():
        if pid.startswith("custom_"):
            continue  # o banco próprio usa o flag da engine que aponta
        overrides[f"stock_{pid}_enabled"] = bool(ligado)
    return dataclasses.replace(cfg, **overrides)


@app.post("/api/midia/buscar", tags=["midia"])
def buscar_midia(payload: SearchMediaPayload, request: Request) -> dict[str, Any]:
    """Busca fotos/vídeos no banco de stock (Pexels/Pixabay/etc.).

    ⚠️ NOVO (23/09/2026): usa as chaves do usuário LOGADO quando existirem;
    sem login, cai nas chaves do .env (comportamento antigo).
    """
    if not _BACKBONE_IMPORTED:
        raise HTTPException(500, detail=f"Backbone não carregado: {_BACKBONE_ERROR}")
    # ⚠️ CORRIGIDO (23/09/2026): era `_, _, _, _cfg` — pegava o agent, não o config.
    cfg, _, _, _ = _get_backbone()
    try:
        # Chaves do usuário logado (ou global do .env) — não o singleton.
        cfg_usuario = _config_do_usuario(request) or cfg
        db = StockDatabase(cfg_usuario)
        if payload.provider:
            busca = db.pesquisar(
                query=payload.query,
                provider=payload.provider,
                max_results=payload.max_results,
                apenas_fotos=payload.apenas_fotos,
                apenas_videos=payload.apenas_videos,
            )
        else:
            # ⚠️ NOVO (23/09/2026): SEM provider explícito, busca em TODOS os
            # bancos habilitados do usuário, intercalando os resultados.
            # Antes: caía no stock_provider do config — só 1 banco respondia.
            busca = db.pesquisar_multi(
                query=payload.query,
                max_results=payload.max_results,
                apenas_fotos=payload.apenas_fotos,
                apenas_videos=payload.apenas_videos,
            )
        resultados = getattr(busca, "results", None)
        if resultados is None:
            # fallback: alguns builds antigos devolviam lista pura
            resultados = busca if isinstance(busca, list) else []
    except Exception as e:
        raise HTTPException(500, detail=f"Erro busca stock: {e}")

    serializados = []
    for r in resultados or []:
        if isinstance(r, StockMedia):
            # CORRIGIDO: os nomes dos campos são EN no dataclass
            # (url, thumbnail_url, media_type, source, width, height),
            # não PT como estava escrito aqui (titulo, url_full, tipo...).
            # O mapeamento antigo estourava AttributeError em 8 campos.
            serializados.append({
                "id": r.id,
                "titulo": r.description or r.id,
                "url_thumbnail": r.thumbnail_url,
                "url_full": r.download_url or r.url,
                # ⚠️ CORRIGIDO (22/09/2026): era `r.url` — que no Pexels é a
                # PÁGINA do site (pexels.com/photo/...), não o arquivo.
                # O frontend usava esse campo como fonte do clipe e o vídeo
                # saía todo azul (background-image com página não desenha
                # nada; aparecia o fundo do tema). Agora o preview aponta
                # pro ARQUIVO real, igual ao url_full.
                "url_preview": r.download_url or r.url,
                "video_url": r.video_url,
                "tipo": r.media_type,
                "provider": r.source,
                "largura": r.width,
                "altura": r.height,
                "duracao": 0,
                "tags": r.tags,
                "descricao": r.description,
            })
        elif isinstance(r, dict):
            serializados.append(r)
    return {"ok": True, "query": payload.query, "total": len(serializados), "resultados": serializados}


# ═══════════════════════════════════════════════════════════════════════
# Etapa 06 · Gerar (long-running via WebSocket /jobs)
# ═══════════════════════════════════════════════════════════════════════

def _run_generation_sync(job_id: str, payload: GeneratePayload):
    """Executa a geração em thread separada e grava eventos em _jobs[job_id]."""
    cfg, engine, _, _ = _get_backbone()
    job = _jobs[job_id]

    def _evt(evento: str, dados: dict):
        job["events"].append({
            "time": time.time(), "event": evento, "data": dados,
        })
        # trim para não explodir memória
        if len(job["events"]) > 500:
            job["events"] = job["events"][-200:]

    try:
        job["status"] = "running"
        _evt("progress", {"pct": 1, "etapa": "inicializando", "msg": "Montando projeto..."})

        # ── Progresso em tempo real ────────────────────────────────────
        # O engine emite via `_notify(event, data)`, e para progresso o
        # payload é: {"progresso": 0.85, "etapa": "...", "mensagem": "..."}
        # — note que `progresso` vem como FRAÇÃO (0..1), não 0..100.
        #
        # CORRIGIDO (19/09/2026): o callback era
        # `def _on_engine_progress(pct, etapa="", mensagem="")`, mas o engine
        # chama `cb(event, data)`. Resultado: `pct` recebia a STRING
        # "progress" e `etapa` o dict; `int(pct)` estourava ValueError e o
        # `except` engolia em silêncio. O job ficava travado em 0% para
        # sempre — mesmo com o vídeo gerado com sucesso.
        def _on_engine_progress(evento: str, dados: dict):
            try:
                if evento != "progress":
                    return
                fracao = float(dados.get("progresso", 0) or 0)
                job["progress"] = int(round(fracao * 100))
                job["etapa"] = str(dados.get("etapa", ""))
                _evt("progress", {
                    "pct": job["progress"],
                    "etapa": dados.get("etapa", ""),
                    "msg": dados.get("mensagem", ""),
                })
            except Exception:
                pass

        engine.on_progress(_on_engine_progress)

        # ── Trilha: música pronta do usuário ───────────────────────────
        # ARQUITETURA: o MusicClipStudio recebe a MÚSICA PRONTA e monta o
        # vídeo-clipe em cima dela. O app NÃO gera música (sem servidor de
        # IA musical; o ACE-Step trava >1min). Sem áudio, gera clipe mudo.
        trilha = None
        if payload.audio_path:
            candidato = UPLOAD_DIR / Path(payload.audio_path).name
            if candidato.exists():
                trilha = str(candidato)
                _evt("progress", {"pct": 8, "etapa": "áudio",
                                  "msg": f"Música do usuário: {candidato.name}"})
            else:
                _evt("progress", {"pct": 8, "etapa": "áudio",
                                  "msg": f"AVISO: áudio não encontrado ({payload.audio_path}) — clipe mudo"})

        # ── Pipeline completo ──────────────────────────────────────────
        # CORRIGIDO (19/09/2026): antes o backend montava o projeto e depois
        # chamava engine.renderizar_projeto(), MÉTODO QUE NÃO EXISTE — o
        # AttributeError caía no except e o job terminava em "error".
        # O engine já tem o pipeline completo em generate(): ele cria os
        # beats, renderiza o HTML, converte para vídeo, combina o áudio
        # enviado e queima as legendas.
        # ── Imagens escolhidas pelo usuário (etapa 05) ──────────────────
        # ⚠️ CORRIGIDO (21/09/2026): `selected_media` existia no contrato e
        # NUNCA era lido — a seleção feita na tela morria aqui e o clipe saía
        # com as imagens que o backend quisesse. Agora ela é a fonte
        # principal; `project.images`/`project.efeitos` ficam como fallback
        # (o frontend manda os dois).
        imagens = list(payload.project.images or [])
        efeitos = list(payload.project.efeitos or [])

        if payload.selected_media:
            imagens = [
                str(m.get("url") or "")
                for m in payload.selected_media
                if isinstance(m, dict) and m.get("url")
            ]
            efeitos = [
                str(m.get("efeito") or "ken_burns")
                for m in payload.selected_media
                if isinstance(m, dict) and m.get("url")
            ]
            _evt("progress", {
                "pct": 12, "etapa": "imagens",
                "msg": f"{len(imagens)} cenas escolhidas na etapa 05",
            })

        # ── GUARDA: só arquivo de mídia direto entra no render ─────────
        # ⚠️ NOVO (22/09/2026): páginas HTML do provedor (ex. pexels.com/
        # photo/...) não desenham em background-image/<video> — a camada
        # ficava transparente e o clipe saía TODO AZUL (fundo do tema),
        # sem nenhuma mídia, sem erro aparente. Falha rápido e com
        # mensagem clara em vez de entregar MP4 azul.
        _EXT_MIDIA = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp",
                      ".mp4", ".webm", ".mov", ".m4v", ".ogv")

        def _eh_arquivo_midia(u: str) -> bool:
            if not u:
                return False
            if u.startswith("data:") or u.startswith("file:"):
                return True
            caminho = u.split("?", 1)[0].split("#", 1)[0].lower()
            return caminho.endswith(_EXT_MIDIA)

        ruins = [(i, u) for i, u in enumerate(imagens) if not _eh_arquivo_midia(u)]
        if ruins:
            i, u = ruins[0]
            raise RuntimeError(
                f"Mídia da cena {i + 1} não é um arquivo direto ({u[:80]}...). "
                "Isso quebrava o render silenciosamente (vídeo azul). "
                "Refaça a busca na etapa 05 com o backend atualizado."
            )

        # ⚠️ NOVO (22/09/2026): legendas com os TEMPOS REAIS da transcrição
        # (Whisper, etapa 03) quando o frontend as envia. Sem elas, cai no
        # comportamento antigo (SRT dividindo a letra em blocos iguais).
        legendas_custom = [
            {"inicio": float(l.get("inicio", 0)), "fim": float(l.get("fim", 0)), "texto": str(l.get("texto", ""))}
            for l in (payload.subtitle_lines or [])
            if isinstance(l, dict) and str(l.get("texto", "")).strip()
        ]

        saida = engine.generate(
            lyrics=payload.project.lyrics,
            description=payload.project.description,
            title=payload.project.title,
            artist=payload.project.artist,
            music_prompt=payload.project.music_prompt,
            images=imagens,
            efeitos=efeitos,
            format=payload.project.format,
            duration_beat=payload.project.duration_beat,
            output=str(CLIPS_DIR / f"{job_id}.mp4"),
            audio_path=trilha,
            legenda_estilo=payload.project.legenda_estilo,
            legendas=legendas_custom,
        )

        if not saida:
            raise RuntimeError(
                "O engine não gerou nenhum vídeo. Causa provável: sem beats "
                "(informe letra ou descrição)."
            )

        arquivo_saida = Path(saida)
        if not arquivo_saida.is_file() or arquivo_saida.stat().st_size == 0:
            raise RuntimeError("O engine terminou sem produzir um arquivo MP4 válido.")

        job["resultado"] = {
            "output_path": str(arquivo_saida),
            "download_url": f"/static/output/clipes/{arquivo_saida.name}",
        }
        job["status"] = "done"
        _evt("done", {"output": str(saida)})

    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)
        _evt("error", {"message": str(e)})


@app.post("/api/jobs/gerar", tags=["jobs"])
def iniciar_geracao(payload: GeneratePayload) -> dict[str, Any]:
    """Cria um job assíncrono de geração. Acompanhe via /ws/jobs/{job_id}."""
    if not _BACKBONE_IMPORTED:
        raise HTTPException(500, detail=f"Backbone não carregado: {_BACKBONE_ERROR}")
    job_id = uuid.uuid4().hex[:12]
    _jobs[job_id] = {
        "id": job_id,
        "status": "queued",
        "progress": 0,
        "events": [],
        "created_at": time.time(),
    }
    t = threading.Thread(target=_run_generation_sync, args=(job_id, payload), daemon=True)
    t.start()
    return {"ok": True, "job_id": job_id}


@app.get("/api/jobs/{job_id}", tags=["jobs"])
def get_job(job_id: str) -> dict[str, Any]:
    if job_id not in _jobs:
        raise HTTPException(404, detail="Job não encontrado")
    return _jobs[job_id]


@app.websocket("/ws/jobs/{job_id}")
async def ws_job(websocket: WebSocket, job_id: str):
    await websocket.accept()
    if job_id not in _jobs:
        await websocket.send_json({"type": "error", "message": "Job não encontrado"})
        await websocket.close()
        return
    job = _jobs[job_id]
    # Envia snapshot inicial
    await websocket.send_json({"type": "snapshot", "job": job})
    ultimo_idx = len(job["events"])
    try:
        while True:
            eventos_novos = job["events"][ultimo_idx:]
            for ev in eventos_novos:
                await websocket.send_json({"type": "event", **ev})
            ultimo_idx = len(job["events"])
            if job["status"] in ("done", "error"):
                await websocket.send_json({"type": "fim", "status": job["status"],
                                           "resultado": job.get("resultado"),
                                           "error": job.get("error")})
                break
            await asyncio.sleep(0.3)
    except WebSocketDisconnect:
        pass
