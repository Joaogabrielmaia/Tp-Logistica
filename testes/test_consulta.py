import contextlib
import io
import math
import os
import random
import tempfile
import unittest

from logistica.caminhos import (CicloNegativo, a_estrela, bellman_ford, bfs_caminho, dfs_caminho, dijkstra,
                                dijkstra_caminho, floyd_warshall)
from logistica.cli import principal
from logistica.consulta import LIMITE_FLOYD, comparar_caminhos, grafo_da_instancia, grafo_de_texto, resumir_grafo
from logistica.erros import ErroExplicado
from logistica.grafo import GrafoDirigido
from logistica.leitor import ErroInstancia, ler_instancia
from logistica.servico import ErroRequisicao, Servico

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, "dados")


def aleatorio(rng, n, densidade, negativo=False):
    g = GrafoDirigido(n, permitir_negativo=negativo)
    for u in range(n):
        for v in range(n):
            if u != v and rng.random() < densidade:
                g.adicionar_arco(u, v, float(rng.randint(0 if not negativo else 1, 20)))
    return g


def custo(g, caminho):
    return sum(g.peso(a, b) for a, b in zip(caminho, caminho[1:]))


def rodar_cli(*argv):
    saida, erro = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(erro):
        try:
            codigo = principal(list(argv))
        except SystemExit as e:
            codigo = e.code
    return codigo, saida.getvalue(), erro.getvalue()


class TestAlgoritmosDeCaminho(unittest.TestCase):
    def test_todos_concordam_com_floyd_warshall(self):
        rng = random.Random(7)
        for caso in range(40):
            n = rng.randint(2, 12)
            g = aleatorio(rng, n, rng.choice([0.15, 0.4, 0.8]))
            D, _ = floyd_warshall(g)
            dist, _, _ = dijkstra(g, 0)
            bf, _ = bellman_ford(g, 0)
            for t in range(n):
                self.assertAlmostEqual(dist[t], D[0][t])
                self.assertAlmostEqual(bf[t], D[0][t])
                c = dijkstra_caminho(g, 0, t)
                a = a_estrela(g, 0, t)
                if D[0][t] == math.inf:
                    self.assertIsNone(c)
                    self.assertIsNone(a)
                    self.assertIsNone(bfs_caminho(g, 0, t))
                    self.assertIsNone(dfs_caminho(g, 0, t))
                else:
                    self.assertAlmostEqual(custo(g, c), D[0][t])
                    self.assertAlmostEqual(custo(g, a), D[0][t])
                    d = dfs_caminho(g, 0, t)
                    self.assertEqual((d[0], d[-1]), (0, t))
                    self.assertTrue(all(g.tem_arco(x, y) for x, y in zip(d, d[1:])))

    def test_bfs_acha_o_menor_numero_de_arcos(self):
        rng = random.Random(3)
        for _ in range(30):
            n = rng.randint(2, 10)
            g = aleatorio(rng, n, 0.3)
            uns = GrafoDirigido(n)
            for u in range(n):
                for v, _, _ in g.adj[u]:
                    uns.adicionar_arco(u, v, 1.0)
            D, _ = floyd_warshall(uns)
            for t in range(n):
                c = bfs_caminho(g, 0, t)
                self.assertEqual(c is None, D[0][t] == math.inf)
                if c:
                    self.assertEqual(len(c) - 1, D[0][t])

    def test_a_estrela_otimo_com_arredondamento_das_bases(self):
        for arquivo, modo in (("solomon/R101.vrp", "viario"), ("cvrp-x/X-n101-k25.vrp", "completo")):
            inst = ler_instancia(os.path.join(DADOS, arquivo), modo=modo)
            coords = [(no.x, no.y) for no in inst.nos]
            dist, _, _ = dijkstra(inst.grafo, 0)
            for t in (1, 15, 50, inst.n):
                self.assertAlmostEqual(custo(inst.grafo, a_estrela(inst.grafo, 0, t, coords)), dist[t])

    def test_peso_negativo_so_bellman_ford_e_floyd(self):
        g = grafo_de_texto("A B 4\nB C -2\nA C 3", dirigido=True)
        r = comparar_caminhos(g, "A", "C")
        por = {l["algoritmo"]: l for l in r["linhas"]}
        self.assertEqual(por["dijkstra"]["situacao"], "nao_aplicavel")
        self.assertEqual(por["a_estrela"]["situacao"], "nao_aplicavel")
        self.assertEqual(por["bellman_ford"]["custo"], 2.0)
        self.assertEqual(por["floyd_warshall"]["custo"], 2.0)
        self.assertEqual(por["bfs"]["custo"], 3.0)

    def test_ciclo_negativo_detectado(self):
        g = grafo_de_texto("A B 4; B C -6; C A 1", dirigido=True)
        with self.assertRaises(CicloNegativo) as ctx:
            bellman_ford(g.grafo, 0)
        self.assertEqual(ctx.exception.ciclo[0], ctx.exception.ciclo[-1])
        r = comparar_caminhos(g, "A", "C")
        self.assertIn("ciclo negativo", r["conclusao"])
        r = comparar_caminhos(grafo_de_texto("A B -1"), "A", "B")
        self.assertIn("não dirigida", r["conclusao"])

    def test_dois_vertices_e_uma_aresta(self):
        r = comparar_caminhos(grafo_de_texto("A B 1"), "A", "B")
        self.assertTrue(all(l["caminho"] == ["A", "B"] and l["custo"] == 1.0 for l in r["linhas"]))
        r = comparar_caminhos(grafo_de_texto("A B 1", dirigido=True), "B", "A")
        self.assertTrue(all(l["situacao"] == "sem_caminho" for l in r["linhas"]))

    def test_origem_igual_ao_destino(self):
        r = comparar_caminhos(grafo_de_texto("A B 1"), "A", "A")
        self.assertTrue(all(l["caminho"] == ["A"] and l["custo"] == 0 for l in r["linhas"]))

    def test_floyd_recusado_acima_do_limite(self):
        inst = ler_instancia(os.path.join(DADOS, "kaggle/ecommerce/entregas.csv"), modo="viario")
        self.assertGreater(inst.grafo.n, LIMITE_FLOYD)
        r = comparar_caminhos(grafo_da_instancia(inst), 0, 10, ("dijkstra", "floyd_warshall"))
        self.assertEqual(r["linhas"][1]["situacao"], "nao_aplicavel")
        self.assertIn("O(n³)", r["linhas"][1]["observacao"])


