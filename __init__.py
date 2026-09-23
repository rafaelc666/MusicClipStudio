"""
Gerador de Clipes Musicais — Aplicativo independente.

Gera clipes musicais (lyric videos, videoclipes) usando:
  - scene_engine (novo motor): beats → HTML → Playwright → Vídeo
  - ACE-Step: geração de trilhas sonoras
  - Compositor: sobreposição de áudio e legendas

Sem narração/TTS — o áudio é exclusivamente musical.

Uso standalone:
    python -m MusicClipStudio

Uso como módulo importado:
    from gerador_clipes_musicais import MusicClipEngine, MusicClipPipeline
"""

from MusicClipStudio.config import ClipConfig, load_config, save_config, get_config
from MusicClipStudio.engine import MusicClipEngine
from MusicClipStudio.pipeline import MusicClipPipeline, ClipJob
from MusicClipStudio.montar import montar_clipe
from MusicClipStudio.audio import gerar_trilha, gerar_vocal
from MusicClipStudio.legendas import gerar_srt_letras
from MusicClipStudio.integrar import integrar_clipe_audio, integrar_narracao_clipe, integrar_trocar_audio
from MusicClipStudio.batcher import ClipBatcher, BatchConfig
from MusicClipStudio.database import StockDatabase
from MusicClipStudio.agent import ClipAgent
from MusicClipStudio.maintenance_agent import MaintenanceAgent
from MusicClipStudio.ui_config import APIConfigUI, abrir_configuracao

__all__ = [
    "ClipConfig",
    "load_config",
    "save_config",
    "get_config",
    "MusicClipEngine",
    "MusicClipPipeline",
    "ClipJob",
    "montar_clipe",
    "gerar_trilha",
    "gerar_vocal",
    "gerar_srt_letras",
    "integrar_clipe_audio",
    "integrar_narracao_clipe",
    "integrar_trocar_audio",
    "ClipBatcher",
    "BatchConfig",
    "StockDatabase",
    "MaintenanceAgent",
    "APIConfigUI",
    "abrir_configuracao",
    "ClipAgent",
]

__version__ = "2.0.0"