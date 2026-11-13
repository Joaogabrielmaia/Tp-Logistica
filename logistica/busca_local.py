import time
from .avaliacao import EPS, EstadoRota, melhor_insercao_em_rota, inserir


def _tentar_realocar(inst, par, sol):
    estados = sol.estados
    for a in range(len(estados)):
        origem = estados[a]
        for idx in range(len(origem.nos)):
            u = origem.nos[idx]
            sem = EstadoRota(inst, par, origem.nos[:idx] + origem.nos[idx + 1:])
            if not sem.viavel:
                continue
            ganho = origem.custo - sem.custo
            melhor_total = -EPS
            melhor_alvo = None
            for b in range(len(estados)):
                alvo = sem if b == a else estados[b]
                if not alvo.nos:
                    continue
                resultado = melhor_insercao_em_rota(inst, par, alvo, u, limite=ganho + melhor_total)
                if resultado is None:
                    continue
                delta, pos = resultado
                total = delta - ganho
                if total < melhor_total:
                    melhor_total = total
                    melhor_alvo = (b, pos)
            if melhor_alvo is not None:
                b, pos = melhor_alvo
                if b == a:
                    estados[a] = inserir(inst, par, sem, u, pos)
                else:
                    estados[a] = sem
                    estados[b] = inserir(inst, par, estados[b], u, pos)
                sol.compactar()
                return True
    return False


# Tolerância dos filtros rápidos: um candidato só é descartado sem avaliação completa quando
# é claramente inviável ou claramente pior; os casos de fronteira seguem para a avaliação exata,
# de modo que a busca aceita exatamente os mesmos movimentos que a avaliação completa aceitaria.
TOL = 1e-6


def _perfil(inst, est):
    D, q = inst.D, inst.q
    nos = est.nos
    tam = len(nos)
    ida = [0.0] * (tam + 1)
    carga = [0.0] * (tam + 1)
    anterior = 0
    for k, u in enumerate(nos):
        ida[k + 1] = ida[k] + D[anterior][u]
        carga[k + 1] = carga[k] + q[u]
        anterior = u
    volta = [0.0] * (tam + 1)
    seguinte = 0
    for k in range(tam - 1, -1, -1):
        u = nos[k]
        volta[k] = volta[k + 1] + D[u][seguinte]
        seguinte = u
    return ida, volta, carga


def _saida(inst, est, i):
    if i == 0:
        return 0, inst.e[0]
    p = est.nos[i - 1]
    return p, est.E[i - 1] + inst.s[p]


def _chega_a_tempo(inst, est, j, anterior, partida):
    if j == len(est.nos):
        return partida + inst.T[anterior][0] <= inst.l[0] + EPS + TOL
    v = est.nos[j]
    inicio = partida + inst.T[anterior][v]
    if inicio < inst.e[v]:
        inicio = inst.e[v]
    return inicio <= est.L[j] + EPS + TOL


def _tentar_trocar(inst, par, sol):
    D, T, q, s, e, l = inst.D, inst.T, inst.q, inst.s, inst.e, inst.l
    cap = par.capacidade + EPS + TOL
    dmax = par.distancia_maxima
    so_distancia = not par.peso_prioridade
    estados = sol.estados

    def encaixa(r, i, v):
        p, partida = _saida(inst, r, i)
        inicio = partida + T[p][v]
        if inicio < e[v]:
            inicio = e[v]
        if inicio > l[v] + EPS + TOL:
            return False
        return _chega_a_tempo(inst, r, i + 1, v, inicio + s[v])

    def nova_distancia(r, i, v):
        nos = r.nos
        p = nos[i - 1] if i else 0
        n = nos[i + 1] if i + 1 < len(nos) else 0
        u = nos[i]
        return r.dist - D[p][u] - D[u][n] + D[p][v] + D[v][n]

    for a in range(len(estados)):
        for b in range(a + 1, len(estados)):
            ra, rb = estados[a], estados[b]
            base = ra.custo + rb.custo
            filtrar_tempo = ra.viavel and rb.viavel
            for i, u in enumerate(ra.nos):
                for j, v in enumerate(rb.nos):
                    if ra.carga - q[u] + q[v] > cap or rb.carga - q[v] + q[u] > cap:
                        continue
                    if so_distancia or dmax is not None:
                        da = nova_distancia(ra, i, v)
                        db = nova_distancia(rb, j, u)
                        if dmax is not None and (da > dmax + EPS + TOL or db > dmax + EPS + TOL):
                            continue
                        if so_distancia and 2 * par.custo_fixo_veiculo + da + db >= base - EPS + TOL:
                            continue
                    if filtrar_tempo and not (encaixa(ra, i, v) and encaixa(rb, j, u)):
                        continue
                    na = ra.nos[:i] + [v] + ra.nos[i + 1:]
                    nb = rb.nos[:j] + [u] + rb.nos[j + 1:]
                    ea = EstadoRota(inst, par, na)
                    if not ea.viavel:
                        continue
                    eb = EstadoRota(inst, par, nb)
                    if not eb.viavel:
                        continue
                    if ea.custo + eb.custo < base - EPS:
                        estados[a], estados[b] = ea, eb
                        return True
    return False


