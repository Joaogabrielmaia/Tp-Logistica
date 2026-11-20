import random
import unittest

from logistica.avaliacao import EstadoRota, melhor_insercao_em_rota
from logistica.leitor import gerar_instancia_sintetica
from logistica.modelo import Parametros
from logistica.verificador import Trechos, avaliar_rota, custo_da_rota


def instancia_com_prioridade(n, semente, modo="completo"):
    return gerar_instancia_sintetica(n, semente=semente, capacidade=80, modo=modo).com_prioridades(semente)


class TesteEstadoRota(unittest.TestCase):
    def test_estado_coincide_com_verificador(self):
        rng = random.Random(2)
        for semente in range(12):
            inst = instancia_com_prioridade(15, semente, "viario" if semente % 2 else "completo")
            par = Parametros(80, 20, custo_fixo_veiculo=3.0, peso_prioridade=0.5)
            trechos = Trechos(inst)
            for _ in range(30):
                tam = rng.randint(0, 6)
                rota = rng.sample(range(1, inst.n + 1), tam)
                est = EstadoRota(inst, par, rota)
                ok, _, d, c, p = avaliar_rota(inst, par, trechos, rota)
                self.assertEqual(est.viavel, ok)
                self.assertAlmostEqual(est.dist, d, places=6)
                self.assertAlmostEqual(est.carga, c, places=6)
                if rota:
                    self.assertAlmostEqual(est.custo, custo_da_rota(par, d, p), places=6)


class TesteInsercao(unittest.TestCase):
    def test_insercao_o1_igual_a_forca_bruta(self):
        rng = random.Random(9)
        casos = 0
        for semente in range(10):
            inst = instancia_com_prioridade(20, semente)
            for lam, dmax in ((0.0, None), (0.7, None), (0.0, 400.0), (0.3, 500.0)):
                par = Parametros(80, 20, distancia_maxima=dmax, peso_prioridade=lam)
                for _ in range(25):
                    tam = rng.randint(0, 5)
                    rota = rng.sample(range(1, inst.n + 1), tam)
                    est = EstadoRota(inst, par, rota)
                    if not est.viavel:
                        continue
                    restantes = [u for u in range(1, inst.n + 1) if u not in rota]
                    u = rng.choice(restantes)
                    melhor = None
                    for pos in range(len(rota) + 1):
                        cand = EstadoRota(inst, par, rota[:pos] + [u] + rota[pos:])
                        if cand.viavel:
                            delta = cand.custo - est.custo + (par.custo_fixo_veiculo if not rota else 0.0)
                            if melhor is None or delta < melhor - 1e-9:
                                melhor = delta
                    res = melhor_insercao_em_rota(inst, par, est, u)
                    if melhor is None:
                        self.assertIsNone(res)
                    else:
                        self.assertIsNotNone(res)
                        self.assertAlmostEqual(res[0], melhor, places=6)
                        casos += 1
        self.assertGreater(casos, 100)


if __name__ == "__main__":
    unittest.main()
