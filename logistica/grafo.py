import math
from collections import deque


class GrafoDirigido:
    def __init__(self, n):
        self.n = n
        self.adj = [[] for _ in range(n)]
        self.m = 0
        self._mapas = {}

    def adicionar_arco(self, u, v, peso, tempo=None):
        if not (0 <= u < self.n and 0 <= v < self.n):
            raise ValueError("vértice fora do intervalo")
        if peso < 0:
            raise ValueError("peso negativo não suportado")
        self.adj[u].append((v, peso, peso if tempo is None else tempo))
        self.m += 1
        self._mapas.pop(u, None)

    def adicionar_aresta(self, u, v, peso, tempo=None):
        self.adicionar_arco(u, v, peso, tempo)
        self.adicionar_arco(v, u, peso, tempo)

    def sucessores(self, u):
        return self.adj[u]

    def grau_saida(self, u):
        return len(self.adj[u])

    def _mapa(self, u):
        mapa = self._mapas.get(u)
        if mapa is None:
            mapa = {}
            for v, peso, tempo in self.adj[u]:
                if v not in mapa or peso < mapa[v][0]:
                    mapa[v] = (peso, tempo)
            self._mapas[u] = mapa
        return mapa

    def tem_arco(self, u, v):
        return v in self._mapa(u)

    def peso(self, u, v):
        par = self._mapa(u).get(v)
        return None if par is None else par[0]

    def tempo(self, u, v):
        par = self._mapa(u).get(v)
        return None if par is None else par[1]

    # Grafo com os arcos invertidos; a BFS no original e no transposto confirma que o cliente tem caminho de ida e de
    # volta ao depósito.
    def transposto(self):
        g = GrafoDirigido(self.n)
        for u in range(self.n):
            for v, peso, tempo in self.adj[u]:
                g.adicionar_arco(v, u, peso, tempo)
        return g

    def matriz_pesos(self):
        inf = math.inf
        M = [[inf] * self.n for _ in range(self.n)]
        for u in range(self.n):
            M[u][u] = 0.0
            for v, peso, _ in self.adj[u]:
                if peso < M[u][v]:
                    M[u][v] = peso
        return M


# Conjuntos disjuntos com compressão de caminho e união por posto: operações em tempo quase constante amortizado.
class UnionFind:
    def __init__(self, n):
        self.pai = list(range(n))
        self.posto = [0] * n
        self.componentes = n

    def encontrar(self, x):
        raiz = x
        while self.pai[raiz] != raiz:
            raiz = self.pai[raiz]
        while self.pai[x] != raiz:
            self.pai[x], x = raiz, self.pai[x]
        return raiz

    def unir(self, a, b):
        ra, rb = self.encontrar(a), self.encontrar(b)
        if ra == rb:
            return False
        if self.posto[ra] < self.posto[rb]:
            ra, rb = rb, ra
        self.pai[rb] = ra
        if self.posto[ra] == self.posto[rb]:
            self.posto[ra] += 1
        self.componentes -= 1
        return True


def alcancaveis(grafo, origem):
    visto = [False] * grafo.n
    visto[origem] = True
    fila = deque([origem])
    while fila:
        u = fila.popleft()
        for v, _, _ in grafo.adj[u]:
            if not visto[v]:
                visto[v] = True
                fila.append(v)
    return visto


def componentes_fracamente_conexas(grafo):
    uf = UnionFind(grafo.n)
    for u in range(grafo.n):
        for v, _, _ in grafo.adj[u]:
            uf.unir(u, v)
    grupos = {}
    for v in range(grafo.n):
        grupos.setdefault(uf.encontrar(v), []).append(v)
    return list(grupos.values())


def clientes_inalcancaveis(grafo, deposito=0):
    ida = alcancaveis(grafo, deposito)
    volta = alcancaveis(grafo.transposto(), deposito)
    return [v for v in range(grafo.n) if v != deposito and not (ida[v] and volta[v])]


# Árvore geradora mínima: ordena as arestas e aceita cada uma que une componentes distintos, O(m log m).
def kruskal(n, arestas):
    uf = UnionFind(n)
    escolhidas = []
    for peso, u, v in sorted(arestas):
        if uf.unir(u, v):
            escolhidas.append((u, v, peso))
            if len(escolhidas) == n - 1:
                break
    return escolhidas, uf.componentes
