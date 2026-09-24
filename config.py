"""
Configuração do Gerador de Clipes Musicais v2.

Adiciona campos para:
  - Letras da música (obrigatório para gerar beats visuais)
  - Banco de dados de mídia gratuita
  - Integração com moneyprinter
  - Agente de direção de imagens
"""

import json
import os
import sys
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field


def _env_chave(nome: str) -> str:
    """Lê uma chave de API da variável de ambiente (default vazio).

    SEGURANÇA (21/09/2026): as chaves NÃO vivem mais no código-fonte.
    Cada pessoa que usar o projeto configura a própria chave por:

      1. Variável de ambiente (ex.: export STOCK_PEXELS_API_KEY=...)
      2. Arquivo .env na raiz do projeto (ver .env.example)
      3. Botão "APIs" do app (salva em ~/.gerador_clipes_config.json)

    A config salva no ~/.gerador_clipes_config.json sobrescreve o que
    vier do ambiente — ordem: arquivo do usuário > env > vazio.
    """
    return os.getenv(nome, "").strip()


def _carregar_env_projeto() -> None:
    """Carrega o .env da raiz do projeto (se existir) para o ambiente.

    Parser mínimo, sem dependências: ignora linhas vazias e comentários,
    aceita valores entre aspas e NUNCA sobrescreve variável já exportada
    no shell (o que veio do ambiente tem prioridade sobre o .env).
    """
    arquivo = Path(__file__).parent / ".env"
    if not arquivo.exists():
        return
    try:
        for linha in arquivo.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, _, valor = linha.partition("=")
            chave = chave.strip()
            valor = valor.strip().strip('"').strip("'")
            if chave and chave not in os.environ:
                os.environ[chave] = valor
    except OSError:
        pass


_carregar_env_projeto()


