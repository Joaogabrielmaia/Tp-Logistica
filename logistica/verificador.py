import math
from dataclasses import dataclass, field
from typing import List

from .modelo import PESOS_PRIORIDADE
from .rede_viaria import arredondar, distancia_euclidiana

TOL = 1e-6


# Custo de cada trecho da rota obtido do grafo e não das matrizes do solver; no modo viário usa Bellman-Ford,
# independente do Dijkstra.
class Trechos:
    def __init__(self, inst):
        self.inst = inst
        self._cache = {}

    def _bellman_ford(self, origem):
        g = self.inst.grafo
        inf = math.inf
        dist = [inf] * g.n
        tempo = [inf] * g.n
        dist[origem] = 0.0
        tempo[origem] = 0.0
        # Bellman-Ford: no máximo n-1 rodadas de relaxação; para antes se nada mudar.
        for _ in range(g.n - 1):
            mudou = False
            for u in range(g.n):
                if dist[u] == inf:
                    continue
                for v, peso, t in g.adj[u]:
                    if dist[u] + peso < dist[v] - 1e-12:
                        dist[v] = dist[u] + peso
                        tempo[v] = tempo[u] + t
                        mudou = True
            if not mudou:
                break
        return dist, tempo

    def obter(self, u, v):
        inst = self.inst
        if inst.modo == "completo":
            if u == v:
                return 0.0, 0.0
            if not inst.grafo.tem_arco(u, v):
                return math.inf, math.inf
            d = arredondar(distancia_euclidiana(inst.nos[u], inst.nos[v]), inst.regra)
            return d, d
        if u not in self._cache:
            self._cache[u] = self._bellman_ford(u)
        dist, tempo = self._cache[u]
        return dist[v], tempo[v]


@dataclass
class Relatorio:
    viavel: bool
    erros: List[str] = field(default_factory=list)
    distancia: float = 0.0
    custo: float = 0.0
    carga_por_rota: List[float] = field(default_factory=list)
    distancia_por_rota: List[float] = field(default_factory=list)


def avaliar_rota(inst, par, trechos, rota):
    nos = inst.nos
    erros = []
    t = nos[0].inicio
    anterior = 0
    servico_anterior = 0.0
    distancia = 0.0
    carga = 0.0
    prioridade = 0.0
    for u in rota:
        d, tempo = trechos.obter(anterior, u)
        if math.isinf(d):
            erros.append("sem caminho de %d para %d" % (anterior, u))
            return False, erros, distancia, carga, prioridade
        distancia += d
        t = t + servico_anterior + tempo
        if t < nos[u].inicio:
            t = nos[u].inicio
        if t > nos[u].fim + TOL:
            erros.append("janela de tempo violada no cliente %d (início %.3f > fim %.3f)" % (u, t, nos[u].fim))
        carga += nos[u].demanda
        prioridade += PESOS_PRIORIDADE.get(nos[u].prioridade, 1.0) * t
        anterior = u
        servico_anterior = nos[u].servico
    d, tempo = trechos.obter(anterior, 0)
    if math.isinf(d):
        erros.append("sem caminho de %d de volta ao depósito" % anterior)
        return False, erros, distancia, carga, prioridade
    distancia += d
    t = t + servico_anterior + tempo
    if t > nos[0].fim + TOL:
        erros.append("retorno ao depósito após o fim da janela (%.3f > %.3f)" % (t, nos[0].fim))
    if carga > par.capacidade + TOL:
        erros.append("capacidade excedida (%.1f > %.1f)" % (carga, par.capacidade))
    if par.distancia_maxima is not None and distancia > par.distancia_maxima + TOL:
        erros.append("distância máxima excedida (%.3f > %.3f)" % (distancia, par.distancia_maxima))
    return not erros, erros, distancia, carga, prioridade


def custo_da_rota(par, distancia, prioridade):
    return par.custo_fixo_veiculo + distancia + par.peso_prioridade * prioridade


# Confere de forma independente cobertura exata dos clientes, capacidade, janelas, distância, frota e o custo
# informado.
def verificar(inst, par, rotas, custo_informado=None, exigir_todos=True):
    trechos = Trechos(inst)
    erros = []
    rotas = [list(r) for r in rotas if r]
    vistos = {}
    for i, rota in enumerate(rotas):
        for u in rota:
            if not (1 <= u <= inst.n):
                erros.append("rota %d contém nó inválido %d" % (i + 1, u))
            elif u in vistos:
                erros.append("cliente %d aparece nas rotas %d e %d" % (u, vistos[u] + 1, i + 1))
            else:
                vistos[u] = i
    if exigir_todos:
        faltando = [u for u in range(1, inst.n + 1) if u not in vistos]
        if faltando:
            erros.append("clientes não atendidos: %s" % faltando[:10])
    if len(rotas) > par.frota_maxima:
        erros.append("frota excedida (%d > %d)" % (len(rotas), par.frota_maxima))
    total_dist = 0.0
    total_custo = 0.0
    cargas, dists = [], []
    for i, rota in enumerate(rotas):
        if any(not (1 <= u <= inst.n) for u in rota):
            continue
        ok, e, d, c, p = avaliar_rota(inst, par, trechos, rota)
        erros.extend("rota %d: %s" % (i + 1, msg) for msg in e)
        total_dist += d
        total_custo += custo_da_rota(par, d, p)
        cargas.append(c)
        dists.append(d)
    if custo_informado is not None and abs(custo_informado - total_custo) > 1e-5 * max(1.0, abs(total_custo)):
        erros.append("custo informado %.6f difere do recalculado %.6f" % (custo_informado, total_custo))
    return Relatorio(not erros, erros, total_dist, total_custo, cargas, dists)
