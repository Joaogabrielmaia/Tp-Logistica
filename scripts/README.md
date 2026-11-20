# scripts/ — apoio ao relatório e à entrega

Esses scripts não fazem parte da ferramenta; servem para gerar o material do relatório a partir dos resultados. Os de figuras e prints precisam do que está em `requirements-relatorio.txt` (matplotlib, numpy e playwright).

| Script | O que faz |
|---|---|
| `tabelas.py` | Lê os CSV de `resultados/` e gera `relatorio/tabelas_geradas.tex`, com as tabelas e os números citados no texto. |
| `figuras.py` | Gera os gráficos do relatório em `relatorio/figuras/`. |
| `capturar_telas.py` | Abre a interface num navegador sem janela, roda um exemplo com as entregas do Kaggle e salva os prints das telas. |
| `empacotar.sh` | Monta o `.zip` de entrega com código, dados, resultados, documentos e relatório. |

Ordem para refazer tudo: `python main.py benchmark todos`, depois `python scripts/tabelas.py`, `python scripts/figuras.py` e `python scripts/capturar_telas.py`, e por fim compilar o relatório.
