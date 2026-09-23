"""Mostra lado a lado as URLs de endpoint usadas no codigo.

Objetivo: separar ERRO DE ENDPOINT (URL errada) de ERRO DE METODO (nome de
funcao errada). Sao categorias diferentes de bug.

Uso: python _utils/_diag_endpoints.py
"""
import json
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent))

cfg_json = json.loads((Path.home() / ".gerador_clipes_config.json").read_text(encoding="utf-8"))
from MusicClipStudio.database import StockDatabase  # noqa: E402

db = StockDatabase()
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def probe(nome, url, headers):
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(url, headers=headers), timeout=15, context=ctx)
        return f"  {nome:<52} HTTP {r.status}"
    except urllib.error.HTTPError as e:
        return f"  {nome:<52} HTTP {e.code} {e.reason}"
    except Exception as e:  # noqa: BLE001
        return f"  {nome:<52} {type(e).__name__}: {e}"


print("=" * 92)
print("CATEGORIA 1 — ERRO DE ENDPOINT (URL / path errado)")
print("=" * 92)

K = cfg_json["stock_pexels_api_key"]
UA = {"Authorization": K, "User-Agent": "GeradorClipesMusicais/1.0"}
print("\n[PEXELS]")
print(probe("  X  /v1/search/photos   (o que testar_conexao usava)",
            "https://api.pexels.com/v1/search/photos?query=nature&per_page=1", UA))
print(probe("  OK /v1/search          (correto)",
            "https://api.pexels.com/v1/search?query=nature&per_page=1", UA))

C = {"Authorization": f"Bearer {cfg_json['stock_coverr_api_key']}", "User-Agent": "Mozilla/5.0"}
print("\n[COVERR]")
print(probe("  X  ?per_page=1         (o que testar_conexao usava)",
            "https://api.coverr.co/videos?query=nature&per_page=1", C))
print(probe("  OK ?page_size=1        (correto)",
            "https://api.coverr.co/videos?query=nature&page_size=1", C))

O = {"User-Agent": "GeradorClipesMusicais/1.0", "Accept": "application/json"}
OT = {"Authorization": f"Token {cfg_json['stock_openverse_api_key']}", **O}
print("\n[OPENVERSE] — path CORRETO, credencial ERRADA")
print(probe("  OK /v1/images/ anonimo (correto)",
            "https://api.openverse.org/v1/images/?q=nature&page_size=1", O))
print(probe("  X  /v1/images/ com Token (token invalido)",
            "https://api.openverse.org/v1/images/?q=nature&page_size=1", OT))
print(probe("  X  /images/  (sem /v1)",
            "https://api.openverse.org/images/?q=nature&page_size=1", O))

print()
print("=" * 92)
print("CATEGORIA 2 — ERRO DE METODO (nome de funcao errado no backend)")
print("=" * 92)

checks = [
    ("engine.py", "MusicClipEngine", "analyze_lyrics", "criar_beats"),
    ("engine.py", "MusicClipEngine", "renderizar_projeto", "generate"),
    ("database.py", "StockDatabase", "buscar", "pesquisar"),
    ("agent.py", "ClipAgent", "generate_image_prompts", "analisar"),
]
from MusicClipStudio.engine import MusicClipEngine  # noqa: E402
from MusicClipStudio.agent import ClipAgent  # noqa: E402

objs = {"MusicClipEngine": MusicClipEngine(), "StockDatabase": db, "ClipAgent": ClipAgent()}
print()
for arquivo, cls, errado, certo in checks:
    o = objs[cls]
    marca_e = "X " if not hasattr(o, errado) else "OK"
    marca_c = "OK" if hasattr(o, certo) else "X "
    print(f"  {arquivo:<14} {cls}.{errado:<24} [{marca_e}]  ->  {certo:<16} [{marca_c}]")
