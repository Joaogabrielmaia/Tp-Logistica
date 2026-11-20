import glob
import os
import tempfile
import unittest

from logistica.construtivo import clientes_inatendiveis
from logistica.leitor import ErroInstancia, ler_entregas_csv, ler_instancia, ler_solomon_txt
from logistica.solver import resolver
from logistica.verificador import verificar

RAIZ = os.path.join(os.path.dirname(__file__), "..", "dados", "kaggle")
CSV = os.path.join(RAIZ, "ecommerce", "entregas.csv")
GH = os.path.join(RAIZ, "gehring-homberger")


class TesteGehringHomberger(unittest.TestCase):
    def test_todas_as_300_instancias_sao_lidas(self):
        arquivos = sorted(glob.glob(os.path.join(GH, "*.txt")))
        self.assertEqual(len(arquivos), 300)
        for caminho in arquivos[::25]:
            inst = ler_solomon_txt(caminho)
            n = int(os.path.basename(caminho).split("_")[1]) * 100
            self.assertEqual(inst.n, n, caminho)
            self.assertEqual(inst.nos[0].demanda, 0)

    def test_instancia_de_200_clientes_resolvida_e_verificada(self):
        inst = ler_instancia(os.path.join(GH, "c1_2_1.txt"))
        self.assertEqual(inst.n, 200)
        self.assertEqual(inst.capacidade, 200)
        par = inst.parametros_padrao()
        res = resolver(inst, par, iteracoes=50, semente=1)
        self.assertTrue(verificar(inst, par, res.rotas, res.custo).viavel)

    def test_cabecalho_invalido(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("x\n1 2 3\n")
        with self.assertRaises(ErroInstancia):
            ler_solomon_txt(f.name)
        os.remove(f.name)


class TesteEntregas(unittest.TestCase):
    def test_leitura_e_mapeamento(self):
        inst = ler_entregas_csv(CSV, limite=50)
        self.assertEqual(inst.n, 50)
        self.assertEqual(inst.nos[0].demanda, 0)
        self.assertTrue(all(no.prioridade in (1, 2, 3) for no in inst.nos[1:]))
        self.assertTrue(all(no.fim > no.inicio for no in inst.nos[1:]))

    def test_prioridade_do_arquivo_nao_e_sobrescrita(self):
        inst = ler_entregas_csv(CSV, limite=60)
        outra = inst.com_prioridades(5)
        self.assertEqual([no.prioridade for no in inst.nos], [no.prioridade for no in outra.nos])

    def test_todas_as_1000_entregas_sao_atendiveis(self):
        inst = ler_entregas_csv(CSV)
        self.assertEqual(inst.n, 1000)
        self.assertEqual(clientes_inatendiveis(inst, inst.parametros_padrao()), [])

    def test_resolve_e_verifica_nos_dois_modos(self):
        for modo in ("completo", "viario"):
            inst = ler_entregas_csv(CSV, modo=modo, limite=40)
            par = inst.parametros_padrao()
            res = resolver(inst, par, iteracoes=100, semente=1)
            self.assertTrue(verificar(inst, par, res.rotas, res.custo).viavel, modo)

    def test_colunas_ausentes(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write("a,b\n1,2\n")
        with self.assertRaises(ErroInstancia):
            ler_entregas_csv(f.name)
        os.remove(f.name)


class TesteLimiteDeTempo(unittest.TestCase):
    def test_instancia_grande_respeita_o_prazo_e_continua_viavel(self):
        import time
        inst = ler_entregas_csv(CSV, limite=500)
        par = inst.parametros_padrao()
        inicio = time.time()
        res = resolver(inst, par, iteracoes=20000, semente=1, tempo_limite=5)
        self.assertLess(time.time() - inicio, 25)
        self.assertTrue(res.interrompido)
        self.assertTrue(verificar(inst, par, res.rotas, res.custo).viavel)

    def test_sem_limite_nao_marca_interrupcao(self):
        inst = ler_entregas_csv(CSV, limite=30)
        res = resolver(inst, inst.parametros_padrao(), iteracoes=50, semente=1)
        self.assertFalse(res.interrompido)


if __name__ == "__main__":
    unittest.main()
