"""Testa os endpoints de persistência de projetos (/api/projetos).

Valida o ciclo completo:
criar -> listar -> obter -> atualizar (upsert) -> apagar -> 404.

Uso: python _utils/_test_projetos.py
     python _utils/_test_projetos.py 8011     # outra porta

Por padrão usa a 8300 (porta dedicada do backend — ver _utils/_portas.py).
"""
import json
import os
import sys
import urllib.error
import urllib.request

# Porta configurável: argumento > env > 8300 (porta dedicada do backend)
PORTA = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("MCS_PORT", "8300"))
BASE = f"http://127.0.0.1:{PORTA}"

falhas = []


def req(metodo: str, caminho: str, corpo: dict | None = None):
    url = BASE + caminho
    dados = json.dumps(corpo).encode() if corpo is not None else None
    r = urllib.request.Request(url, data=dados, method=metodo)
    if dados:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        txt = e.read().decode()
        try:
            return e.code, json.loads(txt)
        except json.JSONDecodeError:
            return e.code, {"raw": txt}


def checar(nome: str, cond: bool, detalhe: str = ""):
    marca = "OK  " if cond else "FALHA"
    print(f"  [{marca}] {nome}" + (f"  — {detalhe}" if detalhe else ""))
    if not cond:
        falhas.append(nome)


print("=" * 74)
print("TESTE · PERSISTENCIA DE PROJETOS (/api/projetos)")
print("=" * 74)

# 0. backend no ar?
try:
    st, _ = req("GET", "/api/health")
    checar("backend responde /api/health", st == 200, f"HTTP {st}")
except Exception as e:
    print(f"  [FALHA] backend nao esta no ar em {BASE}: {e}")
    print(f"          rode: python -m uvicorn backend.app.main:app --port {PORTA}")
    sys.exit(1)

print()

# 1. CRIAR
st, r = req("POST", "/api/projetos", {
    "title": "Clipe de Teste",
    "letra": "luz da manha sobre o mar",
    "musica": {"duracao": 45},
    "completedSteps": {"letra": True},
})
checar("POST cria projeto", st == 200 and r.get("ok"), f"HTTP {st}")
pid = (r.get("projeto") or {}).get("id", "")
checar("id gerado", bool(pid), pid)
checar("titulo gravado", (r.get("projeto") or {}).get("title") == "Clipe de Teste")

# 2. LISTAR
st, r = req("GET", "/api/projetos")
checar("GET lista", st == 200 and "projetos" in r, f"HTTP {st}")
lista = r.get("projetos", [])
checar("projeto aparece na lista", any(p["id"] == pid for p in lista),
       f"{len(lista)} projeto(s)")

# 3. OBTER
st, r = req("GET", f"/api/projetos/{pid}")
checar("GET por id", st == 200 and r.get("id") == pid, f"HTTP {st}")
checar("letra preservada", r.get("letra") == "luz da manha sobre o mar")
checar("musica.duracao preservada", (r.get("musica") or {}).get("duracao") == 45)

# 4. ATUALIZAR (upsert — mesmo id, nao pode duplicar)
st, _ = req("GET", "/api/projetos-stats")
antes = _.get("total", 0)
st, r = req("POST", "/api/projetos", {"id": pid, "title": "Titulo Editado"})
checar("POST atualiza com mesmo id", st == 200 and r["projeto"]["id"] == pid)
st, r = req("GET", "/api/projetos-stats")
depois = r.get("total", 0)
checar("upsert NAO duplicou", antes == depois, f"{antes} -> {depois}")
st, r = req("GET", f"/api/projetos/{pid}")
checar("titulo foi atualizado", r.get("title") == "Titulo Editado", r.get("title", ""))

# 5. APAGAR
st, r = req("DELETE", f"/api/projetos/{pid}")
checar("DELETE remove", st == 200 and r.get("ok"), f"HTTP {st}")
st, r = req("GET", f"/api/projetos/{pid}")
checar("GET apos delete -> 404", st == 404, f"HTTP {st}")

# 6. ID inexistente
st, r = req("DELETE", "/api/projetos/nao_existe_xyz")
checar("DELETE de id inexistente -> 404", st == 404, f"HTTP {st}")

print()
if falhas:
    print(f"  {len(falhas)} FALHA(S): {', '.join(falhas)}")
    sys.exit(1)
print("  TODOS OS TESTES PASSARAM")
print("=" * 74)
