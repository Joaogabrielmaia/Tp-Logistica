import csv
import math
import os
import statistics
import time
from multiprocessing import Pool

from .avaliacao import EstadoRota
from .exato import resolver_exato
from .leitor import VELOCIDADE_KMH, gerar_instancia_sintetica, ler_entregas_csv, ler_instancia, ler_vrplib
from .modelo import Parametros
from .solver import resolver
from .verificador import verificar

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, "dados")
ABLACAO = ["solomon/C101", "solomon/C201", "solomon/R101", "solomon/R201", "solomon/RC101", "solomon/RC201", "cvrp-x/X-n101-k25", "cvrp-x/X-n153-k22"]


def _gravar(saida, nome, linhas):
    os.makedirs(saida, exist_ok=True)
    caminho = os.path.join(saida, nome + ".csv")
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)
    print("gravado", caminho, "(%d linhas)" % len(linhas))


def _fmt(x, casas=2):
    return round(x, casas) + 0.0


def _rodar_referencia(args):
    rel, iteracoes, semente = args
    inst = ler_vrplib(os.path.join(DADOS, rel + ".vrp"))
    par = inst.parametros_padrao()
    res = resolver(inst, par, iteracoes=iteracoes, semente=semente)
    ver = verificar(inst, par, res.rotas, res.custo)
    construtivo = min(res.etapas[0]["distancia"], res.etapas[1]["distancia"])
    return {
        "instancia": inst.nome,
        "clientes": inst.n,
        "bks_distancia": _fmt(inst.bks_custo, 1),
        "bks_veiculos": len(inst.bks_rotas),
        "construtivo": _fmt(construtivo),
        "busca_local": _fmt(res.etapas[2]["distancia"]),
        "final": _fmt(res.distancia),
        "veiculos": res.veiculos,
        "gap_percentual": _fmt((res.distancia / inst.bks_custo - 1) * 100),
        "tempo_s": _fmt(res.tempo_total),
        "verificada": "sim" if ver.viavel else "NAO",
    }


def _resumo(linhas):
    gaps = [float(l["gap_percentual"]) for l in linhas]
    return {
        "instancia": "MÉDIA / MEDIANA / MÁX",
        "clientes": "",
        "bks_distancia": "",
        "bks_veiculos": "",
        "construtivo": "",
        "busca_local": "",
        "final": "",
        "veiculos": "",
        "gap_percentual": "%.2f / %.2f / %.2f" % (statistics.mean(gaps), statistics.median(gaps), max(gaps)),
        "tempo_s": _fmt(sum(float(l["tempo_s"]) for l in linhas)),
        "verificada": "%d/%d" % (sum(1 for l in linhas if l["verificada"] == "sim"), len(linhas)),
    }


def _conjunto_referencia(prefixo, nomes, iteracoes, semente=1):
    tarefas = [(rel, iteracoes, semente) for rel in nomes]
    with Pool(min(4, os.cpu_count() or 1)) as pool:
        linhas = pool.map(_rodar_referencia, tarefas)
    linhas.append(_resumo(linhas))
    return linhas


def solomon(saida, iteracoes, rapido):
    nomes = sorted(f[:-4] for f in os.listdir(os.path.join(DADOS, "solomon")) if f.endswith(".vrp"))
    nomes = ["solomon/" + n for n in nomes]
    if rapido:
        nomes = nomes[::8]
    _gravar(saida, "solomon", _conjunto_referencia("solomon", nomes, iteracoes))


def cvrp_x(saida, iteracoes, rapido):
    nomes = sorted(f[:-4] for f in os.listdir(os.path.join(DADOS, "cvrp-x")) if f.endswith(".vrp"))
    nomes = ["cvrp-x/" + n for n in nomes]
    if rapido:
        nomes = nomes[:2]
    _gravar(saida, "cvrp_x", _conjunto_referencia("cvrp_x", nomes, iteracoes))