class TestGrafoDigitado(unittest.TestCase):
    def test_erros_de_formato(self):
        for texto in ("", "   ", "A B x", "A B 1 2", "A B nan", "# só comentário"):
            with self.assertRaises(ErroExplicado) as ctx:
                grafo_de_texto(texto)
            self.assertTrue(ctx.exception.motivo)
        self._arquivo_grande_pela_linha_de_comando()

    def test_virgula_decimal_e_vertice_isolado(self):
        g = grafo_de_texto("A B 2,5\nC")
        self.assertEqual(g.grafo.peso(0, 1), 2.5)
        self.assertEqual(g.grafo.n, 3)
        self.assertEqual(resumir_grafo(g)["componentes_fracas"], 2)

    def test_vertice_inexistente(self):
        with self.assertRaises(ErroExplicado) as ctx:
            comparar_caminhos(grafo_de_texto("A B 1"), "A", "Z")
        self.assertIn("A, B", ctx.exception.motivo)

    def test_mao_unica_mantem_conexidade(self):
        inst = ler_instancia(os.path.join(DADOS, "solomon/R101.vrp"), modo="viario", mao_unica=0.5)
        r = resumir_grafo(grafo_da_instancia(inst))
        self.assertGreater(r["arcos_mao_unica"], 0)
        self.assertTrue(r["fortemente_conexo"])
        codigo, _, erro = rodar_cli("grafo", os.path.join(DADOS, "solomon/R101.vrp"), "--mao-unica", "0.3")
        self.assertEqual(codigo, 1)
        self.assertIn("só vale com --modo viario", erro)

    def test_resumo_da_instancia(self):
        r = resumir_grafo(grafo_da_instancia(ler_instancia(os.path.join(DADOS, "solomon/R101.vrp"), modo="viario")))
        self.assertEqual(r["vertices"], 101)
        self.assertTrue(r["fortemente_conexo"])
        self.assertEqual(r["agm_arestas"], 100)


    def _arquivo_grande_pela_linha_de_comando(self):
        # 2500 vértices em grade: o campo de texto recusa, o arquivo pela linha de comando aceita, e os três
        # algoritmos de menor custo chegam ao mesmo valor
        lado = 50
        linhas = []
        for v in range(lado * lado):
            if (v + 1) % lado:
                linhas.append("%d %d %d" % (v, v + 1, 1 + v % 7))
            if v + lado < lado * lado:
                linhas.append("%d %d %d" % (v, v + lado, 1 + v % 5))
        texto = "\n".join(linhas)
        with self.assertRaises(ErroExplicado):
            grafo_de_texto(texto)
        g = grafo_de_texto(texto, arquivo=True)
        r = comparar_caminhos(g, "0", str(lado * lado - 1), ("dijkstra", "a_estrela", "bellman_ford"))
        custos = {l["custo"] for l in r["linhas"]}
        self.assertEqual(len(custos), 1)
        with tempfile.TemporaryDirectory() as d:
            caminho = os.path.join(d, "grade.txt")
            with open(caminho, "w", encoding="utf-8") as arq:
                arq.write(texto)
            with contextlib.redirect_stdout(io.StringIO()) as saida:
                self.assertEqual(principal(["caminho", "--grafo-arquivo", caminho, "0", str(lado * lado - 1), "--algoritmos", "dijkstra"]), 0)
            self.assertIn("Dijkstra", saida.getvalue())


