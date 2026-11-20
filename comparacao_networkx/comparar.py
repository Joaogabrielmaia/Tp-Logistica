"""Comparação de desempenho com a NetworkX, só a título de comparação.

A ferramenta (pasta logistica/) não importa a NetworkX nem nenhuma outra biblioteca de grafos; o teste
testes/test_sem_biblioteca_de_grafos.py garante isso. Este script fica fora da ferramenta: ele pega os grafos que o
nosso código monta, copia os mesmos arcos para um grafo da NetworkX e roda os dois lados, conferindo se as respostas
batem e medindo o tempo de cada um.

Uso, a partir da raiz do projeto:  python comparacao_networkx/comparar.py
Precisa de:                         pip install -r comparacao_networkx/requirements.txt
"""
import csv
import math
import os
import random
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

try:
    import networkx as nx
except ImportError:
    sys.exit("Este script de comparação precisa da NetworkX: pip install -r comparacao_networkx/requirements.txt\n"
             "(a ferramenta em si não precisa dela)")

from logistica.caminhos import CicloNegativo, a_estrela, bellman_ford, dijkstra, floyd_warshall, matrizes_de_caminhos
from logistica.grafo import GrafoDirigido, alcancaveis, kruskal
from logistica.leitor import ler_instancia

DADOS = os.path.join(RAIZ, "dados")
SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultados.csv")
INSTANCIAS = [
    ("solomon/R101.vrp", 101),
    ("solomon/C101.vrp", 101),
    ("kaggle/gehring-homberger/c1_2_1.txt", 201),
    ("kaggle/gehring-homberger/c1_4_1.txt", 401),
    ("kaggle/ecommerce/entregas.csv", 1001),
]


def para_networkx(g):
    G = nx.DiGraph()
    G.add_nodes_from(range(g.n))
    for u in range(g.n):
        for v, peso, _ in g.adj[u]:
            if not G.has_edge(u, v) or peso < G[u][v]["weight"]:
                G.add_edge(u, v, weight=peso)
    return G


def cronometrar(funcao, repeticoes=1):
    melhor = math.inf
    resultado = None
    for _ in range(repeticoes):
        t = time.perf_counter()
        resultado = funcao()
        melhor = min(melhor, time.perf_counter() - t)
    return resultado, melhor


def maior_diferenca(a, b):
    return max(abs(x - y) for x, y in zip(a, b) if x < math.inf and y < math.inf) if a else 0.0


def linha(instancia, n, m, algoritmo, ours, theirs, t_nosso, t_nx, diferenca, observacao=""):
    return {"instancia": instancia, "vertices": n, "arcos": m, "algoritmo": algoritmo,
            "respostas_iguais": "sim" if ours == theirs else "não", "maior_diferenca": "%.2e" % diferenca,
            "tempo_nosso_s": "%.4f" % t_nosso, "tempo_networkx_s": "%.4f" % t_nx,
            "razao_nosso_sobre_nx": "%.2f" % (t_nosso / t_nx if t_nx > 0 else math.nan), "observacao": observacao}