def _ablacao_uma(args):
    rel, iteracoes = args
    inst = ler_vrplib(os.path.join(DADOS, rel + ".vrp"))
    par = inst.parametros_padrao()
    res = resolver(inst, par, iteracoes=iteracoes, semente=1)
    linha = {"instancia": inst.nome, "bks": _fmt(inst.bks_custo, 1)}
    chaves = {"economias": "economias", "insercao": "insercao_solomon", "busca local": "construtivo_mais_busca_local", "ruína e recriação": "mais_ruina_recriacao", "polimento final": "mais_polimento"}
    for e in res.etapas:
        linha[chaves[e["etapa"]]] = _fmt(e["distancia"])
        linha[chaves[e["etapa"]] + "_gap_pct"] = _fmt((e["distancia"] / inst.bks_custo - 1) * 100)
    return linha


def ablacao(saida, iteracoes, rapido):
    nomes = ABLACAO[:2] if rapido else ABLACAO
    with Pool(min(4, os.cpu_count() or 1)) as pool:
        linhas = pool.map(_ablacao_uma, [(n, iteracoes) for n in nomes])
    _gravar(saida, "ablacao", linhas)


def escala(saida, iteracoes, rapido):
    tamanhos = [25, 50] if rapido else [25, 50, 100, 150, 200, 300, 400]
    linhas = []
    for n in tamanhos:
        t0 = time.time()
        inst = gerar_instancia_sintetica(n, semente=7, capacidade=100, modo="completo")
        t_grafo = time.time() - t0
        t0 = time.time()
        inst_v = gerar_instancia_sintetica(n, semente=7, capacidade=100, modo="viario")
        t_viario = time.time() - t0
        par = inst.parametros_padrao()
        t0 = time.time()
        res0 = resolver(inst, par, usar_otimizador=False)
        t_construtivo = time.time() - t0
        t0 = time.time()
        res = resolver(inst, par, iteracoes=1000, semente=1)
        t_total = time.time() - t0
        ver = verificar(inst, par, res.rotas, res.custo)
        linhas.append({
            "clientes": n,
            "arcos_grafo_completo": inst.grafo.m,
            "arcos_rede_viaria": inst_v.grafo.m,
            "construir_completo_s": _fmt(t_grafo, 3),
            "construir_viario_dijkstra_s": _fmt(t_viario, 3),
            "construtivo_e_busca_local_s": _fmt(t_construtivo, 3),
            "mil_iteracoes_s": _fmt(t_total - t_construtivo, 3),
            "distancia": _fmt(res.distancia),
            "veiculos": res.veiculos,
            "verificada": "sim" if ver.viavel else "NAO",
        })
        print("escala n=%d ok" % n)
    _gravar(saida, "escala", linhas)


def grafo_viario(saida, iteracoes, rapido):
    sementes = range(2) if rapido else range(6)
    linhas = []
    for s in sementes:
        completo = gerar_instancia_sintetica(80, semente=s, capacidade=100, modo="completo")
        viario = gerar_instancia_sintetica(80, semente=s, capacidade=100, modo="viario")
        rc = resolver(completo, completo.parametros_padrao(), iteracoes=min(iteracoes, 5000), semente=1)
        rv = resolver(viario, viario.parametros_padrao(), iteracoes=min(iteracoes, 5000), semente=1)
        vv = verificar(viario, viario.parametros_padrao(), rv.rotas, rv.custo)
        linhas.append({
            "semente": s,
            "arcos_completo": completo.grafo.m,
            "arcos_viario": viario.grafo.m,
            "distancia_completo": _fmt(rc.distancia),
            "distancia_viario": _fmt(rv.distancia),
            "acrescimo_percentual": _fmt((rv.distancia / rc.distancia - 1) * 100),
            "veiculos_completo": rc.veiculos,
            "veiculos_viario": rv.veiculos,
            "verificada_viario": "sim" if vv.viavel else "NAO",
        })
    _gravar(saida, "grafo_viario", linhas)


def _inicio_medio(inst, par, rotas, prioridade):
    soma, qtd = 0.0, 0
    for rota in rotas:
        est = EstadoRota(inst, par, rota)
        for u, t in zip(rota, est.E):
            if inst.nos[u].prioridade == prioridade:
                soma += t
                qtd += 1
    return soma / qtd if qtd else float("nan")


