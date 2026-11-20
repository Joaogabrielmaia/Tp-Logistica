from .avaliacao import EPS, EstadoRota, Solucao, melhor_insercao_em_rota, inserir


class ClienteInatendivel(Exception):
    def __init__(self, clientes):
        super().__init__("clientes impossíveis de atender isoladamente: " + str(clientes))
        self.clientes = clientes


def clientes_inatendiveis(inst, par):
    ruins = []
    for u in range(1, inst.n + 1):
        if not EstadoRota(inst, par, [u]).viavel:
            ruins.append(u)
    return ruins


# Clarke-Wright: começa com uma rota por cliente e funde rotas pela maior economia d0i + dj0 - dij quando a fusão é
# viável.
def economias(inst, par):
    ruins = clientes_inatendiveis(inst, par)
    if ruins:
        raise ClienteInatendivel(ruins)
    n = inst.n
    D = inst.D
    rota_de = {u: [u] for u in range(1, n + 1)}
    pares = []
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                pares.append((D[0][i] + D[j][0] - D[i][j], i, j))
    pares.sort(key=lambda x: (-x[0], x[1], x[2]))
    for ganho, i, j in pares:
        if ganho <= EPS:
            break
        a, b = rota_de[i], rota_de[j]
        if a is b or a[-1] != i or b[0] != j:
            continue
        candidata = EstadoRota(inst, par, a + b)
        if not candidata.viavel:
            continue
        uniao = a + b
        for u in uniao:
            rota_de[u] = uniao
    vistos = set()
    rotas = []
    for u in range(1, n + 1):
        r = rota_de[u]
        if id(r) not in vistos:
            vistos.add(id(r))
            rotas.append(r)
    return Solucao.de_rotas(inst, par, rotas)


# Inserção sequencial no estilo I1 de Solomon: abre a rota pelo cliente mais difícil e insere o de melhor critério até
# não caber mais.
def insercao_solomon(inst, par, mu=1.0, lam=1.0, alfa1=1.0):
    ruins = clientes_inatendiveis(inst, par)
    if ruins:
        raise ClienteInatendivel(ruins)
    n = inst.n
    D = inst.D
    nao_roteados = set(range(1, n + 1))
    estados = []
    while nao_roteados:
        semente = max(nao_roteados, key=lambda u: (D[0][u] + inst.e[u], -u))
        estado = EstadoRota(inst, par, [semente])
        nao_roteados.discard(semente)
        while True:
            melhor_u = None
            melhor_c2 = None
            melhor_pos = None
            for u in nao_roteados:
                resultado = melhor_insercao_em_rota(inst, par, estado, u)
                if resultado is None:
                    continue
                delta, pos = resultado
                c1 = alfa1 * delta
                c2 = lam * D[0][u] - c1
                if melhor_c2 is None or c2 > melhor_c2:
                    melhor_c2 = c2
                    melhor_u = u
                    melhor_pos = pos
            if melhor_u is None:
                break
            estado = inserir(inst, par, estado, melhor_u, melhor_pos)
            nao_roteados.discard(melhor_u)
        estados.append(estado)
    return Solucao(estados)
