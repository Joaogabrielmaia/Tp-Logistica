import math
import os
import random

from .caminhos import matrizes_de_caminhos
from .modelo import Instancia, No
from .rede_viaria import grafo_completo, grafo_viario


class ErroInstancia(ValueError):
    pass


# O roteamento guarda as matrizes de distância e de tempo entre todo par de pontos (n² valores cada): com 2000 clientes
# já são uns 1,5 GB de memória em Python. Acima disso a instância é recusada antes de montar as matrizes.
LIMITE_CLIENTES = 2000


def construir_instancia(nome, tipo, nos, capacidade, frota, modo="completo", regra="exato", semente=0, k_vizinhos=5, bks_custo=None, bks_rotas=None, mao_unica=0.0):
    if len(nos) < 2:
        raise ErroInstancia("a instância precisa de um depósito e ao menos um cliente")
    if len(nos) - 1 > LIMITE_CLIENTES:
        raise ErroInstancia("instância grande demais: %d clientes (o limite é %d)" % (len(nos) - 1, LIMITE_CLIENTES))
    predecessores = None
    if modo == "completo":
        grafo = grafo_completo(nos, regra)
        D = grafo.matriz_pesos()
        T = [linha[:] for linha in D]
    elif modo == "viario":
        grafo = grafo_viario(nos, k=k_vizinhos, semente=semente, fracao_mao_unica=mao_unica, regra=regra)
        D, T, predecessores = matrizes_de_caminhos(grafo)
    else:
        raise ErroInstancia("modo de grafo desconhecido: " + str(modo))
    return Instancia(nome, tipo, nos, grafo, capacidade, frota, D, T, modo, predecessores, bks_custo, bks_rotas, regra)


def _ler_secoes(caminho):
    cabecalho = {}
    secoes = {}
    atual = None
    with open(caminho, encoding="utf-8") as f:
        for bruta in f:
            linha = bruta.strip()
            if not linha or linha == "EOF":
                continue
            if ":" in linha:
                chave, valor = linha.split(":", 1)
                cabecalho[chave.strip()] = valor.strip()
                atual = None
            elif linha.endswith("_SECTION"):
                atual = linha
                secoes[atual] = []
            elif atual is not None:
                secoes[atual].append(linha.split())
    return cabecalho, secoes


def ler_solucao_bks(caminho):
    rotas = []
    custo = None
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if linha.startswith("Route"):
                rotas.append([int(x) for x in linha.split(":", 1)[1].split()])
            elif linha.startswith("Cost"):
                custo = float(linha.split()[1])
    return rotas, custo


def ler_vrplib(caminho, modo="completo", semente=0, mao_unica=0.0):
    if not os.path.isfile(caminho):
        raise ErroInstancia("arquivo não encontrado: " + caminho)
    cab, secoes = _ler_secoes(caminho)
    for obrigatoria in ("NODE_COORD_SECTION", "DEMAND_SECTION"):
        if obrigatoria not in secoes:
            raise ErroInstancia("seção ausente: " + obrigatoria)
    if "CAPACITY" not in cab:
        raise ErroInstancia("capacidade ausente")
    nome = cab.get("NAME", os.path.splitext(os.path.basename(caminho))[0])
    tipo = cab.get("TYPE", "CVRP")
    capacidade = float(cab["CAPACITY"])
    servico_padrao = float(cab.get("SERVICE_TIME", 0))
    coords = {int(l[0]): (float(l[1]), float(l[2])) for l in secoes["NODE_COORD_SECTION"]}
    demandas = {int(l[0]): float(l[1]) for l in secoes["DEMAND_SECTION"]}
    janelas = {int(l[0]): (float(l[1]), float(l[2])) for l in secoes.get("TIME_WINDOW_SECTION", [])}
    dimensao = int(cab.get("DIMENSION", len(coords)))
    if len(coords) != dimensao or len(demandas) != dimensao:
        raise ErroInstancia("DIMENSION inconsistente com as seções")
    ids = sorted(coords)
    nos = []
    for indice, ident in enumerate(ids):
        x, y = coords[ident]
        inicio, fim = janelas.get(ident, (0.0, math.inf))
        servico = 0.0 if indice == 0 else servico_padrao
        nos.append(No(indice, x, y, demandas[ident], inicio, fim, servico, 3))
    if nos[0].demanda != 0:
        raise ErroInstancia("o depósito deve ter demanda zero")
    if any(no.demanda > capacidade for no in nos):
        raise ErroInstancia("há cliente com demanda maior que a capacidade do veículo")
    # As BKS de Solomon usam distância truncada na 1ª casa decimal; as do conjunto X, o inteiro mais próximo.
    regra = "decimo" if tipo.upper() == "CVRPTW" else "inteiro"
    frota = int(cab["VEHICLES"]) if "VEHICLES" in cab else len(nos) - 1
    bks_rotas = bks_custo = None
    sol = os.path.splitext(caminho)[0] + ".sol"
    if os.path.isfile(sol):
        bks_rotas, bks_custo = ler_solucao_bks(sol)
    return construir_instancia(nome, tipo, nos, capacidade, frota, modo, regra, semente, 5, bks_custo, bks_rotas, mao_unica)