class TestErrosExplicados(unittest.TestCase):
    def test_cli_sem_traceback(self):
        casos = [
            ("resolver", "nao_existe.vrp"),
            ("resolver", os.path.join(DADOS, "solomon/R101.vrp"), "--frota", "0"),
            ("resolver", os.path.join(DADOS, "solomon/R101.vrp"), "--iteracoes", "-1"),
            ("resolver", os.path.join(DADOS, "solomon/R101.vrp"), "--capacidade", "5"),
            ("resolver", os.path.join(DADOS, "solomon/R101.vrp"), "--peso-prioridade", "-1"),
            ("caminho", os.path.join(DADOS, "solomon/R101.vrp"), "0", "999"),
            ("caminho", "--arestas", "A B x", "A", "B"),
            ("grafo", os.path.join(DADOS, "solomon/R101.vrp"), "--arestas", "A B 1"),
        ]
        for argv in casos:
            codigo, _, erro = rodar_cli(*argv)
            self.assertEqual(codigo, 1, argv)
            self.assertIn("Erro:", erro)
            self.assertIn("Por quê:", erro)
            self.assertNotIn("Traceback", erro)

    def test_cli_argumento_invalido_em_portugues(self):
        codigo, _, erro = rodar_cli("resolver", "x.vrp", "--iteracoes", "abc")
        self.assertEqual(codigo, 2)
        self.assertIn("valor inteiro inválido", erro)

    def test_cli_caminho_com_grafo_proprio(self):
        codigo, saida, _ = rodar_cli("caminho", "--arestas", "A B 4; A C 1; C B 1", "A", "B")
        self.assertEqual(codigo, 0)
        self.assertIn("mesmo menor custo, 2.", saida)

    def test_leitor_formato_vazio_e_binario(self):
        with tempfile.TemporaryDirectory() as d:
            vazio = os.path.join(d, "a.vrp")
            open(vazio, "w").close()
            binario = os.path.join(d, "b.vrp")
            with open(binario, "wb") as f:
                f.write(bytes(range(256)))
            outro = os.path.join(d, "c.png")
            with open(outro, "w") as f:
                f.write("x")
            for caminho, trecho in ((vazio, "arquivo vazio"), (binario, "formato não reconhecido"), (outro, "formato não reconhecido")):
                with self.assertRaises(ErroInstancia) as ctx:
                    ler_instancia(caminho)
                self.assertIn(trecho, str(ctx.exception))

    def test_servico_explica_e_aceita_txt_e_csv(self):
        s = Servico(DADOS, os.path.join(RAIZ, "resultados"))
        with self.assertRaises(ErroRequisicao) as ctx:
            s.resolver({"arquivo": "solomon/R101.vrp", "frota": 0})
        self.assertTrue(ctx.exception.motivo and ctx.exception.dica)
        for rel, ext in (("kaggle/gehring-homberger/c1_2_1.txt", ".txt"), ("kaggle/ecommerce/entregas_100.csv", ".csv")):
            with open(os.path.join(DADOS, rel), encoding="utf-8") as f:
                chave = s.enviar({"nome": "teste", "extensao": ext, "conteudo": f.read()})
            self.assertGreater(s.instancia({"arquivo": chave})["n"], 0)
        with self.assertRaises(ErroRequisicao):
            s.enviar({"nome": "x", "extensao": ".png", "conteudo": "abc"})

    def test_pular_inatendiveis(self):
        from logistica.solver import resolver_atendiveis
        from logistica.verificador import verificar
        inst = ler_instancia(os.path.join(DADOS, "solomon/R101.vrp"), modo="viario")
        par = inst.parametros_padrao()
        res, fora = resolver_atendiveis(inst, par, iteracoes=300, semente=1)
        self.assertTrue(fora)
        atendidos = sorted(u for r in res.rotas for u in r)
        self.assertEqual(atendidos, [u for u in range(1, inst.n + 1) if u not in fora])
        self.assertTrue(verificar(inst, par, res.rotas, res.custo, exigir_todos=False).viavel)
        self.assertFalse(verificar(inst, par, res.rotas, res.custo, exigir_todos=True).viavel)
        codigo, saida, erro = rodar_cli("resolver", os.path.join(DADOS, "solomon/R101.vrp"), "--modo", "viario", "--iteracoes", "300", "--pular-inatendiveis")
        self.assertEqual(codigo, 0)
        self.assertIn("deixados de fora", saida)
        codigo, _, erro = rodar_cli("resolver", os.path.join(DADOS, "solomon/R101.vrp"), "--modo", "viario", "--iteracoes", "300")
        self.assertEqual(codigo, 1)
        self.assertIn("--pular-inatendiveis", erro)

    def test_servico_caminho(self):
        s = Servico(DADOS, os.path.join(RAIZ, "resultados"))
        r = s.caminho({"arquivo": "solomon/R101.vrp", "modo": "viario", "origem": "0", "destino": "15"})
        self.assertEqual(len(r["nos"]), 101)
        self.assertIsNotNone(r["arestas"])
        r = s.caminho({"proprio": True, "arestas": "A B 1", "origem": "A", "destino": "B"})
        self.assertEqual(r["linhas"][2]["caminho"], ["A", "B"])
        with self.assertRaises(ErroRequisicao):
            s.caminho({"proprio": True, "arestas": "A B 1", "origem": "A", "destino": ""})


if __name__ == "__main__":
    unittest.main()
