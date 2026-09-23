"""
Compatibilidade com Moneyprinter.

Se moneyprinter estiver instalado, fornece camadas de compatibilidade
para reutilizar seu sistema de geração de imagens/vídeos.

Moneyprinter é um projeto de IA para gerar conteúdo visual.
Este módulo permite que o gerador de clipes use seus recursos.
"""

import os
import sys
import importlib
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from MusicClipStudio.config import ClipConfig, get_config


class MoneyPrinterCompat:
    """Camada de compatibilidade com moneyprinter."""

    def __init__(self, config: Optional[ClipConfig] = None):
        self.config = config or get_config()
        self.enabled = self.config.moneyprinter_enabled
        self.path = Path(self.config.moneyprinter_path) if self.config.moneyprinter_path else None
        self._module = None

        if self.enabled and self.path and self.path.exists():
            self._init_moneyprinter()

    def _init_moneyprinter(self):
        """Tenta importar moneyprinter."""
        try:
            if self.path and str(self.path) not in sys.path:
                sys.path.insert(0, str(self.path))
            self._module = importlib.import_module("moneyprinter")
            print("[MoneyPrinter] Módulo carregado com sucesso")
        except ImportError:
            print("[MoneyPrinter] Módulo não encontrado")
            self._module = None
            self.enabled = False

    def gerar_imagem(
        self,
        prompt: str,
        width: int = 1920,
        height: int = 1080,
    ) -> Optional[str]:
        """Gera imagem usando moneyprinter."""
        if not self.enabled or not self._module:
            return None
        try:
            result = self._module.generate_image(prompt, width, height)
            return result
        except Exception as e:
            print(f"[MoneyPrinter] Erro: {e}")
            return None

    def gerar_video(
        self,
        prompt: str,
        duration: float = 5.0,
        width: int = 1920,
        height: int = 1080,
    ) -> Optional[str]:
        """Gera vídeo curto usando moneyprinter."""
        if not self.enabled or not self._module:
            return None
        try:
            result = self._module.generate_video(prompt, duration, width, height)
            return result
        except Exception as e:
            print(f"[MoneyPrinter] Erro: {e}")
            return None

    def esta_disponivel(self) -> bool:
        """Verifica se moneyprinter está disponível."""
        return self.enabled and self._module is not None

    def configurar(self, path: str):
        """Configura caminho do moneyprinter."""
        self.config.moneyprinter_path = path
        self.path = Path(path)
        if self.path.exists():
            self.enabled = True
            self._init_moneyprinter()


def encontrar_moneyprinter() -> Optional[str]:
    """Tenta encontrar instalação do moneyprinter no sistema."""
    possible_paths = [
        Path.home() / "moneyprinter",
        Path.home() / "MoneyPrinter",
        Path("C:/moneyprinter"),
        Path("D:/moneyprinter"),
        Path("C:/MoneyPrinter"),
        Path("D:/MoneyPrinter"),
        Path.home() / ".moneyprinter",
    ]

    for p in possible_paths:
        if p.exists() and (p / "moneyprinter.py").exists():
            return str(p)

    # Buscar por requirements.txt ou similar
    try:
        import subprocess
        resultado = subprocess.run(
            ["pip", "show", "moneyprinter"],
            capture_output=True, text=True,
        )
        if resultado.returncode == 0:
            location = None
            for line in resultado.stdout.split("\n"):
                if "Location:" in line:
                    location = line.split(":")[1].strip()
            if location:
                return location
    except Exception:
        pass

    return None