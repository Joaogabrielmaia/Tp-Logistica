# resultados/ — saída dos experimentos

Cada CSV aqui foi gerado por `python main.py benchmark <nome>` (ou `todos`). As tabelas e figuras do relatório são feitas a partir desses arquivos pelos scripts em `scripts/`, então nenhum número do relatório foi digitado à mão. Com a mesma semente, as distâncias se repetem; só os tempos mudam de máquina para máquina.

| Arquivo | Experimento |
|---|---|
| `solomon.csv` | As 56 instâncias de Solomon (100 clientes, janelas de tempo) comparadas com a melhor solução conhecida. |
| `cvrp_x.csv` | 9 instâncias do conjunto X (101 a 303 clientes, só capacidade). |
| `kaggle_gh.csv` | Instâncias Gehring-Homberger do Kaggle, de 200 a 1000 clientes. |
| `kaggle_entregas.csv` | As entregas de e-commerce do Kaggle (100 a 1000), com e sem prioridade, medindo o atraso por nível de urgência. |
| `ablacao.csv` | Quanto cada etapa do solver contribui: só construção, mais busca local, mais ruína e recriação, mais polimento. |
| `escala.csv` | Tempo de cada fase de 25 a 400 clientes, para comparar com a complexidade esperada. |
| `grafo_viario.csv` | Grafo completo contra rede viária: número de arcos e quanto a distância aumenta. |
| `prioridade.csv` | Efeito do peso λ da prioridade no horário de atendimento dos clientes urgentes. |
| `exato.csv` | Heurística contra o solver exato em instâncias de até 9 clientes. |

Em todas as linhas a coluna `verificada` diz se a solução passou no verificador independente. Todas passaram.
