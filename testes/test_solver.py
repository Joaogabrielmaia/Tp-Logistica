import os
import unittest

from logistica.construtivo import ClienteInatendivel, economias, insercao_solomon
from logistica.leitor import construir_instancia, gerar_instancia_sintetica, ler_vrplib
from logistica.modelo import No, Parametros
from logistica.solver import resolver
from logistica.verificador import verificar

RAIZ = os.path.join(os.path.dirname(__file__), "..", "dados")


def carregar(rel, **kw):
    return ler_vrplib(os.path.join(RAIZ, rel), **kw)


class TesteConstrutivos(unittest.TestCase):
    def test_construtivos_geram_solucoes_viaveis(self):
        for nome in ("solomon/C101.vrp", "solomon/R101.vrp", "solomon/RC201.vrp", "cvrp-x/X-n101-k25.vrp"):
            inst = carregar(nome)
            par = Parametros(inst.capacidade, 1000)
            for construtor in (economias, insercao_solomon):
                sol = construtor(inst, par)
                rel = verificar(inst, par, sol.rotas(), sol.custo())
                self.assertTrue(rel.viavel, (nome, construtor.__name__, rel.erros))

    def test_cliente_impossivel_e_detectado(self):
        nos = [No(0, 0, 0, 0, 0, 50, 0), No(1, 100, 0, 1, 0, 10, 0), No(2, 5, 0, 1, 0, 50, 0)]
        inst = construir_instancia("x", "CVRPTW", nos, 10, 2)
        with self.assertRaises(ClienteInatendivel) as ctx:
            economias(inst, inst.parametros_padrao())
        self.assertEqual(ctx.exception.clientes, [1])


class TesteSolver(unittest.TestCase):
    def test_solucoes_viaveis_e_proximas_da_bks(self):
        for nome in ("solomon/C101.vrp", "solomon/R101.vrp", "solomon/RC101.vrp", "solomon/R201.vrp", "cvrp-x/X-n101-k25.vrp"):
            inst = carregar(nome)
            par = inst.parametros_padrao()
            res = resolver(inst, par, iteracoes=2000, semente=1)
            rel = verificar(inst, par, res.rotas, res.custo)
            self.assertTrue(rel.viavel, (nome, rel.erros))
            self.assertGreaterEqual(res.distancia, inst.bks_custo - 1e-6, nome)
            self.assertLess(res.distancia / inst.bks_custo - 1.0, 0.08, nome)

    def test_reprodutibilidade(self):
        inst = carregar("solomon/R102.vrp")
        par = inst.parametros_padrao()
        a = resolver(inst, par, iteracoes=800, semente=5)
        b = resolver(inst, par, iteracoes=800, semente=5)
        self.assertEqual(a.rotas, b.rotas)
        self.assertEqual(a.custo, b.custo)

    def test_otimizador_nao_piora_a_solucao_inicial(self):
        inst = carregar("solomon/RC102.vrp")
        par = inst.parametros_padrao()
        res = resolver(inst, par, iteracoes=800, semente=2)
        custos = [e["custo"] for e in res.etapas]
        self.assertLessEqual(custos[-1], custos[2] + 1e-9)
        self.assertLessEqual(custos[2], min(custos[0], custos[1]) + 1e-9)

    def test_frota_insuficiente_e_sinalizada(self):
        inst = gerar_instancia_sintetica(25, semente=3, capacidade=60, janelas=False)
        par = Parametros(60, 1)
        res = resolver(inst, par, iteracoes=200, semente=0)
        self.assertFalse(res.viavel_frota)
        rel = verificar(inst, par, res.rotas)
        self.assertFalse(rel.viavel)

    def test_distancia_maxima_e_respeitada(self):
        inst = gerar_instancia_sintetica(30, semente=6, capacidade=100, janelas=False)
        par = Parametros(100, 30, distancia_maxima=260.0)
        res = resolver(inst, par, iteracoes=600, semente=0)
        rel = verificar(inst, par, res.rotas, res.custo)
        self.assertTrue(rel.viavel, rel.erros)
        self.assertTrue(all(d <= 260.0 + 1e-6 for d in rel.distancia_por_rota))

    def test_prioridade_antecipa_clientes_urgentes(self):
        melhores = 0
        for semente in range(4):
            inst = gerar_instancia_sintetica(40, semente=semente, capacidade=90).com_prioridades(semente)
            base = Parametros(90, inst.frota)
            comp = Parametros(90, inst.frota, peso_prioridade=1.0)
            r0 = resolver(inst, base, iteracoes=600, semente=1)
            r1 = resolver(inst, comp, iteracoes=600, semente=1)
            self.assertTrue(verificar(inst, comp, r1.rotas, r1.custo).viavel)

            def media_alta(rotas):
                from logistica.avaliacao import EstadoRota
                total, qtd = 0.0, 0
                for rota in rotas:
                    est = EstadoRota(inst, base, rota)
                    for u, t in zip(rota, est.E):
                        if inst.nos[u].prioridade == 1:
                            total += t
                            qtd += 1
                return total / max(1, qtd)

            if media_alta(r1.rotas) < media_alta(r0.rotas):
                melhores += 1
        self.assertGreaterEqual(melhores, 3)

    def test_modo_viario_resolve_e_verifica(self):
        inst = gerar_instancia_sintetica(30, semente=8, modo="viario")
        par = inst.parametros_padrao()
        res = resolver(inst, par, iteracoes=500, semente=0)
        rel = verificar(inst, par, res.rotas, res.custo)
        self.assertTrue(rel.viavel, rel.erros)


class TesteVerificador(unittest.TestCase):
    def setUp(self):
        self.inst = carregar("solomon/C101.vrp")
        self.par = self.inst.parametros_padrao()
        self.rotas = [list(r) for r in self.inst.bks_rotas]

    def test_detecta_cliente_duplicado(self):
        rotas = [r[:] for r in self.rotas]
        rotas[1].append(rotas[0][0])
        self.assertFalse(verificar(self.inst, self.par, rotas).viavel)

    def test_detecta_cliente_faltando(self):
        rotas = [r[:] for r in self.rotas]
        rotas[0].pop()
        rel = verificar(self.inst, self.par, rotas)
        self.assertTrue(any("não atendidos" in e for e in rel.erros))

    def test_detecta_capacidade(self):
        par = Parametros(30, 25)
        rel = verificar(self.inst, par, self.rotas)
        self.assertTrue(any("capacidade" in e for e in rel.erros))

    def test_detecta_janela_de_tempo(self):
        rotas = [r[:] for r in self.rotas]
        rotas[0].reverse()
        rel = verificar(self.inst, self.par, rotas)
        self.assertTrue(any("janela" in e or "depósito" in e for e in rel.erros))

    def test_detecta_custo_informado_errado(self):
        rel = verificar(self.inst, self.par, self.rotas, custo_informado=self.inst.bks_custo + 5)
        self.assertFalse(rel.viavel)

    def test_detecta_frota_excedida(self):
        par = Parametros(200, 3)
        rel = verificar(self.inst, par, self.rotas)
        self.assertTrue(any("frota" in e for e in rel.erros))


if __name__ == "__main__":
    unittest.main()
