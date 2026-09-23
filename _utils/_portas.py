"""
FONTE ÚNICA DA VERDADE das portas do MusicClipStudio.

Por que existe: o projeto brigava com outras coisas na máquina nas portas
3000/8000 (padrão que TODO projeto Next/FastAPI pega). O usuário reclamou
disso muitas vezes. Solução: portas dedicadas, registradas aqui e nos `.bat`.

    frontend (Next.js)  ->  3100
    backend  (FastAPI)  ->  8300

⚠️ Se mudar aqui, mudar TAMBÉM:
    - musicclipstudio-landing/package.json        (scripts dev/start)
    - musicclipstudio-landing/next.config.ts      (BACKEND_INTERNAL_URL)
    - musicclipstudio-landing/.env.local
    - backend/app/main.py                         (CORS allow_origins)
    - INICIAR_MusicClipStudio.bat / PARAR_... / RUN_WEB.bat
    - _Atalhos/*                                  (URL do atalho da Desktop)

Uso:
    python _utils/_portas.py            # mostra o mapa e quem está nas portas
"""

PORT_FRONT = 3100
PORT_BACK = 8300

URL_FRONT = f"http://127.0.0.1:{PORT_FRONT}"
URL_BACK = f"http://127.0.0.1:{PORT_BACK}"
URL_STUDIO = f"{URL_FRONT}/studio"


def main() -> None:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _check_ports import get_tcp_listeners, process_name

    listeners = get_tcp_listeners()
    print("=" * 62)
    print("  MusicClipStudio · MAPA DE PORTAS")
    print("=" * 62)
    print(f"  frontend (Next)   :{PORT_FRONT}")
    print(f"  backend  (FastAPI):{PORT_BACK}")
    print(f"  Studio            : {URL_STUDIO}")
    print("-" * 62)
    for nome, porta in (("frontend", PORT_FRONT), ("backend", PORT_BACK)):
        pid = listeners.get(porta)
        if pid is None:
            print(f"  [ LIVRE  ] :{porta:<5} {nome}")
        else:
            print(f"  [OCUPADA] :{porta:<5} {nome}  <- {process_name(pid)}")
    print("=" * 62)


if __name__ == "__main__":
    main()