def ler_solomon_txt(caminho, modo="completo", semente=0, regra="exato", mao_unica=0.0):
    if not os.path.isfile(caminho):
        raise ErroInstancia("arquivo não encontrado: " + caminho)
    with open(caminho, encoding="utf-8", errors="replace") as f:
        linhas = [l.split() for l in f.read().splitlines() if l.strip()]
    nome = os.path.splitext(os.path.basename(caminho))[0]
    inicio = None
    for i, l in enumerate(linhas):
        if l and l[0].upper() == "VEHICLE":
            inicio = i
            break
    if inicio is None or inicio + 2 >= len(linhas):
        raise ErroInstancia("cabeçalho VEHICLE ausente")
    try:
        frota = int(linhas[inicio + 2][0])
        capacidade = float(linhas[inicio + 2][1])
    except (ValueError, IndexError):
        raise ErroInstancia("frota e capacidade inválidas")
    corpo = []
    for l in linhas[inicio + 3:]:
        if len(l) == 7:
            try:
                corpo.append([float(v) for v in l])
            except ValueError:
                continue
    if len(corpo) < 2:
        raise ErroInstancia("a instância precisa de um depósito e ao menos um cliente")
    corpo.sort(key=lambda v: v[0])
    nos = [No(i, v[1], v[2], v[3], v[4], v[5], v[6], 3) for i, v in enumerate(corpo)]
    if nos[0].demanda != 0:
        raise ErroInstancia("o depósito deve ter demanda zero")
    if any(no.demanda > capacidade for no in nos):
        raise ErroInstancia("há cliente com demanda maior que a capacidade do veículo")
    return construir_instancia(nome, "CVRPTW", nos, capacidade, frota, modo, regra, semente, mao_unica=mao_unica)


VELOCIDADE_KMH = 35.0
CAPACIDADE_ENTREGAS = 500.0
SERVICO_HORAS = 0.1