def _soma_ponderada(inst, par, rotas):
    total = 0.0
    for rota in rotas:
        est = EstadoRota(inst, par, rota)
        for u, t in zip(rota, est.E):
            total += inst.w[u] * t
    return total


def prioridade(saida, iteracoes, rapido):
    sementes = range(2) if rapido else range(5)
    pesos = [0.0, 0.5, 1.0, 2.0, 5.0]
    linhas = []
    for janelas in (True, False):
        for peso in pesos:
            dist, alta, baixa, ponderada = [], [], [], []
            for s in sementes:
                inst = gerar_instancia_sintetica(60, semente=s, capacidade=100, janelas=janelas).com_prioridades(s)
                base = Parametros(100, inst.frota)
                par = Parametros(100, inst.frota, peso_prioridade=peso)
                res = resolver(inst, par, iteracoes=min(iteracoes, 3000), semente=1)
                assert verificar(inst, par, res.rotas, res.custo).viavel
                dist.append(res.distancia)
                alta.append(_inicio_medio(inst, base, res.rotas, 1))
                baixa.append(_inicio_medio(inst, base, res.rotas, 3))
                ponderada.append(_soma_ponderada(inst, base, res.rotas))
            linhas.append({
                "cenario": "com janelas" if janelas else "sem janelas",
                "peso_prioridade": peso,
                "distancia_media": _fmt(statistics.mean(dist)),
                "inicio_medio_prioridade_alta": _fmt(statistics.mean(alta)),
                "inicio_medio_prioridade_baixa": _fmt(statistics.mean(baixa)),
                "soma_ponderada_inicios": _fmt(statistics.mean(ponderada), 0),
                "instancias": len(list(sementes)),
            })
    _gravar(saida, "prioridade", linhas)


def exato(saida, iteracoes, rapido):
    sementes = range(4) if rapido else range(25)
    linhas = []
    for janelas in (True, False):
        for s in sementes:
            inst = gerar_instancia_sintetica(8, semente=s, capacidade=60, janelas=janelas)
            par = inst.parametros_padrao()
            t0 = time.time()
            custo, _ = resolver_exato(inst, par, limite_clientes=8)
            t_exato = time.time() - t0
            if custo is None:
                continue
            t0 = time.time()
            res = resolver(inst, par, iteracoes=2000, semente=1)
            t_heur = time.time() - t0
            linhas.append({
                "instancia": "n8-s%d-%s" % (s, "janelas" if janelas else "sem-janelas"),
                "otimo": _fmt(custo),
                "heuristica": _fmt(res.custo),
                "gap_percentual": _fmt((res.custo / custo - 1) * 100),
                "tempo_exato_s": _fmt(t_exato, 3),
                "tempo_heuristica_s": _fmt(t_heur, 3),
            })
    gaps = [float(l["gap_percentual"]) for l in linhas]
    linhas.append({
        "instancia": "RESUMO: %d/%d ótimas, gap médio %.2f%%, máximo %.2f%%" % (sum(1 for g in gaps if g < 1e-6), len(gaps), statistics.mean(gaps), max(gaps)),
        "otimo": "", "heuristica": "", "gap_percentual": "", "tempo_exato_s": "", "tempo_heuristica_s": "",
    })
    _gravar(saida, "exato", linhas)


FAMILIAS_GH = ["c1", "c2", "r1", "r2", "rc1", "rc2"]
TAMANHOS_GH = [2, 4, 6, 8, 10]


# Para 600 a 1000 clientes roda-se a construção e a busca local, sem a ruína e recriação, que em Python
# levaria vários minutos por instância nessa escala.
def _linha_kaggle(inst, par, rotas, custo, distancia, construtivo, tempo, metodo):
    ver = verificar(inst, par, rotas, custo)
    return {
        "instancia": inst.nome,
        "clientes": inst.n,
        "metodo": metodo,
        "veiculos": len(rotas),
        "construtivo": _fmt(construtivo),
        "final": _fmt(distancia),
        "melhoria_percentual": _fmt((1 - distancia / construtivo) * 100),
        "tempo_s": _fmt(tempo),
        "verificada": "sim" if ver.viavel else "NAO",
    }


