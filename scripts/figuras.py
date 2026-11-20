import csv
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, ScalarFormatter
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from logistica.leitor import gerar_instancia_sintetica

RES = os.path.join(RAIZ, "resultados")
OUT = os.path.join(RAIZ, "relatorio", "figuras")
AZUL, LARANJA, VERDE, CINZA, VERMELHO = "#1f5fd1", "#d9822b", "#2e9d6a", "#8a93a6", "#c0392b"

plt.rcParams.update({"font.size": 8.5, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 150, "savefig.bbox": "tight"})

def _com_virgula(valor, _pos):
    return ("%g" % valor).replace(".", ",")


def salvar(fig, nome):
    # eixos lineares com vírgula decimal; eixos log e rótulos fixos (famílias, instâncias) ficam como estão
    for ax in fig.axes:
        for eixo, escala in ((ax.xaxis, ax.get_xscale()), (ax.yaxis, ax.get_yscale())):
            if escala == "linear" and isinstance(eixo.get_major_formatter(), ScalarFormatter):
                eixo.set_major_formatter(FuncFormatter(_com_virgula))
    fig.savefig(os.path.join(OUT, nome))



def ler(nome):
    with open(os.path.join(RES, nome + ".csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def gap_solomon():
    linhas = [l for l in ler("solomon") if not l["instancia"].startswith("M")]
    grupos = ["C1", "C2", "R1", "R2", "RC1", "RC2"]
    def grupo(n):
        return n[:3] if n.startswith("RC") else n[:2]
    fig, ax = plt.subplots(figsize=(6.2, 2.5))
    x = 0
    ticks, rotulos = [], []
    cores = [AZUL, AZUL, LARANJA, LARANJA, VERDE, VERDE]
    for g, cor in zip(grupos, cores):
        sel = [l for l in linhas if grupo(l["instancia"]) == g]
        xs = np.arange(x, x + len(sel))
        ax.bar(xs, [float(l["gap_percentual"]) for l in sel], color=cor, width=0.8)
        ticks.append(x + (len(sel) - 1) / 2)
        rotulos.append(g)
        x += len(sel) + 1
    ax.set_xticks(ticks)
    ax.set_xticklabels(rotulos)
    ax.set_ylabel("diferença para a BKS (%)")
    ax.set_xlabel("família de instâncias Solomon")
    salvar(fig, "fig_gap_solomon.pdf")
    plt.close(fig)


def ablacao():
    linhas = ler("ablacao")
    etapas = [("economias_gap_pct", "economias"), ("insercao_solomon_gap_pct", "inserção"), ("construtivo_mais_busca_local_gap_pct", "+ busca local"), ("mais_ruina_recriacao_gap_pct", "+ ruína e recriação")]
    fig, ax = plt.subplots(figsize=(6.2, 2.7))
    larg = 0.2
    cores = [CINZA, "#b6bfd1", LARANJA, AZUL]
    xs = np.arange(len(linhas))
    for k, ((chave, nome), cor) in enumerate(zip(etapas, cores)):
        valores = [max(float(l[chave]), 0.05) for l in linhas]
        ax.bar(xs + (k - 1.5) * larg, valores, larg, label=nome, color=cor)
    ax.set_yscale("log")
    ax.set_xticks(xs)
    ax.set_xticklabels([l["instancia"] for l in linhas], rotation=30, ha="right")
    ax.set_ylabel("diferença para a BKS (%, escala log)")
    ax.legend(ncol=4, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, 1.18), frameon=False)
    salvar(fig, "fig_ablacao.pdf")
    plt.close(fig)


def escala():
    linhas = ler("escala")
    n = np.array([float(l["clientes"]) for l in linhas])
    series = [("construtivo e busca local", "construtivo_e_busca_local_s", AZUL), ("1000 iterações de ruína e recriação", "mil_iteracoes_s", LARANJA), ("grafo viário com Dijkstra", "construir_viario_dijkstra_s", VERDE)]
    fig, ax = plt.subplots(figsize=(6.2, 2.7))
    for nome, chave, cor in series:
        t = np.array([float(l[chave]) for l in linhas])
        inc = np.polyfit(np.log(n), np.log(np.maximum(t, 1e-4)), 1)[0]
        ax.plot(n, t, "o-", color=cor, label=("%s (expoente ≈ %.1f)" % (nome, inc)).replace(".", ","), ms=3.5)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("número de clientes")
    ax.set_ylabel("tempo (s)")
    ax.legend(fontsize=7, frameon=False)
    salvar(fig, "fig_escala.pdf")
    plt.close(fig)


def prioridade():
    linhas = ler("prioridade")
    fig, eixos = plt.subplots(1, 2, figsize=(6.4, 2.6), sharey=False)
    for ax, cen in zip(eixos, ("com janelas", "sem janelas")):
        g = [l for l in linhas if l["cenario"] == cen]
        pesos = [float(l["peso_prioridade"]) for l in g]
        ax.plot(pesos, [float(l["inicio_medio_prioridade_alta"]) for l in g], "o-", color=VERMELHO, label="início médio, prioridade alta", ms=3.5)
        ax.plot(pesos, [float(l["inicio_medio_prioridade_baixa"]) for l in g], "s-", color=CINZA, label="início médio, prioridade baixa", ms=3.5)
        ax.set_title(cen, fontsize=8.5)
        ax.set_xlabel("peso de prioridade (λ)")
        ax2 = ax.twinx()
        ax2.plot(pesos, [float(l["distancia_media"]) for l in g], "^--", color=AZUL, label="distância total média", ms=3.5)
        ax2.grid(False)
        ax2.spines["right"].set_visible(True)
        if cen == "com janelas":
            ax.set_ylabel("instante médio de início")
        else:
            ax2.set_ylabel("distância total")
    h1, l1 = eixos[0].get_legend_handles_labels()
    h2, l2 = eixos[0].figure.axes[1].get_legend_handles_labels()
    fig.legend(h1 + h2, l1 + l2, fontsize=7, frameon=False, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.12))
    fig.tight_layout()
    salvar(fig, "fig_prioridade.pdf")
    plt.close(fig)


def modos_do_grafo():
    fig, eixos = plt.subplots(1, 2, figsize=(6.2, 3.0))
    for ax, modo, titulo in zip(eixos, ("completo", "viario"), ("Grafo completo", "Rede viária (k = 5 e árvore geradora)")):
        inst = gerar_instancia_sintetica(24, semente=3, modo=modo, janelas=False)
        vistos = set()
        for u in range(inst.grafo.n):
            for v, _, _ in inst.grafo.adj[u]:
                chave = (min(u, v), max(u, v))
                if chave in vistos:
                    continue
                vistos.add(chave)
                a, b = inst.nos[u], inst.nos[v]
                ax.plot([a.x, b.x], [a.y, b.y], color="#b6bfd1", lw=0.45 if modo == "completo" else 0.9, zorder=1)
        ax.scatter([n.x for n in inst.nos[1:]], [n.y for n in inst.nos[1:]], s=14, color=AZUL, zorder=2)
        ax.scatter([inst.nos[0].x], [inst.nos[0].y], marker="s", s=40, color="black", zorder=3)
        ax.set_title("%s: %d arcos" % (titulo, inst.grafo.m), fontsize=8)
        ax.set_aspect("equal")
        ax.axis("off")
    salvar(fig, "fig_modos_grafo.pdf")
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for f in (gap_solomon, ablacao, escala, prioridade, modos_do_grafo):
        f()
        print("ok", f.__name__)
