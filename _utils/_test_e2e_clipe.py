"""E2E REAL: gera um video-clipe a partir de uma musica pronta.

Este e o teste que prova a arquitetura nova: o app recebe a musica pronta
e monta o video-clipe. NAO gera musica.

Uso: python _utils/_test_e2e_clipe.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\dev-projetos")

from MusicClipStudio.engine import MusicClipEngine  # noqa: E402

RAIZ = Path(r"D:\dev-projetos\MusicClipStudio")
MUSICA = RAIZ / "output" / "uploads" / "teste_musica.mp3"
SAIDA = RAIZ / "output" / "e2e_teste.mp4"

print("=" * 74)
print("E2E · VIDEO-CLIPE A PARTIR DE MUSICA PRONTA")
print("=" * 74)
print(f"  musica : {MUSICA.name}  ({'existe' if MUSICA.exists() else 'NAO EXISTE'})")
print(f"  saida  : {SAIDA}")
print()

if not MUSICA.exists():
    print("  [ERRO] musica de teste nao encontrada")
    sys.exit(1)

eventos = []


def on_prog(evento, dados):
    pct = dados.get("progresso", 0)
    etapa = dados.get("etapa", "")
    msg = dados.get("mensagem", "")
    linha = f"  [{int(pct * 100):>3}%] {etapa:<10} {msg}"
    if not eventos or eventos[-1] != linha:
        eventos.append(linha)
        print(linha)


e = MusicClipEngine()
e.on_progress(on_prog)

t0 = time.time()
resultado = e.generate(
    lyrics="Luz da manha sobre o mar\nO vento chama o meu nome\nEu vou seguir o horizonte",
    title="Teste E2E",
    artist="MusicClipStudio",
    format="9/16",
    output=str(SAIDA),
    audio_path=str(MUSICA),
)
dur = time.time() - t0

print()
print("=" * 74)
if resultado and Path(resultado).exists():
    arq = Path(resultado)
    print(f"  SUCESSO em {dur:.1f}s")
    print(f"  arquivo : {arq.name}")
    print(f"  tamanho : {arq.stat().st_size / 1024 / 1024:.2f} MB")
else:
    print(f"  FALHOU em {dur:.1f}s — resultado: {resultado}")
print("=" * 74)
