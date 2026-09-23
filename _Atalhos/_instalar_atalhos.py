"""
Script helper: instala os atalhos do MusicClipStudio WEB
na Área de Trabalho (Desktop) do usuário atual do Windows.

USO: python _Atalhos\_instalar_atalhos.py
"""
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTE_BAT = ROOT / "_Atalhos" / "MusicClipStudio_WEB.bat"
DESKTOP = Path.home() / "Desktop"

def main() -> int:
    print("=" * 60)
    print("   MusicClipStudio WEB · Instalar atalhos na Desktop")
    print("=" * 60)
    print(f"   Usuário.....: {os.environ.get('USERNAME', Path.home().name)}")
    print(f"   Desktop.....: {DESKTOP}")
    print(f"   Origem BAT..: {FONTE_BAT}\n")

    if not FONTE_BAT.exists():
        print(f"[ERRO] Fonte não encontrada: {FONTE_BAT}")
        return 1

    DESKTOP.mkdir(parents=True, exist_ok=True)

    # ── 1. Lançador completo (bat) ──
    dst_bat = DESKTOP / "MusicClipStudio WEB.bat"
    try:
        shutil.copy2(FONTE_BAT, dst_bat)
        print(f"✔ OK   Atalho BAT instalado: {dst_bat.name}")
    except Exception as e:
        print(f"✖ FALHA ao copiar BAT: {e}")
        return 2

    # ── 2. Atalho rápido .url (apenas abre navegador) ──
    dst_url = DESKTOP / "MusicClipStudio Studio (Web).url"
    conteudo_url = (
        "[{000214A0-0000-0000-C000-000000000046}]\r\n"
        "Prop3=19,2\r\n"
        "[InternetShortcut]\r\n"
        "URL=http://127.0.0.1:3100/studio\r\n"
        "HotKey=0\r\n"
        "IconIndex=0\r\n"
        r"IconFile=%SystemRoot%\system32\msedge.dll" + "\r\n"
    )
    try:
        dst_url.write_text(conteudo_url, encoding="utf-16-le")  # .url prefere UTF-16LE
        # Mas alguns Windows esperam ASCII; fallback ok
        if not dst_url.exists() or dst_url.stat().st_size < 10:
            dst_url.write_text(conteudo_url, encoding="ascii", errors="ignore")
        print(f"✔ OK   Atalho URL instalado: {dst_url.name}")
    except Exception as e:
        # Fallback ASCII
        try:
            dst_url.write_text(conteudo_url, encoding="ascii")
            print(f"✔ OK   Atalho URL (fallback ASCII): {dst_url.name}")
        except Exception as e2:
            print(f"⚠ AVISO  Não deu para criar .url: {e} / {e2}")

    print("\n────────────────────────────────────────────────────────")
    print("  INSTALAÇÃO CONCLUÍDA.")
    print()
    print("  Como usar:")
    print("   • Duplo clique em  MusicClipStudio WEB.bat")
    print("       → inicia backend + frontend + abre navegador")
    print()
    print("   • Se a stack já estiver rodando")
    print("       → use  MusicClipStudio Studio (Web).url")
    print("────────────────────────────────────────────────────────")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
