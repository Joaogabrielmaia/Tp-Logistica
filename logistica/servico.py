import math
import os
import tempfile
import threading

from .avaliacao import EstadoRota
from .caminhos import CicloNegativo
from .construtivo import ClienteInatendivel
from .erros import ErroExplicado, explicar, explicar_inatendiveis
from .grafo import clientes_inalcancaveis
from .leitor import FORMATOS, ErroInstancia, gerar_instancia_sintetica, ler_instancia, listar_instancias
from .modelo import NOMES_PRIORIDADE, Parametros
from .erros import motivos_inatendivel
from .solver import resolver, resolver_atendiveis
from .verificador import verificar

LIMITE_ITERACOES = 200000
LIMITE_CLIENTES_SINTETICOS = 2000


# Erro devolvido à interface com status 400: além da mensagem, leva o motivo e o que fazer, que a tela mostra.
class ErroRequisicao(Exception):
    def __init__(self, mensagem, motivo="", dica=""):
        super().__init__(mensagem)
        self.motivo = motivo
        self.dica = dica

    @classmethod
    def de(cls, erro):
        return cls(*explicar(erro))


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
        mao = float(corpo.get("mao_unica", 0) or 0)
        if not (0 <= mao <= 1):
            raise ErroRequisicao("mão única fora do intervalo", "é a porcentagem das ruas que vira mão única, de 0 a 100%.", "escolha um valor entre 0 e 100.")
        if mao and modo != "viario":
            raise ErroRequisicao("mão única só existe na rede viária",
                                 "no grafo completo há arco direto nos dois sentidos entre todo par de pontos.",
                                 "marque Rede viária no passo 2 ou zere o campo Mão única.")
        if arquivo in self.registro:
            base, bruto = self.registro[arquivo]
            if modo != base.modo or mao:
                inst = bruto(modo, semente, mao)
            else:
                inst = base
        else:
            caminho = os.path.normpath(os.path.join(self.dados, arquivo))
            # Recusa caminhos que saem da pasta de dados (travessia de diretório).
            if os.path.commonpath([caminho, os.path.normpath(self.dados)]) != os.path.normpath(self.dados) or not os.path.isfile(caminho):
                raise ErroRequisicao("instância não encontrada", "só são lidos arquivos dentro da pasta dados/ do projeto.", "escolha a instância na lista ou envie o arquivo pelo botão Enviar.")
            try:
                inst = ler_instancia(caminho, modo=modo, semente=semente, mao_unica=mao)
            except ErroInstancia as e:
                raise ErroRequisicao.de(e)
        if corpo.get("prioridades"):
            inst = inst.com_prioridades(int(corpo.get("semente_prioridade", 0)))
        return inst

    def gerar(self, corpo):
        n = int(corpo.get("n", 40))
        if not (1 <= n <= LIMITE_CLIENTES_SINTETICOS):
            raise ErroRequisicao("o número de clientes deve estar entre 1 e %d" % LIMITE_CLIENTES_SINTETICOS,
                                 "acima de %d clientes a geração e o cálculo deixam de ser interativos em Python; com 0 clientes não há o que rotear (1 cliente já dá o menor grafo: depósito e cliente)." % LIMITE_CLIENTES_SINTETICOS,
                                 "para instâncias maiores, use as bases de dados/ (por exemplo, kaggle/ecommerce/entregas.csv com 1000 entregas).")
        if float(corpo.get("capacidade", 100)) <= 0:
            raise ErroRequisicao("a capacidade precisa ser positiva", "com capacidade 0 nenhum pedido caberia em um veículo.", "informe um valor maior que 0.")
        semente = int(corpo.get("semente", 0))
        capacidade = float(corpo.get("capacidade", 100))
        agrupada = bool(corpo.get("agrupada", False))
        janelas = bool(corpo.get("janelas", True))

        def fabricar(modo, sem, mao=0.0):
            return gerar_instancia_sintetica(n, semente=semente, capacidade=capacidade, agrupada=agrupada, janelas=janelas, modo=modo, mao_unica=mao)

        inst = fabricar(corpo.get("modo", "completo"), semente)
        with self.trava:
            self.contador += 1
            chave = "gerada-%d" % self.contador
            self.registro[chave] = (inst, fabricar)
        return chave

    def enviar(self, corpo):
        conteudo = corpo.get("conteudo")
        if not isinstance(conteudo, str) or not conteudo.strip():
            raise ErroRequisicao("arquivo vazio", "o arquivo enviado não tem conteúdo.", "envie um .vrp, .txt (Solomon) ou .csv (entregas do Kaggle) com dados.")
        if len(conteudo) > 5_000_000:
            raise ErroRequisicao("arquivo grande demais", "o envio pela interface aceita até 5 MB.", "coloque o arquivo em dados/ e rode pela linha de comando.")
        # O formato é decidido pela extensão do arquivo original (.vrp, .txt de Solomon ou .csv de entregas).
        extensao = str(corpo.get("extensao", ".vrp")).lower()
        if not extensao.startswith("."):
            extensao = "." + extensao
        if extensao not in FORMATOS:
            raise ErroRequisicao.de(ErroInstancia("formato não reconhecido: '%s' (aceitos: .vrp, .txt, .csv)" % extensao))
        fd, caminho = tempfile.mkstemp(suffix=extensao)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(conteudo)
            inst = ler_instancia(caminho)
        except (ErroInstancia, ValueError, KeyError) as e:
            raise ErroRequisicao.de(e)
        finally:
            if os.path.exists(caminho):
                os.remove(caminho)
        nome = str(corpo.get("nome", "enviada"))[:40]
        inst.nome = nome

        def refazer(modo, sem, mao=0.0):
            fd2, c2 = tempfile.mkstemp(suffix=extensao)
            try:
                with os.fdopen(fd2, "w", encoding="utf-8") as f:
                    f.write(conteudo)
                nova = ler_instancia(c2, modo=modo, semente=sem, mao_unica=mao)
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
                raise ErroRequisicao("valor inválido em %s: '%s'" % (chave, valor), "o campo precisa ser um número.", "corrija o campo na tela.")

        capacidade = numero("capacidade", inst.capacidade)
        frota = numero("frota", inst.frota, int)
        dmax = numero("distancia_maxima", None)
        fixo = numero("custo_fixo", 0.0)
        peso = numero("peso_prioridade", 0.0)
        if capacidade <= 0:
            raise ErroRequisicao("capacidade %g inválida" % capacidade, "a capacidade é quanto cabe em um veículo; com 0 ou menos nenhum pedido caberia.", "informe um valor maior que 0 (ou deixe vazio para usar o da instância).")
        if frota < 1:
            raise ErroRequisicao("frota %d inválida" % frota, "a frota é o número máximo de veículos; com 0 nenhum cliente seria atendido.", "informe pelo menos 1 (ou deixe vazio para usar o da instância).")
        if dmax is not None and dmax <= 0:
            raise ErroRequisicao("distância máxima %g inválida" % dmax, "é o limite de distância de cada rota e precisa ser positivo.", "informe um valor maior que 0 ou deixe vazio para não ter limite.")
        if fixo < 0:
            raise ErroRequisicao("custo fixo negativo", "um custo fixo negativo premiaria usar mais veículos.", "use 0 ou um valor positivo.")
        if peso < 0:
            raise ErroRequisicao("peso de prioridade negativo", "λ pesa o atraso dos clientes urgentes; negativo premiaria atendê-los tarde e o custo poderia ficar negativo.", "use 0 (sem prioridade) ou um valor positivo, por exemplo 0,01.")
        maior = max(inst.nos, key=lambda no: no.demanda)
        if maior.demanda > capacidade:
            raise ErroRequisicao("o cliente %d tem demanda %g, maior que a capacidade %g" % (maior.id, maior.demanda, capacidade),
                                 "um pedido maior que o veículo vazio não cabe em nenhuma rota.",
                                 "aumente a capacidade para pelo menos %g." % maior.demanda)
        return Parametros(capacidade=capacidade, frota_maxima=frota, distancia_maxima=dmax, custo_fixo_veiculo=fixo, peso_prioridade=peso)

    def resolver(self, corpo):
        inst = self._carregar(corpo)
        par = self._parametros(inst, corpo)
        iteracoes = int(corpo.get("iteracoes", 5000))
        if not (0 <= iteracoes <= LIMITE_ITERACOES):
            raise ErroRequisicao("iterações devem estar entre 0 e %d" % LIMITE_ITERACOES, "o limite evita que uma requisição prenda o servidor por muito tempo.", "escolha um valor da lista.")
        semente = int(corpo.get("semente", 0))
        # Evita travar a demonstração em instâncias grandes: o solver devolve a melhor solução viável ao fim do prazo.
        limite_tempo = float(corpo.get("tempo_limite", 0) or 0)
        if not (0 <= limite_tempo <= 3600):
            raise ErroRequisicao("o tempo limite deve estar entre 0 e 3600 segundos", "0 quer dizer sem limite; acima de 1 hora a requisição prenderia o servidor.", "escolha um valor da lista.")
        pular = bool(corpo.get("pular_inatendiveis"))
        inalcancaveis = clientes_inalcancaveis(inst.grafo, 0)
        if inalcancaveis and not pular:
            raise ErroRequisicao("clientes sem caminho de ida e volta ao depósito: %s" % inalcancaveis[:10],
                                 "a BFS no grafo e no grafo transposto mostrou que esses clientes não são alcançáveis a partir do depósito, ou não têm como voltar.",
                                 "use o grafo completo, outra semente da rede viária ou marque Pular clientes impossíveis.")
        fora = []
        try:
            if pular:
                res, fora = resolver_atendiveis(inst, par, iteracoes=iteracoes, semente=semente, tempo_limite=limite_tempo or None)
            else:
                res = resolver(inst, par, iteracoes=iteracoes, semente=semente, tempo_limite=limite_tempo or None)
        except ClienteInatendivel as e:
            erro = explicar_inatendiveis(inst, par, e.clientes, como_pular="" if pular else "marque Pular clientes impossíveis (passo 3) para atender os demais e listar estes")
            raise ErroRequisicao(erro.mensagem, erro.motivo, erro.dica)
        rel = verificar(inst, par, res.rotas, res.custo, exigir_todos=not fora)
        dados = self._json_resultado(inst, par, res, rel)
        dados["fora"] = [{"cliente": u, "motivo": "; ".join(motivos_inatendivel(inst, par, u))} for u in fora]
        return dados

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

    def _grafo_consulta(self, corpo):
        from .consulta import grafo_da_instancia, grafo_de_texto
        if corpo.get("proprio"):
            return grafo_de_texto(corpo.get("arestas", ""), dirigido=bool(corpo.get("dirigido")))
        return grafo_da_instancia(self._carregar(corpo))

    # Caminho entre dois vértices com os seis algoritmos, no grafo da instância (modo escolhido) ou num grafo digitado.
    def caminho(self, corpo):
        from .consulta import comparar_caminhos, resumir_grafo
        try:
            g = self._grafo_consulta(corpo)
            origem, destino = corpo.get("origem"), corpo.get("destino")
            if origem in (None, "") or destino in (None, ""):
                raise ErroExplicado("informe a origem e o destino", "o caminho liga dois vértices.", "preencha os campos Origem e Destino.")
            r = comparar_caminhos(g, origem, destino)
            r["resumo"] = resumir_grafo(g)
            r["resumo"].pop("agm")
        except (ErroExplicado, CicloNegativo) as e:
            raise ErroRequisicao.de(e)
        coords = g.coordenadas
        if coords is None:
            import math
            n = g.grafo.n
            coords = [(math.cos(2 * math.pi * i / n - math.pi / 2), math.sin(2 * math.pi * i / n - math.pi / 2)) for i in range(n)]
        r["nos"] = [{"rotulo": str(rot), "x": x, "y": y} for rot, (x, y) in zip(g.rotulos, coords)]
        r["arestas"] = None
        if g.grafo.m <= 4000 and (corpo.get("proprio") or corpo.get("modo") == "viario"):
            r["arestas"] = [[u, v, p] for u in range(g.grafo.n) for v, p, _ in g.grafo.adj[u]]
        for linha in r["linhas"]:
            linha.setdefault("indices", None)
        return r

    def desempenho(self):
        import csv
        saida = {}
        if os.path.isdir(self.resultados):
            for nome in sorted(os.listdir(self.resultados)):
                if nome.endswith(".csv"):
                    with open(os.path.join(self.resultados, nome), encoding="utf-8") as f:
                        saida[nome[:-4]] = list(csv.DictReader(f))
        return saida
