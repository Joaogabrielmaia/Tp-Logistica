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


# Algoritmos de caminho entre dois vértices, usados na consulta de caminhos (linha de comando e aba Caminhos).
# Cada um devolve a lista de vértices do caminho, ou None quando o destino não é alcançável a partir da origem.

class CicloNegativo(ValueError):
    def __init__(self, ciclo):
        super().__init__("ciclo de peso negativo: " + " -> ".join(map(str, ciclo)))
        self.ciclo = ciclo


# Busca em largura: ignora os pesos e acha o caminho com menos arcos, O(n + m).
def bfs_caminho(grafo, origem, destino):
    from collections import deque
    pred = [-1] * grafo.n
    visto = [False] * grafo.n
    visto[origem] = True
    fila = deque([origem])
    while fila:
        u = fila.popleft()
        if u == destino:
            break
        for v, _, _ in grafo.adj[u]:
            if not visto[v]:
                visto[v] = True
                pred[v] = u
                fila.append(v)
    return reconstruir_caminho(pred, origem, destino)


# Busca em profundidade com pilha explícita (sem recursão, então não estoura em grafos grandes). Devolve o primeiro
# caminho que encontra, que em geral não é o menor: serve para mostrar a diferença em relação à BFS e ao Dijkstra.
def dfs_caminho(grafo, origem, destino):
    pred = [-1] * grafo.n
    visto = [False] * grafo.n
    pilha = [origem]
    while pilha:
        u = pilha.pop()
        if visto[u]:
            continue
        visto[u] = True
        if u == destino:
            break
        for v, _, _ in reversed(grafo.adj[u]):
            if not visto[v]:
                pred[v] = u
                pilha.append(v)
    return reconstruir_caminho(pred, origem, destino)


def dijkstra_caminho(grafo, origem, destino):
    dist, _, pred = dijkstra(grafo, origem)
    return reconstruir_caminho(pred, origem, destino) if dist[destino] < math.inf else None


# A*: Dijkstra guiado por uma estimativa h(v) do que falta até o destino. A estimativa é a distância em linha reta
# multiplicada pela menor razão peso/linha reta entre os arcos do grafo; assim nenhum caminho fica mais curto que
# h(v) (nem com o arredondamento das bases), h nunca superestima e o caminho devolvido é ótimo.
def a_estrela(grafo, origem, destino, coordenadas=None):
    h = [0.0] * grafo.n
    if coordenadas:
        def reta(a, b):
            return math.hypot(coordenadas[a][0] - coordenadas[b][0], coordenadas[a][1] - coordenadas[b][1])
        razao = math.inf
        for u in range(grafo.n):
            for v, peso, _ in grafo.adj[u]:
                r = reta(u, v)
                if r > 1e-12:
                    razao = min(razao, peso / r)
        if razao == math.inf:
            razao = 0.0
        razao = max(0.0, razao)
        h = [razao * reta(v, destino) for v in range(grafo.n)]
    dist = [math.inf] * grafo.n
    pred = [-1] * grafo.n
    dist[origem] = 0.0
    fila = [(h[origem], origem)]
    fechado = [False] * grafo.n
    while fila:
        _, u = heapq.heappop(fila)
        if fechado[u]:
            continue
        fechado[u] = True
        if u == destino:
            break
        for v, peso, _ in grafo.adj[u]:
            nd = dist[u] + peso
            if nd < dist[v]:
                dist[v] = nd
                pred[v] = u
                heapq.heappush(fila, (nd + h[v], v))
    return reconstruir_caminho(pred, origem, destino) if dist[destino] < math.inf else None


# Bellman-Ford: relaxa todos os arcos até n-1 vezes, O(nm). Aceita peso negativo; se ainda relaxar na rodada n, há
# um ciclo negativo alcançável e não existe menor caminho (dá para diminuir o custo sem fim).
def bellman_ford(grafo, origem):
    n = grafo.n
    dist = [math.inf] * n
    pred = [-1] * n
    dist[origem] = 0.0
    for _ in range(n - 1):
        mudou = False
        for u in range(n):
            if dist[u] == math.inf:
                continue
            for v, peso, _ in grafo.adj[u]:
                if dist[u] + peso < dist[v]:
                    dist[v] = dist[u] + peso
                    pred[v] = u
                    mudou = True
        if not mudou:
            break
    for u in range(n):
        if dist[u] == math.inf:
            continue
        for v, peso, _ in grafo.adj[u]:
            if dist[u] + peso < dist[v]:
                pred[v] = u
                x = v
                for _ in range(n):
                    x = pred[x]
                ciclo = [x]
                y = pred[x]
                while y != x:
                    ciclo.append(y)
                    y = pred[y]
                ciclo.append(x)
                ciclo.reverse()
                raise CicloNegativo(ciclo)
    return dist, pred


def bellman_ford_caminho(grafo, origem, destino):
    dist, pred = bellman_ford(grafo, origem)
    return reconstruir_caminho(pred, origem, destino) if dist[destino] < math.inf else None


# Floyd-Warshall: menores caminhos entre todos os pares, O(n^3) em tempo e O(n^2) em memória. prox[i][j] guarda o
# vértice seguinte a i no caminho até j, o que permite reconstruir o trajeto.
def floyd_warshall(grafo):
    n = grafo.n
    D = grafo.matriz_pesos()
    prox = [[(j if D[i][j] < math.inf else -1) for j in range(n)] for i in range(n)]
    for i in range(n):
        prox[i][i] = i
    for k in range(n):
        Dk = D[k]
        for i in range(n):
            dik = D[i][k]
            if dik == math.inf:
                continue
            Di = D[i]
            pi = prox[i]
            pik = pi[k]
            for j in range(n):
                nd = dik + Dk[j]
                if nd < Di[j]:
                    Di[j] = nd
                    pi[j] = pik
    for i in range(n):
        if D[i][i] < 0:
            # D[i][i] < 0 quer dizer que dá para sair de i e voltar com custo negativo
            raise CicloNegativo([i, "...", i])
    return D, prox


def floyd_warshall_caminho(grafo, origem, destino, matrizes=None):
    D, prox = matrizes or floyd_warshall(grafo)
    if prox[origem][destino] == -1:
        return None
    caminho = [origem]
    atual = origem
    while atual != destino:
        atual = prox[atual][destino]
        caminho.append(atual)
    return caminho
