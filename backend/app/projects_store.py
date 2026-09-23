"""
Persistência de projetos do MusicClipStudio (SQLite local).

Por que existe
--------------
O app web não guardava nada: fechou a aba, perdeu o projeto. O wizard mantinha
tudo em memória React (`StudioProjectState` no `StudioClientShell.tsx`).

Decisão de arquitetura (19/09/2026): **SQLite local, sem API externa.**
O produto (§14 de STATUS_MIGRACAO_WEB.md) roda na máquina do usuário, recebe
a música pronta e monta o clipe. Não há multiusuário, não há hospedagem —
então Postgres/Supabase/Firebase seriam complexidade sem retorno.

O que NÃO é
-----------
- Não é um ORM. É `sqlite3` da stdlib, direto.
- Não exige nenhuma chave de API, nenhum servidor, nenhuma instalação extra.
- Não substitui os 7 bancos de imagens (`database.py`) — aquilo é conteúdo
  visual; isto é o registro dos projetos do usuário.

Formato
-------
A tabela guarda o `StudioProjectState` do frontend como JSON num campo `data`,
mais algumas colunas "espelho" (id, title, created_at, updated_at) para poder
listar e ordenar sem desserializar tudo.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Optional


# ── Local do banco ──────────────────────────────────────────────────────
# Fica junto do output do app, não em ~/. Assim o "projeto" viaja com a pasta
# do MusicClipStudio (fácil de fazer backup: copiar output/).
def _default_db_path(base_dir: Path) -> Path:
    d = Path(base_dir) / "output"
    d.mkdir(parents=True, exist_ok=True)
    return d / "projetos.db"


class ProjectsStore:
    """CRUD de projetos em SQLite. Thread-safe (o backend FastAPI é multithread)."""

    def __init__(self, db_path: Optional[Path | str] = None, base_dir: Optional[Path] = None):
        if db_path is None:
            if base_dir is None:
                base_dir = Path(__file__).resolve().parent.parent.parent
            db_path = _default_db_path(Path(base_dir))
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # FastAPI roda handlers em threadpool; sqlite3 não gosta de ser
        # compartilhado entre threads sem cuidado. Um lock simples resolve,
        # e check_same_thread=False permite a conexão única.
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._criar_schema()

    # ── schema ──────────────────────────────────────────────────────────

    def _criar_schema(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id          TEXT PRIMARY KEY,
                    title       TEXT NOT NULL DEFAULT '',
                    created_at  INTEGER NOT NULL,
                    updated_at  INTEGER NOT NULL,
                    status      TEXT NOT NULL DEFAULT 'rascunho',
                    data        TEXT NOT NULL
                )
                """
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_projects_updated "
                "ON projects(updated_at DESC)"
            )
            self._conn.commit()

    # ── helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _agora_ms() -> int:
        return int(time.time() * 1000)

    def _row_para_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        """Reconstrói o projeto a partir da linha.

        O `data` é a fonte da verdade (é o que o frontend enviou). As colunas
        espelho só entram como fallback, caso o JSON venha incompleto.
        """
        try:
            projeto = json.loads(row["data"])
        except (json.JSONDecodeError, TypeError):
            projeto = {}
        if not isinstance(projeto, dict):
            projeto = {}

        projeto.setdefault("id", row["id"])
        projeto.setdefault("title", row["title"])
        projeto.setdefault("createdAt", row["created_at"])
        # metadados úteis para a lista, não fazem parte do estado original
        projeto["updatedAt"] = row["updated_at"]
        projeto["status"] = row["status"]
        return projeto

    # ── CRUD ────────────────────────────────────────────────────────────

    def listar(self, limite: int = 50) -> list[dict[str, Any]]:
        """Lista projetos, mais recentes primeiro."""
        with self._lock:
            cur = self._conn.execute(
                "SELECT * FROM projects ORDER BY updated_at DESC LIMIT ?",
                (int(limite),),
            )
            return [self._row_para_dict(r) for r in cur.fetchall()]

    def obter(self, project_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            )
            row = cur.fetchone()
        return self._row_para_dict(row) if row else None

    def salvar(self, projeto: dict[str, Any]) -> dict[str, Any]:
        """Cria ou atualiza (upsert) um projeto.

        Se não vier `id`, gera um. Devolve o projeto como ficou gravado.
        """
        if not isinstance(projeto, dict):
            raise ValueError("projeto deve ser um dict")

        dados = dict(projeto)
        pid = str(dados.get("id") or "").strip()
        if not pid:
            pid = "proj_" + uuid.uuid4().hex[:12]
        dados["id"] = pid

        agora = self._agora_ms()
        criado = dados.get("createdAt")
        if not isinstance(criado, (int, float)) or criado <= 0:
            criado = agora
        dados["createdAt"] = int(criado)

        titulo = str(dados.get("title") or "").strip() or "Clipe sem título"
        dados["title"] = titulo
        status = str(dados.get("status") or "rascunho")

        payload = json.dumps(dados, ensure_ascii=False)

        with self._lock:
            self._conn.execute(
                """
                INSERT INTO projects (id, title, created_at, updated_at, status, data)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title      = excluded.title,
                    updated_at = excluded.updated_at,
                    status     = excluded.status,
                    data       = excluded.data
                """,
                (pid, titulo, int(criado), agora, status, payload),
            )
            self._conn.commit()

        gravado = dict(dados)
        gravado["updatedAt"] = agora
        gravado["status"] = status
        return gravado

    def apagar(self, project_id: str) -> bool:
        """Remove o projeto. Devolve True se algo foi removido."""
        with self._lock:
            cur = self._conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            self._conn.commit()
            return cur.rowcount > 0

    def contar(self) -> int:
        with self._lock:
            cur = self._conn.execute("SELECT COUNT(*) AS n FROM projects")
            return int(cur.fetchone()["n"])

    def fechar(self) -> None:
        with self._lock:
            self._conn.close()
