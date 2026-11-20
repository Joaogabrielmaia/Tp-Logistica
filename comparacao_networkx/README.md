# comparacao_networkx/ — somente a título de comparação

> **A ferramenta não usa a NetworkX.** Nada da pasta `logistica/` importa a NetworkX ou qualquer outra biblioteca de
> grafos: o grafo, Dijkstra, A*, Bellman-Ford, Floyd-Warshall, Kruskal, union-find e BFS foram escritos por nós.
> Esta pasta existe só para comparar desempenho e conferir as respostas, como o enunciado permite ("salvo para
> comparação de performance"). Ela fica fora da ferramenta, não entra no `main.py` e não é necessária para usá-la.

O teste `testes/test_sem_biblioteca_de_grafos.py` garante isso de duas formas: lê o código de `logistica/`,
`main.py` e `testes/` e falha se encontrar import de NetworkX, igraph, graph-tool, OSMnx, OR-Tools ou outra
biblioteca de grafos; e roda a ferramenta num processo em que a NetworkX está bloqueada, mostrando que tudo funciona
sem ela.

## Como foi feita a comparação

`comparar.py` lê as instâncias com o nosso leitor, monta a rede viária com o nosso código e copia exatamente os
mesmos arcos para um `DiGraph` da NetworkX. Depois roda o mesmo algoritmo dos dois lados, confere se as respostas
são iguais e mede o tempo (o menor de algumas repetições). Os números abaixo são de `resultados.csv`, gerado com
NetworkX 3.7 e Python 3.13; em outra máquina os tempos mudam, as respostas não.

```
pip install -r comparacao_networkx/requirements.txt
python comparacao_networkx/comparar.py
```

## Resultados

As respostas foram iguais nos 34 casos: mesmas distâncias (diferença máxima 0), mesmo peso da árvore geradora mínima,
mesma resposta sobre conexidade e, nos 200 grafos aleatórios com peso negativo, o mesmo diagnóstico de ciclo
negativo.

| Instância | Algoritmo | Respostas iguais | Nosso (s) | NetworkX (s) |
| --- | --- | --- | --- | --- |
| R101 (rede viária) | Dijkstra, uma origem | sim | 0,0001 | 0,0001 |
| R101 (rede viária) | Dijkstra, todas as origens (matriz) | sim | 0,0063 | 0,0139 |
| R101 (rede viária) | A* (0 até 100) | sim | 0,0001 | 0,0001 |
| R101 (rede viária) | Bellman-Ford, uma origem | sim | 0,0002 | 0,0004 |
| R101 (rede viária) | Floyd-Warshall, todos os pares | sim | 0,0227 | 0,0600 |
| R101 (rede viária) | Kruskal (peso da árvore geradora mínima) | sim | 0,0001 | 0,0005 |
| R101 (rede viária) | BFS (fortemente conexo?) | sim | 0,0002 | 0,0001 |
| C101 (rede viária) | Dijkstra, uma origem | sim | 0,0001 | 0,0001 |
| C101 (rede viária) | Dijkstra, todas as origens (matriz) | sim | 0,0063 | 0,0134 |
| C101 (rede viária) | A* (0 até 100) | sim | 0,0002 | 0,0001 |
| C101 (rede viária) | Bellman-Ford, uma origem | sim | 0,0004 | 0,0003 |
| C101 (rede viária) | Floyd-Warshall, todos os pares | sim | 0,0087 | 0,0562 |
| C101 (rede viária) | Kruskal (peso da árvore geradora mínima) | sim | 0,0001 | 0,0004 |
| C101 (rede viária) | BFS (fortemente conexo?) | sim | 0,0002 | 0,0001 |
| c1_2_1 (rede viária) | Dijkstra, uma origem | sim | 0,0001 | 0,0002 |
| c1_2_1 (rede viária) | Dijkstra, todas as origens (matriz) | sim | 0,0275 | 0,0639 |
| c1_2_1 (rede viária) | A* (0 até 200) | sim | 0,0003 | 0,0002 |
| c1_2_1 (rede viária) | Bellman-Ford, uma origem | sim | 0,0004 | 0,0004 |
| c1_2_1 (rede viária) | Floyd-Warshall, todos os pares | sim | 0,0571 | 0,4436 |
| c1_2_1 (rede viária) | Kruskal (peso da árvore geradora mínima) | sim | 0,0003 | 0,0011 |
| c1_2_1 (rede viária) | BFS (fortemente conexo?) | sim | 0,0004 | 0,0002 |
| c1_4_1 (rede viária) | Dijkstra, uma origem | sim | 0,0003 | 0,0006 |
| c1_4_1 (rede viária) | Dijkstra, todas as origens (matriz) | sim | 0,1165 | 0,2724 |
| c1_4_1 (rede viária) | A* (0 até 400) | sim | 0,0006 | 0,0003 |
| c1_4_1 (rede viária) | Bellman-Ford, uma origem | sim | 0,0036 | 0,0012 |
| c1_4_1 (rede viária) | Kruskal (peso da árvore geradora mínima) | sim | 0,0006 | 0,0021 |
| c1_4_1 (rede viária) | BFS (fortemente conexo?) | sim | 0,0008 | 0,0003 |
| entregas (rede viária) | Dijkstra, uma origem | sim | 0,0009 | 0,0023 |
| entregas (rede viária) | Dijkstra, todas as origens (matriz) | sim | 0,8855 | 2,0462 |
| entregas (rede viária) | A* (0 até 1000) | sim | 0,0019 | 0,0004 |
| entregas (rede viária) | Bellman-Ford, uma origem | sim | 0,0060 | 0,0045 |
| entregas (rede viária) | Kruskal (peso da árvore geradora mínima) | sim | 0,0022 | 0,0063 |
| entregas (rede viária) | BFS (fortemente conexo?) | sim | 0,0024 | 0,0010 |
| 200 grafos aleatórios com peso negativo | Bellman-Ford (distância ou ciclo negativo) | sim | 0,0023 | 0,0035 |

## O que os tempos mostram

- **Matriz de distâncias (Dijkstra de todas as origens)**, que é o que a ferramenta calcula na rede viária: o nosso
  levou 0,89 s contra 2,05 s com 1001 vértices, cerca de 2,3 vezes mais rápido.
- **Floyd-Warshall:** de 2,6 a 7,8 vezes mais rápido nas instâncias de 101 e 201 vértices.
- **Kruskal:** de 2,9 a 5 vezes mais rápido.
- **Onde a NetworkX ganha:** no A* de um único par, porque o nosso monta a estimativa para todos os vértices antes
  de começar, e na checagem de conexidade forte, que a NetworkX faz numa passada só, enquanto nós rodamos a BFS no
  grafo e no transposto.
- Nos casos de uma origem só (Dijkstra, Bellman-Ford), os tempos ficam na mesma ordem: frações de milissegundo.

A conclusão é que a implementação própria dá as mesmas respostas da biblioteca de referência e tem desempenho
comparável, melhor justamente nas operações que a ferramenta mais usa.
