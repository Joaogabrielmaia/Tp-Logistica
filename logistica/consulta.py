import math
import re
import time

from .caminhos import (CicloNegativo, a_estrela, bellman_ford_caminho, bfs_caminho, dfs_caminho, dijkstra_caminho,
                       floyd_warshall, floyd_warshall_caminho)
from .erros import ErroExplicado
from .grafo import GrafoDirigido, alcancaveis, componentes_fracamente_conexas, kruskal

ALGORITMOS = ("bfs", "dfs", "dijkstra", "a_estrela", "bellman_ford", "floyd_warshall")
NOMES = {
    "bfs": "BFS (busca em largura)",
    "dfs": "DFS (busca em profundidade)",
    "dijkstra": "Dijkstra",
    "a_estrela": "A*",
    "bellman_ford": "Bellman-Ford",
    "floyd_warshall": "Floyd-Warshall",
}
O_QUE_GARANTE = {
    "bfs": "menor número de arcos (ignora os pesos)",
    "dfs": "um caminho qualquer, não necessariamente o menor",
    "dijkstra": "menor custo, com pesos não negativos",
    "a_estrela": "menor custo, guiado pela distância em linha reta",
    "bellman_ford": "menor custo, aceita peso negativo e detecta ciclo negativo",
    "floyd_warshall": "menor custo entre todos os pares",
}
LIMITE_VERTICES_TEXTO = 2000
LIMITE_ARESTAS_TEXTO = 20000
# Floyd-Warshall é O(n^3): com 1001 vértices seriam cerca de 10^9 passos em Python.
LIMITE_FLOYD = 300


class Grafo:
    def __init__(self, grafo, rotulos, coordenadas=None, origem_dados=""):
        self.grafo = grafo
        self.rotulos = rotulos
        self.coordenadas = coordenadas
        self.origem_dados = origem_dados

    def indice(self, rotulo):
        texto = str(rotulo).strip()
        if texto in self._mapa():
            return self._mapa()[texto]
        raise ErroExplicado(
            "vértice '%s' não existe neste grafo" % texto,
            "os vértices válidos são %s." % self._faixa(),
            "use um dos vértices listados; nas instâncias o 0 é o depósito e os clientes vão de 1 a n.")

    def _mapa(self):
        if not hasattr(self, "_cache"):
            self._cache = {str(r): i for i, r in enumerate(self.rotulos)}
        return self._cache

    def _faixa(self):
        if all(str(r) == str(i) for i, r in enumerate(self.rotulos)):
            return "de 0 a %d" % (len(self.rotulos) - 1)
        nomes = [str(r) for r in self.rotulos[:20]]
        return ", ".join(nomes) + (" ..." if len(self.rotulos) > 20 else "")


def grafo_da_instancia(inst):
    return Grafo(inst.grafo, list(range(inst.grafo.n)), [(no.x, no.y) for no in inst.nos], "instância %s (modo %s)" % (inst.nome, inst.modo))


