"""
Integração com o Gerador de Vídeos principal.

Pontes para que o gerador principal possa delegar geração
de clipes musicais a este módulo, e vice-versa.
"""

import sys
from pathlib import Path
from typing import Optional, Callable

sys.path.insert(0, str(Path(__file__).parent.parent))


def integrar_clipe_audio(
    audio_path: str,
    imagens: list[str],
    saida: str,
    formato: str = "9/16",
    lyrics: str = "",
    callback_log: Optional[Callable] = None,
    callback_prog: Optional[Callable] = None,
) -> Optional[str]:
    """
    Ponto de entrada: gera clipe a partir de áudio + imagens.

    Se audio_path é válido, usa ele. Caso contrário, gera nova trilha.
    """
    from MusicClipStudio.pipeline import MusicClipPipeline

    pipeline = MusicClipPipeline()

    if not audio_path or not Path(audio_path).exists():
        job = pipeline.criar_job(
            description=lyrics or "",
            music_prompt="epic cinematic music",
            images=imagens,
            duracao=30,
            formato=formato,
        )
        resultado = pipeline.executar(job)
        return str(resultado) if resultado else None

    # Tem áudio válido
    from MusicClipStudio.montar import montar_clipe
    from MusicClipStudio.schema import project_from_lyrics

    project = project_from_lyrics(
        lyrics=lyrics or "",
        description="",
    )

    resultado = montar_clipe(
        project=project,
        audio_path=audio_path,
        saida=saida,
        formato=formato,
        lyrics=lyrics,
        callback_log=callback_log or print,
        callback_prog=callback_prog or (lambda x: None),
    )
    return resultado


def integrar_narracao_clipe(
    texto_narracao: str,
    imagens: list[str],
    saida: str,
    formato: str = "9/16",
) -> Optional[str]:
    """
    Gera clipe com texto sobre imagens (estilo lyric video).

    O texto aparece como legenda/lyrics no vídeo.
    """
    from MusicClipStudio.engine import MusicClipEngine

    engine = MusicClipEngine()
    return engine.generate(
        lyrics=texto_narracao,
        images=imagens,
        duracao=30,
        formato=formato,
        saida=saida,
    )


def integrar_trocar_audio(
    video_path: str,
    novo_audio: str,
    saida: Optional[str] = None,
) -> str:
    """
    Troca o áudio de um vídeo existente (remix).

    Útil para mudar a trilha musical de um clipe já editado.
    """
    import subprocess

    saida = saida or str(Path(video_path).with_name(Path(video_path).stem + "_remix.mp4"))
    cmd = [
        "ffmpeg", "-y", "-i", video_path, "-i", novo_audio,
        "-c:v", "copy", "-c:a", "aac", "-shortest",
        saida,
    ]
    subprocess.run(cmd, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    return saida


def integrar_listar_capacidades() -> dict:
    """Lista capacidades de integração."""
    return {
        "entradas": [
            "audio_path + imagens → clipe musical",
            "texto/letra + imagens → lyric video",
            "video + novo_audio → remix",
        ],
        "saidas": [
            "Vídeo MP4 com áudio musical",
            "Legendas SRT opcionais",
            "Thumbnails PNG",
        ],
        "integracoes": [
            "scene_engine: HTML → Vídeo (novo motor)",
            "ACE-Step: Trilhas sonoras",
            "StockDatabase: Fotos/vídeos gratuitos",
            "ClipAgent: Direção visual IA",
        ],
    }