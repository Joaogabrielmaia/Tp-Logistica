import math
import random
import time

from .avaliacao import EstadoRota, Solucao, melhor_insercao_em_rota

L_MAX = 10
C_BARRA = 10
# Probabilidade de ignorar uma posição na reinserção, para diversificar.
PISCAR = 0.01


# Para cada cliente, os demais ordenados por distância, calculado uma vez por chamada.
def _vizinhos(inst):
    n = inst.n
    D = inst.D
    return [None] + [sorted((v for v in range(1, n + 1)), key=lambda v: (D[u][v], v)) for u in range(1, n + 1)]


# Remove trechos contíguos de rotas próximas a um cliente sorteado (remoção de strings adjacentes, Christiaens e
# Vanden Berghe 2020).
def _ruina(inst, estados, viz, rng):
    n = inst.n
    nrotas = len(estados)
    media = n / max(1, nrotas)
    ls_max = min(L_MAX, media)
    ks_max = 4.0 * C_BARRA / (1.0 + ls_max) - 1.0
    ks = int(rng.uniform(1.0, ks_max + 1.0))
    rota_de = {}
    for r, est in enumerate(estados):
        for u in est.nos:
            rota_de[u] = r
    semente = rng.randint(1, n)
    modificadas = {}
    removidos = []
    for c in viz[semente]:
        if len(modificadas) >= ks:
            break
        r = rota_de.get(c)
        if r is None or r in modificadas:
            continue
        nos = estados[r].nos
        lt_max = min(len(nos), ls_max)
        lt = int(rng.uniform(1.0, lt_max + 1.0))
        lt = min(lt, len(nos))
        idx = nos.index(c)
        lo = max(0, idx - lt + 1)
        hi = min(idx, len(nos) - lt)
        ini = rng.randint(lo, hi)
        removidos.extend(nos[ini:ini + lt])
        modificadas[r] = nos[:ini] + nos[ini + lt:]
    return removidos, modificadas


def _ordenar(inst, removidos, rng):
    r = rng.random() * 11.0
    if r < 4:
        rng.shuffle(removidos)
    elif r < 8:
        removidos.sort(key=lambda u: -inst.q[u])
    elif r < 10:
        removidos.sort(key=lambda u: -inst.D[0][u])
    else:
        removidos.sort(key=lambda u: inst.D[0][u])
    return removidos


def _recriar(inst, par, estados, removidos, rng):
    for u in removidos:
        melhor = None
        for r, est in enumerate(estados):
            res = melhor_insercao_em_rota(inst, par, est, u, rng, PISCAR, None if melhor is None else melhor[0])
            if res is None:
                continue
            delta, pos = res
            if melhor is None or delta < melhor[0]:
                melhor = (delta, r, pos)
        if melhor is not None:
            _, r, pos = melhor
            nos = estados[r].nos
            estados[r] = EstadoRota(inst, par, nos[:pos] + [u] + nos[pos:])
        else:
            ativos = sum(1 for e in estados if e.nos)
            novo = EstadoRota(inst, par, [u])
            if ativos >= par.frota_maxima or not novo.viavel:
                return False
            estados.append(novo)
    return True


def otimizar(inst, par, inicial, iteracoes=20000, semente=0, tempo_limite=None, temperatura_inicial=None, temperatura_final=None, historico=None):
    rng = random.Random(semente)
    viz = _vizinhos(inst)
    atual = inicial.copiar()
    atual.compactar()
    melhor = atual.copiar()
    custo_atual = atual.custo()
    custo_melhor = custo_atual
    # Temperaturas proporcionais ao custo médio por cliente, para o recozimento não depender da escala da instância.
    escala = max(1e-9, custo_atual / max(1, inst.n))
    t0 = temperatura_inicial if temperatura_inicial is not None else 0.5 * escala
    tf = temperatura_final if temperatura_final is not None else 0.005 * escala
    inicio = time.time()
    amostra = max(1, iteracoes // 200)
    it = 0
    while it < iteracoes:
        if tempo_limite is not None and time.time() - inicio > tempo_limite:
            break
        frac = it / iteracoes
        # Resfriamento geométrico de t0 até tf ao longo das iterações.
        temp = t0 * (tf / t0) ** frac
        estados = list(atual.estados)
        removidos, modificadas = _ruina(inst, estados, viz, rng)
        for idx, nos in modificadas.items():
            estados[idx] = EstadoRota(inst, par, nos)
        estados = [e for e in estados if e.nos]
        _ordenar(inst, removidos, rng)
        ok = _recriar(inst, par, estados, removidos, rng)
        if ok:
            candidata = Solucao(estados)
            custo_cand = candidata.custo()
            # Recozimento simulado: uma piora é aceita com probabilidade exp(-delta/temp).
            if custo_cand < custo_atual - temp * math.log(rng.random() + 1e-300):
                atual = candidata
                custo_atual = custo_cand
                if custo_atual < custo_melhor - 1e-9:
                    melhor = atual.copiar()
                    custo_melhor = custo_atual
        it += 1
        if historico is not None and (it % amostra == 0 or it == 1):
            historico.append((it, custo_melhor))
    return melhor, it
