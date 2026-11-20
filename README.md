# Roteamento e Carga de Veículos em Centros Logísticos

Trabalho Prático de Teoria dos Grafos (PUC Minas), Tema 10: planejamento de rotas logísticas com restrições de
**tempo, distância, prioridade e capacidade de carga** dos veículos. Implementação em Python 3, somente biblioteca
padrão, sem bibliotecas de grafos (NetworkX e similares não são usadas em nenhum ponto).

Tutorial de uso: `docs/tutorial.md`.

## Por onde começar

Cada pasta tem um README explicando o que tem dentro:

- `logistica/README.md`: o código, arquivo por arquivo, na ordem do fluxo (dado, grafo, solver, verificação, tela);
- `testes/README.md`: o que cada teste confere e como rodar;
- `dados/README.md`: as bases usadas, de onde vieram e as suposições sobre o CSV do Kaggle;
- `resultados/README.md`: o que mede cada experimento;
- `docs/README.md`: Etapa 1, diagramas, tutorial e matriz de rastreabilidade;
- `relatorio/README.md` e `scripts/README.md`: como o relatório e suas tabelas são gerados.

## Como executar

Requer Python 3.10 ou superior. Não há dependências para rodar o sistema.

```
python main.py
python main.py resolver dados/solomon/R101.vrp --iteracoes 5000 --mostrar-rotas
python main.py resolver dados/solomon/RC101.vrp --prioridades --peso-prioridade 1.0
python main.py resolver dados/cvrp-x/X-n101-k25.vrp --modo viario
python main.py resolver dados/kaggle/gehring-homberger/c1_2_1.txt --iteracoes 2000
python main.py resolver dados/kaggle/ecommerce/entregas.csv --iteracoes 500
python main.py resolver dados/solomon/R101.vrp --modo viario --mao-unica 0.3
python main.py caminho dados/solomon/R101.vrp 0 15 --modo viario
python main.py caminho --arestas "A B 4; A C 1; C B 1; B D 1" A D
python main.py grafo dados/solomon/R101.vrp --modo viario --mostrar-agm
python main.py benchmark todos
python -m unittest discover -s testes -t .
```

`python main.py` abre a interface web em `http://127.0.0.1:8000`. Ela permite escolher a instância (ou gerar/enviar uma),
o modo do grafo, as restrições e o número de iterações, e mostra mapa, cronograma, carga, convergência e experimentos.
A aba Caminhos compara os algoritmos de caminho entre dois vértices, no grafo da instância ou num grafo digitado.

Erros (arquivo inválido, parâmetro fora do intervalo, cliente impossível de atender, vértice inexistente) aparecem
sempre em três partes, na tela e no terminal: o que aconteceu, por quê e o que fazer. Nenhum erro conhecido mostra traceback.

## Modelagem

Grafo dirigido ponderado `G = (V, A, d, t)`, com o depósito e os clientes como vértices. Cada rota é um circuito que passa
pelo depósito e a solução é uma partição dos clientes em rotas viáveis.

| Modo | Construção | Custos |
|---|---|---|
| `completo` | arco entre todo par de pontos | distância euclidiana com a regra de arredondamento da base |
| `viario` | k vizinhos mais próximos + árvore geradora mínima (Kruskal, union-find); `--mao-unica` torna parte das ruas de mão única | caminhos mínimos por Dijkstra |

Restrições: capacidade, janelas de tempo com espera, distância máxima por rota, frota máxima, custo fixo por veículo e
prioridade (peso `λ` sobre o instante de início do atendimento, com pesos 3, 2 e 1 para prioridade alta, média e baixa).

## Algoritmos

| Etapa | Algoritmo | Arquivo |
|---|---|---|
| Caminhos mínimos | Dijkstra com heap binário | `logistica/caminhos.py` |
| Conexidade | Kruskal, union-find, BFS no grafo e no transposto | `logistica/grafo.py` |
| Solução inicial | Economias de Clarke-Wright e inserção de Solomon | `logistica/construtivo.py` |
| Avaliação | Folgas de tempo (inserção viável em O(1)) | `logistica/avaliacao.py` |
| Melhoria | Busca local e ruína e recriação com recozimento simulado | `logistica/busca_local.py`, `logistica/otimizador.py` |
| Validação | Verificador independente (Bellman-Ford) e solver exato | `logistica/verificador.py`, `logistica/exato.py` |
| Caminho entre dois vértices | BFS, DFS, Dijkstra, A*, Bellman-Ford e Floyd-Warshall, lado a lado | `logistica/caminhos.py`, `logistica/consulta.py` |
| Explicação de erros | o que houve, por quê e o que fazer | `logistica/erros.py` |

## Estrutura

```
logistica/      código do sistema (modelo, grafo, algoritmos, serviço, servidor, web)
testes/         testes automatizados (unittest)
dados/          Solomon e CVRP-X com BKS; dados/kaggle/ com Gehring-Homberger e entregas de e-commerce
resultados/     CSV dos experimentos (gerados por python main.py benchmark)
docs/           documento da Etapa 1, diagramas UML e matriz de rastreabilidade
relatorio/      relatório final em LaTeX (template SBC)
scripts/        geração de figuras e capturas de tela do relatório (exigem requirements-relatorio.txt)
```

## Dados

Dois conjuntos do Kaggle (Gehring-Homberger, CC BY 4.0, e entregas de e-commerce, CC0) completam os dados. Benchmarks de Solomon (1987) e Uchoa et al. (2017), obtidos do repositório PyVRP/Instances (licença MIT). Detalhes e
convenções de arredondamento em `dados/README.md`. A prioridade dos clientes é sintética (semente fixa) e a rede viária é
construída a partir das coordenadas; ambas são declaradas como tais nos resultados.