# Lê um grafo digitado como lista de arestas, uma por linha (ou separadas por ';'): "origem destino peso". O peso é
# opcional (vale 1) e os vértices podem ser números ou nomes. Uma linha com um só vértice cria um vértice isolado.
def grafo_de_texto(texto, dirigido=False):
    if not isinstance(texto, str) or not texto.strip():
        raise ErroExplicado(
            "nenhuma aresta informada",
            "o grafo próprio é montado a partir da lista de arestas, e ela está vazia.",
            "escreva uma aresta por linha no formato 'origem destino peso', por exemplo: A B 5")
    rotulos, indice, arcos = [], {}, []

    def vertice(nome):
        if nome not in indice:
            indice[nome] = len(rotulos)
            rotulos.append(nome)
        return indice[nome]

    linhas = [l for parte in texto.replace("\r", "").split("\n") for l in parte.split(";")]
    for numero, linha in enumerate(linhas, 1):
        # vírgula entre dígitos é decimal (2,5); fora disso separa campos
        linha = re.sub(r"(?<=\d),(?=\d)", ".", linha.split("#")[0]).replace(",", " ").strip()
        if not linha:
            continue
        campos = linha.split()
        if len(campos) == 1:
            vertice(campos[0])
            continue
        if len(campos) > 3:
            raise ErroExplicado(
                "linha %d com campos demais: '%s'" % (numero, linha),
                "cada linha tem no máximo três campos: origem, destino e peso.",
                "separe as arestas em linhas diferentes (ou com ';').")
        peso = 1.0
        if len(campos) == 3:
            try:
                peso = float(campos[2])
            except ValueError:
                raise ErroExplicado(
                    "peso inválido na linha %d: '%s'" % (numero, campos[2]),
                    "o terceiro campo é o peso da aresta e precisa ser um número.",
                    "o peso é um número, por exemplo: A B 2.5 (ou 2,5)")
            if math.isnan(peso) or math.isinf(peso):
                raise ErroExplicado(
                    "peso não finito na linha %d" % numero,
                    "NaN e infinito não são pesos válidos: a soma do caminho deixaria de fazer sentido.",
                    "informe um número finito.")
        arcos.append((vertice(campos[0]), vertice(campos[1]), peso))
    if len(rotulos) > LIMITE_VERTICES_TEXTO or len(arcos) > LIMITE_ARESTAS_TEXTO:
        raise ErroExplicado(
            "grafo digitado grande demais (%d vértices, %d arestas)" % (len(rotulos), len(arcos)),
            "o campo de texto é para grafos pequenos de demonstração; o limite é %d vértices e %d arestas." % (LIMITE_VERTICES_TEXTO, LIMITE_ARESTAS_TEXTO),
            "para grafos grandes, use uma instância de dados/ no modo rede viária.")
    if not rotulos:
        raise ErroExplicado("nenhuma aresta informada", "todas as linhas estão vazias ou são comentários.", "escreva ao menos uma aresta, por exemplo: A B 5")
    g = GrafoDirigido(len(rotulos), permitir_negativo=True)
    for u, v, peso in arcos:
        if dirigido:
            g.adicionar_arco(u, v, peso)
        else:
            g.adicionar_aresta(u, v, peso)
    return Grafo(g, rotulos, None, "grafo digitado (%s)" % ("dirigido" if dirigido else "não dirigido"))


def _custo(grafo, caminho):
    return sum(grafo.peso(a, b) for a, b in zip(caminho, caminho[1:]))


def _tem_negativo(grafo):
    return any(peso < 0 for u in range(grafo.n) for _, peso, _ in grafo.adj[u])