@dataclass
class ClipConfig:
    """Configuração do gerador de clipes musicais v2."""

    # ── Diretórios ─────────────────────────────────────────
    base_dir: str = ""
    output_dir: str = ""
    thumbnails_dir: str = ""
    templates_dir: str = ""
    database_dir: str = ""

    # ── Conteúdo obrigatório ───────────────────────────────
    lyrics: str = ""                          # Letra da música (obrigatória para clipe)
    description: str = ""                     # Descrição/explicação do clipe (alternativa à letra)

    # ── Áudio ──────────────────────────────────────────────
    default_audio_format: str = "9/16"
    default_audio_fps: int = 30
    default_music_prompt: str = "epic cinematic orchestral music, powerful, dramatic, no vocals"
    default_music_duration: int = 30
    default_music_steps: int = 8
    default_music_cfg: float = 7.0
    default_music_seed: int = -1

    # ── Vídeo ──────────────────────────────────────────────
    default_video_format: str = "9/16"
    default_video_fps: int = 30
    default_effect: str = "zoom_in"
    default_transition: str = "fade"

    # ── Visual ─────────────────────────────────────────────
    default_accent_color: str = "#FFCC00"
    default_bg_color: str = "#1A1A2E"
    default_style: str = "vox_editorial"

    # ── Legendas ───────────────────────────────────────────
    lyrics_active: bool = True
    lyrics_position: str = "bottom"
    lyrics_color: str = "#FFFFFF"
    lyrics_font_size: int = 48
    lyrics_max_words: int = 4
    lyrics_font: str = "Montserrat"

    # ── Banco de dados de mídia gratuita ───────────────────
    stock_api_key: str = ""                    # Chave API (compatibilidade)
    stock_pexels_api_key: str = _env_chave("STOCK_PEXELS_API_KEY")
    stock_pixabay_api_key: str = _env_chave("STOCK_PIXABAY_API_KEY")
    stock_unsplash_api_key: str = _env_chave("STOCK_UNSPLASH_API_KEY")
    stock_provider: str = "pexels"             # pexels, pixabay, unsplash
    stock_max_results: int = 20
    stock_category: str = "music"
    stock_search_query: str = ""
    stock_pexels_enabled: bool = True
    stock_pixabay_enabled: bool = True
    stock_unsplash_enabled: bool = True
    stock_pixabay_videos: bool = True          # Buscar vídeos também no Pixabay
    stock_nasa_api_key: str = _env_chave("STOCK_NASA_API_KEY")
    stock_nasa_enabled: bool = True
    stock_coverr_api_key: str = _env_chave("STOCK_COVERR_API_KEY")
    stock_coverr_app_id: str = _env_chave("STOCK_COVERR_APP_ID")
    stock_coverr_enabled: bool = True
    stock_giphy_api_key: str = _env_chave("STOCK_GIPHY_API_KEY")
    stock_giphy_enabled: bool = True
    stock_openverse_api_key: str = _env_chave("STOCK_OPENVERSE_API_KEY")
    stock_openverse_enabled: bool = True
    # ⚠️ NOVO (23/09/2026): URLs de API por banco (JSON {"pexels": "https://..."}).
    # Vazio = usa as URLs oficiais. Permite endpoint próprio/proxy por banco —
    # definido pelo usuário no diálogo de chaves e injetado via
    # dataclasses.replace no request do usuário logado.
    stock_urls: str = ""

    # ── IA para busca nos bancos (⚠️ NOVO 24/09/2026) ──────────
    # Chave GENÉRICA: Google (AIza…), Groq (gsk_…), OpenRouter
    # (sk-or-…) ou qualquer OpenAI-compatible (sk-…) — o provedor é
    # detectado pelo prefixo (ver ia_busca.py). A IA não busca: só
    # traduz a intenção (letra PT → termos visuais EN, que os bancos
    # indexam melhor). Sem chave ou com erro → fluxo determinístico
    # antigo; a busca nunca quebra por causa desta chave.
    stock_ia_api_key: str = _env_chave("STOCK_IA_API_KEY")
    stock_ia_model: str = ""        # vazio = default do provedor
    stock_ia_base_url: str = ""     # só p/ OpenAI-compatible fora da lista
    stock_ia_enabled: bool = True

    # ── Agente de direção de imagens ───────────────────────
    agent_enabled: bool = True
    agent_model: str = ""                     # Modelo LLM para agente
    agent_style: str = "cinematic"
    agent_mood: str = "epic"

    # ── Moneyprinter ───────────────────────────────────────
    moneyprinter_enabled: bool = False
    moneyprinter_path: str = ""               # Caminho da instalação moneyprinter

    # Internos
    _version: int = 2
    _first_run: bool = True

    def __post_init__(self):
        base = self._detect_base_dir()

        if not self.base_dir:
            self.base_dir = str(base)
        if not self.output_dir:
            self.output_dir = str(base / "producao" / "clipes")
        if not self.thumbnails_dir:
            self.thumbnails_dir = str(base / "assets" / "thumbnails")
        if not self.templates_dir:
            self.templates_dir = str(base / "assets" / "templates")
        if not self.database_dir:
            self.database_dir = str(base / "database")

    @staticmethod
    def _detect_base_dir() -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).parent
        return Path(__file__).parent

    @property
    def output_path(self) -> Path:
        p = Path(self.output_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def thumbnails_path(self) -> Path:
        p = Path(self.thumbnails_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_dir": self.base_dir,
            "output_dir": self.output_dir,
            "thumbnails_dir": self.thumbnails_dir,
            "templates_dir": self.templates_dir,
            "database_dir": self.database_dir,
            "lyrics": self.lyrics,
            "description": self.description,
            "default_audio_format": self.default_audio_format,
            "default_audio_fps": self.default_audio_fps,
            "default_music_prompt": self.default_music_prompt,
            "default_music_duration": self.default_music_duration,
            "default_music_steps": self.default_music_steps,
            "default_music_cfg": self.default_music_cfg,
            "default_music_seed": self.default_music_seed,
            "default_video_format": self.default_video_format,
            "default_video_fps": self.default_video_fps,
            "default_effect": self.default_effect,
            "default_transition": self.default_transition,
            "default_accent_color": self.default_accent_color,
            "default_bg_color": self.default_bg_color,
            "default_style": self.default_style,
            "lyrics_active": self.lyrics_active,
            "lyrics_position": self.lyrics_position,
            "lyrics_color": self.lyrics_color,
            "lyrics_font_size": self.lyrics_font_size,
            "lyrics_max_words": self.lyrics_max_words,
            "lyrics_font": self.lyrics_font,
            "stock_api_key": self.stock_api_key,
            "stock_pexels_api_key": self.stock_pexels_api_key,
            "stock_pixabay_api_key": self.stock_pixabay_api_key,
            "stock_unsplash_api_key": self.stock_unsplash_api_key,
            "stock_provider": self.stock_provider,
            "stock_max_results": self.stock_max_results,
            "stock_category": self.stock_category,
            "stock_search_query": self.stock_search_query,
            "stock_pexels_enabled": self.stock_pexels_enabled,
            "stock_pixabay_enabled": self.stock_pixabay_enabled,
            "stock_unsplash_enabled": self.stock_unsplash_enabled,
            "stock_pixabay_videos": self.stock_pixabay_videos,
            "stock_nasa_api_key": self.stock_nasa_api_key,
            "stock_nasa_enabled": self.stock_nasa_enabled,
            "stock_coverr_api_key": self.stock_coverr_api_key,
            "stock_coverr_app_id": self.stock_coverr_app_id,
            "stock_coverr_enabled": self.stock_coverr_enabled,
            "stock_giphy_api_key": self.stock_giphy_api_key,
            "stock_giphy_enabled": self.stock_giphy_enabled,
            "stock_openverse_api_key": self.stock_openverse_api_key,
            "stock_openverse_enabled": self.stock_openverse_enabled,
            "stock_ia_api_key": self.stock_ia_api_key,
            "stock_ia_model": self.stock_ia_model,
            "stock_ia_base_url": self.stock_ia_base_url,
            "stock_ia_enabled": self.stock_ia_enabled,
            "agent_enabled": self.agent_enabled,
            "agent_model": self.agent_model,
            "agent_style": self.agent_style,
            "agent_mood": self.agent_mood,
            "moneyprinter_enabled": self.moneyprinter_enabled,
            "moneyprinter_path": self.moneyprinter_path,
            "_version": self._version,
            "_first_run": self._first_run,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClipConfig":
        known = {f.name for f in cls.__dataclass_fields__.values() if f.init}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


CLIP_CONFIG_FILE = Path.home() / ".gerador_clipes_config.json"


def load_config() -> ClipConfig:
    if CLIP_CONFIG_FILE.exists():
        try:
            with open(CLIP_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ClipConfig.from_dict(data)
        except Exception:
            pass
    return ClipConfig()


def save_config(config: ClipConfig) -> None:
    try:
        with open(CLIP_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[clip_config] Aviso: não foi possível salvar: {e}")


_config_instance: ClipConfig | None = None


def get_config() -> ClipConfig:
    global _config_instance
    if _config_instance is None:
        _config_instance = load_config()
    return _config_instance