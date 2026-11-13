import math

INF = math.inf
EPS = 1e-9


# Estado de uma rota: início mais cedo (E) e mais tarde (L) de cada visita, carga, distância e penalidade, calculados
# uma vez para que testar uma inserção custe O(1).
class EstadoRota:
    __slots__ = ("nos", "E", "L", "carga", "dist", "pen", "viavel", "fim", "custo")

    def __init__(self, inst, par, nos):
        self.nos = nos
        self._calcular(inst, par)

    def _calcular(self, inst, par):
        D, T, s, e, l, q, w = inst.D, inst.T, inst.s, inst.e, inst.l, inst.q, inst.w
        nos = self.nos
        E = []
        t = e[0]
        anterior = 0
        servico_anterior = 0.0
        dist = 0.0
        carga = 0.0
        pen = 0.0
        viavel = True
        for u in nos:
            t = t + servico_anterior + T[anterior][u]
            # Chegar antes da janela obriga o veículo a esperar até e[u].
            if t < e[u]:
                t = e[u]
            if t > l[u] + EPS:
                viavel = False
            E.append(t)
            dist += D[anterior][u]
            carga += q[u]
            pen += w[u] * t
            anterior = u
            servico_anterior = s[u]
        t = t + servico_anterior + T[anterior][0]
        dist += D[anterior][0]
        if t > l[0] + EPS:
            viavel = False
        if carga > par.capacidade + EPS:
            viavel = False
        if par.distancia_maxima is not None and dist > par.distancia_maxima + EPS:
            viavel = False
        self.E = E
        self.carga = carga
        self.dist = dist
        self.pen = pen
        self.fim = t
        self.viavel = viavel
        if nos:
            self.custo = par.custo_fixo_veiculo + dist + par.peso_prioridade * pen
        else:
            self.custo = 0.0
        # L[k] é o início mais tarde na posição k que ainda mantém viável o resto da rota (folga para trás,
        # Savelsbergh 1985).
        L = [0.0] * len(nos)
        if viavel and nos:
            proximo_L = l[0]
            proximo = 0
            for k in range(len(nos) - 1, -1, -1):
                u = nos[k]
                L[k] = min(l[u], proximo_L - T[u][proximo] - s[u])
                proximo_L = L[k]
                proximo = u
        self.L = L


def melhor_insercao_em_rota(inst, par, estado, u, rng=None, piscar=0.0, limite=None):
    D, T, s, e, l = inst.D, inst.T, inst.s, inst.e, inst.l
    nos = estado.nos
    tam = len(nos)
    if estado.carga + inst.q[u] > par.capacidade + EPS:
        return None
    E, L = estado.E, estado.L
    melhor = limite
    melhor_pos = -1
    lam = par.peso_prioridade
    dmax = par.distancia_maxima
    eu, lu, su = e[u], l[u], s[u]
    Du = D[u]
    aleatorio = rng.random if piscar else None
    for pos in range(tam + 1):
        # Piscar: ignora algumas posições ao acaso para diversificar a recriação.
        if piscar and aleatorio() < piscar:
            continue
        if pos == 0:
            p = 0
        else:
            p = nos[pos - 1]
        nx = 0 if pos == tam else nos[pos]
        # Distância extra ao desviar de p para nx passando por u. O termo de prioridade nunca é negativo,
        # então uma posição que já não melhora a melhor encontrada é descartada antes do teste de janelas.
        delta = D[p][u] + Du[nx] - D[p][nx]
        if melhor is not None and delta >= melhor:
            continue
        if dmax is not None and estado.dist + delta > dmax + EPS:
            continue
        if pos == 0:
            chegada = e[0] + T[0][u]
        else:
            chegada = E[pos - 1] + s[p] + T[p][u]
        inicio_u = chegada if chegada > eu else eu
        if inicio_u > lu + EPS:
            continue
        # A inserção é viável se o novo início em nx não passa de L[pos]; não é preciso recalcular o resto da rota.
        chegada_nx = inicio_u + su + T[u][nx]
        if nx != 0 and chegada_nx < e[nx]:
            chegada_nx = e[nx]
        if chegada_nx > (l[0] if pos == tam else L[pos]) + EPS:
            continue
        if lam:
            delta += lam * _delta_prioridade(inst, estado, u, pos, inicio_u)
            if melhor is not None and delta >= melhor:
                continue
        melhor = delta
        melhor_pos = pos
    if melhor_pos < 0:
        return None
    return melhor, melhor_pos


# Variação do termo de prioridade: u entra com início inicio_u e empurra para mais tarde os clientes que vêm depois
# dele.
def _delta_prioridade(inst, estado, u, pos, inicio_u):
    T, s, e, w = inst.T, inst.s, inst.e, inst.w
    nos, E = estado.nos, estado.E
    total = w[u] * inicio_u
    t = inicio_u
    anterior = u
    for k in range(pos, len(nos)):
        v = nos[k]
        t = t + s[anterior] + T[anterior][v]
        if t < e[v]:
            t = e[v]
        if t == E[k]:
            break
        total += w[v] * (t - E[k])
        anterior = v
    return total


def inserir(inst, par, estado, u, pos):
    nos = estado.nos[:pos] + [u] + estado.nos[pos:]
    return EstadoRota(inst, par, nos)


class Solucao:
    __slots__ = ("estados",)

    def __init__(self, estados):
        self.estados = estados

    def copiar(self):
        return Solucao(list(self.estados))

    def custo(self):
        return sum(est.custo for est in self.estados)

    def distancia(self):
        return sum(est.dist for est in self.estados)

    def rotas(self):
        return [list(est.nos) for est in self.estados if est.nos]

    def compactar(self):
        self.estados = [est for est in self.estados if est.nos]

    @staticmethod
    def de_rotas(inst, par, rotas):
        return Solucao([EstadoRota(inst, par, list(r)) for r in rotas if r])
