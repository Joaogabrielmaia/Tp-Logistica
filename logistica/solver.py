import time
from dataclasses import dataclass, field
from typing import List, Optional

from .avaliacao import Solucao
from .busca_local import polir
from .construtivo import economias, insercao_solomon
from .otimizador import otimizar


@dataclass
class Resultado:
    rotas: List[List[int]]
    custo: float
    distancia: float
    veiculos: int
    viavel_frota: bool
    etapas: List[dict] = field(default_factory=list)
    historico: List[tuple] = field(default_factory=list)
    tempo_total: float = 0.0
    iteracoes: int = 0
    solucao: Optional[Solucao] = None
    interrompido: bool = False


def _registrar(etapas, nome, sol, inicio):
    etapas.append({"etapa": nome, "custo": sol.custo(), "distancia": sol.distancia(), "veiculos": len(sol.rotas()), "tempo": time.time() - inicio})


# Etapas: economias e inserção, escolha da melhor, busca local, ruína e recriação, polimento. O tempo_limite vale para
# o conjunto de todas as etapas.
def resolver(inst, par, iteracoes=20000, semente=0, tempo_limite=None, usar_otimizador=True):
    inicio = time.time()
    etapas = []
    candidatas = []
    for nome, construtor in (("economias", economias), ("insercao", insercao_solomon)):
        sol = construtor(inst, par)
        _registrar(etapas, nome, sol, inicio)
        candidatas.append(sol)
    # Prefere a construção que respeita a frota; entre elas, a de menor custo.
    atual = min(candidatas, key=lambda s: (len(s.rotas()) > par.frota_maxima, s.custo()))
    prazo = inicio + tempo_limite if tempo_limite is not None else None
    polir(inst, par, atual, prazo=prazo)
    _registrar(etapas, "busca local", atual, inicio)
    historico = []
    iters = 0
    if usar_otimizador and iteracoes > 0:
        restante = None if prazo is None else max(0.0, prazo - time.time())
        atual, iters = otimizar(inst, par, atual, iteracoes=iteracoes, semente=semente, tempo_limite=restante, historico=historico)
        _registrar(etapas, "ruína e recriação", atual, inicio)
        polir(inst, par, atual, prazo=prazo)
        _registrar(etapas, "polimento final", atual, inicio)
    atual.compactar()
    return Resultado(
        rotas=atual.rotas(),
        custo=atual.custo(),
        distancia=atual.distancia(),
        veiculos=len(atual.rotas()),
        viavel_frota=len(atual.rotas()) <= par.frota_maxima,
        etapas=etapas,
        historico=historico,
        tempo_total=time.time() - inicio,
        iteracoes=iters,
        solucao=atual,
        interrompido=prazo is not None and time.time() > prazo,
    )
