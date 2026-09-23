"""Le os atalhos da Desktop do MusicClipStudio (target/args/wdir).

Os .lnk foram criados a partir dos .bat do projeto. Como as portas mudaram
(3000/8000 -> 3100/8300), e' preciso conferir se algum atalho aponta para
uma URL antiga gravada literalmente.

Uso: python _utils/_ler_atalhos.py
"""
import ctypes
import os
from ctypes import wintypes
from pathlib import Path

DESKTOP = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
ALVOS = [
    "MusicClipStudio WEB.lnk",
    "Parar MusicClipStudio.lnk",
    "Diagnostico MusicClipStudio.lnk",
]


def ler_lnk(caminho: Path) -> dict:
    """Le um .lnk via IShellLink + IPersistFile (COM puro, sem pywin32)."""
    import comtypes.client  # type: ignore

    shell = comtypes.client.CreateObject("WScript.Shell")
    lnk = shell.CreateShortcut(str(caminho))
    return {
        "target": lnk.TargetPath,
        "args": lnk.Arguments,
        "wdir": lnk.WorkingDirectory,
        "icon": lnk.IconLocation,
    }


def main() -> None:
    print("=" * 66)
    print("  Atalhos da Desktop - MusicClipStudio")
    print("=" * 66)
    for alvo in ALVOS:
        p = DESKTOP / alvo
        if not p.exists():
            print(f"\n[--] {alvo}  (nao existe)")
            continue
        print(f"\n[OK] {alvo}")
        try:
            info = ler_lnk(p)
            for k, v in info.items():
                print(f"     {k:7}: {v}")
        except Exception as e:
            print(f"     (nao foi possivel ler: {e})")
    print("=" * 66)


if __name__ == "__main__":
    main()
