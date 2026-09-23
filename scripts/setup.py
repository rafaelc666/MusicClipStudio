"""
Setup e dependências para Gerador de Clipes Musicais v2.
"""

import subprocess
import sys
from pathlib import Path


def instalar_dependencias():
    pacotes = [
        "moviepy",
        "Pillow",
        "numpy",
        "ace-step-engine",
    ]

    print("[SETUP] Instalando dependências...")
    for pacote in pacotes:
        print(f"   Instalando {pacote}...")
        resultado = subprocess.run(
            [sys.executable, "-m", "pip", "install", pacote],
            capture_output=True, text=True,
        )
        if resultado.returncode == 0:
            print(f"   [OK] {pacote} instalado")
        else:
            print(f"   [WARN] {pacote}: {resultado.stderr[:200]}")

    print("\n[SETUP] Instalação concluída!")


if __name__ == "__main__":
    instalar_dependencias()