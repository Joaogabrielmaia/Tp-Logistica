import math


# Erro com explicação para o usuário: o que aconteceu, por que acontece e o que fazer. A linha de comando e a
# interface mostram os três textos, em vez de um traceback.
class ErroExplicado(ValueError):
    def __init__(self, mensagem, motivo="", dica=""):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.motivo = motivo
        self.dica = dica


# Explicações dos erros que vêm da leitura das bases (leitor.py), indexadas pelo começo da mensagem.
EXPLICACOES = [
    ("arquivo não encontrado",
     "o caminho informado não existe a partir da pasta onde o comando foi rodado.",
     "confira o nome e rode da raiz do projeto, por exemplo: python main.py resolver dados/solomon/R101.vrp"),
    ("instância grande demais",
     "o roteamento guarda a distância e o tempo entre todo par de pontos (n² valores); acima de 2000 clientes isso passa de 1,5 GB de memória em Python e o computador trava antes de calcular.",
     "use uma instância de até 2000 clientes; para medir caminhos mínimos em grafos maiores, use python main.py caminho --grafo-arquivo (até 1 milhão de vértices)."),
    ("arquivo vazio",
     "o arquivo não tem conteúdo, então não há depósito nem clientes para montar o grafo.",
     "use um arquivo .vrp (VRPLIB), .txt (Solomon) ou .csv (entregas do Kaggle) com dados."),
    ("formato não reconhecido",
     "a ferramenta só lê três formatos: VRPLIB (.vrp), texto de Solomon (.txt) e o CSV de entregas do Kaggle (.csv).",
     "converta a base para um desses formatos; os exemplos estão em dados/."),
    ("seção ausente",
     "o arquivo foi lido como VRPLIB, mas falta uma seção obrigatória (coordenadas, demandas ou depósito).",
     "confira se o arquivo é mesmo VRPLIB; um .txt no formato de Solomon precisa da extensão .txt."),
    ("capacidade ausente",
     "sem a capacidade do veículo não dá para checar a restrição de carga.",
     "inclua a linha CAPACITY no cabeçalho do arquivo."),
    ("dimension inconsistente",
     "o cabeçalho diz um número de vértices e as seções trazem outro, então o arquivo está incompleto ou corrompido.",
     "confira DIMENSION e o número de linhas em NODE_COORD_SECTION e DEMAND_SECTION."),
    ("há cliente com demanda maior que a capacidade",
     "um cliente pede mais carga do que cabe em um veículo vazio; nenhuma rota consegue atendê-lo.",
     "aumente a capacidade ou corrija a demanda desse cliente."),
    ("há entrega com peso maior que a capacidade",
     "uma entrega pesa mais do que cabe em um veículo vazio; nenhuma rota consegue levá-la.",
     "aumente a capacidade (na interface, campo Capacidade) ou retire essa entrega do arquivo."),
    ("o depósito deve ter demanda zero",
     "o depósito é o ponto de partida dos veículos; ele não recebe carga, então a demanda dele precisa ser 0.",
     "corrija a demanda do vértice do depósito (o primeiro do arquivo) para 0."),
    ("frota e capacidade inválidas",
     "o número de veículos e a capacidade precisam ser números positivos.",
     "confira a linha abaixo de VEHICLE / NUMBER CAPACITY no arquivo."),
    ("valor não numérico",
     "alguma coluna numérica do CSV (latitude, longitude, peso, janela ou prioridade) tem texto no lugar de número.",
     "abra o CSV e procure células vazias ou com texto nessas colunas."),
    ("arquivo sem entregas",
     "o CSV tem o cabeçalho, mas nenhuma linha de entrega.",
     "use um arquivo com pelo menos uma entrega."),
    ("conteúdo inválido",
     "uma linha do arquivo não tem o formato esperado (por exemplo, texto onde deveria haver um número).",
     "confira a linha indicada; os arquivos em dados/ servem de modelo."),
    ("a instância precisa de um depósito e ao menos um cliente",
     "um roteamento precisa de um vértice de partida (depósito) e de pelo menos um cliente para visitar.",
     "o menor caso possível é o depósito e um cliente, ou seja, um grafo com 2 vértices."),
    ("colunas ausentes",
     "o CSV não tem as colunas do conjunto de entregas do Kaggle que o leitor usa.",
     "as colunas esperadas estão em dados/README.md; o arquivo de exemplo é dados/kaggle/ecommerce/entregas.csv."),
    ("cabeçalho vehicle ausente",
     "o arquivo .txt não segue o formato de Solomon (VEHICLE, NUMBER CAPACITY e a tabela CUSTOMER).",
     "use um arquivo do conjunto Gehring-Homberger, como dados/kaggle/gehring-homberger/c1_2_1.txt."),
]


def explicar(erro):
    if isinstance(erro, ErroExplicado) and (erro.motivo or erro.dica):
        return erro.mensagem, erro.motivo, erro.dica
    texto = str(erro)
    for prefixo, motivo, dica in EXPLICACOES:
        if texto.lower().startswith(prefixo):
            return texto, motivo, dica
    return texto, "", ""


# Diz por que cada cliente não pode ser atendido nem sozinho (depósito -> cliente -> depósito). É o mesmo teste que o
# construtivo faz antes de montar rotas, só que separando a causa.
def motivos_inatendivel(inst, par, u):
    motivos = []
    if inst.D[0][u] == math.inf or inst.D[u][0] == math.inf:
        motivos.append("não há caminho de ida e volta entre o depósito e o cliente na rede viária")
        return motivos
    if inst.q[u] > par.capacidade + 1e-9:
        motivos.append("demanda %g maior que a capacidade %g" % (inst.q[u], par.capacidade))
    chegada = inst.e[0] + inst.s[0] + inst.T[0][u]
    if chegada > inst.l[u] + 1e-9:
        motivos.append("saindo do depósito na abertura, chega em t=%.1f, depois do fim da janela (%.1f)" % (chegada, inst.l[u]))
    else:
        retorno = max(chegada, inst.e[u]) + inst.s[u] + inst.T[u][0]
        if retorno > inst.l[0] + 1e-9:
            motivos.append("não dá tempo de voltar: retorno em t=%.1f, depois do fechamento do depósito (%.1f)" % (retorno, inst.l[0]))
    if par.distancia_maxima is not None:
        ida_volta = inst.D[0][u] + inst.D[u][0]
        if ida_volta > par.distancia_maxima + 1e-9:
            motivos.append("ida e volta somam %.1f, acima da distância máxima %g" % (ida_volta, par.distancia_maxima))
    return motivos or ["combinação das restrições"]


def explicar_inatendiveis(inst, par, clientes, limite=5, como_pular=""):
    linhas = ["cliente %d: %s" % (u, "; ".join(motivos_inatendivel(inst, par, u))) for u in clientes[:limite]]
    if len(clientes) > limite:
        linhas.append("e mais %d clientes" % (len(clientes) - limite))
    return ErroExplicado(
        "%d cliente(s) impossível(is) de atender: %s" % (len(clientes), ", ".join(map(str, clientes[:10])) + (" ..." if len(clientes) > 10 else "")),
        "cada cliente precisa caber em pelo menos uma rota depósito -> cliente -> depósito. " + " | ".join(linhas),
        "relaxe a restrição que aparece no motivo (capacidade, distância máxima ou tempo)" + (", ou " + como_pular if como_pular else " ou retire esses clientes") + ".",
    )
