"""Testa ao vivo as chaves de API de stock salvas em ~/.gerador_clipes_config.json.

Uso:  python _utils/_test_api_keys.py
Espelha exatamente o formato de request usado em database.py.
"""
import json
import ssl
import urllib.error
import urllib.request
from pathlib import Path

CFG = Path.home() / ".gerador_clipes_config.json"
cfg = json.loads(CFG.read_text(encoding="utf-8"))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def req(url, headers=None):
    r = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(r, timeout=25, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")[:400]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:400]
    except Exception as e:  # noqa: BLE001
        return "ERR", f"{type(e).__name__}: {e}"


rows = []


def t(name, res):
    rows.append((name, res[0], res[1].replace("\n", " ")[:200]))


k_pexels = cfg.get("stock_pexels_api_key", "")
k_pixabay = cfg.get("stock_pixabay_api_key", "")
k_unsplash = cfg.get("stock_unsplash_api_key", "")
k_nasa = cfg.get("stock_nasa_api_key", "")
k_coverr = cfg.get("stock_coverr_api_key", "")
k_giphy = cfg.get("stock_giphy_api_key", "")
k_openverse = cfg.get("stock_openverse_api_key", "")

t("PEXELS", req(
    "https://api.pexels.com/v1/search?query=nature&per_page=2",
    {"Authorization": k_pexels, "User-Agent": "GeradorClipesMusicais/1.0"}))

t("PIXABAY", req(
    f"https://pixabay.com/api/?key={k_pixabay}&q=nature&per_page=3",
    {"User-Agent": "Mozilla/5.0"}))

t("UNSPLASH", req(
    "https://api.unsplash.com/search/photos?query=nature&per_page=2",
    {"Authorization": f"Client-ID {k_unsplash}"}))

t("NASA (images-api, sem key — como o codigo faz)", req(
    "https://images-api.nasa.gov/search?q=moon&page_size=2",
    {"User-Agent": "Mozilla/5.0"}))

t("NASA (api.nasa.gov — valida a key de verdade)", req(
    f"https://api.nasa.gov/planetary/apod?api_key={k_nasa}"))

t("COVERR (Bearer token)", req(
    "https://api.coverr.co/videos?query=nature&page_size=2",
    {"Authorization": f"Bearer {k_coverr}", "User-Agent": "Mozilla/5.0"}))

t("GIPHY", req(
    f"https://api.giphy.com/v1/gifs/search?api_key={k_giphy}&q=nature&limit=2&rating=g",
    {"User-Agent": "Mozilla/5.0"}))

t("OPENVERSE (anonimo, sem token)", req(
    "https://api.openverse.org/v1/images/?q=nature&page_size=2",
    {"User-Agent": "GeradorClipesMusicais/1.0", "Accept": "application/json"}))

t("OPENVERSE (com Token)", req(
    "https://api.openverse.org/v1/images/?q=nature&page_size=2",
    {"Authorization": f"Token {k_openverse}",
     "User-Agent": "GeradorClipesMusicais/1.0", "Accept": "application/json"}))

print(f"{'PROVEDOR':<50} {'HTTP':<6} RESPOSTA")
print("-" * 110)
for name, status, body in rows:
    print(f"{name:<50} {str(status):<6} {body}")
