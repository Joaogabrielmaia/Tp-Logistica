# logistica/ — código do sistema

Aqui está todo o código da ferramenta. É Python puro, só com a biblioteca padrão. Nenhuma biblioteca de grafos foi usada: grafo, Dijkstra, Kruskal, union-find e BFS foram implementados por nós.

Para entender o fluxo, sugiro ler os arquivos nesta ordem: o dado entra pelo leitor, vira um grafo, o solver monta e melhora as rotas, o verificador confere e o servidor mostra tudo na tela.

## 1. Dados e grafo

| Arquivo | O que faz |
|---|---|
| `modelo.py` | Classes `No` e `Instancia`: depósito, clientes, demanda, janela de tempo, serviço e prioridade. Também guarda as matrizes de distância e tempo. |
| `leitor.py` | Lê os formatos que usamos: VRPLIB (`.vrp`), texto de Solomon (`.txt`, usado nas instâncias Gehring-Homberger do Kaggle) e o CSV de entregas do Kaggle. Também gera instâncias sintéticas com semente fixa. |
| `grafo.py` | Grafo dirigido ponderado com lista de adjacência. Tem union-find, Kruskal e BFS no grafo e no transposto, que usamos para achar clientes que não podem ser alcançados ou que não conseguem voltar ao depósito. |
| `rede_viaria.py` | Monta o modo "rede viária": cada ponto liga aos 5 vizinhos mais próximos, e a árvore geradora mínima (Kruskal) garante que o grafo fique conexo. Com `--mao-unica` (ou o campo na tela), parte das ruas vira mão única; as arestas da árvore são sempre de mão dupla, então todo ponto continua alcançando todos. |
| `caminhos.py` | Dijkstra com heap binário. Gera a matriz de menor caminho que o solver usa no modo viário e reconstrói o trajeto pelos predecessores, que é o que aparece desenhado no mapa. Também tem BFS, DFS, A*, Bellman-Ford (com detecção de ciclo negativo) e Floyd-Warshall, usados na consulta de caminho entre dois vértices. |
| `consulta.py` | Roda esses seis algoritmos entre dois vértices e compara custo, número de arcos e tempo; lê um grafo digitado como lista de arestas (`A B 5`) e resume a estrutura (graus, conexidade, árvore geradora mínima). |

## 2. Algoritmos de roteamento

| Arquivo | O que faz |
|---|---|
| `avaliacao.py` | Coração da eficiência. Cada rota guarda as folgas de tempo (chegada mais cedo `E` e saída mais tarde `L`), e com isso testar se um cliente cabe numa posição custa O(1) em vez de refazer a rota inteira. |
| `construtivo.py` | Solução inicial por dois métodos: economias de Clarke-Wright e inserção de Solomon (I1). O solver roda os dois e fica com o melhor. |
| `busca_local.py` | Melhora a solução com 4 movimentos: realocar, trocar, inverter trecho (2-opt) e trocar finais de rota. Filtros de custo constante descartam antes os candidatos que não têm chance, o que deixou a busca de 2 a 8 vezes mais rápida sem mudar as rotas. |
| `otimizador.py` | Ruína e recriação: tira um pedaço de clientes próximos e reinsere, aceitando às vezes uma solução pior (recozimento simulado) para não travar num ótimo local. |
| `solver.py` | Junta tudo: construção, busca local, ruína e recriação e polimento final, respeitando o tempo limite escolhido. |
| `exato.py` | Solver exato para instâncias de até 9 clientes (nos experimentos usamos 8). Serve só para conferir se a heurística chega no ótimo nos casos pequenos. |
| `verificador.py` | Conferência independente da solução. Recalcula o custo de cada trecho direto do grafo, sem usar as matrizes do solver; no modo viário usa Bellman-Ford, que é um algoritmo diferente do Dijkstra usado na solução. Se uma restrição for violada, ele aponta qual. |

## 3. Interface e execução

| Arquivo | O que faz |
|---|---|
| `servico.py` | Recebe os parâmetros da tela, valida cada um (limites, arquivo, caminho dentro da pasta de dados) e chama o solver. |
| `servidor.py` | Servidor HTTP da biblioteca padrão, com uma API JSON e os arquivos da pasta `web/`. |
| `web/` | A interface: `index.html` (estrutura), `estilo.css` (visual) e `app.js` (mapa em canvas, cronograma, carga, convergência, caminhos e experimentos). |
| `cli.py` | Linha de comando: abrir a interface, resolver uma instância, calcular caminhos (`caminho`), resumir o grafo (`grafo`) ou rodar os experimentos. Valida cada parâmetro antes de rodar. |
| `erros.py` | Explicação dos erros: para cada erro conhecido, o que aconteceu, por quê e o que fazer. Também diz por que um cliente não pode ser atendido (capacidade, janela de tempo, distância ou falta de caminho). |
| `benchmark.py` | Os experimentos do relatório. Cada um grava um CSV em `resultados/`. |

## Restrições que o sistema respeita

Capacidade do veículo, janela de tempo (com espera se chegar cedo), distância máxima por rota, tamanho da frota, custo fixo por veículo e prioridade do cliente. A prioridade entra na função objetivo com um peso λ que o usuário escolhe: quanto maior, mais cedo os clientes urgentes são atendidos, em troca de um pouco mais de distância.
