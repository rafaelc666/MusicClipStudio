"""
Schema para clipes musicais.

Define beats visuais derivados de letras/descrição da música.
Usa os tipos do scene_engine (Beat, VisualElement) para compatibilidade.
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field, field, fields
from enum import Enum
from typing import Optional

FPS = 24
WIDTH = 1920
HEIGHT = 1080


class ClipComponentType(str, Enum):
    """Tipos de componentes visuais para clipes musicais."""
    KINETIC_TITLE = "kinetic_title"
    PARALLAX_IMAGE = "parallax_image"
    LOWER_THIRD = "lower_third"
    SUBTITLE_BURN = "subtitle_burn"
    HIGHLIGHT_SWIPE = "highlight_sweep"
    ANNOTATED_MAP = "annotated_map"
    CALLOUT_LINE = "callout_line"
    GRAIN_OVERLAY = "grain_overlay"
    VIDEO_BACKGROUND = "video_background"
    PHOTO_MOSAIC = "photo_mosaic"


class ClipBeatType(str, Enum):
    """Tipos de beats para clipes musicais."""
    HOOK = "hook"
    VERSE = "verse"
    CHORUS = "chorus"
    BRIDGE = "bridge"
    OUTRO = "outro"
    INSTRUMENTAL = "instrumental"


@dataclass
class MusicVisualElement:
    """Elemento visual para clipe musical."""
    type: str                          # ClipComponentType
    text: Optional[str] = None         # Texto/legenda
    images: list[str] = field(default_factory=list)  # Caminhos de imagens
    videos: list[str] = field(default_factory=list)  # Caminhos de vídeos
    accent_color: str = "#FFCC00"
    bg_color: Optional[str] = None
    animation: str = "fade_in"
    speaker_name: Optional[str] = None
    speaker_title: Optional[str] = None
    x: float = 0
    y: float = 0
    width: float = 100
    height: float = 100
    photo_query: Optional[str] = None  # Query para banco de fotos


@dataclass
class MusicBeat:
    """Beat para clipe musical."""
    id: int
    type: str                          # ClipBeatType
    duration: float
    script: str                        # Trecho da letra / descrição
    visual: MusicVisualElement
    lyrics_line: str = ""              # Linha de letra para este beat
    photo_sources: list[str] = field(default_factory=list)  # Fontes de imagens
    is_instrumental: bool = False


@dataclass
class MusicClipProject:
    """Projeto de clipe musical completo."""
    project_id: str = ""
    title: str = ""
    artist: str = ""
    lyrics: str = ""
    description: str = ""
    music_prompt: str = ""
    beats: list[MusicBeat] = field(default_factory=list)
    style: str = "vox_editorial"
    format: str = "9/16"
    fps: int = FPS
    width: int = WIDTH
    height: int = HEIGHT
    accent_color: str = "#FFCC00"
    bg_color: str = "#1A1A2E"
    output_path: str = ""
    created_at: str = ""


def letras_para_beats(
    lyrics: str,
    duration_estimada: float = 5.0,
    max_palavras: int = 12,
) -> list[MusicBeat]:
    """
    Converte letra de música em beats visuais.

    Cada verso/refrão vira um beat com tipo apropriado:
    - Verso → parallax_image ou kinetic_title
    - Refrão → highlight_sweep ou kinetic_title
    - Hook → kinetic_title com destaque
    - Ponte → lower_third

    Args:
        lyrics: Letra completa da música
        duration_estimada: Duração estimada por beat
        max_palavras: Máximo de palavras por beat

    Returns:
        Lista de MusicBeat
    """
    if not lyrics or not lyrics.strip():
        return []

    linhas = [l.strip() for l in lyrics.split("\n") if l.strip()]
    if not linhas:
        return []

    beats = []
    beat_id = 0
    current_line = []
    current_words = 0
    current_type = ClipBeatType.VERSE

    for linha in linhas:
        palavras = linha.split()
        num_palavras = len(palavras)

        if is_chorus_line(linha):
            current_type = ClipBeatType.CHORUS
        elif is_hook_line(linha):
            current_type = ClipBeatType.HOOK
        elif is_bridge_line(linha):
            current_type = ClipBeatType.BRIDGE
        elif is_outro_line(linha):
            current_type = ClipBeatType.OUTRO

        if current_words + num_palavras > max_palavras and current_line:
            beat_id += 1
            texto = " ".join(current_line)
            visual = _criar_visual(texto, current_type)
            beats.append(MusicBeat(
                id=beat_id,
                type=current_type.value,
                duration=duration_estimada,
                script=texto,
                visual=visual,
                lyrics_line=texto,
            ))
            current_line = []
            current_words = 0

        current_line.append(linha)
        current_words += num_palavras

    if current_line:
        beat_id += 1
        texto = " ".join(current_line)
        visual = _criar_visual(texto, current_type)
        beats.append(MusicBeat(
            id=beat_id,
            type=current_type.value,
            duration=duration_estimada,
            script=texto,
            visual=visual,
            lyrics_line=texto,
        ))

    return beats


def descricao_para_beats(
    description: str,
    duration_estimada: float = 5.0,
) -> list[MusicBeat]:
    """
    Converte descrição/explicação do clipe em beats visuais.

    Útil quando o usuário explica o conceito do clipe em vez de fornecer letras.
    """
    if not description or not description.strip():
        return []

    frases = re.split(r'[.!?]+', description)
    frases = [f.strip() for f in frases if f.strip()]

    beats = []
    for i, frase in enumerate(frases, 1):
        visual = MusicVisualElement(
            type=ClipComponentType.KINETIC_TITLE.value,
            text=frase[:200],
            accent_color="#FFCC00",
            animation="fade_in",
        )
        beats.append(MusicBeat(
            id=i,
            type=ClipBeatType.VERSE.value,
            duration=duration_estimada,
            script=frase,
            visual=visual,
        ))

    return beats


def project_from_lyrics(
    lyrics: str,
    title: str = "",
    artist: str = "",
    music_prompt: str = "",
    description: str = "",
    format: str = "9/16",
    duration_beat: float = 5.0,
) -> MusicClipProject:
    """
    Cria um projeto de clipe completo a partir de letras.

    Verso principal: apenas letras → kinetic_title / parallax_image
    Se description fornecido → usa como contexto visual adicional
    """
    import datetime

    beats = []

    if lyrics.strip():
        beats = letras_para_beats(lyrics, duration_estimada=duration_beat)
    elif description.strip():
        beats = descricao_para_beats(description, duration_estimada=duration_beat)

    accent = "#FFCC00"
    bg = "#1A1A2E"

    for i, beat in enumerate(beats):
        beat.visual.accent_color = accent
        if not beat.visual.bg_color:
            beat.visual.bg_color = bg
        if beat.type == ClipBeatType.CHORUS.value:
            beat.visual.animation = "highlight_sweep"
        elif beat.type == ClipBeatType.HOOK.value:
            beat.visual.type = ClipComponentType.HIGHLIGHT_SWIPE.value

    project = MusicClipProject(
        project_id=f"clip_{int(datetime.datetime.now().timestamp())}",
        title=title,
        artist=artist,
        lyrics=lyrics,
        description=description,
        music_prompt=music_prompt,
        beats=beats,
        style="vox_editorial",
        format=format,
        accent_color=accent,
        bg_color=bg,
    )

    return project


def is_chorus_line(text: str) -> bool:
    """Detecta se uma linha é refrão."""
    chorus_markers = ["refrão", "chorus", "pré-refrão", "pré", "pré-ref"]
    text_lower = text.lower()
    return any(m in text_lower for m in chorus_markers)


def is_hook_line(text: str) -> bool:
    """Detecta se uma linha é hook."""
    hook_markers = ["hook", "gancho", "destaque"]
    return any(m in text.lower() for m in hook_markers)


def is_bridge_line(text: str) -> bool:
    """Detecta se uma linha é ponte/bridge."""
    bridge_markers = ["ponte", "bridge", "interlúdio", "interlude"]
    return any(m in text.lower() for m in bridge_markers)


def is_outro_line(text: str) -> bool:
    """Detecta se uma linha é final/outro."""
    outro_markers = ["outro", "final", "encerramento", "fim"]
    return any(m in text.lower() for m in outro_markers)


def _criar_visual(texto: str, beat_type: ClipBeatType) -> MusicVisualElement:
    """Cria elemento visual baseado no tipo de beat."""
    if beat_type in (ClipBeatType.CHORUS, ClipBeatType.HOOK):
        return MusicVisualElement(
            type=ClipComponentType.HIGHLIGHT_SWIPE.value,
            text=texto,
            accent_color="#FFCC00",
            animation="highlight_in",
        )
    elif beat_type == ClipBeatType.BRIDGE:
        return MusicVisualElement(
            type=ClipComponentType.LOWER_THIRD.value,
            text=texto,
            accent_color="#00E5FF",
            animation="slide_in",
        )
    elif beat_type == ClipBeatType.OUTRO:
        return MusicVisualElement(
            type=ClipComponentType.KINETIC_TITLE.value,
            text=texto,
            accent_color="#E94560",
            animation="fade_out",
        )
    else:
        return MusicVisualElement(
            type=ClipComponentType.KINETIC_TITLE.value,
            text=texto,
            accent_color="#FFCC00",
            animation="fade_in",
        )


def project_to_scene_beats(project: MusicClipProject) -> list:
    """
    Converte MusicBeat → Beat (scene_engine compatível).

    Para integração com scene_engine.pipeline.VoxPipeline.
    """
    from MusicClipStudio.scene_engine.scene_types import Beat, VisualElement, SceneStyle

    beats = []
    for mb in project.beats:
        visual = VisualElement(
            type=mb.visual.type,
            text=mb.visual.text,
            images=mb.visual.images,
            accent_color=mb.visual.accent_color,
            bg_color=mb.visual.bg_color,
            animation=mb.visual.animation,
            speaker_name=mb.visual.speaker_name,
            speaker_title=mb.visual.speaker_title,
            x=mb.visual.x,
            y=mb.visual.y,
            width=mb.visual.width,
            height=mb.visual.height,
        )
        beats.append(Beat(
            id=mb.id,
            type=mb.type,
            duration=mb.duration,
            script=mb.script,
            visual=visual,
        ))

    return beats