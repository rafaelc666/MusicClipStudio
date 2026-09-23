"""Testa o fluxo REAL: StockDatabase + ClipConfig (nao requests crus).

Mostra quais provedores retornam 0 resultados e por que.
"""
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent))

from MusicClipStudio.config import ClipConfig          # noqa: E402
from MusicClipStudio.database import StockDatabase      # noqa: E402

cfg = ClipConfig()
cfg.load() if hasattr(cfg, "load") else None

print("=== CHAVES CARREGADAS PELA ClipConfig ===")
for campo in sorted(vars(cfg)):
    if "api_key" in campo:
        val = getattr(cfg, campo) or ""
        print(f"  {campo:<32} {'[VAZIA]' if not val else val[:10] + '...' + val[-4:]}")

db = StockDatabase(cfg)

print("\n=== TESTE UNITARIO POR PROVEDOR (chamada direta) ===")
tabela = [
    ("pexels", db._buscar_pexels, True),
    ("pixabay", db._buscar_pixabay, True),
    ("unsplash", db._buscar_unsplash, False),
    ("nasa", db._buscar_nasa, False),
    ("coverr", db._buscar_coverr, False),
    ("giphy", db._buscar_giphy, False),
    ("openverse", db._buscar_openverse, False),
]

for nome, fn, aceita_tipos in tabela:
    try:
        if aceita_tipos:
            res = fn("nature", 5, False, False)
        else:
            res = fn("nature", 5)
        print(f"  {nome:<12} -> {len(res):>3} resultados")
    except Exception as e:  # noqa: BLE001
        print(f"  {nome:<12} -> EXCECAO {type(e).__name__}: {e}")
        traceback.print_exc()

print("\n=== TESTE DO METODO PUBLICO search() ===")
for nome, _, _ in tabela:
    try:
        res = db.search("nature", provider=nome, max_results=5)
        print(f"  search({nome:<12}) -> {len(res):>3} resultados")
    except Exception as e:  # noqa: BLE001
        print(f"  search({nome:<12}) -> EXCECAO {type(e).__name__}: {e}")

print("\n=== TESTE testar_conexao() (usado pela GUI) ===")
if hasattr(db, "testar_conexao"):
    for nome, _, _ in tabela:
        try:
            print(f"  {nome:<12} -> {db.testar_conexao(nome)}")
        except Exception as e:  # noqa: BLE001
            print(f"  {nome:<12} -> EXCECAO {type(e).__name__}: {e}")
else:
    print("  (metodo nao existe)")
