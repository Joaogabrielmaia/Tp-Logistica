import math
import random

from .grafo import GrafoDirigido, UnionFind, kruskal


def distancia_euclidiana(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


# Convenções das bases: decimo trunca na 1ª casa (Solomon/DIMACS), inteiro arredonda ao mais próximo (conjunto X),
# exato não arredonda.
def arredondar(d, regra):
    if regra == "decimo":
        return int(d * 10 + 1e-9) / 10.0
    if regra == "inteiro":
        return float(int(d + 0.5))
    return d


def grafo_completo(nos, regra="exato"):
    n = len(nos)
    g = GrafoDirigido(n)
    for u in range(n):
        a = nos[u]
        linha = g.adj[u]
        for v in range(n):
            if u != v:
                d = arredondar(distancia_euclidiana(a, nos[v]), regra)
                linha.append((v, d, d))
        g.m += n - 1
    return g


def grafo_viario(nos, k=5, semente=0, desvio_max=0.3, fracao_mao_unica=0.0, regra="exato"):
    n = len(nos)
    rng = random.Random(semente)
    pares = []
    for u in range(n):
        for v in range(u + 1, n):
            pares.append((distancia_euclidiana(nos[u], nos[v]), u, v))
    # A árvore geradora mínima garante conexidade mesmo quando os k vizinhos mais próximos formam ilhas.
    mst, _ = kruskal(n, pares)
    base = {(min(u, v), max(u, v)) for u, v, _ in mst}
    mst_set = set(base)
    for u in range(n):
        candidatos = sorted(((distancia_euclidiana(nos[u], nos[v]), v) for v in range(n) if v != u))[:k]
        for _, v in candidatos:
            base.add((min(u, v), max(u, v)))
    g = GrafoDirigido(n)
    for u, v in sorted(base):
        # Desvio aleatório sobre a reta: ruas reais são mais longas que a distância euclidiana.
        d = arredondar(distancia_euclidiana(nos[u], nos[v]) * (1.0 + rng.random() * desvio_max), regra)
        # Arestas da árvore ficam sempre de mão dupla, para que a conexidade não dependa do sorteio das mãos únicas.
        if (u, v) in mst_set or rng.random() >= fracao_mao_unica:
            g.adicionar_aresta(u, v, d)
        elif rng.random() < 0.5:
            g.adicionar_arco(u, v, d)
        else:
            g.adicionar_arco(v, u, d)
    return g
