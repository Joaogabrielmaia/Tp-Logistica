import sys

# O README pede Python 3.10 ou mais novo; numa versão antiga o programa avisa com clareza
# em vez de falhar no meio com um erro difícil de entender.
if sys.version_info < (3, 10):
    sys.stderr.write("Erro: este projeto pede Python 3.10 ou mais novo (encontrado %d.%d).\n"
                     "O que fazer: instale uma versão atual em python.org e rode de novo com python3 main.py\n" % sys.version_info[:2])
    sys.exit(1)

from logistica.cli import principal

if __name__ == "__main__":
    sys.exit(principal(sys.argv[1:]))
