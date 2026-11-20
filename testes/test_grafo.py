import itertools
import random
import unittest

from logistica.grafo import (GrafoDirigido, UnionFind, alcancaveis, clientes_inalcancaveis,
                             componentes_fracamente_conexas, kruskal)


class TesteUnionFind(unittest.TestCase):
    def test_unir_e_encontrar(self):
        uf = UnionFind(6)
        self.assertEqual(uf.componentes, 6)
        self.assertTrue(uf.unir(0, 1))
        self.assertTrue(uf.unir(1, 2))
        self.assertFalse(uf.unir(0, 2))
        self.assertEqual(uf.encontrar(0), uf.encontrar(2))
        self.assertNotEqual(uf.encontrar(0), uf.encontrar(3))
        self.assertEqual(uf.componentes, 4)


class TesteGrafo(unittest.TestCase):
    def test_arcos_e_pesos(self):
        g = GrafoDirigido(3)
        g.adicionar_arco(0, 1, 2.5, 4.0)
        self.assertTrue(g.tem_arco(0, 1))
        self.assertFalse(g.tem_arco(1, 0))
        self.assertEqual(g.peso(0, 1), 2.5)
        self.assertEqual(g.tempo(0, 1), 4.0)
        self.assertIsNone(g.peso(1, 0))
        g.adicionar_arco(0, 1, 1.0)
        self.assertEqual(g.peso(0, 1), 1.0)
        self.assertEqual(g.m, 2)

    def test_entradas_invalidas(self):
        g = GrafoDirigido(2)
        with self.assertRaises(ValueError):
            g.adicionar_arco(0, 5, 1.0)
        with self.assertRaises(ValueError):
            g.adicionar_arco(0, 1, -1.0)

    def test_transposto(self):
        g = GrafoDirigido(3)
        g.adicionar_arco(0, 1, 1.0)
        g.adicionar_arco(1, 2, 2.0)
        t = g.transposto()
        self.assertTrue(t.tem_arco(1, 0))
        self.assertTrue(t.tem_arco(2, 1))
        self.assertFalse(t.tem_arco(0, 1))

    def test_matriz(self):
        g = GrafoDirigido(3)
        g.adicionar_aresta(0, 1, 3.0)
        M = g.matriz_pesos()
        self.assertEqual(M[0][1], 3.0)
        self.assertEqual(M[1][1], 0.0)
        self.assertEqual(M[0][2], float("inf"))


class TesteConexidade(unittest.TestCase):
    def test_alcancaveis_e_componentes(self):
        g = GrafoDirigido(6)
        g.adicionar_aresta(0, 1, 1.0)
        g.adicionar_aresta(1, 2, 1.0)
        g.adicionar_aresta(3, 4, 1.0)
        self.assertEqual(alcancaveis(g, 0), [True, True, True, False, False, False])
        comps = sorted(sorted(c) for c in componentes_fracamente_conexas(g))
        self.assertEqual(comps, [[0, 1, 2], [3, 4], [5]])
        self.assertEqual(clientes_inalcancaveis(g, 0), [3, 4, 5])

    def test_mao_unica_sem_retorno(self):
        g = GrafoDirigido(3)
        g.adicionar_aresta(0, 1, 1.0)
        g.adicionar_arco(1, 2, 1.0)
        self.assertEqual(clientes_inalcancaveis(g, 0), [2])

    def test_kruskal_contra_forca_bruta(self):
        rng = random.Random(7)
        for _ in range(25):
            n = rng.randint(3, 6)
            arestas = [(rng.randint(1, 9) + rng.random(), u, v) for u in range(n) for v in range(u + 1, n)]
            escolhidas, comps = kruskal(n, arestas)
            self.assertEqual(comps, 1)
            peso_kruskal = sum(p for _, _, p in escolhidas)
            melhor = None
            for comb in itertools.combinations(arestas, n - 1):
                uf = UnionFind(n)
                if all(uf.unir(u, v) for _, u, v in comb):
                    total = sum(p for p, _, _ in comb)
                    if melhor is None or total < melhor:
                        melhor = total
            self.assertAlmostEqual(peso_kruskal, melhor, places=9)

    def test_kruskal_grafo_desconexo(self):
        escolhidas, comps = kruskal(4, [(1.0, 0, 1), (2.0, 2, 3)])
        self.assertEqual(len(escolhidas), 2)
        self.assertEqual(comps, 2)


if __name__ == "__main__":
    unittest.main()
