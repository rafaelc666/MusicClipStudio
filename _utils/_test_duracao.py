"""Valida a logica de duracao do clipe (musica manda, beats sao fallback)."""
import sys
from pathlib import Path

sys.path.insert(0, r"D:\dev-projetos")

from MusicClipStudio.engine import MusicClipEngine  # noqa: E402

MUSICA = Path(r"D:\dev-projetos\MusicClipStudio\output\uploads\teste_musica.mp3")

e = MusicClipEngine()
p = e.gerar_projeto(lyrics="Luz da manha sobre o mar\nO vento chama o meu nome")

beats = sum(b.duration for b in p.beats)
com_musica = e._duracao_do_clipe(p, str(MUSICA))
sem_musica = e._duracao_do_clipe(p, None)

print(f"  MP3 de teste existe    : {MUSICA.exists()}")
print(f"  duracao por BEATS      : {beats}s")
print(f"  duracao COM musica     : {com_musica}s   <- deve seguir a musica")
print(f"  duracao SEM musica     : {sem_musica}s   <- deve ser os beats")

ok = abs(com_musica - 45.0) < 0.5
print()
print(f"  REGRA 'musica manda'   : {'OK' if ok else 'FALHOU'}")
