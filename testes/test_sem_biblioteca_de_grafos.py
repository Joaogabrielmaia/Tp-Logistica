import ast
import os
import subprocess
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# O enunciado proíbe bibliotecas prontas de grafos (como a NetworkX), salvo para comparação de desempenho.
# A comparação fica isolada em comparacao_networkx/; a ferramenta e os testes não podem depender de nenhuma delas.
PROIBIDAS = {"networkx", "igraph", "graph_tool", "osmnx", "ortools", "pyvrp", "scipy", "rustworkx", "snap", "pygraphviz", "dgl", "torch_geometric"}


def arquivos_da_ferramenta():
    for pasta in ("logistica", "testes"):
        for raiz, _, nomes in os.walk(os.path.join(RAIZ, pasta)):
            for nome in nomes:
                if nome.endswith(".py"):
                    yield os.path.join(raiz, nome)
    yield os.path.join(RAIZ, "main.py")


def modulos_importados(caminho):
    with open(caminho, encoding="utf-8") as f:
        arvore = ast.parse(f.read())
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            for alias in no.names:
                yield alias.name.split(".")[0]
        elif isinstance(no, ast.ImportFrom) and no.module and no.level == 0:
            yield no.module.split(".")[0]


class TestSemBibliotecaDeGrafos(unittest.TestCase):
    def test_ferramenta_nao_importa_biblioteca_de_grafos(self):
        encontrados = []
        for caminho in arquivos_da_ferramenta():
            for modulo in modulos_importados(caminho):
                if modulo in PROIBIDAS:
                    encontrados.append((os.path.relpath(caminho, RAIZ), modulo))
        self.assertEqual(encontrados, [], "a ferramenta não pode importar bibliotecas de grafos")

        # Mesmo instalada, a NetworkX fica bloqueada neste processo: importar qualquer biblioteca proibida falharia,
        # e a ferramenta precisa resolver uma instância e calcular caminhos assim mesmo.
        programa = (
            "import sys\n"
            "for nome in %r: sys.modules[nome] = None\n"
            "from logistica.cli import principal\n"
            "assert principal(['resolver', 'exemplos/dois_vertices.vrp']) == 0\n"
            "assert principal(['caminho', 'dados/solomon/R101.vrp', '0', '15', '--modo', 'viario']) == 0\n"
            "assert principal(['grafo', '--arestas', 'A B 1']) == 0\n"
            "print('ok sem bibliotecas de grafos')\n" % sorted(PROIBIDAS)
        )
        r = subprocess.run([sys.executable, "-c", programa], cwd=RAIZ, capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ok sem bibliotecas de grafos", r.stdout)


if __name__ == "__main__":
    unittest.main()
