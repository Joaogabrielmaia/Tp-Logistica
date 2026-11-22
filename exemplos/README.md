# exemplos/ — casos para testar a ferramenta na hora

Arquivos pequenos para mostrar o comportamento em casos-limite. Os válidos rodam; os inválidos existem de propósito,
para mostrar que o erro é tratado e explicado (o que aconteceu, por quê e o que fazer), sem traceback.

| Arquivo | Para quê | Comando |
|---|---|---|
| `dois_vertices.vrp` | menor instância possível: depósito e 1 cliente (2 vértices, 1 aresta) | `python main.py resolver exemplos/dois_vertices.vrp` |
| `grafo_exemplo.txt` | grafo digitado para a consulta de caminhos | `python main.py caminho --grafo-arquivo exemplos/grafo_exemplo.txt A D` |
| `so_deposito.vrp` | inválido: só o depósito, sem clientes | `python main.py resolver exemplos/so_deposito.vrp` |
| `vazio.vrp` | inválido: arquivo vazio | `python main.py resolver exemplos/vazio.vrp` |
| `texto_qualquer.vrp` | inválido: texto sem as seções do formato VRPLIB | `python main.py resolver exemplos/texto_qualquer.vrp` |
| `colunas_erradas.csv` | inválido: CSV sem as colunas das entregas do Kaggle | `python main.py resolver exemplos/colunas_erradas.csv` |
| `nao_e_instancia.png` | inválido: formato que a ferramenta não lê | `python main.py resolver exemplos/nao_e_instancia.png` |

## Grafo grande

Para testar os algoritmos de caminho em escala, `gerar_grafo_grande.py` cria um grafo em grade com atalhos (por
padrão, 50 000 vértices e cerca de 125 000 arestas) e salva em `exemplos/grafo_grande.txt`:

```
python exemplos/gerar_grafo_grande.py 50000
python main.py caminho --grafo-arquivo exemplos/grafo_grande.txt 0 49999
```

Leva uns 2 segundos: BFS, DFS, Dijkstra, A* e Bellman-Ford rodam, e o Floyd-Warshall é recusado com a estimativa de
tempo (O(n³), uns 145 dias). O arquivo pela linha de comando aceita até 1 milhão de vértices; o campo de texto da
interface fica em 2 000, porque é para exemplos pequenos.

Na interface, os mesmos arquivos podem ser enviados pelo botão "Enviar arquivo".
