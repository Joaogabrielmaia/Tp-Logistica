# Matriz de rastreabilidade

Fonte: `TP.pdf` (enunciado do professor). Estados: APROVADO (evidência verificada no repositório), APROVADO COM RESSALVAS (limitação documentada) e
NO CANVAS (item entregue pelo Canvas, fora do repositório).

| # | Requisito do enunciado | Onde é atendido | Validação e evidência | Estado |
|---|---|---|---|---|
| 1 | Tema 10: rotas com restrições de tempo, distância, prioridade e capacidade | `avaliacao.py`, `construtivo.py`, `otimizador.py`, `modelo.py` | `testes/test_solver.py`, `testes/test_avaliacao.py`, verificador independente | APROVADO |
| 2 | Estrutura de grafo e algoritmos compatíveis | `grafo.py`, `caminhos.py`, `rede_viaria.py`, `consulta.py` (BFS, DFS, Dijkstra, A*, Bellman-Ford e Floyd-Warshall entre dois vértices) | `testes/test_grafo.py`, `testes/test_caminhos.py`, `testes/test_consulta.py` (Dijkstra contra Floyd-Warshall, Kruskal contra força bruta, os seis algoritmos contra Floyd-Warshall) | APROVADO |
| 3 | Proibido NetworkX e bibliotecas de grafos (salvo para comparação de desempenho) | somente biblioteca padrão em `logistica/`; a NetworkX aparece só em `comparacao_networkx/`, isolada, a título de comparação | `testes/test_sem_biblioteca_de_grafos.py` falha se a ferramenta importar biblioteca de grafos e roda a ferramenta com a NetworkX bloqueada; `requirements-relatorio.txt` só para figuras do relatório | APROVADO |
| 4 | Demonstrar a correção da solução | `verificador.py`, `exato.py` | 65 BKS reproduzidas exatamente; 50 instâncias pequenas comparadas com o ótimo; `resultados/exato.csv` | APROVADO |
| 5 | Analisar a complexidade | relatório, seção 4 | expoentes medidos em `resultados/escala.csv` | APROVADO COM RESSALVAS (ver limitações) |
| 6 | Discutir limitações | relatório, seção 8 | texto do relatório | APROVADO |
| 7 | Linguagem Python | todo o código | `main.py` | APROVADO |
| 8 | Relatório em LaTeX com template SBC, 12 a 15 páginas | `relatorio/relatorio.tex`, `relatorio/relatorio.pdf` | contagem de páginas ao compilar | APROVADO |
| 9 | Relatório: contextualizar, modelagem, diagramas, resultados e telas | seções 1 a 7 do relatório | figuras de UML, resultados e capturas reais da interface | APROVADO |
| 10 | Responsabilidades de cada membro no relatório | seção 10 do relatório | tabela por integrante (Tabela de responsabilidades); branches `joao`, `pedro` e `thomas` | APROVADO |
| 11 | Etapa 1: descrição, justificativa da modelagem, plano, UML | `docs/etapa1/etapa1.pdf` | 5 diagramas UML | APROVADO |
| 12 | Etapa 2: protótipo funcional com código versionado em Git | repositório | branch de cada integrante com seus commits, integradas na `main` com merge commit | APROVADO |
| 13 | Interface gráfica com os resultados | `logistica/web/` (mapa, cronograma, carga, convergência, caminhos e experimentos; erros com motivo e o que fazer) | telas no relatório; `testes/test_servidor.py`, `testes/test_consulta.py` | APROVADO |
| 14 | Bases de dados para execução e testes | `dados/` (Solomon, CVRP-X e `dados/kaggle/`) | 65 instâncias de referência, 300 Gehring-Homberger e 1000 entregas, os dois últimos do Kaggle; leitores em `logistica/leitor.py`, testes em `testes/test_kaggle.py`, resultados em `resultados/kaggle_*.csv` | APROVADO |
| 15 | Entrega: .zip com código, .tex e PDF; cada membro entrega | `scripts/empacotar.sh` gera o zip com código, `.tex` e PDFs | um zip por integrante, enviado até 22/11, 23:59 | NO CANVAS |
| 16 | Vídeo de 12 a 18 min com todos os membros | vídeo com a demonstração das features de cada integrante | enviado junto com o zip | NO CANVAS |
| 17 | Slides e apresentação presencial de 10 min | slides da apresentação | usados na apresentação em sala e no vídeo | NO CANVAS |
| 18 | Histórico Git com commits individuais avaliados | repositório | cada integrante commitou a sua parte com a própria conta, na própria branch | APROVADO |

Observação do enunciado: só são avaliadas entregas com todos os itens; a falta de um deles zera a nota.


Ver `docs/tutorial.md` para o tutorial de uso.
