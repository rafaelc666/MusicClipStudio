"""
ace_step_engine.py
Wrapper Python para gerar trilhas sonoras via ACE-Step 1.5.
Padrão igual ao tts_engine.py: subprocess isolado no venv do Chatterbox.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Callable

WORKER_ACE = Path(r"D:\Chatterbox_TTS\worker_ace_cli.py")
VENV_PYTHON = Path(r"D:\ACE-Step\.venv\Scripts\python.exe")

PASTA_TRILHAS = Path(__file__).resolve().parent / "output" / "trilhas"
PASTA_TRILHAS.mkdir(parents=True, exist_ok=True)


def verificar_dependencias() -> dict:
    if not VENV_PYTHON.exists():
        return {"ok": False, "erro": f"venv nao encontrado: {VENV_PYTHON}"}
    if not WORKER_ACE.exists():
        return {"ok": False, "erro": f"worker nao encontrado: {WORKER_ACE}"}
    return {"ok": True}


def gerar_trilha(
    prompt: str,
    nome_arquivo: str = "",
    duration: int = 30,
    steps: int = 8,
    cfg: float = 7.0,
    seed: int = -1,
    with_vocal: bool = False,
    lyrics: str = "",
    on_log: Optional[Callable[[str], None]] = None,
) -> dict:
    """
    Gera trilha sonora. Retorna dict com success/output/error.
    on_log: callback opcional para receber linhas de log em tempo real.
    """
    check = verificar_dependencias()
    if not check["ok"]:
        return {"success": False, "error": check["erro"]}

    if not nome_arquivo:
        nome_arquivo = f"trilha_{int(__import__('time').time())}.wav"
    if not nome_arquivo.lower().endswith(".wav"):
        nome_arquivo += ".wav"

    output_path = PASTA_TRILHAS / nome_arquivo

    cmd = [
        str(VENV_PYTHON),
        str(WORKER_ACE),
        "--prompt", prompt,
        "--output", str(output_path),
        "--duration", str(duration),
        "--steps", str(steps),
        "--cfg", str(cfg),
        "--seed", str(seed),
    ]
    if with_vocal:
        cmd.append("--with-vocal")
        if lyrics:
            cmd.extend(["--lyrics", lyrics])

    if on_log:
        on_log(f"[BATCHER-ACE] Comando: {' '.join(cmd)}")

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        stdout_lines = []
        for line in proc.stdout:
            line = line.rstrip()
            stdout_lines.append(line)
            if on_log:
                on_log(line)
        proc.wait()
        full_output = "\n".join(stdout_lines)
        if proc.returncode == 0:
            for line in reversed(stdout_lines):
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue
            return {
                "success": True,
                "output": str(output_path),
                "stdout": full_output,
            }
        else:
            return {
                "success": False,
                "error": f"Worker falhou (codigo {proc.returncode})",
                "stdout": full_output,
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def listar_trilhas() -> list:
    """Lista trilhas ja geradas."""
    if not PASTA_TRILHAS.exists():
        return []
    return sorted(
        [f.name for f in PASTA_TRILHAS.glob("*.wav")],
        key=lambda n: (PASTA_TRILHAS / n).stat().st_mtime,
        reverse=True,
    )


if __name__ == "__main__":
    print("=== ACE-Step 1.5 - Teste Rapido ===")
    check = verificar_dependencias()
    print(f"Dependencias: {check}")
    if not check["ok"]:
        sys.exit(1)

    result = gerar_trilha(
        prompt="calm ambient background music, no vocals, atmospheric",
        nome_arquivo="teste_ace.wav",
        duration=10,
        steps=8,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
