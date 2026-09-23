"""Testa os bancos de imagem/video da web com requisicao REAL.

Responde a pergunta: "as API keys dos bancos de imagens e videos da web
funcionam?" — nao basta ver se a chave existe no config; e preciso provar
que a API responde.

Uso:
    python _utils/_testar_bancos_api.py
"""
import json
import sys
import urllib.error
import urllib.request

sys.path.insert(0, r"D:\dev-projetos")
sys.path.insert(0, r"D:\dev-projetos\MusicClipStudio")

from MusicClipStudio.config import load_config          # noqa: E402
from MusicClipStudio.database import StockDatabase      # noqa: E402

PROVEDORES = [
    ("pexels",    "fotos + videos"),
    ("pixabay",   "fotos + videos"),
    ("unsplash",  "fotos"),
    ("nasa",      "fotos espaco"),
    ("coverr",    "videos"),
    ("giphy",     "gifs"),
    ("openverse", "fotos/video CC"),
]

# Chave no config que cada provedor usa — para conferir presenca tambem.
CHAVE_CFG = {
    "pexels":    "stock_pexels_api_key",
    "pixabay":   "stock_pixabay_api_key",
    "unsplash":  "stock_unsplash_api_key",
    "nasa":      "stock_nasa_api_key",
    "coverr":    "stock_coverr_api_key",
    "giphy":     "stock_giphy_api_key",
    "openverse": "stock_openverse_api_key",
}


def main() -> int:
    cfg = load_config()
    db = StockDatabase(cfg)

    print("=" * 74)
    print("BANCOS DE IMAGEM/VIDEO DA WEB — teste de conexao REAL")
    print("=" * 74)
    print()
    print(f"  {'PROVEDOR':<11} {'CHAVE':<8} {'CONEXAO':<9} OBS")
    print(f"  {'-'*11} {'-'*8} {'-'*9} {'-'*38}")

    ok = 0
    detalhes = []

    for nome, tipo in PROVEDORES:
        # 1) A chave esta salva no config?
        campo = CHAVE_CFG[nome]
        valor = getattr(cfg, campo, None)
        tem_chave = bool(valor)
        marca_chave = "sim" if tem_chave else "NAO"

        # 2) A API responde de verdade?
        try:
            r = db.testar_conexao(nome)
            sucesso = r.get("sucesso") if isinstance(r, dict) else bool(r)
            msg = str(r.get("mensagem", ""))[:38] if isinstance(r, dict) else ""
            n = r.get("resultados") if isinstance(r, dict) else None
            obs = f"{msg} {f'({n} itens)' if n else ''}".strip()
        except Exception as e:
            sucesso = False
            obs = f"{type(e).__name__}: {str(e)[:30]}"

        marca = "OK" if sucesso else "FALHA"
        if sucesso:
            ok += 1
        print(f"  {nome:<11} {marca_chave:<8} {marca:<9} {obs}  [{tipo}]")
        detalhes.append((nome, tem_chave, sucesso))

    print()
    print(f"  RESULTADO: {ok}/{len(PROVEDORES)} provedores respondendo")

    # Distingue "chave ausente" de "API falhou" — sao problemas diferentes.
    sem_chave = [n for n, c, s in detalhes if not c]
    falhou = [n for n, c, s in detalhes if c and not s]
    if sem_chave:
        print(f"  Sem chave no config : {', '.join(sem_chave)}")
    if falhou:
        print(f"  Com chave, mas falhou: {', '.join(falhou)}")
    if ok == len(PROVEDORES):
        print("  Todas as chaves configuradas estao funcionando.")

    # 3) Prova final: uma busca de midia de verdade (o que o produto usa).
    print()
    print("=" * 74)
    print("BUSCA REAL (o caminho que o produto usa)")
    print("=" * 74)
    try:
        res = db.pesquisar_todos("sunset ocean city", max_results=8)
        # ATENCAO: o campo e' `.results` (ingles), nao `.resultados`.
        itens = list(getattr(res, "results", None) or [])
        total = getattr(res, "total", len(itens))
        print(f"  pesquisar_todos('sunset ocean city') -> "
              f"{len(itens)} exibidos de {total} encontrados")
        for it in itens[:8]:
            tipo = getattr(it, "media_type", "?")
            prov = getattr(it, "source", "?")
            dl = str(getattr(it, "download_url", "") or "")
            marca = "" if dl else "  (!sem download_url)"
            print(f"    [{str(tipo):<5}] {str(prov):<10} {dl[:52]}{marca}")
        if not itens:
            print("    (nenhum resultado — vale investigar)")
    except Exception as e:
        print(f"  ERRO na busca: {type(e).__name__}: {e}")

    return 0 if ok == len(PROVEDORES) else 1


if __name__ == "__main__":
    sys.exit(main())
