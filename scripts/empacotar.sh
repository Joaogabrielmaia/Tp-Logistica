#!/bin/sh
set -e
cd "$(dirname "$0")/.."
saida="${1:-entrega.zip}"
rm -f "$saida"
zip -r "$saida" main.py README.md apresentacao entrega requirements-relatorio.txt logistica testes dados exemplos comparacao_networkx resultados scripts docs relatorio \
  -x "*/__pycache__/*" "*.pyc" "*.aux" "*.log" "*.out" "*.toc" "*.bbl" "*.blg"
echo "gerado $saida"
