# Tutorial rápido

## 1. Abrir a ferramenta

```
python main.py
```

O navegador abre sozinho (se não abrir, entre em http://127.0.0.1:8000). Só precisa de Python 3; não há nada para instalar.

## 2. De onde vêm os dados

A ferramenta lê arquivos da pasta `dados/`. Todos aparecem na lista "Instância":

| Para demonstrar | Arquivo | Tempo |
|---|---|---|
| Benchmark clássico, com melhor solução conhecida | `solomon/RC101.vrp` | cerca de 2 s |
| Dados reais do Kaggle, entregas urbanas | `kaggle/ecommerce/entregas_100.csv` ou `entregas_200.csv` | 1 a 4 s |
| Benchmark do Kaggle, 200 clientes | `kaggle/gehring-homberger/c1_2_1.txt` (iguala a melhor solução publicada) | cerca de 2 s |
| Instância criada na hora | quadro "Gerar instância sintética" | segundos |

Os arquivos `entregas.csv` (1000 entregas) e as instâncias Gehring-Homberger de 600 a 1000 clientes são grandes; use o tempo limite de 10 s.

## 3. Usar

1. Escolha a instância.
2. Modo do grafo: **completo** (todas as ligações) ou **rede viária** (ruas esparsas, caminhos mínimos por Dijkstra).
3. Restrições: capacidade, frota, distância máxima, custo fixo por veículo. Para antecipar clientes urgentes, dê um **peso de prioridade** maior que zero (por exemplo, 0,01 nas entregas do Kaggle). As entregas do Kaggle já trazem prioridade no arquivo; nas demais instâncias, marque "prioridades" para sorteá-las (sintéticas).
4. Otimização: iterações (1.000 a 5.000 bastam na demonstração) e **tempo limite**.
5. Clique em **Calcular rotas**.

## 4. Ler o resultado

- **Mapa:** rotas sobre o grafo; passe o mouse para ver o cliente.
- **Cronograma:** janelas de tempo, esperas e atendimentos por veículo.
- **Carga:** ocupação do veículo e a ordem de carregamento (o último cliente entregue entra primeiro).
- **Convergência:** custo ao longo das etapas (economias, inserção, busca local, ruína e recriação).
- **Cartão "Verificação independente":** "Aprovada" quer dizer que um verificador separado recalculou tudo e todas as restrições conferem.
- **Experimentos:** tabelas já calculadas (não são cálculo ao vivo).

## 5. Caminho entre dois vértices

Na aba **Caminhos**, informe a origem e o destino (nas instâncias, 0 é o depósito e os clientes vão de 1 a n) e clique em
**Calcular caminho**. A tabela mostra BFS, DFS, Dijkstra, A*, Bellman-Ford e Floyd-Warshall lado a lado, com custo,
número de arcos, tempo e o caminho; clique numa linha para destacá-la no desenho. Ela usa o grafo da instância no modo
escolhido em **Grafo** (com a rede viária, também dá para pôr ruas de mão única).

Para testar um grafo qualquer, marque **Usar grafo próprio** e escreva uma aresta por linha, `origem destino peso`.
O menor caso é `A B 1`. Marque **Dirigido** para que cada linha valha só num sentido; com peso negativo, Dijkstra e A*
não rodam e o Bellman-Ford mostra o resultado (ou o ciclo negativo, se houver).

## 6. Quando algo dá errado

Todo erro aparece em três partes: o que aconteceu, **Por quê** e **O que fazer**. Exemplos: arquivo em formato
desconhecido, capacidade menor que a demanda de um cliente, frota 0, cliente que não cabe na janela de tempo nem
sozinho, vértice que não existe na consulta de caminhos.

## 7. Outras formas de usar

```
python main.py resolver dados/solomon/RC101.vrp --iteracoes 5000 --mostrar-rotas
python main.py resolver dados/kaggle/ecommerce/entregas_100.csv --peso-prioridade 0.01
python main.py caminho dados/solomon/R101.vrp 0 15 --modo viario
python main.py caminho --arestas "A B 4; B C -2; A C 3" --dirigido A C
python main.py grafo dados/solomon/R101.vrp --modo viario --mao-unica 0.3 --mostrar-agm
python main.py benchmark solomon --rapido --saida resultados_teste
python -m unittest discover -s testes -t .
```

O `--rapido` roda só uma parte das instâncias; com `--saida resultados_teste` ele grava numa pasta à parte e não mexe nos CSV oficiais de `resultados/`, que são os usados no relatório.
