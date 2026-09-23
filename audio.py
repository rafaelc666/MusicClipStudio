"""
Geração de áudio para clipes musicais v2.

Wrapper ao redor do gerador_audio.gerador_trilha para criar trilhas
sonoras otimizadas para clipes musicais.

NÃO gera narração/TTS — o áudio é exclusivamente musical.
"""

import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from MusicClipStudio.config import get_config


PRESETS_CLIP = [
    ("Hino Épico", "epic cinematic orchestral music, powerful, dramatic, no vocals, motivational"),
    ("Lo-fi Chill", "lo-fi hip hop beat, chill, relaxing, soft piano, no vocals"),
    ("Trap Eletrônico", "trap beat, electronic, modern, 808 bass, no vocals"),
    ("Ambiente Cinematográfico", "ambient cinematic soundtrack, atmospheric, deep bass, no vocals"),
    ("Pop Motivacional", "upbeat pop music, motivational, energetic, no vocals"),
    ("Rock Alternativo", "alternative rock, energetic, guitar driven, no vocals"),
    ("R&B Suave", "smooth r&b, soulful, mellow, no vocals"),
    ("EDM Festival", "edm festival anthem, euphoric, drops, no vocals"),
    ("Rap Instrumental", "hip hop instrumental, boom bap, hard-hitting, no vocals"),
    ("MPB Nostálgica", "brazilian mpb, nostalgic, acoustic, warm, no vocals"),
]

PRESETS_NARRACAO_REFERENCIA = [
    ("Narração Documentário", "deep calm narrator voice, documentary style, authoritative"),
    ("Narração YouTube", "energetic narrator voice, youtube style, engaging, enthusiastic"),
    ("Narração ASMR", "whisper voice, ASMR, soft, intimate, close mic"),
    ("Narração Infantil", "friendly narrator voice, children's content, warm, playful"),
    ("Narração Jovem", "young dynamic narrator voice, tiktok style, energetic"),
]

# Alias para compatibilidade com código existente e testes
PRESETS_NARRACAO = PRESETS_NARRACAO_REFERENCIA


def gerar_trilha(
    prompt: str,
    duracao: int = 30,
    steps: int = 8,
    cfg: float = 7.0,
    seed: int = -1,
    nome: str = "",
    pasta_saida: Optional[str] = None,
) -> Optional[str]:
    """
    Gera uma trilha musical para clipe via ACE-Step.

    Returns:
        Caminho do arquivo WAV gerado ou None
    """
    try:
        import ace_step_engine as ace
    except ImportError:
        print("[gerar_audio] ERRO: ace_step_engine não encontrado")
        return None

    if not nome:
        nome = f"trilha_{int(time.time())}.wav"

    pasta = Path(pasta_saida) if pasta_saida else Path(__file__).parent / "output" / "audio"
    pasta.mkdir(parents=True, exist_ok=True)

    resultado = ace.gerar_trilha(
        prompt=prompt,
        nome_arquivo=nome,
        duration=duracao,
        steps=steps,
        cfg=cfg,
        seed=seed,
    )

    if resultado.get("success"):
        return resultado.get("output")
    return None


def gerar_vocal(
    texto: str,
    voz: str = "razo",
    estilo: str = "youtube",
    nome: str = "",
) -> Optional[str]:
    """
    Gera vocal com o texto fornecido (experimental, para faixas vocais).

    Diferente de narração — gera performance vocal sobre texto.
    """
    try:
        from MusicClipStudio.core.tts_worker import TTSWorker
    except ImportError:
        print("[gerar_audio] ERRO: TTS worker não encontrado")
        return None

    if not nome:
        nome = f"vocal_{int(time.time())}.wav"

    worker = TTSWorker()
    try:
        worker.save_wav(texto, nome, engine="piper")
        return nome
    except Exception as e:
        print(f"[gerar_audio] ERRO ao gerar vocal: {e}")
        return None


def listar_presets() -> dict:
    """Retorna presets organizados por categoria."""
    return {
        "trilhas": PRESETS_CLIP,
        "narracao": PRESETS_NARRACAO,
    }