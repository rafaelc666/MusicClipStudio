"""Dispara um job real de geracao e acompanha ate o fim.

Autossuficiente: gera a musica de teste, envia pelo /api/upload/audio e so
entao dispara o job. Assim o script funciona sozinho, sem depender de um
arquivo deixado de outro teste.

Uso:
    python _utils/_teste_gerador_e2e.py

Requer o backend rodando (python -m uvicorn backend.app.main:app --port 8300).
"""
import io
import json
import math
import struct
import sys
import time
import urllib.request
import wave

BASE = "http://127.0.0.1:8300"


def _gerar_wav(segundos: float = 3.0) -> bytes:
    """Um tom simples e valido — serve como 'musica pronta' do usuario."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(44100)
        frames = bytearray()
        for i in range(int(44100 * segundos)):
            v = int(12000 * math.sin(2 * math.pi * 440 * i / 44100))
            frames += struct.pack("<hh", v, v)
        w.writeframes(bytes(frames))
    return buf.getvalue()


def _enviar_audio(wav: bytes) -> str:
    """Envia pelo endpoint real e devolve o `path` para o job."""
    b = "----MCSE2EBoundary"
    body = (
        f"--{b}\r\n"
        'Content-Disposition: form-data; name="file"; filename="musica_teste.wav"\r\n'
        "Content-Type: audio/wav\r\n\r\n"
    ).encode() + wav + f"\r\n--{b}--\r\n".encode()

    r = urllib.request.Request(
        BASE + "/api/upload/audio",
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={b}"},
    )
    with urllib.request.urlopen(r, timeout=30) as resp:
        d = json.loads(resp.read().decode())
    if not d.get("ok"):
        raise RuntimeError(f"upload falhou: {d}")
    return d["path"]


def main() -> int:
    # 0. Backend no ar?
    try:
        with urllib.request.urlopen(BASE + "/api/health", timeout=10) as resp:
            h = json.loads(resp.read().decode())
    except Exception as e:
        print(f"[ERRO] backend nao respondeu em {BASE}: {e}")
        print("       suba com: python -m uvicorn backend.app.main:app --port 8300")
        return 1
    print(f"backend ok · backbone_ready={h.get('backbone_ready')}")

    # 1. Musica de teste (gerada na hora — o script nao depende de nada externo)
    wav = _gerar_wav(3.0)
    audio_path = _enviar_audio(wav)
    print(f"musica de teste enviada · {len(wav)} bytes · path={audio_path}")
    print()

    payload = {
        "project": {
            "lyrics": (
                "Cidade a noite brilha\n"
                "O neon corta a chuva\n"
                "Eu sigo sem destino\n"
                "Procurando voce"
            ),
            "title": "Teste do Gerador",
            "description": "clipe de teste com musica enviada",
            "artist": "Teste",
            "format": "9/16",
        },
        "audio_path": audio_path,
    }

    r = urllib.request.Request(
        BASE + "/api/jobs/gerar",
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(r, timeout=30) as resp:
        d = json.loads(resp.read().decode())

    jid = d["job_id"]
    print(f"job criado: {jid}", flush=True)
    print(flush=True)

    for i in range(120):
        time.sleep(5)
        try:
            with urllib.request.urlopen(BASE + f"/api/jobs/{jid}", timeout=15) as resp:
                j = json.loads(resp.read().decode())
        except Exception as e:
            print(f"  [{i*5:>4}s] (erro ao ler job: {e})", flush=True)
            continue

        st = j.get("status")
        pr = j.get("progress", 0)
        ult = ""
        for e in reversed(j.get("events", [])):
            data = e.get("data", {})
            if "pct" in data:
                ult = f"{data.get('etapa','')} | {str(data.get('msg',''))[:58]}"
                break

        print(f"  [{i*5:>4}s] {st:8} {pr:>3}%  {ult}", flush=True)

        if st in ("done", "error"):
            print(flush=True)
            print("SEQUENCIA COMPLETA:")
            for e in j.get("events", []):
                dd = e.get("data", {})
                if "pct" in dd:
                    print(f"   {dd['pct']:>4}%  {str(dd.get('etapa','')):<12} "
                          f"{str(dd.get('msg',''))[:56]}")
            print(flush=True)
            res = j.get("resultado") or j.get("error")
            print("RESULTADO:", json.dumps(res, ensure_ascii=False), flush=True)
            _limpar(audio_path)
            return 0 if st == "done" else 1

    print("TIMEOUT: o job nao terminou em 10 minutos.", flush=True)
    _limpar(audio_path)
    return 1


def _limpar(audio_path: str) -> None:
    """Devolve a musica de teste para a lixeira (nunca apaga direto).

    O usuario tem a regra de mover descartes para D:\\dev-projetos\\lixeira\\
    em vez de deletar. Um WAV de teste nao e excecao.
    """
    import shutil
    from pathlib import Path

    origem = Path(__file__).resolve().parent.parent / "output" / Path(audio_path)
    if not origem.exists():
        return
    destino_dir = Path("D:/dev-projetos/lixeira/MusicClipStudio_e2e")
    try:
        destino_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(origem), str(destino_dir / origem.name))
        print(f"(musica de teste movida para {destino_dir})", flush=True)
    except Exception as e:
        print(f"(aviso: nao movi a musica de teste: {e})", flush=True)


if __name__ == "__main__":
    sys.exit(main())
