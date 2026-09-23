# -*- coding: utf-8 -*-
"""
Worker de subprocess para engines TTS pesados (XTTS).

Este script é chamado via subprocess pelo Python principal quando os pacotes
TTS não estão disponíveis no ambiente atual. Ele roda dentro do venv que já
possui as dependências instaladas (ex: D:\GeradorAudio\venv).

Uso:
    python tts_worker.py "<json_args>"

O JSON deve conter:
    engine: "xtts"
    text: str
    voice_ref: str | None
    output_path: str
    mode: "single" | "clone" | "multi"
    language: str
    speed: float
    pause_between: float
"""

import sys
import os
import json
from pathlib import Path

# Garante que o core seja importável dentro do venv
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from core.narration import NarrationEngine, NarrationModeEnum


def main() -> int:
    if len(sys.argv) < 2:
        print("ERRO: argumentos JSON ausentes", file=sys.stderr)
        return 2

    try:
        args = json.loads(sys.argv[1])
    except Exception as exc:
        print(f"ERRO: JSON inválido: {exc}", file=sys.stderr)
        return 2

    engine_name = args.get("engine", "xtts")
    text = args.get("text", "")
    voice_ref = args.get("voice_ref")
    output_path = args.get("output_path")
    mode = args.get("mode", "single")
    language = args.get("language", "pt_BR")
    speaker = args.get("speaker", "Vivian")

    if not output_path:
        print("ERRO: output_path obrigatório", file=sys.stderr)
        return 2

    try:
        engine = NarrationEngine.get_engine(engine_name)
        engine.generate(
            text=text,
            voice_ref=voice_ref,
            output=Path(output_path),
            mode=mode,
            speaker=speaker,
            language=language,
        )
        print(f"OK:{output_path}")
        return 0
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
