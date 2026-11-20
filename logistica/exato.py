import itertools
import math

from .verificador import Trechos, avaliar_rota, custo_da_rota


# Enumera as permutações de cada subconjunto de clientes e combina os subconjuntos por programação dinâmica; só para
# instâncias muito pequenas.
def resolver_exato(inst, par, limite_clientes=9):
    n = inst.n
    if n > limite_clientes:
        raise ValueError("instância grande demais para o solver exato")
    trechos = Trechos(inst)
    inf = math.inf
    custo_subconjunto = {}
    melhor_ordem = {}
    for mascara in range(1, 1 << n):
        clientes = [i + 1 for i in range(n) if mascara >> i & 1]
        melhor = inf
        ordem = None
        for perm in itertools.permutations(clientes):
            ok, _, d, _, p = avaliar_rota(inst, par, trechos, perm)
            if not ok:
                continue
            c = custo_da_rota(par, d, p)
            if c < melhor:
                melhor = c
                ordem = perm
        custo_subconjunto[mascara] = melhor
        melhor_ordem[mascara] = ordem
    cheio = (1 << n) - 1
    melhor_total = {0: (0.0, 0)}
    for mascara in range(1, cheio + 1):
        baixo = mascara & -mascara
        sub = mascara
        melhor = (inf, 0)
        while sub:
            if sub & baixo and custo_subconjunto[sub] < inf:
                resto = mascara ^ sub
                anterior = melhor_total.get(resto)
                if anterior is not None and anterior[0] < inf:
                    total = custo_subconjunto[sub] + anterior[0]
                    veic = anterior[1] + 1
                    if veic <= par.frota_maxima and total < melhor[0]:
                        melhor = (total, veic, sub)
            sub = (sub - 1) & mascara
        melhor_total[mascara] = melhor if melhor[0] < inf else (inf, 0)
    custo = melhor_total[cheio][0]
    if custo == inf:
        return None, None
    rotas = []
    mascara = cheio
    while mascara:
        sub = melhor_total[mascara][2]
        rotas.append(list(melhor_ordem[sub]))
        mascara ^= sub
    return custo, rotas
