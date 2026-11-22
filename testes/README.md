# testes/ — testes automatizados

São 88 testes com `unittest`, da biblioteca padrão. Para rodar todos, a partir da raiz do projeto:

```
python -m unittest discover -s testes -t .
```

A ideia foi não testar só "se roda", mas comparar cada peça com uma forma independente de chegar no mesmo resultado.

| Arquivo | O que conferimos |
|---|---|
| `test_grafo.py` | Kruskal contra enumeração de todas as árvores em grafos pequenos; union-find; BFS e alcançabilidade, inclusive com grafo desconexo e ruas de mão única. |
| `test_caminhos.py` | Dijkstra contra Floyd-Warshall em grafos aleatórios, com pesos iguais, pesos zero e vértices sem caminho. |
| `test_avaliacao.py` | A inserção em O(1) pelas folgas de tempo dá o mesmo resultado que recalcular a rota inteira. |
| `test_busca_local.py` | Depois da busca local, uma busca "ingênua", sem os filtros, não encontra nenhuma melhoria. Isso mostra que os filtros de velocidade não fazem perder movimento bom. |
| `test_solver.py` | Toda solução sai viável; o verificador pega cada tipo de erro (cliente repetido ou faltando, capacidade, janela, distância, frota, custo errado); prioridade e tempo limite funcionam. |
| `test_exato.py` | A heurística chega no ótimo do solver exato nas instâncias pequenas. |
| `test_leitor.py` | Reprodução exata do custo das 65 melhores soluções conhecidas (BKS) de Solomon e do conjunto X; arquivos com erro (seção faltando, dimensão errada, demanda maior que a capacidade); rede viária conexa e nunca mais curta que a linha reta. |
| `test_kaggle.py` | Leitura das instâncias Gehring-Homberger e do CSV de entregas; a prioridade do CSV não é sobrescrita; o tempo limite é respeitado em instância grande. |
| `test_consulta.py` | Os seis algoritmos de caminho contra Floyd-Warshall em grafos aleatórios; BFS com o menor número de arcos; A* ótimo mesmo com o arredondamento das bases; peso negativo, ciclo negativo, 2 vértices e 1 aresta, sem caminho; grafo digitado com erro; arquivo de arestas grande pela linha de comando; mão única sem perder a conexidade; pular clientes impossíveis (os de fora não aparecem e o verificador aprova o resto); erros da linha de comando sempre com "Por quê" e sem traceback; envio de .txt e .csv. |
| `test_sem_biblioteca_de_grafos.py` | Garante a regra do enunciado: lê o código da ferramenta e falha se houver import de NetworkX ou outra biblioteca de grafos, e roda a ferramenta com essas bibliotecas bloqueadas. |
| `test_servidor.py` | A API lista as instâncias, devolve solução já verificada, manda o caminho físico no modo viário, aceita envio de arquivo e recusa entradas inválidas. |

Um dos testes existe por causa de um defeito real que encontramos: o gerador sintético criava clientes impossíveis de atender no modo viário. Corrigimos e deixamos o teste para o erro não voltar.