def _tentar_cauda(inst, par, sol):
    D = inst.D
    cap = par.capacidade + EPS + TOL
    dmax = par.distancia_maxima
    fixo = par.custo_fixo_veiculo
    so_distancia = not par.peso_prioridade
    estados = sol.estados
    perfis = [_perfil(inst, est) for est in estados]
    for a in range(len(estados)):
        for b in range(a + 1, len(estados)):
            ra, rb = estados[a], estados[b]
            ida_a, volta_a, carga_a = perfis[a]
            ida_b, volta_b, carga_b = perfis[b]
            ta, tb = len(ra.nos), len(rb.nos)
            base = ra.custo + rb.custo
            filtrar_tempo = ra.viavel and rb.viavel
            for i in range(ta + 1):
                ultimo_a = ra.nos[i - 1] if i else 0
                primeiro_a = ra.nos[i] if i < ta else 0
                if filtrar_tempo:
                    pa, partida_a = _saida(inst, ra, i)
                for j in range(tb + 1):
                    if (i == ta and j == tb) or (i == 0 and j == 0):
                        continue
                    if carga_a[i] + carga_b[tb] - carga_b[j] > cap or carga_b[j] + carga_a[ta] - carga_a[i] > cap:
                        continue
                    if so_distancia or dmax is not None:
                        primeiro_b = rb.nos[j] if j < tb else 0
                        ultimo_b = rb.nos[j - 1] if j else 0
                        da = ida_a[i] + D[ultimo_a][primeiro_b] + volta_b[j]
                        db = ida_b[j] + D[ultimo_b][primeiro_a] + volta_a[i]
                        if dmax is not None and (da > dmax + EPS + TOL or db > dmax + EPS + TOL):
                            continue
                        if so_distancia:
                            vazias = (i == 0 and j == tb) + (j == 0 and i == ta)
                            if fixo * (2 - vazias) + da + db >= base - EPS + TOL:
                                continue
                    if filtrar_tempo:
                        if not _chega_a_tempo(inst, rb, j, pa, partida_a):
                            continue
                        pb, partida_b = _saida(inst, rb, j)
                        if not _chega_a_tempo(inst, ra, i, pb, partida_b):
                            continue
                    na = ra.nos[:i] + rb.nos[j:]
                    nb = rb.nos[:j] + ra.nos[i:]
                    ea = EstadoRota(inst, par, na)
                    if not ea.viavel:
                        continue
                    eb = EstadoRota(inst, par, nb)
                    if not eb.viavel:
                        continue
                    if ea.custo + eb.custo < base - EPS:
                        estados[a], estados[b] = ea, eb
                        sol.compactar()
                        return True
    return False


def _tentar_inverter(inst, par, sol):
    D = inst.D
    so_distancia = not par.peso_prioridade
    estados = sol.estados
    for a, r in enumerate(estados):
        nos = r.nos
        tam = len(nos)
        if so_distancia:
            frente = [0.0] * tam
            tras = [0.0] * tam
            for k in range(1, tam):
                frente[k] = frente[k - 1] + D[nos[k - 1]][nos[k]]
                tras[k] = tras[k - 1] + D[nos[k]][nos[k - 1]]
        for i in range(tam - 1):
            p = nos[i - 1] if i else 0
            for j in range(i + 1, tam):
                if so_distancia:
                    n = nos[j + 1] if j + 1 < tam else 0
                    antes = D[p][nos[i]] + frente[j] - frente[i] + D[nos[j]][n]
                    depois = D[p][nos[j]] + tras[j] - tras[i] + D[nos[i]][n]
                    if depois - antes >= -EPS + TOL:
                        continue
                novos = nos[:i] + nos[i:j + 1][::-1] + nos[j + 1:]
                e = EstadoRota(inst, par, novos)
                if e.viavel and e.custo < r.custo - EPS:
                    estados[a] = e
                    return True
    return False


VIZINHANCAS = (_tentar_realocar, _tentar_inverter, _tentar_trocar, _tentar_cauda)


# Aplica as vizinhanças até nenhuma melhorar (ótimo local). Só aceita movimento viável e estritamente melhor, o que
# garante terminação; prazo interrompe para uso interativo.
def polir(inst, par, sol, vizinhancas=VIZINHANCAS, limite_passos=100000, prazo=None):
    passos = 0
    melhorou = True
    while melhorou and passos < limite_passos:
        melhorou = False
        for mover in vizinhancas:
            while True:
                if prazo is not None and time.time() > prazo:
                    return sol
                if not mover(inst, par, sol):
                    break
                melhorou = True
                passos += 1
                if passos >= limite_passos:
                    return sol
    return sol
