import itertools
import unittest

from logistica.exato import resolver_exato
from logistica.leitor import gerar_instancia_sintetica
from logistica.modelo import Parametros
from logistica.solver import resolver
from logistica.verificador import Trechos, avaliar_rota, custo_da_rota, verificar


def particoes(itens):
    if not itens:
        yield []
        return
    primeiro, resto = itens[0], itens[1:]
    for tamanho in range(len(resto) + 1):
        for comp in itertools.combinations(resto, tamanho):
            grupo = [primeiro] + list(comp)
            sobra = [x for x in resto if x not in comp]
            for p in particoes(sobra):
                yield [grupo] + p


def forca_bruta_total(inst, par):
    trechos = Trechos(inst)
    melhor = None
    for part in particoes(list(range(1, inst.n + 1))):
        if len(part) > par.frota_maxima:
            continue
        total = 0.0
        viavel = True
        for grupo in part:
            custo_grupo = None
            for perm in itertools.permutations(grupo):
                ok, _, d, _, p = avaliar_rota(inst, par, trechos, perm)
                if ok:
                    c = custo_da_rota(par, d, p)
                    if custo_grupo is None or c < custo_grupo:
                        custo_grupo = c
            if custo_grupo is None:
                viavel = False
                break
            total += custo_grupo
        if viavel and (melhor is None or total < melhor):
            melhor = total
    return melhor


class TesteSolverExato(unittest.TestCase):
    def test_exato_contra_enumeracao_completa(self):
        for semente in range(10):
            inst = gerar_instancia_sintetica(5, semente=semente, capacidade=50)
            par = Parametros(50, 4, custo_fixo_veiculo=2.0)
            ref = forca_bruta_total(inst, par)
            custo, rotas = resolver_exato(inst, par)
            if ref is None:
                self.assertIsNone(custo)
            else:
                self.assertAlmostEqual(custo, ref, places=6)
                self.assertTrue(verificar(inst, par, rotas, custo).viavel)

    def test_heuristica_nunca_vence_o_exato_e_quase_sempre_empata(self):
        iguais = total = 0
        for semente in range(14):
            for janelas in (True, False):
                inst = gerar_instancia_sintetica(7, semente=semente, capacidade=60, janelas=janelas)
                par = inst.parametros_padrao()
                custo, _ = resolver_exato(inst, par)
                if custo is None:
                    continue
                melhor = min(resolver(inst, par, iteracoes=1500, semente=s).custo for s in (0, 1))
                self.assertGreaterEqual(melhor, custo - 1e-6)
                total += 1
                iguais += abs(melhor - custo) < 1e-6
        self.assertGreater(total, 20)
        self.assertGreaterEqual(iguais / total, 0.95)

    def test_instancia_grande_e_recusada(self):
        inst = gerar_instancia_sintetica(12, semente=1)
        with self.assertRaises(ValueError):
            resolver_exato(inst, inst.parametros_padrao())


if __name__ == "__main__":
    unittest.main()
