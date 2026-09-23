"""Testa os endpoints do backend com o TestClient (sem subir servidor).

Foca nas rotas que estavam quebradas por metodo fantasma.

Uso: PYTHONPATH=D:/dev-projetos python _utils/_test_endpoints.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent))   # D:/dev-projetos  -> importa MusicClipStudio
sys.path.insert(0, str(ROOT))          # MusicClipStudio  -> importa backend

from fastapi.testclient import TestClient  # noqa: E402

from backend.app.main import app  # noqa: E402

c = TestClient(app)
falhas = []


def mostra(titulo, r):
    ok = r.status_code == 200
    marca = "OK   " if ok else "FALHA"
    print(f"\n[{marca}] {titulo}  ->  HTTP {r.status_code}")
    try:
        corpo = r.json()
    except Exception:
        print("   (resposta não-JSON)")
        if not ok:
            falhas.append(titulo)
        return None
    if ok:
        print(f"   {str(corpo)[:320]}")
    else:
        print(f"   {str(corpo)[:400]}")
        falhas.append(titulo)
    return corpo


print("=" * 78)
print("ENDPOINTS DO BACKEND · MusicClipStudio")
print("=" * 78)

r = mostra("GET /api/health", c.get("/api/health"))

mostra("POST /api/letra/analisar", c.post("/api/letra/analisar", json={
    "lyrics": "Luz da manhã sobre o mar\nO vento chama o meu nome\nEu vou seguir",
    "description": "clipe épico",
}))

mostra("POST /api/midia/buscar  (era db.buscar inexistente)", c.post("/api/midia/buscar", json={
    "query": "ocean sunset", "provider": "pexels", "max_results": 3,
}))

mostra("POST /api/imagens/gerar-prompts  (era agent.gerar_prompts_busca)", c.post(
    "/api/imagens/gerar-prompts", json={
        "lyrics": "Luz da manhã sobre o mar\nO vento chama o meu nome",
        "description": "clipe épico",
    }))

mostra("POST /api/midia/buscar (pixabay)", c.post("/api/midia/buscar", json={
    "query": "city night neon", "provider": "pixabay", "max_results": 3,
}))

print("\n" + "=" * 78)
if falhas:
    print(f"RESULTADO: {len(falhas)} endpoint(s) com falha:")
    for f in falhas:
        print(f"  - {f}")
else:
    print("RESULTADO: todos os endpoints responderam HTTP 200")
print("=" * 78)