def _rodar_gh(args):
    arquivo, iteracoes, semente, completo = args
    inst = ler_instancia(os.path.join(DADOS, "kaggle", "gehring-homberger", arquivo + ".txt"))
    par = inst.parametros_padrao()
    res = resolver(inst, par, iteracoes=iteracoes, semente=semente, usar_otimizador=completo)
    construtivo = min(res.etapas[0]["distancia"], res.etapas[1]["distancia"])
    return _linha_kaggle(inst, par, res.rotas, res.custo, res.distancia, construtivo, res.tempo_total, "completo" if completo else "busca local")


def kaggle_gh(saida, iteracoes, rapido):
    tamanhos = [2] if rapido else TAMANHOS_GH
    tarefas = [("%s_%d_1" % (f, d), min(iteracoes, 500), 1, d <= 4) for d in tamanhos for f in FAMILIAS_GH]
    with Pool(min(4, os.cpu_count() or 1)) as pool:
        linhas = pool.map(_rodar_gh, tarefas, chunksize=1)
    _gravar(saida, "kaggle_gh", linhas)


def _atraso_medio(inst, par, rotas, prioridade):
    soma, qtd = 0.0, 0
    for rota in rotas:
        est = EstadoRota(inst, par, rota)
        for u, t in zip(rota, est.E):
            if u and inst.nos[u].prioridade == prioridade:
                soma += t - inst.nos[u].inicio
                qtd += 1
    return soma / qtd * 60.0 / VELOCIDADE_KMH if qtd else float("nan")


def _rodar_entregas(args):
    n, peso, modo, iteracoes, semente, completo = args
    inst = ler_entregas_csv(os.path.join(DADOS, "kaggle", "ecommerce", "entregas.csv"), modo=modo, semente=semente, limite=n)
    base = inst.parametros_padrao()
    par = Parametros(base.capacidade, base.frota_maxima, peso_prioridade=peso)
    res = resolver(inst, par, iteracoes=iteracoes, semente=semente, usar_otimizador=completo)
    rotas, custo, distancia, tempo = res.rotas, res.custo, res.distancia, res.tempo_total
    metodo = "completo" if completo else "busca local"
    ver = verificar(inst, par, rotas, custo)
    return {
        "entregas": n,
        "grafo": modo,
        "metodo": metodo,
        "peso_prioridade": peso,
        "distancia_km": _fmt(distancia),
        "veiculos": len(rotas),
        "atraso_medio_alta_min": _fmt(_atraso_medio(inst, base, rotas, 1)),
        "atraso_medio_media_min": _fmt(_atraso_medio(inst, base, rotas, 2)),
        "atraso_medio_baixa_min": _fmt(_atraso_medio(inst, base, rotas, 3)),
        "tempo_s": _fmt(tempo),
        "verificada": "sim" if ver.viavel else "NAO",
    }


def kaggle_entregas(saida, iteracoes, rapido):
    tamanhos = [100] if rapido else [100, 200, 500, 1000]
    tarefas = [(n, peso, "completo", min(iteracoes, {100: 2000, 200: 2000, 500: 500}.get(n, 0)), 1, n <= 500) for n in tamanhos for peso in (0.0, 0.01, 0.05)]
    if not rapido:
        tarefas.append((200, 0.0, "viario", 2000, 1, True))
    with Pool(min(4, os.cpu_count() or 1)) as pool:
        linhas = pool.map(_rodar_entregas, tarefas, chunksize=1)
    _gravar(saida, "kaggle_entregas", linhas)


CONJUNTOS = {"solomon": solomon, "cvrp_x": cvrp_x, "ablacao": ablacao, "escala": escala, "grafo_viario": grafo_viario, "prioridade": prioridade, "exato": exato, "kaggle_gh": kaggle_gh, "kaggle_entregas": kaggle_entregas}


def executar(conjunto, saida, iteracoes, rapido):
    nomes = list(CONJUNTOS) if conjunto == "todos" else [conjunto]
    for nome in nomes:
        inicio = time.time()
        print("== %s" % nome)
        CONJUNTOS[nome](saida, iteracoes, rapido)
        print("   %.1f s" % (time.time() - inicio))
    return 0
