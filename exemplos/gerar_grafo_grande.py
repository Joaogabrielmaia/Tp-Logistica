# Gera um grafo grande para testar os algoritmos de caminho em escala:
#   python exemplos/gerar_grafo_grande.py 50000
#   python main.py caminho --grafo-arquivo exemplos/grafo_grande.txt 0 49999
# O grafo é uma grade (cada vértice liga ao vizinho da direita e ao de baixo) com pesos de 1 a 20 e alguns atalhos
# longos e mais caros, para o menor caminho não ser óbvio. Com a mesma semente sai sempre o mesmo grafo.
import os
import random
import sys

n = int(sys.argv[1]) if len(sys.argv) > 1 else 50000
largura = max(2, int(n ** 0.5))
rnd = random.Random(1)
linhas = []
for v in range(n):
    if (v + 1) % largura and v + 1 < n:
        linhas.append("%d %d %d" % (v, v + 1, rnd.randint(1, 20)))
    if v + largura < n:
        linhas.append("%d %d %d" % (v, v + largura, rnd.randint(1, 20)))
for _ in range(n // 2):
    linhas.append("%d %d %d" % (rnd.randrange(n), rnd.randrange(n), rnd.randint(20, 200)))
saida = os.path.join(os.path.dirname(os.path.abspath(__file__)), "grafo_grande.txt")
with open(saida, "w", encoding="utf-8") as f:
    f.write("\n".join(linhas) + "\n")
print("gerado %s: %d vértices, %d arestas" % (saida, n, len(linhas)))
