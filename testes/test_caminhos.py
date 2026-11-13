import math
import random
import unittest

from logistica.caminhos import dijkstra, matrizes_de_caminhos, reconstruir_caminho
from logistica.grafo import GrafoDirigido


def floyd_warshall(g):
    M = g.matriz_pesos()
    n = g.n
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if M[i][k] + M[k][j] < M[i][j]:
                    M[i][j] = M[i][k] + M[k][j]
    return M


def grafo_aleatorio(rng, n, densidade, pesos_iguais=False, zeros=False):
    g = GrafoDirigido(n)
    for u in range(n):
        for v in range(n):
            if u != v and rng.random() < densidade:
                if pesos_iguais:
                    p = 1.0
                elif zeros and rng.random() < 0.2:
                    p = 0.0
                else:
                    p = float(rng.randint(1, 20))
                g.adicionar_arco(u, v, p)
    return g


class TesteDijkstra(unittest.TestCase):
    def test_contra_floyd_warshall(self):
        rng = random.Random(11)
        for caso in range(60):
            n = rng.randint(2, 14)
            g = grafo_aleatorio(rng, n, rng.choice([0.1, 0.3, 0.7]), pesos_iguais=caso % 5 == 0, zeros=caso % 7 == 0)
            ref = floyd_warshall(g)
            D, _, _ = matrizes_de_caminhos(g)
            for i in range(n):
                for j in range(n):
                    self.assertAlmostEqual(D[i][j], ref[i][j], places=9) if not math.isinf(ref[i][j]) else self.assertTrue(math.isinf(D[i][j]))

    def test_caminho_reconstruido_soma_a_distancia(self):
        rng = random.Random(5)
        g = grafo_aleatorio(rng, 12, 0.3)
        for origem in range(12):
            dist, _, pred = dijkstra(g, origem)
            for destino in range(12):
                caminho = reconstruir_caminho(pred, origem, destino)
                if math.isinf(dist[destino]):
                    self.assertIsNone(caminho)
                else:
                    self.assertEqual(caminho[0], origem)
                    self.assertEqual(caminho[-1], destino)
                    soma = sum(g.peso(a, b) for a, b in zip(caminho, caminho[1:]))
                    self.assertAlmostEqual(soma, dist[destino], places=9)

    def test_tempo_acompanha_o_caminho(self):
        g = GrafoDirigido(3)
        g.adicionar_arco(0, 1, 1.0, 10.0)
        g.adicionar_arco(1, 2, 1.0, 20.0)
        g.adicionar_arco(0, 2, 5.0, 1.0)
        dist, tempo, _ = dijkstra(g, 0)
        self.assertEqual(dist[2], 2.0)
        self.assertEqual(tempo[2], 30.0)

    def test_origem_isolada(self):
        g = GrafoDirigido(3)
        dist, _, pred = dijkstra(g, 1)
        self.assertEqual(dist[1], 0.0)
        self.assertTrue(math.isinf(dist[0]))
        self.assertEqual(reconstruir_caminho(pred, 1, 1), [1])


if __name__ == "__main__":
    unittest.main()
