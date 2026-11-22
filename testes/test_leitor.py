import glob
import os
import tempfile
import unittest

from logistica.grafo import clientes_inalcancaveis
from logistica.leitor import LIMITE_CLIENTES, ErroInstancia, gerar_instancia_sintetica, ler_vrplib, listar_instancias
from logistica.rede_viaria import arredondar
from logistica.verificador import verificar

RAIZ = os.path.join(os.path.dirname(__file__), "..", "dados")


class TesteReferencias(unittest.TestCase):
    def test_todas_as_bks_sao_viaveis_e_reproduzem_o_custo(self):
        arquivos = sorted(glob.glob(os.path.join(RAIZ, "*", "*.vrp")))
        self.assertEqual(len(arquivos), 65)
        for caminho in arquivos:
            inst = ler_vrplib(caminho)
            par = inst.parametros_padrao()
            rel = verificar(inst, par, inst.bks_rotas, custo_informado=inst.bks_custo)
            self.assertTrue(rel.viavel, (caminho, rel.erros))
            self.assertAlmostEqual(rel.distancia, inst.bks_custo, places=4, msg=caminho)

    def test_listagem(self):
        nomes = listar_instancias(RAIZ)
        self.assertIn("solomon/C101.vrp", nomes)
        self.assertEqual(len([n for n in nomes if n.endswith(".vrp")]), 65)
        self.assertIn("kaggle/ecommerce/entregas.csv", nomes)
        self.assertEqual(len([n for n in nomes if n.startswith("kaggle/gehring-homberger/")]), 300)


class TesteArredondamento(unittest.TestCase):
    def test_regras(self):
        self.assertEqual(arredondar(3.99, "decimo"), 3.9)
        self.assertEqual(arredondar(5.0, "decimo"), 5.0)
        self.assertEqual(arredondar(3.5, "inteiro"), 4.0)
        self.assertEqual(arredondar(3.49, "inteiro"), 3.0)
        self.assertEqual(arredondar(3.14159, "exato"), 3.14159)


class TesteErros(unittest.TestCase):
    def escrever(self, texto):
        fd, caminho = tempfile.mkstemp(suffix=".vrp")
        with os.fdopen(fd, "w") as f:
            f.write(texto)
        self.addCleanup(os.remove, caminho)
        return caminho

    def base(self, capacidade="CAPACITY : 10", dimensao=3, demanda2=5):
        return ("NAME : t\nTYPE : CVRP\nDIMENSION : %d\n%s\nEDGE_WEIGHT_TYPE : EUC_2D\nNODE_COORD_SECTION\n"
                "1 0 0\n2 3 4\n3 6 8\nDEMAND_SECTION\n1 0\n2 %d\n3 4\nDEPOT_SECTION\n1\n-1\nEOF\n" % (dimensao, capacidade, demanda2))

    def test_arquivo_valido(self):
        inst = ler_vrplib(self.escrever(self.base()))
        self.assertEqual(inst.n, 2)
        self.assertEqual(inst.D[0][1], 5.0)

    def test_arquivo_inexistente(self):
        with self.assertRaises(ErroInstancia):
            ler_vrplib("/nao/existe.vrp")

    def test_capacidade_ausente(self):
        with self.assertRaises(ErroInstancia):
            ler_vrplib(self.escrever(self.base(capacidade="")))

    def test_dimensao_inconsistente(self):
        with self.assertRaises(ErroInstancia):
            ler_vrplib(self.escrever(self.base(dimensao=7)))
        # acima do limite de clientes a instância é recusada antes de montar as matrizes n²
        n = LIMITE_CLIENTES + 2
        texto = ("NAME : grande\nTYPE : CVRP\nDIMENSION : %d\nCAPACITY : 10\nEDGE_WEIGHT_TYPE : EUC_2D\nNODE_COORD_SECTION\n" % n
                 + "".join("%d %d %d\n" % (i + 1, i % 97, i // 97) for i in range(n)) + "DEMAND_SECTION\n"
                 + "".join("%d %d\n" % (i + 1, 0 if i == 0 else 1) for i in range(n)) + "DEPOT_SECTION\n1\n-1\nEOF\n")
        with self.assertRaises(ErroInstancia) as ctx:
            ler_vrplib(self.escrever(texto))
        self.assertIn("grande demais", str(ctx.exception))

    def test_demanda_maior_que_capacidade(self):
        with self.assertRaises(ErroInstancia):
            ler_vrplib(self.escrever(self.base(demanda2=50)))

    def test_secao_ausente(self):
        with self.assertRaises(ErroInstancia):
            ler_vrplib(self.escrever("NAME : t\nCAPACITY : 5\nNODE_COORD_SECTION\n1 0 0\nEOF\n"))


class TesteRedeViaria(unittest.TestCase):
    def test_rede_conexa_e_sem_clientes_isolados(self):
        for semente in range(8):
            inst = gerar_instancia_sintetica(40, semente=semente, modo="viario", janelas=False)
            self.assertEqual(clientes_inalcancaveis(inst.grafo, 0), [])
            for linha in inst.D:
                self.assertTrue(all(d < float("inf") for d in linha))

    def test_distancia_viaria_nunca_menor_que_a_euclidiana(self):
        inst = gerar_instancia_sintetica(30, semente=3, modo="viario", janelas=False)
        from logistica.rede_viaria import distancia_euclidiana
        for u in range(inst.n + 1):
            for v in range(inst.n + 1):
                self.assertGreaterEqual(inst.D[u][v] + 1e-9, distancia_euclidiana(inst.nos[u], inst.nos[v]))

    def test_caminho_fisico_usa_arcos_existentes(self):
        inst = gerar_instancia_sintetica(30, semente=4, modo="viario", janelas=False)
        caminho = inst.caminho_fisico(0, 17)
        self.assertEqual(caminho[0], 0)
        self.assertEqual(caminho[-1], 17)
        soma = 0.0
        for a, b in zip(caminho, caminho[1:]):
            self.assertTrue(inst.grafo.tem_arco(a, b))
            soma += inst.grafo.peso(a, b)
        self.assertAlmostEqual(soma, inst.D[0][17], places=9)

    def test_instancias_sinteticas_sempre_atendiveis_individualmente(self):
        from logistica.construtivo import clientes_inatendiveis
        for modo in ("completo", "viario"):
            for semente in range(25):
                inst = gerar_instancia_sintetica(80, semente=semente, modo=modo)
                self.assertEqual(clientes_inatendiveis(inst, inst.parametros_padrao()), [], (modo, semente))

    def test_modo_completo_tem_todos_os_arcos(self):
        inst = gerar_instancia_sintetica(10, semente=1, modo="completo")
        self.assertEqual(inst.grafo.m, 11 * 10)


if __name__ == "__main__":
    unittest.main()
