import copy
import random
from dataclasses import dataclass
from typing import List, Optional

# Peso w do termo de prioridade: alta pesa 3, média 2 e baixa 1.
PESOS_PRIORIDADE = {1: 3.0, 2: 2.0, 3: 1.0}
NOMES_PRIORIDADE = {1: "alta", 2: "média", 3: "baixa"}
PROPORCOES_PADRAO = (0.2, 0.3, 0.5)


@dataclass(frozen=True)
class No:
    id: int
    x: float
    y: float
    demanda: float
    inicio: float
    fim: float
    servico: float
    prioridade: int = 3


@dataclass
class Parametros:
    capacidade: float
    frota_maxima: int
    distancia_maxima: Optional[float] = None
    custo_fixo_veiculo: float = 0.0
    peso_prioridade: float = 0.0


# Instância = nós + grafo + matrizes D e T usadas pelos algoritmos (as do próprio grafo no modo completo; caminhos
# mínimos no modo viário).
class Instancia:
    def __init__(self, nome, tipo, nos, grafo, capacidade, frota, D, T, modo, predecessores=None, bks_custo=None, bks_rotas=None, regra="exato"):
        self.regra = regra
        self.nome = nome
        self.tipo = tipo
        self.nos = nos
        self.grafo = grafo
        self.capacidade = capacidade
        self.frota = frota
        self.D = D
        self.T = T
        self.modo = modo
        self.predecessores = predecessores
        self.bks_custo = bks_custo
        self.bks_rotas = bks_rotas
        self.prioridade_propria = False
        self._derivar()

    def _derivar(self):
        self.n = len(self.nos) - 1
        self.q = [no.demanda for no in self.nos]
        self.e = [no.inicio for no in self.nos]
        self.l = [no.fim for no in self.nos]
        self.s = [no.servico for no in self.nos]
        self.w = [PESOS_PRIORIDADE.get(no.prioridade, 1.0) for no in self.nos]
        self.w[0] = 0.0

    def parametros_padrao(self):
        return Parametros(capacidade=self.capacidade, frota_maxima=self.frota)

    def com_prioridades(self, semente, proporcoes=PROPORCOES_PADRAO):
        # Instâncias cuja prioridade vem do próprio arquivo (entregas do Kaggle) não são sobrescritas pelas prioridades sintéticas.
        if self.prioridade_propria:
            return self
        novos = atribuir_prioridades(self.nos, semente, proporcoes)
        copia = copy.copy(self)
        copia.nos = novos
        copia._derivar()
        return copia

    # Cópia só com o depósito e os clientes em `manter`, renumerados de 1 a k. As distâncias e tempos vêm da instância
    # original (caminhos pela rede inteira, inclusive passando por clientes deixados de fora), então o trajeto continua
    # o mesmo; só o solver usa a cópia, e as rotas voltam à numeração original antes da verificação.
    def subinstancia(self, manter):
        indices = [0] + list(manter)
        copia = copy.copy(self)
        copia.nos = [self.nos[i] for i in indices]
        copia.D = [[self.D[a][b] for b in indices] for a in indices]
        copia.T = [[self.T[a][b] for b in indices] for a in indices]
        copia.grafo = None
        copia.predecessores = None
        copia.bks_custo = None
        copia.bks_rotas = None
        copia._derivar()
        return copia

    def caminho_fisico(self, origem, destino):
        if self.predecessores is None:
            return [origem, destino]
        from .caminhos import reconstruir_caminho
        return reconstruir_caminho(self.predecessores[origem], origem, destino)


def atribuir_prioridades(nos, semente, proporcoes=PROPORCOES_PADRAO):
    rng = random.Random(semente)
    p1, p2, _ = proporcoes
    resultado = [nos[0]]
    for no in nos[1:]:
        r = rng.random()
        prioridade = 1 if r < p1 else (2 if r < p1 + p2 else 3)
        resultado.append(No(no.id, no.x, no.y, no.demanda, no.inicio, no.fim, no.servico, prioridade))
    return resultado
