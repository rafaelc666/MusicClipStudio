"""
Montagem de clipes musicais v2.

Usa scene_engine como motor principal (novo motor):
  Beats → HTMLRenderer → VideoRenderer → Compositor → Vídeo final

Também oferece montagem via motor legado (moviepy) para compatibilidade.
"""

import sys
from pathlib import Path
from typing import Optional, Callable

sys.path.insert(0, str(Path(__file__).parent.parent))

from MusicClipStudio.config import get_config


FORMATOS_RESOLUCAO = {
    "9/16": (1080, 1920),
    "16/9": (1920, 1080),
    "3/4": (1080, 1440),
    "4/3": (1440, 1080),
    "1/1": (1080, 1080),
}


def montar_clipe(
    project: object,  # MusicClipProject ou dict com beats/lyrics
    audio_path: str,
    saida: str,
    formato: str = "9/16",
    lyrics: str = "",
    callback_log: Optional[Callable] = None,
    callback_prog: Optional[Callable] = None,
) -> str:
    """
    Monta clipe musical usando o novo motor (scene_engine).

    Args:
        project: MusicClipProject ou dict com informações do clipe
        audio_path: Caminho do áudio (trilha musical)
        saida: Caminho do vídeo de saída
        formato: Formato do vídeo
        lyrics: Letra para legendas
        callback_log: Callback de log
        callback_prog: Callback de progresso

    Returns:
        Caminho do vídeo gerado
    """
    if callback_log is None:
        callback_log = print
    if callback_prog is None:
        callback_prog = lambda x: None

    largura, altura = FORMATOS_RESOLUCAO.get(formato, (1080, 1920))

    # Se project tem beats (MusicClipProject), usar scene_engine
    if hasattr(project, "beats") and project.beats:
        return _montar_scene_engine(
            project=project,
            audio_path=audio_path,
            saida=saida,
            formato=formato,
            largura=largura,
            altura=altura,
            lyrics=lyrics,
            callback_log=callback_log,
            callback_prog=callback_prog,
        )

    # Fallback: montagem simples com áudio + legenda
    return _montar_simples(
        audio_path=audio_path,
        saida=saida,
        formato=formato,
        lyrics=lyrics,
        largura=largura,
        altura=altura,
        callback_log=callback_log,
        callback_prog=callback_prog,
    )


def _montar_scene_engine(
    project,
    audio_path: str,
    saida: str,
    formato: str,
    largura: int,
    altura: int,
    lyrics: str,
    callback_log,
    callback_prog,
) -> str:
    """Montagem usando scene_engine (novo motor)."""
    callback_log("[MONTAR] Montando via scene_engine...")

    from MusicClipStudio.scene_engine.renderers.html_renderer import HTMLRenderer
    from MusicClipStudio.scene_engine.renderers.video_renderer import VideoRenderer
    from MusicClipStudio.scene_engine.compositor import Compositor
    from MusicClipStudio.scene_engine.pipeline import VoxPipeline
    from MusicClipStudio.scene_engine.scene_types import Beat, VisualElement, SceneStyle

    temp_dir = Path(get_config().base_dir) / "gerador_clipes_musicais" / "output" / "_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Criar pipeline
    pipeline = VoxPipeline(
        project_dir=Path(get_config().output_path) / project.project_id if hasattr(project, "project_id") else temp_dir / "pipeline",
        width=largura,
        height=altura,
        fps=project.fps if hasattr(project, "fps") else 24,
        style=SceneStyle.VOX_EDITORIAL,
    )

    # Converter beats
    scene_beats = []
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
        )
        scene_beats.append(Beat(
            id=mb.id,
            type=mb.type,
            duration=mb.duration,
            script=mb.script,
            visual=visual,
        ))

    # Renderizar preview HTML
    html_path = pipeline.render_preview(scene_beats, "composition.html")

    # Renderizar vídeo
    duracao_total = sum(b.duration for b in scene_beats)
    video_path = pipeline.render_video(
        beats=scene_beats,
        output_name="video.mp4",
        audio_path=audio_path if Path(audio_path).exists() else None,
    )

    # Legendas
    if lyrics:
        from MusicClipStudio.legendas import gerar_srt_letras
        srt_path = str(video_path).replace(".mp4", ".srt")
        gerar_srt_letras(lyrics, srt_path, duracao_total)

        caminho_final = str(video_path).replace(".mp4", "_legendado.mp4")
        compositor = Compositor(output_dir=Path(get_config().output_path))
        compositor.add_subtitles(video_path, srt_path, caminho_final)
        video_path = caminho_final

    callback_log(f"[OK] Clip montado: {video_path}")
    return video_path


def _montar_simples(
    audio_path: str,
    saida: str,
    formato: str,
    lyrics: str,
    largura: int,
    altura: int,
    callback_log,
    callback_prog,
) -> str:
    """Montagem simples: imagem preta + áudio + legenda."""
    from moviepy import ImageClip
    import numpy as np

    duracao_estimada = 30

    # Imagem de fundo preta com texto "Musica"
    img = np.zeros((altura, largura, 3), dtype=np.uint8)
    img[:, :] = [20, 20, 30]

    from moviepy import AudioFileClip
    audio = AudioFileClip(audio_path)
    duracao_estimada = audio.duration or 30

    clip = ImageClip(img).set_duration(duracao_estimada).resize((largura, altura))
    clip = clip.set_audio(audio)

    if lyrics:
        from MusicClipStudio.legendas import gerar_srt_letras
        srt_path = str(Path(saida).with_suffix(".srt"))
        gerar_srt_letras(lyrics, srt_path, duracao_estimada)

    clip.write_videofile(saida, fps=30, codec="libx264", audio_codec="aac", preset="medium")
    return saida