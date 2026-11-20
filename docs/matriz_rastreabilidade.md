# Matriz de rastreabilidade

Fonte: `TP.pdf` (enunciado do professor). Estados: APROVADO (evidência verificada), APROVADO COM RESSALVAS
(limitação documentada), PENDENTE (depende de entrega do grupo).

| # | Requisito do enunciado | Onde é atendido | Validação e evidência | Estado |
|---|---|---|---|---|
| 1 | Tema 10: rotas com restrições de tempo, distância, prioridade e capacidade | `avaliacao.py`, `construtivo.py`, `otimizador.py`, `modelo.py` | `testes/test_solver.py`, `testes/test_avaliacao.py`, verificador independente | APROVADO |
| 2 | Estrutura de grafo e algoritmos compatíveis | `grafo.py`, `caminhos.py`, `rede_viaria.py` | `testes/test_grafo.py`, `testes/test_caminhos.py` (Dijkstra contra Floyd-Warshall, Kruskal contra força bruta) | APROVADO |
| 3 | Proibido NetworkX e bibliotecas de grafos | somente biblioteca padrão; sem importações de terceiros em `logistica/` | `grep -R "networkx" .` sem resultados; `requirements-relatorio.txt` só para figuras do relatório | APROVADO |
| 4 | Demonstrar a correção da solução | `verificador.py`, `exato.py` | 65 BKS reproduzidas exatamente; 50 instâncias pequenas comparadas com o ótimo; `resultados/exato.csv` | APROVADO |
| 5 | Analisar a complexidade | relatório, seção 4 | expoentes medidos em `resultados/escala.csv` | APROVADO COM RESSALVAS (ver limitações) |
| 6 | Discutir limitações | relatório, seção 8 | texto do relatório | APROVADO |
| 7 | Linguagem Python | todo o código | `main.py` | APROVADO |
| 8 | Relatório em LaTeX com template SBC, 12 a 15 páginas | `relatorio/relatorio.tex`, `relatorio/relatorio.pdf` | contagem de páginas ao compilar | APROVADO |
| 9 | Relatório: contextualizar, modelagem, diagramas, resultados e telas | seções 1 a 7 do relatório | figuras de UML, resultados e capturas reais da interface | APROVADO |
| 10 | Responsabilidades de cada membro no relatório | seção 10 do relatório | tabela por integrante; branches individuais no repositório | APROVADO |
| 11 | Etapa 1: descrição, justificativa da modelagem, plano, UML | `docs/etapa1/etapa1.pdf` | 5 diagramas UML | APROVADO |
| 12 | Etapa 2: protótipo funcional com código versionado em Git | repositório | branch de cada integrante com seus commits e pull requests na `main` | PENDENTE: cada integrante commitar na sua branch e integrar por PR |
| 13 | Interface gráfica com os resultados | `logistica/web/` | telas no relatório; `testes/test_servidor.py` | APROVADO |
| 14 | Bases de dados para execução e testes | `dados/` (Solomon, CVRP-X e `dados/kaggle/`) | 65 instâncias de referência, 300 Gehring-Homberger e 1000 entregas, os dois últimos do Kaggle; leitores em `logistica/leitor.py`, testes em `testes/test_kaggle.py`, resultados em `resultados/kaggle_*.csv` | APROVADO |
| 15 | Entrega: .zip com código, .tex e PDF; cada membro entrega | `scripts/empacotar.sh` | conferir o conteúdo do zip | PENDENTE: entrega de cada membro no Canvas até 22/11, 23:59 |
| 16 | Vídeo de 12 a 18 min com todos os membros | não produzido | | PENDENTE (decisão do grupo: após fechar o trabalho) |
| 17 | Slides e apresentação presencial de 10 min | não produzido | | PENDENTE (idem) |
| 18 | Histórico Git com commits individuais avaliados | repositório | cada integrante deve commitar a sua parte com a própria conta | PENDENTE |

Observação do enunciado: só são avaliadas entregas com todos os itens; a falta de um deles zera a nota. Os itens 16 e 17
(vídeo e slides) são obrigatórios e precisam estar prontos antes da entrega.


Ver `docs/roteiro_demo.md` para o roteiro da demonstração e `docs/tutorial.md` para o tutorial de uso.
