import heapq
import math


def dijkstra(grafo, origem):
    inf = math.inf
    dist = [inf] * grafo.n
    tempo = [inf] * grafo.n
    pred = [-1] * grafo.n
    dist[origem] = 0.0
    tempo[origem] = 0.0
    fila = [(0.0, origem)]
    while fila:
        # Fila de prioridade (heap binário): cada extração custa O(log n), total O((n+m) log n). Pesos negativos são
        # recusados na construção do grafo.
        d, u = heapq.heappop(fila)
        if d > dist[u]:
            continue
        tu = tempo[u]
        for v, peso, t in grafo.adj[u]:
            nd = d + peso
            if nd < dist[v]:
                dist[v] = nd
                tempo[v] = tu + t
                pred[v] = u
                heapq.heappush(fila, (nd, v))
    return dist, tempo, pred


def reconstruir_caminho(pred, origem, destino):
    if origem == destino:
        return [origem]
    caminho = [destino]
    atual = destino
    while atual != origem:
        atual = pred[atual]
        if atual == -1:
            return None
        caminho.append(atual)
    caminho.reverse()
    return caminho


def matrizes_de_caminhos(grafo):
    D, T, P = [], [], []
    for u in range(grafo.n):
        d, t, p = dijkstra(grafo, u)
        D.append(d)
        T.append(t)
        P.append(p)
    return D, T, P
