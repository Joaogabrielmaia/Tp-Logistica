# docs/ — documentação

| Item | O que é |
|---|---|
| `etapa1/` | Documento da Etapa 1 em LaTeX (template SBC) e o PDF: problema, modelagem em grafos, escolha dos algoritmos, arquitetura e plano. |
| `diagramas/` | Diagramas UML. Cada um tem o arquivo-fonte (Mermaid `.mmd` ou Graphviz `.dot`) e o PDF e PNG gerados dele, para dar para atualizar junto com o código. |
| `tutorial.md` | Passo a passo de como usar a ferramenta, pela interface e pela linha de comando. |
| `matriz_rastreabilidade.md` | Cada requisito do enunciado ligado ao arquivo de código, ao teste e à seção do relatório que o atendem. |

## Diagramas

| Diagrama | Mostra |
|---|---|
| `casos_de_uso` | O que o planejador logístico faz no sistema: carregar a instância, escolher o grafo, definir restrições, calcular, ver e conferir as rotas. |
| `classes_modelo` e `classes_execucao` | As classes do modelo (instância, nó, grafo) e as da execução (solução, rota, resultado, verificação). |
| `componentes` | Os módulos do sistema e como dependem uns dos outros. |
| `sequencia` | O caminho de uma solicitação: da tela ao servidor, ao solver, ao verificador e de volta. |
| `atividades` | O fluxo do solver, da leitura da instância até a verificação, incluindo o corte pelo tempo limite. |

Para regerar: `dot -Tpdf casos_de_uso.dot -o casos_de_uso.pdf` para o Graphviz e `mmdc -i arquivo.mmd -o arquivo.pdf` para os Mermaid.
