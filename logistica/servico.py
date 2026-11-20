import math
import os
import tempfile
import threading

from .avaliacao import EstadoRota
from .construtivo import ClienteInatendivel
from .grafo import clientes_inalcancaveis
from .leitor import ErroInstancia, gerar_instancia_sintetica, ler_instancia, listar_instancias
from .modelo import NOMES_PRIORIDADE, Parametros
from .solver import resolver
from .verificador import verificar

LIMITE_ITERACOES = 200000
LIMITE_CLIENTES_SINTETICOS = 500


class ErroRequisicao(Exception):
    pass


def _finito(x):
    return None if x is None or math.isinf(x) else x


class Servico:
    def __init__(self, dados, resultados):
        self.dados = dados
        self.resultados = resultados
        self.registro = {}
        self.trava = threading.Lock()
        self.contador = 0

    def listar(self):
        itens = []
        for rel in listar_instancias(self.dados):
            itens.append({"arquivo": rel, "grupo": rel.split("/")[0], "nome": os.path.splitext(os.path.basename(rel))[0]})
        for chave, (inst, _) in self.registro.items():
            itens.append({"arquivo": chave, "grupo": "enviadas e geradas", "nome": inst.nome})
        return itens

    def _carregar(self, corpo):
        modo = corpo.get("modo", "completo")
        if modo not in ("completo", "viario"):
            raise ErroRequisicao("modo de grafo inválido")
        arquivo = corpo.get("arquivo")
        if not arquivo:
            raise ErroRequisicao("informe a instância")
        semente = int(corpo.get("semente_grafo", 0))
        if arquivo in self.registro:
            base, bruto = self.registro[arquivo]
            if modo != base.modo:
                inst = bruto(modo, semente)
            else:
                inst = base
        else:
            caminho = os.path.normpath(os.path.join(self.dados, arquivo))
            # Recusa caminhos que saem da pasta de dados (travessia de diretório).
            if os.path.commonpath([caminho, os.path.normpath(self.dados)]) != os.path.normpath(self.dados) or not os.path.isfile(caminho):
                raise ErroRequisicao("instância não encontrada")
            try:
                inst = ler_instancia(caminho, modo=modo, semente=semente)
            except ErroInstancia as e:
                raise ErroRequisicao(str(e))
        if corpo.get("prioridades"):
            inst = inst.com_prioridades(int(corpo.get("semente_prioridade", 0)))
        return inst

    def gerar(self, corpo):
        n = int(corpo.get("n", 40))
        if not (2 <= n <= LIMITE_CLIENTES_SINTETICOS):
            raise ErroRequisicao("n deve estar entre 2 e %d" % LIMITE_CLIENTES_SINTETICOS)
        semente = int(corpo.get("semente", 0))
        capacidade = float(corpo.get("capacidade", 100))
        agrupada = bool(corpo.get("agrupada", False))
        janelas = bool(corpo.get("janelas", True))

        def fabricar(modo, sem):
            return gerar_instancia_sintetica(n, semente=semente, capacidade=capacidade, agrupada=agrupada, janelas=janelas, modo=modo)

        inst = fabricar(corpo.get("modo", "completo"), semente)
        with self.trava:
            self.contador += 1
            chave = "gerada-%d" % self.contador
            self.registro[chave] = (inst, fabricar)
        return chave

    def enviar(self, corpo):
        conteudo = corpo.get("conteudo")
        if not isinstance(conteudo, str) or not conteudo.strip():
            raise ErroRequisicao("arquivo vazio")
        if len(conteudo) > 5_000_000:
            raise ErroRequisicao("arquivo grande demais")
        fd, caminho = tempfile.mkstemp(suffix=".vrp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(conteudo)
            inst = ler_instancia(caminho)
        except (ErroInstancia, ValueError, KeyError) as e:
            raise ErroRequisicao("arquivo inválido: " + str(e))
        finally:
            if os.path.exists(caminho):
                os.remove(caminho)
        nome = str(corpo.get("nome", "enviada"))[:40]
        inst.nome = nome

        def refazer(modo, sem):
            fd2, c2 = tempfile.mkstemp(suffix=".vrp")
            try:
                with os.fdopen(fd2, "w", encoding="utf-8") as f:
                    f.write(conteudo)
                nova = ler_instancia(c2, modo=modo, semente=sem)
                nova.nome = nome
                return nova
            finally:
                os.remove(c2)

        with self.trava:
            self.contador += 1
            chave = "enviada-%d" % self.contador
            self.registro[chave] = (inst, refazer)
        return chave

    def _json_instancia(self, inst):
        dados = {
            "nome": inst.nome,
            "tipo": inst.tipo,
            "n": inst.n,
            "capacidade": inst.capacidade,
            "frota": inst.frota,
            "modo": inst.modo,
            "bks_custo": inst.bks_custo,
            "bks_veiculos": len(inst.bks_rotas) if inst.bks_rotas else None,
            "inalcancaveis": clientes_inalcancaveis(inst.grafo, 0),
            "nos": [
                {"id": no.id, "x": no.x, "y": no.y, "demanda": no.demanda, "inicio": no.inicio, "fim": _finito(no.fim), "servico": no.servico, "prioridade": no.prioridade}
                for no in inst.nos
            ],
        }
        if inst.modo == "viario":
            vistos = set()
            arestas = []
            for u in range(inst.grafo.n):
                for v, _, _ in inst.grafo.adj[u]:
                    chave = (min(u, v), max(u, v))
                    if chave not in vistos:
                        vistos.add(chave)
                        arestas.append(list(chave))
            dados["arestas"] = arestas
        return dados

    def instancia(self, corpo):
        inst = self._carregar(corpo)
        return self._json_instancia(inst)

    def _parametros(self, inst, corpo):
        def numero(chave, padrao, tipo=float):
            valor = corpo.get(chave)
            if valor in (None, ""):
                return padrao
            try:
                return tipo(valor)
            except (TypeError, ValueError):
                raise ErroRequisicao("valor inválido em " + chave)

        capacidade = numero("capacidade", inst.capacidade)
        frota = numero("frota", inst.frota, int)
        dmax = numero("distancia_maxima", None)
        fixo = numero("custo_fixo", 0.0)
        peso = numero("peso_prioridade", 0.0)
        if capacidade <= 0 or frota < 1 or fixo < 0 or peso < 0 or (dmax is not None and dmax <= 0):
            raise ErroRequisicao("parâmetros fora do intervalo permitido")
        if any(no.demanda > capacidade for no in inst.nos):
            raise ErroRequisicao("há cliente com demanda maior que a capacidade informada")
        return Parametros(capacidade=capacidade, frota_maxima=frota, distancia_maxima=dmax, custo_fixo_veiculo=fixo, peso_prioridade=peso)

    def resolver(self, corpo):
        inst = self._carregar(corpo)
        par = self._parametros(inst, corpo)
        iteracoes = int(corpo.get("iteracoes", 5000))
        if not (0 <= iteracoes <= LIMITE_ITERACOES):
            raise ErroRequisicao("iterações devem estar entre 0 e %d" % LIMITE_ITERACOES)
        semente = int(corpo.get("semente", 0))
        # Evita travar a demonstração em instâncias grandes: o solver devolve a melhor solução viável ao fim do prazo.
        limite_tempo = float(corpo.get("tempo_limite", 0) or 0)
        if not (0 <= limite_tempo <= 3600):
            raise ErroRequisicao("o tempo limite deve estar entre 0 e 3600 segundos")
        inalcancaveis = clientes_inalcancaveis(inst.grafo, 0)
        if inalcancaveis:
            raise ErroRequisicao("clientes sem caminho de ida e volta ao depósito: %s" % inalcancaveis[:10])
        try:
            res = resolver(inst, par, iteracoes=iteracoes, semente=semente, tempo_limite=limite_tempo or None)
        except ClienteInatendivel as e:
            raise ErroRequisicao("há clientes impossíveis de atender (janela de tempo, capacidade ou distância): %s" % e.clientes[:10])
        rel = verificar(inst, par, res.rotas, res.custo, exigir_todos=True)
        return self._json_resultado(inst, par, res, rel)

    def _json_resultado(self, inst, par, res, rel):
        rotas = []
        for i, rota in enumerate(res.rotas):
            est = EstadoRota(inst, par, rota)
            chegadas = []
            anterior, servico_anterior, t = 0, 0.0, inst.e[0]
            for u, inicio in zip(rota, est.E):
                t = t + servico_anterior + inst.T[anterior][u]
                chegadas.append(t)
                t = inicio
                anterior, servico_anterior = u, inst.s[u]
            sequencia = [0] + list(rota) + [0]
            caminho = []
            for a, b in zip(sequencia, sequencia[1:]):
                trecho = inst.caminho_fisico(a, b) or [a, b]
                if caminho:
                    trecho = trecho[1:]
                caminho.extend(trecho)
            rotas.append({
                "indice": i + 1,
                "nos": list(rota),
                "carga": est.carga,
                "utilizacao": est.carga / par.capacidade,
                "distancia": est.dist,
                "chegadas": chegadas,
                "inicios": list(est.E),
                "retorno": est.fim,
                "caminho": [[inst.nos[v].x, inst.nos[v].y] for v in caminho],
                "ordem_carregamento": list(reversed(rota)),
            })
        gap = None
        if inst.bks_custo and inst.modo == "completo" and par.custo_fixo_veiculo == 0 and par.peso_prioridade == 0:
            gap = (res.distancia / inst.bks_custo - 1.0) * 100.0
        alta = [t for r in rotas for u, t in zip(r["nos"], r["inicios"]) if inst.nos[u].prioridade == 1]
        return {
            "instancia": self._json_instancia(inst),
            "parametros": {"capacidade": par.capacidade, "frota": par.frota_maxima, "distancia_maxima": par.distancia_maxima, "custo_fixo": par.custo_fixo_veiculo, "peso_prioridade": par.peso_prioridade},
            "resultado": {
                "custo": res.custo,
                "distancia": res.distancia,
                "veiculos": res.veiculos,
                "viavel_frota": res.viavel_frota,
                "tempo": res.tempo_total,
                "iteracoes": res.iteracoes,
                "interrompido": res.interrompido,
                "gap_bks": gap,
                "inicio_medio_prioridade_alta": (sum(alta) / len(alta)) if alta else None,
                "utilizacao_media": sum(r["utilizacao"] for r in rotas) / max(1, len(rotas)),
                "etapas": res.etapas,
                "historico": res.historico,
            },
            "verificacao": {"viavel": rel.viavel, "erros": rel.erros[:20], "distancia": rel.distancia, "custo": rel.custo},
            "rotas": rotas,
            "nomes_prioridade": NOMES_PRIORIDADE,
        }

    def desempenho(self):
        import csv
        saida = {}
        if os.path.isdir(self.resultados):
            for nome in sorted(os.listdir(self.resultados)):
                if nome.endswith(".csv"):
                    with open(os.path.join(self.resultados, nome), encoding="utf-8") as f:
                        saida[nome[:-4]] = list(csv.DictReader(f))
        return saida
