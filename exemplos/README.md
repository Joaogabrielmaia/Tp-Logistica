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

Na interface, os mesmos arquivos podem ser enviados pelo botão "Enviar arquivo".
