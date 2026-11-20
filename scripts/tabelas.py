import csv
import os
import re
import statistics

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(RAIZ, "resultados")
SAIDA = os.path.join(RAIZ, "relatorio", "tabelas_geradas.tex")


def ler(nome):
    with open(os.path.join(RES, nome + ".csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(x):
    return float(x.replace(",", "."))


def fmt(x, casas=2):
    texto = ("%." + str(casas) + "f") % x
    return texto.lstrip("-") if float(texto) == 0 else texto


def linha(celulas):
    return " & ".join(celulas) + " \\\\\n"


def tabela(cabecalho, linhas, alinhamento):
    texto = "\\begin{tabular}{" + alinhamento + "}\n\\toprule\n" + linha(cabecalho) + "\\midrule\n"
    texto += "".join(linha(l) for l in linhas)
    return texto + "\\bottomrule\n\\end{tabular}\n"


def macro(nome, valor):
    return "\\newcommand{\\%s}{%s}\n" % (nome, valor)


def gerar():
    saida = ""
    sol = [l for l in ler("solomon") if not l["instancia"].startswith("M")]
    gaps = [num(l["gap_percentual"]) for l in sol]
    saida += macro("solN", len(sol))
    saida += macro("solGapMedio", fmt(statistics.mean(gaps)))
    saida += macro("solGapMediana", fmt(statistics.median(gaps)))
    saida += macro("solGapMax", fmt(max(gaps)))
    saida += macro("solIgual", sum(1 for g in gaps if abs(g) < 0.005))
    saida += macro("solTempoTotal", fmt(sum(num(l["tempo_s"]) for l in sol), 0))
    saida += macro("solTempoMedio", fmt(statistics.mean(num(l["tempo_s"]) for l in sol), 1))
    saida += macro("solVerificadas", sum(1 for l in sol if l["verificada"] == "sim"))
    saida += macro("solVeicSolver", sum(int(l["veiculos"]) for l in sol))
    saida += macro("solVeicBks", sum(int(l["bks_veiculos"]) for l in sol))
    pior = max(sol, key=lambda l: num(l["gap_percentual"]))
    saida += macro("solPior", pior["instancia"])
    def familia(n):
        return n[:3] if n.startswith("RC") else n[:2]
    linhas = []
    for f in ["C1", "C2", "R1", "R2", "RC1", "RC2"]:
        sel = [l for l in sol if familia(l["instancia"]) == f]
        g = [num(l["gap_percentual"]) for l in sel]
        linhas.append([f, str(len(sel)), fmt(statistics.mean(g)), fmt(max(g)), "%d / %d" % (sum(int(l["veiculos"]) for l in sel), sum(int(l["bks_veiculos"]) for l in sel)), fmt(statistics.mean(num(l["tempo_s"]) for l in sel), 1)])
    saida += "\\newcommand{\\tabSolomon}{\n" + tabela(["Família", "Inst.", "Dif. média (\\%)", "Dif. máx. (\\%)", "Veículos (nós / BKS)", "Tempo (s)"], linhas, "lrrrrr") + "}\n"
    x = [l for l in ler("cvrp_x") if not l["instancia"].startswith("M")]
    gx = [num(l["gap_percentual"]) for l in x]
    saida += macro("xGapMedio", fmt(statistics.mean(gx)))
    saida += macro("xGapMax", fmt(max(gx)))
    saida += macro("xVerificadas", sum(1 for l in x if l["verificada"] == "sim"))
    saida += macro("xN", len(x))
    linhas = [[l["instancia"], l["clientes"], l["bks_distancia"].replace(".0", ""), l["final"].replace(".0", ""), fmt(num(l["gap_percentual"])), "%s / %s" % (l["veiculos"], l["bks_veiculos"]), l["tempo_s"]] for l in x]
    saida += "\\newcommand{\\tabCvrp}{\n" + tabela(["Instância", "Cl.", "BKS", "Solver", "Dif. (\\%)", "Veíc.", "Tempo (s)"], linhas, "lrrrrrr") + "}\n"
    ab = ler("ablacao")
    linhas = [[l["instancia"], l["bks"], fmt(num(l["economias_gap_pct"]), 1), fmt(num(l["insercao_solomon_gap_pct"]), 1), fmt(num(l["construtivo_mais_busca_local_gap_pct"]), 1), fmt(num(l["mais_ruina_recriacao_gap_pct"]), 1)] for l in ab]
    saida += "\\newcommand{\\tabAblacao}{\n" + tabela(["Instância", "BKS", "Econ.", "Inserção", "+ Busca local", "+ Ruína e recr."], linhas, "lrrrrr") + "}\n"
    melhores = [min(num(l["economias_gap_pct"]), num(l["insercao_solomon_gap_pct"])) for l in ab]
    locais = [num(l["construtivo_mais_busca_local_gap_pct"]) for l in ab]
    finais = [num(l["mais_ruina_recriacao_gap_pct"]) for l in ab]
    saida += macro("ablConstrMin", fmt(min(melhores), 1))
    saida += macro("ablConstrMax", fmt(max(melhores), 1))
    saida += macro("ablLocalMin", fmt(min(locais), 1))
    saida += macro("ablLocalMax", fmt(max(locais), 1))
    saida += macro("ablFinalMin", fmt(min(finais), 1))
    saida += macro("ablFinalMax", fmt(max(finais), 1))
    nunca_piorou = all(l_ <= c_ + 1e-9 and f_ <= l_ + 1e-9 for c_, l_, f_ in zip(melhores, locais, finais))
    saida += macro("ablNuncaPiorou", "nenhuma etapa piorou a anterior" if nunca_piorou else "alguma etapa piorou a anterior")
    es = ler("escala")
    def inclinacao(chave):
        import math
        xs = [math.log(num(l["clientes"])) for l in es]
        ys = [math.log(max(num(l[chave]), 1e-4)) for l in es]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    saida += macro("expConstr", fmt(inclinacao("construtivo_e_busca_local_s"), 1))
    saida += macro("expIter", fmt(inclinacao("mil_iteracoes_s"), 1))
    saida += macro("expViario", fmt(inclinacao("construir_viario_dijkstra_s"), 1))
    saida += macro("expCompleto", fmt(inclinacao("construir_completo_s"), 1))
    linhas = [[l["clientes"], l["arcos_grafo_completo"], l["arcos_rede_viaria"], l["construir_completo_s"], l["construir_viario_dijkstra_s"], l["construtivo_e_busca_local_s"], l["mil_iteracoes_s"]] for l in es]
    saida += "\\newcommand{\\tabEscala}{\n" + tabela(["$n$", "Arcos (completo)", "Arcos (viário)", "Grafo completo", "Viário + Dijkstra", "Constr. + busca local", "1000 iter."], linhas, "rrrrrrr") + "}\n"
    saida += macro("escalaTodasVerificadas", "todas as soluções desta tabela foram aprovadas" if all(l["verificada"] == "sim" for l in es) else "nem todas as soluções desta tabela foram aprovadas")
    gv = ler("grafo_viario")
    ac = [num(l["acrescimo_percentual"]) for l in gv]
    saida += macro("viarioAcrescimoMedio", fmt(statistics.mean(ac), 1))
    saida += macro("viarioAcrescimoMin", fmt(min(ac), 1))
    saida += macro("viarioAcrescimoMax", fmt(max(ac), 1))
    saida += macro("viarioN", len(gv))
    saida += macro("viarioVerificadas", sum(1 for l in gv if l["verificada_viario"] == "sim"))
    saida += macro("viarioArcosCompleto", gv[0]["arcos_completo"])
    saida += macro("viarioArcosViario", gv[0]["arcos_viario"])
    linhas = [[l["semente"], l["distancia_completo"], l["distancia_viario"], fmt(num(l["acrescimo_percentual"]), 1), "%s / %s" % (l["veiculos_completo"], l["veiculos_viario"])] for l in gv]
    saida += "\\newcommand{\\tabViario}{\n" + tabela(["Semente", "Dist. completo", "Dist. viário", "Acréscimo (\\%)", "Veíc. (compl. / viário)"], linhas, "rrrrr") + "}\n"
    pr = ler("prioridade")
    linhas = [[l["cenario"], l["peso_prioridade"], l["distancia_media"], l["inicio_medio_prioridade_alta"], l["inicio_medio_prioridade_baixa"], l["soma_ponderada_inicios"]] for l in pr]
    saida += "\\newcommand{\\tabPrioridade}{\n" + tabela(["Cenário", "$\\lambda$", "Dist. média", "Início (alta)", "Início (baixa)", "$\\sum w\\,s$"], linhas, "lrrrrr") + "}\n"
    saida += macro("prioInstancias", pr[0]["instancias"])
    saida += macro("prioPesoMax", pr[-1]["peso_prioridade"])
    for chave, cen in (("Jan", "com janelas"), ("Sem", "sem janelas")):
        grupo = [l for l in pr if l["cenario"] == cen]
        z, m = grupo[0], grupo[-1]
        saida += macro("prio" + chave + "AltaZero", z["inicio_medio_prioridade_alta"])
        saida += macro("prio" + chave + "AltaMax", m["inicio_medio_prioridade_alta"])
        saida += macro("prio" + chave + "BaixaZero", z["inicio_medio_prioridade_baixa"])
        saida += macro("prio" + chave + "BaixaMax", m["inicio_medio_prioridade_baixa"])
        saida += macro("prio" + chave + "DistZero", z["distancia_media"])
        saida += macro("prio" + chave + "DistMax", m["distancia_media"])
        saida += macro("prio" + chave + "PondZero", z["soma_ponderada_inicios"])
        saida += macro("prio" + chave + "PondMax", m["soma_ponderada_inicios"])
        saida += macro("prio" + chave + "DistPct", fmt((num(m["distancia_media"]) / num(z["distancia_media"]) - 1) * 100, 1))
        saida += macro("prio" + chave + "PondPct", fmt((1 - num(m["soma_ponderada_inicios"]) / num(z["soma_ponderada_inicios"])) * 100, 1))
    ex = ler("exato")
    corpo = [l for l in ex if not l["instancia"].startswith("RESUMO")]
    ge = [num(l["gap_percentual"]) for l in corpo]
    saida += macro("exN", len(corpo))
    saida += macro("exOtimas", sum(1 for g in ge if g < 1e-6))
    saida += macro("exGapMedio", fmt(statistics.mean(ge)))
    saida += macro("exGapMax", fmt(max(ge)))
    saida += macro("exTempoExato", fmt(statistics.mean(num(l["tempo_exato_s"]) for l in corpo), 1))
    saida += macro("exTempoHeur", fmt(statistics.mean(num(l["tempo_heuristica_s"]) for l in corpo), 1))
    gh = ler("kaggle_gh")
    bks200 = {"c1": (20, 2704.57), "c2": (6, 1931.44), "r1": (20, 4784.11), "r2": (4, 4483.16), "rc1": (18, 3602.80), "rc2": (6, 3099.53)}
    linhas = []
    for l in gh:
        if l["clientes"] != "200":
            continue
        fam = l["instancia"].split("_")[0]
        bv, bd = bks200[fam]
        dist = num(l["final"])
        igual = int(l["veiculos"]) == bv
        dif = fmt((dist / bd - 1) * 100) if igual else "---"
        linhas.append([l["instancia"].replace("_", "\\_"), l["veiculos"], str(bv), fmt(dist), fmt(bd), dif, fmt(num(l["tempo_s"]), 1)])
    saida += "\\newcommand{\\tabGH}{\n" + tabela(["Instância", "Veíc.", "BKS veíc.", "Distância", "BKS dist.", "Dif. (\\%)", "Tempo (s)"], linhas, "lrrrrrr") + "}\n"
    saida += macro("ghN", len(gh))
    saida += macro("ghVerificadas", sum(1 for l in gh if l["verificada"] == "sim"))
    saida += macro("ghCompletas", sum(1 for l in gh if l["metodo"] == "completo"))
    comp = [l for l in gh if l["metodo"] == "completo"]
    saida += macro("ghMelhoriaMin", fmt(min(num(l["melhoria_percentual"]) for l in comp), 1))
    saida += macro("ghMelhoriaMax", fmt(max(num(l["melhoria_percentual"]) for l in comp), 1))
    busca = [l for l in gh if l["metodo"] == "busca local"]
    saida += macro("ghBuscaMelhoriaMin", fmt(min(num(l["melhoria_percentual"]) for l in busca), 1))
    saida += macro("ghBuscaMelhoriaMax", fmt(max(num(l["melhoria_percentual"]) for l in busca), 1))
    saida += macro("ghTempoMaxBusca", fmt(max(num(l["tempo_s"]) for l in busca), 0))
    saida += macro("ghTempoMaxCompleto", fmt(max(num(l["tempo_s"]) for l in comp), 0))
    en = ler("kaggle_entregas")
    linhas = []
    for l in en:
        if l["metodo"] != "completo" or l["grafo"] != "completo":
            continue
        linhas.append([l["entregas"], l["peso_prioridade"], fmt(num(l["distancia_km"]), 0), l["veiculos"], fmt(num(l["atraso_medio_alta_min"]), 0), fmt(num(l["atraso_medio_media_min"]), 0), fmt(num(l["atraso_medio_baixa_min"]), 0), fmt(num(l["tempo_s"]), 1)])
    saida += "\\newcommand{\\tabEntregas}{\n" + tabela(["Entregas", "$\\lambda$", "Dist. (km)", "Veíc.", "Atraso alta (min)", "Atraso média (min)", "Atraso baixa (min)", "Tempo (s)"], linhas, "rrrrrrrr") + "}\n"
    base = {l["entregas"]: l for l in en if l["peso_prioridade"] == "0.0" and l["grafo"] == "completo" and l["metodo"] == "completo"}
    pri = {l["entregas"]: l for l in en if l["peso_prioridade"] == "0.01" and l["grafo"] == "completo" and l["metodo"] == "completo"}
    saida += macro("entAltaBase", fmt(num(base["200"]["atraso_medio_alta_min"]), 0))
    saida += macro("entAltaPrio", fmt(num(pri["200"]["atraso_medio_alta_min"]), 0))
    saida += macro("entDistPct", fmt((num(pri["200"]["distancia_km"]) / num(base["200"]["distancia_km"]) - 1) * 100, 1))
    saida += macro("entAltaBaseQ", fmt(num(base["500"]["atraso_medio_alta_min"]), 0))
    saida += macro("entAltaPrioQ", fmt(num(pri["500"]["atraso_medio_alta_min"]), 0))
    saida += macro("entDistPctQ", fmt((num(pri["500"]["distancia_km"]) / num(base["500"]["distancia_km"]) - 1) * 100, 1))
    v = [l for l in en if l["grafo"] == "viario"][0]
    saida += macro("entViarioPct", fmt((num(v["distancia_km"]) / num(base["200"]["distancia_km"]) - 1) * 100, 1))
    saida += macro("entVerificadas", sum(1 for l in en if l["verificada"] == "sim"))
    saida += macro("entN", len(en))
    mil = [l for l in en if l["entregas"] == "1000" and l["peso_prioridade"] == "0.0"][0]
    saida += macro("entMil", mil["veiculos"])
    saida += macro("entMilTempo", fmt(num(mil["tempo_s"]), 0))
    # vírgula decimal, como se escreve em português; o {,} evita o espaço extra que o LaTeX põe depois da vírgula em modo matemático
    saida = re.sub(r"(?<=\d)\.(?=\d)", "{,}", saida)
    # o abstract é em inglês e usa ponto decimal
    saida += macro("solGapMedioEn", fmt(statistics.mean(gaps)))
    saida += macro("xGapMedioEn", fmt(statistics.mean(gx)))
    with open(SAIDA, "w", encoding="utf-8") as f:
        f.write(saida)
    print("gravado", SAIDA)


if __name__ == "__main__":
    gerar()
