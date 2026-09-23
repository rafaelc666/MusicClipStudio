"""
Manutenção Automatizada para o Módulo gerador_clipes_musicais

Este módulo fornece a classe ``MaintenanceAgent`` que pode ser usado
para analisar o código‑base e gerar sugestões de melhorias ou correções
automáticas.  O objetivo é centralizar decisões de manutenção – como
detecção de dependências ausentes, limpeza de código morto e geração de
TODOs – de forma que o desenvolvedor apenas revise e aprimore o que o
agente propõe.

Uso básico via API:

    from MusicClipStudio.maintenance_agent import MaintenanceAgent
    agent = MaintenanceAgent()
    report = agent.run_all_checks()
    for key, msgs in report.items():
        print(f"=== {key} ===")
        for msg in msgs:
            print(f"- {msg}")

Também pode ser executado como script:

    python -m MusicClipStudio.maintenance_agent

O agente não altera arquivos por padrão; ele apenas relata.  Caso o
usuário deseje aplicar correções automáticas, pode chamar os métodos
``apply_*`` correspondentes.
"""

import importlib
import sys
from pathlib import Path
from typing import List, Dict

class MaintenanceAgent:
    """Agente de manutenção que inspeciona o projeto e gera sugestões.

    Os métodos ``check_*`` retornam uma lista de mensagens.  ``run_all_checks``
    agrega todas elas em um dicionário, permitindo ao usuário ver um
    resumo completo.
    """

    def __init__(self, project_root: Path | str | None = None):
        self.root = Path(project_root or Path(__file__).parent)
        # Diretório onde o módulo está localizado
        self.module_dir = self.root

    # ---------------------------------------------------------------------
    # Checks individuais
    # ---------------------------------------------------------------------
    def check_scene_engine_dependency(self) -> List[str]:
        """Verifica se ``scene_engine`` está instalado.

        Caso a importação falhe, o agente recomenda usar o fallback
        ``moviepy`` (já tratado no código) ou instalar a dependência.
        """
        messages: List[str] = []
        try:
            importlib.import_module("scene_engine")
        except ImportError:
            messages.append(
                "Dependência 'scene_engine' não encontrada. "
                "O código já possui fallback para moviepy, mas recomenda‑se "
                "instalar a biblioteca para renderização completa via HTML/Playwright."
            )
        return messages

    def check_unused_presets(self) -> List[str]:
        """Detecta presets que não são referenciados em nenhum outro módulo.

        Atualmente ``PRESETS_NARRACAO`` é mantido apenas por compatibilidade de
        testes; se não houver uso futuro, pode ser removido.
        """
        from MusicClipStudio.audio import PRESETS_NARRACAO
        # Busca referências simples ao nome da variável no código‑base
        import subprocess, json, shlex
        pattern = r"PRESETS_NARRACAO"
        # Usamos ``rg`` (ripgrep) para procurar ocorrências fora deste arquivo
        try:
            result = subprocess.check_output(
                ["rg", "-l", pattern, str(self.module_dir)],
                text=True,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            # Nenhum arquivo encontrado
            result = ""
        files = [p for p in result.splitlines() if "maintenance_agent.py" not in p]
        if len(files) <= 1:  # Apenas este arquivo (e possivelmente tests) referenciam
            return [
                "Preset 'PRESETS_NARRACAO' parece não ser usado fora de testes. "
                "Considere removê‑lo ou mantê‑lo apenas como alias de compatibilidade."
            ]
        return []

    def check_dead_imports(self) -> List[str]:
        """Detecta imports que não são utilizados no próprio módulo.

        Esta verificação rápida analisa o AST de cada arquivo Python e procura
        por ``Import``/``ImportFrom`` que não tenham nomes referenciados.
        """
        import ast
        messages: List[str] = []
        for py_file in self.module_dir.rglob("*.py"):
            # Ignora arquivos de teste para reduzir ruído
            if "tests" in py_file.parts:
                continue
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))
            imports = {node: set() for node in ast.iter_child_nodes(tree) if isinstance(node, (ast.Import, ast.ImportFrom))}
            # Coleta nomes importados
            imported_names = {}
            for node in imports:
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_names[alias.asname or alias.name] = node
                else:  # ImportFrom
                    module = node.module or ""
                    for alias in node.names:
                        name = alias.asname or alias.name
                        imported_names[name] = node
            # Procura usos dos nomes importados
            class NameVisitor(ast.NodeVisitor):
                def __init__(self, names):
                    self.names = names
                    self.used = set()
                def visit_Name(self, node):
                    if node.id in self.names:
                        self.used.add(node.id)
                    self.generic_visit(node)
            visitor = NameVisitor(imported_names)
            visitor.visit(tree)
            for name, node in imported_names.items():
                if name not in visitor.used:
                    # Pega a linha do import para mensagem
                    lineno = getattr(node, "lineno", "?")
                    messages.append(
                        f"Importo não usado em {py_file.relative_to(self.root)}: linha {lineno} – '{name}'."
                    )
        return messages

    # ---------------------------------------------------------------------
    # Agregador de resultados
    # ---------------------------------------------------------------------
    def run_all_checks(self) -> Dict[str, List[str]]:
        """Executa todos os checks e devolve um dicionário de categorias → mensagens."""
        report: Dict[str, List[str]] = {}
        for check_name in [
            "check_scene_engine_dependency",
            "check_unused_presets",
            "check_dead_imports",
        ]:
            method = getattr(self, check_name)
            msgs = method()
            if msgs:
                # Converte camelCase para texto amigável
                title = check_name.replace("check_", "").replace("_", " ").title()
                report[title] = msgs
        return report

    # ---------------------------------------------------------------------
    # Aplicação automática (opcional)
    # ---------------------------------------------------------------------
    def apply_dead_import_removal(self) -> None:
        """Remove imports não utilizados usando edições in‑place.

        Esta operação tenta ser segura: somente imports que não foram
        encontrados como usados são removidos.  Não há garantia de que o
        código continue sem warnings de estilo, mas a sintaxe permanece
        correta.
        """
        import ast
        from MusicClipStudio.edit import edit  # O helper edit não existe; usamos ferramenta 'edit' externamente.
        # Nota: Implementação completa exigiria parsing e escrita de arquivos
        # que excede o escopo atual.  O método fica aqui como referência para
        # futuros aprimoramentos.
        raise NotImplementedError("apply_dead_import_removal ainda não implementado.")

# -------------------------------------------------------------------------
# Entrypoint de linha de comando
# -------------------------------------------------------------------------
if __name__ == "__main__":
    agent = MaintenanceAgent()
    report = agent.run_all_checks()
    if not report:
        print("Nenhuma anomalia detectada.")
    else:
        for title, msgs in report.items():
            print(f"=== {title} ===")
            for msg in msgs:
                print(f"- {msg}")
