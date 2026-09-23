"""Auditoria: acha chamadas de metodo em objetos conhecidos que NAO existem.

Motivo: o pipeline engole AttributeError, entao uma chamada fantasma
(`obj.metodo_que_nao_existe()`) faz o app "funcionar" entregando resultado
errado em silencio. Ja aconteceu 4x neste projeto:
  - engine.renderizar_projeto()     -> nao existia (era generate)
  - db.buscar()                     -> nao existia (era pesquisar)
  - agent.gerar_prompts_busca()     -> nao existia (era analisar)
  - compositor.add_audio_to_video() -> nao existia (era VideoRenderer)

Regra importante (aprendida na marra): `self` so pode ser atribuido a UMA
classe por arquivo. Apontar `self` para MusicClipEngine em todos os arquivos
gera 24 falsos positivos. Associe `self` a classe definida NAQUELE arquivo.

Uso: python _utils/_audit_metodos.py
"""
import ast
import inspect
import sys
from pathlib import Path

RAIZ = Path(r"D:\dev-projetos\MusicClipStudio")
sys.path.insert(0, r"D:\dev-projetos")


def carregar(caminho_mod: str, nome_classe: str):
    try:
        mod = __import__(caminho_mod, fromlist=[nome_classe])
        return getattr(mod, nome_classe)
    except Exception as e:
        print(f"  [skip] {nome_classe}: {e}")
        return None


# nomes de variavel -> classe real
CLASSES = {}
for mod, cls in [
    ("MusicClipStudio.scene_engine.compositor", "Compositor"),
    ("MusicClipStudio.scene_engine.renderers.video_renderer", "VideoRenderer"),
    ("MusicClipStudio.scene_engine.renderers.html_renderer", "HTMLRenderer"),
    ("MusicClipStudio.database", "StockDatabase"),
    ("MusicClipStudio.engine", "MusicClipEngine"),
]:
    c = carregar(mod, cls)
    if c:
        CLASSES[cls] = c

# nome de arquivo -> classe que o `self` representa nele
SELF_POR_ARQUIVO = {
    "compositor.py": "Compositor",
    "video_renderer.py": "VideoRenderer",
    "html_renderer.py": "HTMLRenderer",
    "engine.py": "MusicClipEngine",
}

# variaveis inferidas pelo nome.
# ATENCAO: `renderer` e ambiguo — em engine.py e um HTMLRenderer, em
# video_renderer.py e o proprio VideoRenderer. Resolvido por OVERRIDES.
VAR_CLASSES = {
    "compositor": "Compositor",
    "video_renderer": "VideoRenderer",
    "html_renderer": "HTMLRenderer",
    "db": "StockDatabase",
    "self": None,  # resolvido por arquivo
}

# overrides por arquivo: (arquivo, variavel) -> classe
OVERRIDES = {
    ("engine.py", "renderer"): "HTMLRenderer",
    ("video_renderer.py", "renderer"): "VideoRenderer",
    ("html_renderer.py", "renderer"): "HTMLRenderer",
}

problemas = []
checados = 0


def metodos_de(classe):
    return {n for n, _ in inspect.getmembers(classe, predicate=callable)}


def checar_arquivo(arq: Path):
    global checados
    try:
        arvore = ast.parse(arq.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError as e:
        print(f"  [syntax] {arq.name}: {e}")
        return

    self_cls_nome = SELF_POR_ARQUIVO.get(arq.name)

    for node in ast.walk(arvore):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if not isinstance(fn, ast.Attribute):
            continue
        base = fn.value
        if not isinstance(base, ast.Name):
            continue
        var = base.id
        cls_nome = OVERRIDES.get((arq.name, var)) or VAR_CLASSES.get(var)
        if var not in VAR_CLASSES and (arq.name, var) not in OVERRIDES:
            continue
        if cls_nome is None:
            cls_nome = self_cls_nome
        if cls_nome is None:
            continue
        cls = CLASSES.get(cls_nome)
        if cls is None:
            continue
        nome_metodo = fn.attr
        checados += 1
        if nome_metodo not in metodos_de(cls):
            problemas.append((arq.name, node.lineno, f"{var}.{nome_metodo}()", cls_nome))


print("=" * 74)
print("AUDITORIA DE METODOS FANTASMA")
print("=" * 74)
print(f"  classes carregadas: {', '.join(sorted(CLASSES))}")
print()

arquivos = [RAIZ / "engine.py", RAIZ / "database.py", RAIZ / "backend" / "app" / "main.py"]
arquivos += sorted((RAIZ / "scene_engine").rglob("*.py"))

for arq in arquivos:
    if arq.exists():
        checar_arquivo(arq)

for nome, linha, chamada, cls in problemas:
    print(f"  [!] {nome}:{linha}  {chamada}  <- NAO EXISTE em {cls}")

print()
print(f"  {checados} chamadas verificadas · {len(problemas)} fantasma(s)")
print("=" * 74)
sys.exit(1 if problemas else 0)
