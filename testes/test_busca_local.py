import random
import unittest

from logistica.avaliacao import EPS, EstadoRota, Solucao
from logistica.busca_local import polir
from logistica.construtivo import economias
from logistica.leitor import gerar_instancia_sintetica
from logistica.modelo import Parametros


def _algum_movimento_melhora(inst, par, sol):
    estados = sol.estados
    for a, ra in enumerate(estados):
        for i in range(len(ra.nos) - 1):
            for j in range(i + 1, len(ra.nos)):
                nos = ra.nos[:i] + ra.nos[i:j + 1][::-1] + ra.nos[j + 1:]
                e = EstadoRota(inst, par, nos)
                if e.viavel and e.custo < ra.custo - EPS:
                    return "inverter"
        for b in range(a + 1, len(estados)):
            rb = estados[b]
            base = ra.custo + rb.custo
            for i, u in enumerate(ra.nos):
                for j, v in enumerate(rb.nos):
                    ea = EstadoRota(inst, par, ra.nos[:i] + [v] + ra.nos[i + 1:])
                    eb = EstadoRota(inst, par, rb.nos[:j] + [u] + rb.nos[j + 1:])
                    if ea.viavel and eb.viavel and ea.custo + eb.custo < base - EPS:
                        return "trocar"
            for i in range(len(ra.nos) + 1):
                for j in range(len(rb.nos) + 1):
                    if (i == len(ra.nos) and j == len(rb.nos)) or (i == 0 and j == 0):
                        continue
                    ea = EstadoRota(inst, par, ra.nos[:i] + rb.nos[j:])
                    eb = EstadoRota(inst, par, rb.nos[:j] + ra.nos[i:])
                    if ea.viavel and eb.viavel and ea.custo + eb.custo < base - EPS:
                        return "cauda"
    return None


class TesteFiltrosDaBuscaLocal(unittest.TestCase):
    def _conferir(self, inst, par, sol=None):
        sol = sol or economias(inst, par)
        polir(inst, par, sol)
        self.assertTrue(all(e.viavel for e in sol.estados))
        self.assertIsNone(_algum_movimento_melhora(inst, par, Solucao(list(sol.estados))))

    def test_otimo_local_com_avaliacao_completa(self):
        for semente in range(4):
            inst = gerar_instancia_sintetica(35, semente=semente, capacidade=60)
            self._conferir(inst, inst.parametros_padrao())

    def test_com_prioridade_custo_fixo_e_distancia_maxima(self):
        inst = gerar_instancia_sintetica(30, semente=9, capacidade=60).com_prioridades(9)
        base = inst.parametros_padrao()
        self._conferir(inst, Parametros(base.capacidade, base.frota_maxima, distancia_maxima=350, custo_fixo_veiculo=40, peso_prioridade=0.5))

    def test_rotas_longas_sem_janelas_a_partir_de_solucao_aleatoria(self):
        for semente in range(3):
            inst = gerar_instancia_sintetica(45, semente=semente, capacidade=150, janelas=False)
            par = inst.parametros_padrao()
            clientes = list(range(1, inst.n + 1))
            random.Random(semente).shuffle(clientes)
            rotas, atual, carga = [], [], 0.0
            for u in clientes:
                if carga + inst.q[u] > par.capacidade:
                    rotas.append(atual)
                    atual, carga = [], 0.0
                atual.append(u)
                carga += inst.q[u]
            rotas.append(atual)
            inicial = Solucao.de_rotas(inst, par, rotas)
            self.assertIsNotNone(_algum_movimento_melhora(inst, par, Solucao(list(inicial.estados))))
            self._conferir(inst, par, inicial)

    def test_rede_viaria_assimetrica(self):
        inst = gerar_instancia_sintetica(30, semente=5, capacidade=60, modo="viario")
        self._conferir(inst, inst.parametros_padrao())


if __name__ == "__main__":
    unittest.main()
