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

## 5. Outras formas de usar

```
python main.py resolver dados/solomon/RC101.vrp --iteracoes 5000 --mostrar-rotas
python main.py resolver dados/kaggle/ecommerce/entregas_100.csv --peso-prioridade 0.01
python main.py benchmark solomon --rapido
python -m unittest discover -s testes -t .
```