def comparar_caminhos(g, origem, destino, algoritmos=ALGORITMOS):
    s, t = g.indice(origem), g.indice(destino)
    grafo = g.grafo
    negativo = _tem_negativo(grafo)
    linhas = []
    for alg in algoritmos:
        linha = {"algoritmo": alg, "nome": NOMES[alg], "garante": O_QUE_GARANTE[alg], "caminho": None, "custo": None, "arcos": None, "tempo_ms": None, "situacao": "ok", "observacao": ""}
        if negativo and alg in ("dijkstra", "a_estrela"):
            linha["situacao"] = "nao_aplicavel"
            linha["observacao"] = "o grafo tem peso negativo; %s supõe pesos não negativos e poderia errar, então não roda. Use Bellman-Ford." % NOMES[alg]
            linhas.append(linha)
            continue
        if alg == "floyd_warshall" and grafo.n > LIMITE_FLOYD:
            linha["situacao"] = "nao_aplicavel"
            linha["observacao"] = "Floyd-Warshall é O(n³): com %d vértices seriam cerca de %.0e passos. Limite: %d vértices." % (grafo.n, float(grafo.n) ** 3, LIMITE_FLOYD)
            linhas.append(linha)
            continue
        inicio = time.perf_counter()
        try:
            if alg == "bfs":
                caminho = bfs_caminho(grafo, s, t)
            elif alg == "dfs":
                caminho = dfs_caminho(grafo, s, t)
            elif alg == "dijkstra":
                caminho = dijkstra_caminho(grafo, s, t)
            elif alg == "a_estrela":
                caminho = a_estrela(grafo, s, t, g.coordenadas)
                if not g.coordenadas:
                    linha["observacao"] = "sem coordenadas no grafo digitado, a estimativa é 0 e o A* age como o Dijkstra."
            elif alg == "bellman_ford":
                caminho = bellman_ford_caminho(grafo, s, t)
            else:
                caminho = floyd_warshall_caminho(grafo, s, t, floyd_warshall(grafo))
        except CicloNegativo as e:
            linha["situacao"] = "ciclo_negativo"
            ciclo = [g.rotulos[v] if isinstance(v, int) else v for v in e.ciclo]
            linha["observacao"] = "há um ciclo de peso negativo (%s): dá para reduzir o custo sem fim, então não existe menor caminho." % " -> ".join(map(str, ciclo))
            linha["tempo_ms"] = (time.perf_counter() - inicio) * 1000
            linhas.append(linha)
            continue
        linha["tempo_ms"] = (time.perf_counter() - inicio) * 1000
        if caminho is None:
            linha["situacao"] = "sem_caminho"
            linha["observacao"] = "o destino não é alcançável a partir da origem (nenhuma sequência de arcos liga os dois)."
        else:
            linha["caminho"] = [g.rotulos[v] for v in caminho]
            linha["indices"] = caminho
            linha["custo"] = _custo(grafo, caminho)
            linha["arcos"] = len(caminho) - 1
        linhas.append(linha)
    custos = {l["algoritmo"]: l["custo"] for l in linhas if l["custo"] is not None and l["algoritmo"] not in ("bfs", "dfs")}
    conclusao = ""
    if custos:
        menor = min(custos.values())
        iguais = all(abs(c - menor) < 1e-6 for c in custos.values())
        lista = [NOMES[a] for a in custos]
        if len(lista) == 1:
            conclusao = "%s encontrou o menor custo, %s." % (lista[0], _fmt(menor))
        elif iguais:
            conclusao = "%s e %s chegaram ao mesmo menor custo, %s." % (", ".join(lista[:-1]), lista[-1], _fmt(menor))
        else:
            conclusao = "os algoritmos de menor custo divergiram: " + ", ".join("%s %s" % (NOMES[a], _fmt(c)) for a, c in custos.items())
    elif any(l["situacao"] == "sem_caminho" for l in linhas):
        conclusao = "não existe caminho de %s até %s neste grafo." % (origem, destino)
    elif any(l["situacao"] == "ciclo_negativo" for l in linhas):
        conclusao = "o grafo tem ciclo negativo alcançável a partir da origem, então o menor caminho não está definido."
    return {"origem": g.rotulos[s], "destino": g.rotulos[t], "grafo": g.origem_dados, "linhas": linhas, "conclusao": conclusao}


def _fmt(x):
    return ("%.2f" % x).rstrip("0").rstrip(".").replace(".", ",")


# Resumo estrutural: vértices, arcos, graus, conexidade (BFS no grafo e no transposto) e árvore geradora mínima
# (Kruskal sobre as arestas, tomando o menor peso entre os dois sentidos).
def resumir_grafo(g):
    grafo = g.grafo
    graus = [len(grafo.adj[u]) for u in range(grafo.n)]
    ida = alcancaveis(grafo, 0)
    volta = alcancaveis(grafo.transposto(), 0)
    fortemente = all(ida) and all(volta)
    fracas = componentes_fracamente_conexas(grafo)
    pesos = {}
    for u in range(grafo.n):
        for v, peso, _ in grafo.adj[u]:
            if u != v:
                chave = (min(u, v), max(u, v))
                pesos[chave] = min(peso, pesos.get(chave, math.inf))
    arvore, componentes = kruskal(grafo.n, [(p, u, v) for (u, v), p in pesos.items()])
    return {
        "grafo": g.origem_dados,
        "vertices": grafo.n,
        "arcos": grafo.m,
        "grau_min": min(graus) if graus else 0,
        "grau_medio": (sum(graus) / len(graus)) if graus else 0.0,
        "grau_max": max(graus) if graus else 0,
        "fortemente_conexo": fortemente,
        "componentes_fracas": len(fracas),
        "arcos_mao_unica": sum(1 for u in range(grafo.n) for v, _, _ in grafo.adj[u] if u != v and not grafo.tem_arco(v, u)),
        "agm_peso": sum(p for _, _, p in arvore),
        "agm_arestas": len(arvore),
        "agm_completa": componentes == 1,
        "tem_peso_negativo": _tem_negativo(grafo),
    }
