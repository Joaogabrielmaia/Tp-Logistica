# Roteamento e Carga de Veículos em Centros Logísticos

Trabalho Prático de Teoria dos Grafos (PUC Minas), Tema 10: planejamento de rotas logísticas com restrições de
**tempo, distância, prioridade e capacidade de carga** dos veículos. Implementação em Python 3, somente biblioteca
padrão, sem bibliotecas de grafos (NetworkX e similares não são usadas em nenhum ponto).

Tutorial de uso: `docs/tutorial.md`. Roteiro da demonstração: `docs/roteiro_demo.md`.

## Como executar

Requer Python 3.10 ou superior. Não há dependências para rodar o sistema.

```
python main.py
python main.py resolver dados/solomon/R101.vrp --iteracoes 5000 --mostrar-rotas
python main.py resolver dados/solomon/RC101.vrp --prioridades --peso-prioridade 1.0
python main.py resolver dados/cvrp-x/X-n101-k25.vrp --modo viario
python main.py resolver dados/kaggle/gehring-homberger/c1_2_1.txt --iteracoes 2000
python main.py resolver dados/kaggle/ecommerce/entregas.csv --iteracoes 500
python main.py benchmark todos
python -m unittest discover -s testes -t .
```

`python main.py` abre a interface web em `http://127.0.0.1:8000`. Ela permite escolher a instância (ou gerar/enviar uma),
o modo do grafo, as restrições e o número de iterações, e mostra mapa, cronograma, carga, convergência e experimentos.

## Modelagem

Grafo dirigido ponderado `G = (V, A, d, t)`, com o depósito e os clientes como vértices. Cada rota é um circuito que passa
pelo depósito e a solução é uma partição dos clientes em rotas viáveis.

| Modo | Construção | Custos |
|---|---|---|
| `completo` | arco entre todo par de pontos | distância euclidiana com a regra de arredondamento da base |
| `viario` | k vizinhos mais próximos + árvore geradora mínima (Kruskal, union-find) | caminhos mínimos por Dijkstra |

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
