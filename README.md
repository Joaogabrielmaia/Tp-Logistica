# Dados

Instâncias reais de referência (benchmarks) usadas nos testes e nos experimentos.
Os arquivos `.sol` trazem a melhor solução conhecida (BKS) e servem como referência independente.

| Pasta | Conteúdo | Origem |
|---|---|---|
| `solomon/` | 56 instâncias de roteamento com janelas de tempo (100 clientes) | Solomon (1987), Operations Research 35(2), 254-265 |
| `cvrp-x/` | 9 instâncias do conjunto X (101 a 303 clientes) | Uchoa et al. (2017), EJOR 257(3), 845-858 |
| `kaggle/gehring-homberger/` | 300 instâncias com janelas de tempo, de 200 a 1000 clientes (nomes em minúsculas, ex.: `c1_2_1.txt`) | Gehring e Homberger (1999); Kaggle, "VRPTW Benchmark Datasets" (Senju14), CC BY 4.0 |
| `kaggle/ecommerce/entregas.csv` | 1000 entregas urbanas com latitude, longitude, peso, janela de tempo e prioridade | Kaggle, "E-commerce Logistics Route Planning Dataset" (zara2099), CC0 |

Os arquivos foram obtidos do repositório PyVRP/Instances (licença MIT), que os reproduz do CVRPLIB.
As BKS de `solomon/` seguem a convenção DIMACS (distâncias truncadas na primeira casa decimal) e as de `cvrp-x/`
arredondam as distâncias para o inteiro mais próximo. O leitor do projeto aplica a mesma convenção.

A prioridade dos clientes não existe nesses benchmarks. Quando ativada, é atribuída de forma pseudoaleatória
com semente fixa (20% alta, 30% média, 50% baixa) e isso é declarado em todos os resultados que a utilizam.

## Dados do Kaggle

As instâncias Gehring-Homberger não trazem `.sol`; para elas o relatório mostra distância, veículos e a melhoria sobre a
construção inicial, sem comparação com BKS. O `entregas.csv` é lido por `ler_entregas_csv` com as seguintes escolhas, todas declaradas no relatório:
o depósito não existe no arquivo e é colocado no centroide das entregas; latitude e longitude viram quilômetros por projeção equirretangular;
a demanda é `order_weight_kg`; a capacidade padrão é 500 kg (a coluna `vehicle_capacity_kg` varia por linha); o início da janela é `time_of_day`
e o fim é o início mais `delivery_time_window_hrs`; a velocidade é 35 km/h (média da coluna `average_speed_kmph`), de modo que uma unidade de tempo equivale a 1 km;
a prioridade 1 é alta, 2 é média e 3 ou 4 é baixa (o arquivo não define o sentido da escala; assumimos que 1 é a mais urgente).
