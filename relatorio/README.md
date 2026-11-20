# relatorio/ — relatório final

Relatório em LaTeX no template da SBC, com o PDF já compilado (`relatorio.pdf`).

| Arquivo | O que é |
|---|---|
| `relatorio.tex` | Texto do relatório. |
| `tabelas_geradas.tex` | Tabelas e números gerados de `resultados/` por `scripts/tabelas.py`. Não editar à mão. |
| `referencias.bib` | Referências bibliográficas. |
| `figuras/` | Gráficos (`fig_*.pdf`) e prints da interface (`tela_*.png`). |
| `sbc-template.sty`, `sbc.bst`, `caption2.sty` | Arquivos do template da SBC. |

Para compilar: `latexmk -pdf relatorio.tex` dentro desta pasta. No Overleaf, basta subir a pasta inteira junto com `docs/diagramas/`, porque as figuras dos diagramas são lidas de lá.

As seções seguem o que o enunciado pede: definição do problema e dos dados, modelagem em grafos, algoritmos e complexidade, implementação e interface, validação, resultados, limitações e conclusões.