def comparar_instancia(rel):
    inst = ler_instancia(os.path.join(DADOS, rel), modo="viario")
    g, n = inst.grafo, inst.grafo.n
    G = para_networkx(g)
    nome = os.path.splitext(os.path.basename(rel))[0] + " (rede viária)"
    linhas = []
    rep = 5 if n <= 401 else 2

    # Dijkstra de uma origem (o depósito)
    (d_nosso, _, _), t1 = cronometrar(lambda: dijkstra(g, 0), rep)
    d_nx, t2 = cronometrar(lambda: nx.single_source_dijkstra_path_length(G, 0, weight="weight"), rep)
    d_nx = [d_nx.get(v, math.inf) for v in range(n)]
    dif = maior_diferenca(d_nosso, d_nx)
    linhas.append(linha(nome, n, g.m, "Dijkstra, uma origem", dif < 1e-9, True, t1, t2, dif))

    # Dijkstra de todas as origens (é o que a ferramenta faz para montar a matriz de distâncias)
    (D, _, _), t1 = cronometrar(lambda: matrizes_de_caminhos(g))
    todos, t2 = cronometrar(lambda: dict(nx.all_pairs_dijkstra_path_length(G, weight="weight")))
    dif = max(abs(D[u][v] - todos[u][v]) for u in range(n) for v in todos[u])
    linhas.append(linha(nome, n, g.m, "Dijkstra, todas as origens (matriz)", dif < 1e-9, True, t1, t2, dif))

    # A* do depósito até o último vértice, com a heurística de linha reta
    coords = [(no.x, no.y) for no in inst.nos]
    alvo = n - 1
    caminho, t1 = cronometrar(lambda: a_estrela(g, 0, alvo, coords), rep)
    custo_nosso = sum(g.peso(a, b) for a, b in zip(caminho, caminho[1:]))
    custo_nx, t2 = cronometrar(lambda: nx.astar_path_length(G, 0, alvo, heuristic=lambda a, b: 0.0, weight="weight"), rep)
    linhas.append(linha(nome, n, g.m, "A* (0 até %d)" % alvo, abs(custo_nosso - custo_nx) < 1e-9, True, t1, t2, abs(custo_nosso - custo_nx),
                        "na NetworkX sem heurística (equivale ao Dijkstra); a nossa usa a linha reta"))

    # Bellman-Ford de uma origem
    (b_nosso, _), t1 = cronometrar(lambda: bellman_ford(g, 0))
    b_nx, t2 = cronometrar(lambda: nx.single_source_bellman_ford_path_length(G, 0, weight="weight"))
    b_nx = [b_nx.get(v, math.inf) for v in range(n)]
    dif = maior_diferenca(b_nosso, b_nx)
    linhas.append(linha(nome, n, g.m, "Bellman-Ford, uma origem", dif < 1e-9, True, t1, t2, dif))

    # Floyd-Warshall (só nas menores: é O(n^3))
    if n <= 201:
        (F, _), t1 = cronometrar(lambda: floyd_warshall(g))
        F_nx, t2 = cronometrar(lambda: nx.floyd_warshall(G, weight="weight"))
        dif = max(abs(F[u][v] - F_nx[u][v]) for u in range(n) for v in range(n) if F[u][v] < math.inf)
        linhas.append(linha(nome, n, g.m, "Floyd-Warshall, todos os pares", dif < 1e-9, True, t1, t2, dif))

    # Árvore geradora mínima (Kruskal com union-find), sobre as arestas sem direção
    pesos = {}
    for u in range(n):
        for v, p, _ in g.adj[u]:
            chave = (min(u, v), max(u, v))
            pesos[chave] = min(p, pesos.get(chave, math.inf))
    arestas = [(p, u, v) for (u, v), p in pesos.items()]
    (arvore, _), t1 = cronometrar(lambda: kruskal(n, arestas), rep)
    Gu = nx.Graph()
    Gu.add_weighted_edges_from((u, v, p) for p, u, v in arestas)
    T, t2 = cronometrar(lambda: nx.minimum_spanning_tree(Gu, weight="weight", algorithm="kruskal"), rep)
    w1, w2 = sum(p for _, _, p in arvore), T.size(weight="weight")
    linhas.append(linha(nome, n, g.m, "Kruskal (peso da árvore geradora mínima)", abs(w1 - w2) < 1e-6, True, t1, t2, abs(w1 - w2)))

    # Conexidade forte: BFS no grafo e no transposto, a partir do depósito
    forte, t1 = cronometrar(lambda: all(alcancaveis(g, 0)) and all(alcancaveis(g.transposto(), 0)), rep)
    forte_nx, t2 = cronometrar(lambda: nx.is_strongly_connected(G), rep)
    linhas.append(linha(nome, n, g.m, "BFS (fortemente conexo?)", forte, forte_nx, t1, t2, 0.0, "as duas respostas: %s" % ("sim" if forte else "não")))
    return linhas


# Grafos aleatórios com peso negativo: o Bellman-Ford precisa achar a mesma distância ou o mesmo diagnóstico de ciclo.
def comparar_negativos(casos=200):
    rng = random.Random(11)
    iguais, ciclos = 0, 0
    t_nosso = t_nx = 0.0
    for _ in range(casos):
        n = rng.randint(3, 12)
        g = GrafoDirigido(n, permitir_negativo=True)
        G = nx.DiGraph()
        G.add_nodes_from(range(n))
        for u in range(n):
            for v in range(n):
                if u != v and rng.random() < 0.3:
                    p = float(rng.randint(-3, 10))
                    g.adicionar_arco(u, v, p)
                    G.add_edge(u, v, weight=p)
        t = time.perf_counter()
        try:
            nosso = bellman_ford(g, 0)[0]
        except CicloNegativo:
            nosso = "ciclo"
        t_nosso += time.perf_counter() - t
        t = time.perf_counter()
        try:
            d = nx.single_source_bellman_ford_path_length(G, 0, weight="weight")
            deles = [d.get(v, math.inf) for v in range(n)]
        except nx.NetworkXUnbounded:
            deles = "ciclo"
        t_nx += time.perf_counter() - t
        ciclos += deles == "ciclo"
        iguais += (nosso == deles) if isinstance(nosso, str) or isinstance(deles, str) else maior_diferenca(nosso, deles) < 1e-9
    return linha("%d grafos aleatórios com peso negativo" % casos, "3 a 12", "-", "Bellman-Ford (distância ou ciclo negativo)",
                 iguais == casos, True, t_nosso, t_nx, 0.0, "%d de %d iguais; %d tinham ciclo negativo" % (iguais, casos, ciclos))


def main():
    linhas = []
    for rel, _ in INSTANCIAS:
        print("comparando", rel, flush=True)
        linhas += comparar_instancia(rel)
    linhas.append(comparar_negativos())
    with open(SAIDA, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)
    print("\nNetworkX %s, Python %s" % (nx.__version__, sys.version.split()[0]))
    for l in linhas:
        print("%-28s %-42s iguais=%-3s nosso=%ss nx=%ss" % (l["instancia"][:28], l["algoritmo"][:42], l["respostas_iguais"], l["tempo_nosso_s"], l["tempo_networkx_s"]))
    print("gravado", SAIDA)


if __name__ == "__main__":
    main()