def ler_entregas_csv(caminho, modo="completo", semente=0, limite=None, capacidade=CAPACIDADE_ENTREGAS, mao_unica=0.0):
    import csv
    if not os.path.isfile(caminho):
        raise ErroInstancia("arquivo não encontrado: " + caminho)
    obrigatorias = ("order_latitude", "order_longitude", "order_weight_kg", "delivery_time_window_hrs", "order_priority", "time_of_day")
    with open(caminho, newline="", encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        faltando = [c for c in obrigatorias if c not in (leitor.fieldnames or [])]
        if faltando:
            raise ErroInstancia("colunas ausentes: " + ", ".join(faltando))
        try:
            linhas = [{c: float(r[c]) for c in obrigatorias} for r in leitor]
        except (ValueError, TypeError):
            raise ErroInstancia("valor não numérico no arquivo")
    if limite is not None:
        linhas = linhas[:limite]
    if not linhas:
        raise ErroInstancia("arquivo sem entregas")
    lat0 = sum(r["order_latitude"] for r in linhas) / len(linhas)
    lon0 = sum(r["order_longitude"] for r in linhas) / len(linhas)
    # Projeção equirretangular: 1 grau de latitude vale cerca de 110,6 km e a longitude encolhe com cos(latitude). O
    # arquivo não traz depósito, por isso ele fica no centroide.
    km_lat = 110.574
    km_lon = 111.320 * math.cos(math.radians(lat0))
    # Tempo medido em km a 35 km/h (velocidade média do arquivo); o depósito funciona por 48 h para não bloquear
    # janelas tardias.
    horizonte = (24 + 24) * VELOCIDADE_KMH
    nos = [No(0, 0.0, 0.0, 0.0, 0.0, horizonte, 0.0, 3)]
    for i, r in enumerate(linhas, 1):
        x = (r["order_longitude"] - lon0) * km_lon
        y = (r["order_latitude"] - lat0) * km_lat
        peso = r["order_weight_kg"]
        if peso > capacidade:
            raise ErroInstancia("há entrega com peso maior que a capacidade do veículo")
        pronto = r["time_of_day"] * VELOCIDADE_KMH
        fim = pronto + r["delivery_time_window_hrs"] * VELOCIDADE_KMH
        # O arquivo não define o sentido da escala: assumimos 1 como a mais urgente e agrupamos 3 e 4 como prioridade
        # baixa.
        prioridade = 1 if r["order_priority"] <= 1 else (2 if r["order_priority"] <= 2 else 3)
        nos.append(No(i, x, y, peso, pronto, fim, SERVICO_HORAS * VELOCIDADE_KMH, prioridade))
    nome = os.path.splitext(os.path.basename(caminho))[0] + ("-%d" % limite if limite else "")
    frota = len(nos) - 1
    inst = construir_instancia(nome, "CVRPTW", nos, capacidade, frota, modo, "exato", semente, mao_unica=mao_unica)
    inst.prioridade_propria = True
    return inst


FORMATOS = (".vrp", ".txt", ".csv")


def ler_instancia(caminho, modo="completo", semente=0, mao_unica=0.0):
    ext = os.path.splitext(caminho)[1].lower()
    if ext not in FORMATOS:
        raise ErroInstancia("formato não reconhecido: '%s' (aceitos: .vrp, .txt, .csv)" % (ext or "sem extensão"))
    if not os.path.isfile(caminho):
        raise ErroInstancia("arquivo não encontrado: " + caminho)
    if os.path.getsize(caminho) == 0:
        raise ErroInstancia("arquivo vazio: " + caminho)
    try:
        if ext == ".txt":
            return ler_solomon_txt(caminho, modo, semente, mao_unica=mao_unica)
        if ext == ".csv":
            return ler_entregas_csv(caminho, modo, semente, mao_unica=mao_unica)
        return ler_vrplib(caminho, modo, semente, mao_unica)
    except ErroInstancia:
        raise
    except UnicodeDecodeError:
        raise ErroInstancia("formato não reconhecido: o arquivo não é texto")
    # Linha fora do formato (texto onde se esperava número, coluna faltando): vira um erro explicado, sem traceback.
    except (ValueError, IndexError, KeyError) as e:
        raise ErroInstancia("conteúdo inválido no arquivo (%s: %s)" % (type(e).__name__, e))


# O grafo é construído antes das janelas de tempo, que partem das distâncias reais; assim todo cliente é atendível
# individualmente em qualquer modo.
def gerar_instancia_sintetica(n, semente=0, capacidade=100, frota=None, agrupada=False, janelas=True, modo="completo", lado=100, mao_unica=0.0):
    rng = random.Random(semente)
    nos = [No(0, lado / 2, lado / 2, 0, 0.0, math.inf, 0.0, 3)]
    centros = [(rng.uniform(0, lado), rng.uniform(0, lado)) for _ in range(max(2, n // 15))]
    pontos = []
    for _ in range(n):
        if agrupada:
            cx, cy = rng.choice(centros)
            x = min(max(rng.gauss(cx, lado * 0.06), 0), lado)
            y = min(max(rng.gauss(cy, lado * 0.06), 0), lado)
        else:
            x, y = rng.uniform(0, lado), rng.uniform(0, lado)
        pontos.append((round(x), round(y)))
    servico = 10.0
    for i, (x, y) in enumerate(pontos, start=1):
        nos.append(No(i, x, y, rng.randint(5, 30), 0.0, math.inf, servico, 3))
    total = sum(no.demanda for no in nos)
    if frota is None:
        frota = max(2, int(math.ceil(total / capacidade * 1.8)) + 2)
    inst = construir_instancia("sintetica-n%d-s%d" % (n, semente), "CVRPTW" if janelas else "CVRP", nos, capacidade, frota, modo, "exato", semente, mao_unica=mao_unica)
    if janelas:
        D = inst.D
        horizonte = max(lado * 6.0, max(D[0][i] + D[i][0] for i in range(1, n + 1)) + servico + 60.0)
        novos = [No(0, nos[0].x, nos[0].y, 0, 0.0, horizonte, 0.0, 3)]
        for no in nos[1:]:
            ida, volta = D[0][no.id], D[no.id][0]
            baixo = ida + 5.0
            alto = horizonte - volta - servico - 5.0
            centro = rng.uniform(baixo, alto)
            largura = rng.choice([30, 60, 90])
            inicio = max(0.0, centro - largura / 2)
            fim = min(centro + largura / 2, alto + 5.0)
            novos.append(No(no.id, no.x, no.y, no.demanda, float(inicio), float(fim), servico, 3))
        inst.nos = novos
        inst._derivar()
    return inst


def listar_instancias(diretorio):
    resultado = []
    for raiz, _, arquivos in os.walk(diretorio):
        for nome in sorted(arquivos):
            if nome.lower().endswith((".vrp", ".txt", ".csv")):
                resultado.append(os.path.relpath(os.path.join(raiz, nome), diretorio).replace(os.sep, "/"))
    return sorted(resultado)
