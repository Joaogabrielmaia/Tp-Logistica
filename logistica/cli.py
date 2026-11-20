import argparse
import os
import re
import sys

from .caminhos import CicloNegativo
from .construtivo import ClienteInatendivel
from .erros import ErroExplicado, explicar, explicar_inatendiveis
from .leitor import ler_instancia
from .modelo import Parametros
from .solver import resolver
from .verificador import verificar


# argparse escreve os erros em inglês; aqui eles viram português, com uma dica de como ver as opções.
TRADUCOES = [
    (r"invalid int value: '(.*)'", r"valor inteiro inválido: '\1'"),
    (r"invalid float value: '(.*)'", r"valor numérico inválido: '\1'"),
    (r"invalid choice: '(.*)' \(choose from (.*)\)", r"opção inválida: '\1' (escolha entre \2)"),
    (r"the following arguments are required: (.*)", r"faltou informar: \1"),
    (r"unrecognized arguments: (.*)", r"argumentos não reconhecidos: \1"),
    (r"expected one argument", r"essa opção precisa de um valor"),
    (r"^argument (\S+):", r"opção \1:"),
]


class Analisador(argparse.ArgumentParser):
    def error(self, message):
        for padrao, troca in TRADUCOES:
            message = re.sub(padrao, troca, message)
        self.print_usage(sys.stderr)
        sys.stderr.write("Erro: %s\nDica: rode 'python %s -h' para ver as opções.\n" % (message, self.prog))
        sys.exit(2)


def _faixa(nome, valor, minimo=None, maximo=None, estrito=False):
    if valor is None:
        return
    abaixo = minimo is not None and (valor <= minimo if estrito else valor < minimo)
    acima = maximo is not None and valor > maximo
    if abaixo or acima:
        limite = ("maior que %g" % minimo) if estrito else ("pelo menos %g" % minimo)
        if maximo is not None:
            limite += " e no máximo %g" % maximo
        motivos = {
            "--iteracoes": "o número de iterações da ruína e recriação não pode ser negativo (0 = só construção e busca local).",
            "--frota": "a frota é o número máximo de veículos; com 0 veículos nenhum cliente seria atendido.",
            "--capacidade": "a capacidade é quanto cabe em um veículo; com 0 ou menos nenhum pedido caberia.",
            "--distancia-maxima": "é o limite de distância de cada rota; precisa ser positivo.",
            "--tempo-limite": "é o prazo em segundos para o solver; precisa ser positivo (omita para não ter limite).",
            "--peso-prioridade": "λ pesa o atraso dos clientes urgentes; negativo premiaria atender tarde e o custo poderia ficar negativo.",
            "--custo-fixo": "é o custo de usar cada veículo; negativo premiaria usar mais veículos.",
            "--mao-unica": "é a fração das ruas (fora da árvore geradora mínima) que vira mão única, de 0 a 1.",
            "--porta": "portas TCP vão de 1 a 65535.",
        }
        raise ErroExplicado("%s = %g fora do intervalo: precisa ser %s" % (nome, valor, limite), motivos.get(nome, ""), "corrija o valor de %s." % nome)


def _mao_unica(args):
    _faixa("--mao-unica", args.mao_unica, 0, 1)
    if args.mao_unica and args.modo != "viario":
        raise ErroExplicado("--mao-unica só vale com --modo viario",
                            "no grafo completo existe arco direto nos dois sentidos entre todo par de pontos; ruas de mão única são uma característica da rede viária.",
                            "acrescente --modo viario, por exemplo: --modo viario --mao-unica 0.3")
    return args.mao_unica


def _resolver(args):
    _faixa("--iteracoes", args.iteracoes, 0, 200000)
    _faixa("--frota", args.frota, 1)
    _faixa("--capacidade", args.capacidade, 0, estrito=True)
    _faixa("--distancia-maxima", args.distancia_maxima, 0, estrito=True)
    _faixa("--tempo-limite", args.tempo_limite, 0, 3600, estrito=True)
    _faixa("--peso-prioridade", args.peso_prioridade, 0)
    _faixa("--custo-fixo", args.custo_fixo, 0)
    inst = ler_instancia(args.arquivo, modo=args.modo, mao_unica=_mao_unica(args))
    if args.prioridades:
        inst = inst.com_prioridades(args.semente_prioridade)
    # "is None" e não "or": um 0 digitado precisa ser validado, não trocado em silêncio pelo valor da instância
    par = Parametros(
        capacidade=inst.capacidade if args.capacidade is None else args.capacidade,
        frota_maxima=inst.frota if args.frota is None else args.frota,
        distancia_maxima=args.distancia_maxima,
        custo_fixo_veiculo=args.custo_fixo,
        peso_prioridade=args.peso_prioridade,
    )
    try:
        res = resolver(inst, par, iteracoes=args.iteracoes, semente=args.semente, tempo_limite=args.tempo_limite)
    except ClienteInatendivel as e:
        raise explicar_inatendiveis(inst, par, e.clientes)
    rel = verificar(inst, par, res.rotas, res.custo)
    print("Instância: %s (%d cliente%s, modo %s)" % (inst.nome, inst.n, "" if inst.n == 1 else "s", inst.modo))
    for e in res.etapas:
        print("  %-20s distância %10.2f  veículos %3d  (%.2fs)" % (e["etapa"], e["distancia"], e["veiculos"], e["tempo"]))
    print("Distância final: %.2f | veículos: %d | custo: %.2f" % (res.distancia, res.veiculos, res.custo))
    if res.interrompido:
        print("Limite de tempo atingido: a solução mostrada é a melhor encontrada até o prazo.")
    if inst.bks_custo and par.custo_fixo_veiculo == 0 and par.peso_prioridade == 0:
        if inst.modo == "completo":
            print("Melhor conhecida: %.2f | diferença: %+.2f%%" % (inst.bks_custo, (res.distancia / inst.bks_custo - 1) * 100))
        else:
            # a BKS foi calculada em linha reta; na rede viária os trajetos seguem as ruas e a diferença não se compara
            print("Melhor conhecida (grafo completo): %.2f | não comparável no modo viário" % inst.bks_custo)
    print("Verificação independente: %s" % ("aprovada" if rel.viavel else "REPROVADA"))
    for erro in rel.erros:
        print("  - " + erro)
    if not rel.viavel:
        print("Por quê: o solver respeita capacidade, janelas e distância, mas a frota é tratada como meta; quando não há"
              " solução com a frota pedida, ele devolve a melhor que achou e o verificador aponta o que foi violado.")
    if args.mostrar_rotas:
        for i, r in enumerate(res.rotas, 1):
            print("Rota %d: %s" % (i, " ".join(map(str, r))))
    return 0 if rel.viavel else 1


def _grafo_dos_args(args):
    from .consulta import grafo_da_instancia, grafo_de_texto
    if args.arestas is not None or args.grafo_arquivo:
        if args.arestas is not None and args.grafo_arquivo:
            raise ErroExplicado("use --arestas ou --grafo-arquivo, não os dois", "são duas formas de informar o mesmo grafo próprio.", "escolha uma delas.")
        texto = args.arestas
        if args.grafo_arquivo:
            if not os.path.isfile(args.grafo_arquivo):
                raise ErroExplicado("arquivo não encontrado: " + args.grafo_arquivo, "o caminho do arquivo de arestas não existe.", "confira o nome do arquivo.")
            with open(args.grafo_arquivo, encoding="utf-8") as f:
                texto = f.read()
        return grafo_de_texto(texto, dirigido=args.dirigido)
    if not args.arquivo:
        raise ErroExplicado("informe uma instância ou um grafo próprio",
                            "o caminho é calculado sobre um grafo: o de uma instância de dados/ ou um digitado com --arestas.",
                            "exemplos: python main.py caminho dados/solomon/R101.vrp 0 15  |  python main.py caminho --arestas \"A B 1\" A B")
    return grafo_da_instancia(ler_instancia(args.arquivo, modo=args.modo, mao_unica=_mao_unica(args)))


def _caminho(args):
    from .consulta import ALGORITMOS, comparar_caminhos
    if args.arestas is not None or args.grafo_arquivo:
        if args.arquivo and args.destino is None:
            args.origem, args.destino, args.arquivo = args.arquivo, args.origem, None
        elif args.arquivo:
            raise ErroExplicado("com grafo próprio, informe só a origem e o destino",
                                "o primeiro argumento seria uma instância, mas o grafo já veio de --arestas ou --grafo-arquivo.",
                                "exemplo: python main.py caminho --arestas \"A B 1\" A B")
    if args.origem is None or args.destino is None:
        raise ErroExplicado("faltou a origem ou o destino", "o caminho liga dois vértices.", "exemplo: python main.py caminho dados/solomon/R101.vrp 0 15")
    g = _grafo_dos_args(args)
    algoritmos = ALGORITMOS if args.algoritmos == "todos" else tuple(a.strip() for a in args.algoritmos.split(","))
    desconhecidos = [a for a in algoritmos if a not in ALGORITMOS]
    if desconhecidos:
        raise ErroExplicado("algoritmo desconhecido: %s" % ", ".join(desconhecidos), "os algoritmos disponíveis são: %s." % ", ".join(ALGORITMOS), "exemplo: --algoritmos dijkstra,bellman_ford")
    r = comparar_caminhos(g, args.origem, args.destino, algoritmos)
    print("Caminho de %s até %s | grafo: %s" % (r["origem"], r["destino"], r["grafo"]))
    for l in r["linhas"]:
        print("\n%s  [%s]" % (l["nome"], l["garante"]))
        if l["caminho"] is not None:
            caminho = " -> ".join(map(str, l["caminho"]))
            if len(caminho) > 160:
                caminho = caminho[:157] + "..."
            print("  custo %.2f | %d arco(s) | %.2f ms" % (l["custo"], l["arcos"], l["tempo_ms"]))
            print("  " + caminho)
        if l["observacao"]:
            print("  " + l["observacao"])
    if r["conclusao"]:
        print("\nConclusão: " + r["conclusao"])
    return 0


def _grafo(args):
    from .consulta import resumir_grafo
    if args.arestas is None and not args.grafo_arquivo and not args.arquivo:
        raise ErroExplicado("informe uma instância ou um grafo próprio", "o resumo descreve um grafo.", "exemplo: python main.py grafo dados/solomon/R101.vrp --modo viario")
    r = resumir_grafo(_grafo_dos_args(args))
    print("Grafo: %s" % r["grafo"])
    print("  vértices: %d | arcos dirigidos: %d (cada aresta de mão dupla conta como 2 arcos)" % (r["vertices"], r["arcos"]))
    print("  grau de saída: mínimo %d, médio %.2f, máximo %d" % (r["grau_min"], r["grau_medio"], r["grau_max"]))
    print("  fortemente conexo (todos alcançam todos): %s" % ("sim" if r["fortemente_conexo"] else "não"))
    print("  arcos de mão única (sem o arco de volta): %d" % r["arcos_mao_unica"])
    print("  componentes fracamente conexas: %d" % r["componentes_fracas"])
    print("  árvore geradora mínima (Kruskal): %d arestas, peso %.2f%s" % (r["agm_arestas"], r["agm_peso"], "" if r["agm_completa"] else " (floresta: o grafo é desconexo)"))
    if args.mostrar_agm:
        for u, v, p in r["agm"]:
            print("    %s - %s  (%g)" % (u, v, p))
    if r["tem_peso_negativo"]:
        print("  há arcos de peso negativo: só Bellman-Ford e Floyd-Warshall servem para menor caminho")
    return 0


def _benchmark(args):
    from . import benchmark
    _faixa("--iteracoes", args.iteracoes, 0, 200000)
    return benchmark.executar(args.conjunto, args.saida, args.iteracoes, args.rapido)


def _interface(args):
    from .servidor import executar
    _faixa("--porta", args.porta, 1, 65535)
    try:
        executar(args.porta, not args.sem_navegador)
    except OSError as e:
        raise ErroExplicado("não foi possível abrir a porta %d (%s)" % (args.porta, e.strerror or e),
                            "outro programa (ou outra cópia da ferramenta) já está usando essa porta.",
                            "feche o outro programa ou escolha outra porta: python main.py interface --porta 8001")
    return 0


def _adicionar_grafo_proprio(p):
    p.add_argument("--modo", choices=["completo", "viario"], default="completo")
    p.add_argument("--mao-unica", type=float, default=0.0, help="fração das ruas que vira mão única na rede viária (0 a 1)")
    p.add_argument("--arestas", help="grafo próprio: 'origem destino peso' separados por ';', ex.: \"A B 5; B C 2\"")
    p.add_argument("--grafo-arquivo", help="arquivo de texto com uma aresta por linha")
    p.add_argument("--dirigido", action="store_true", help="arestas de --arestas valem só de origem para destino")


def principal(argv=None):
    ap = Analisador(prog="main.py", description="Roteamento e carga de veículos com grafos")
    sub = ap.add_subparsers(dest="comando")
    pi = sub.add_parser("interface", help="abre a interface gráfica no navegador")
    pi.add_argument("--porta", type=int, default=8000)
    pi.add_argument("--sem-navegador", action="store_true")
    pi.set_defaults(funcao=_interface)
    pr = sub.add_parser("resolver", help="resolve uma instância pela linha de comando")
    pr.add_argument("arquivo")
    pr.add_argument("--modo", choices=["completo", "viario"], default="completo")
    pr.add_argument("--mao-unica", type=float, default=0.0, help="fração das ruas que vira mão única na rede viária (0 a 1)")
    pr.add_argument("--iteracoes", type=int, default=5000)
    pr.add_argument("--semente", type=int, default=1)
    pr.add_argument("--tempo-limite", type=float, help="segundos para todas as etapas do solver")
    pr.add_argument("--capacidade", type=float)
    pr.add_argument("--frota", type=int)
    pr.add_argument("--distancia-maxima", type=float)
    pr.add_argument("--custo-fixo", type=float, default=0.0)
    pr.add_argument("--peso-prioridade", type=float, default=0.0)
    pr.add_argument("--prioridades", action="store_true")
    pr.add_argument("--semente-prioridade", type=int, default=1)
    pr.add_argument("--mostrar-rotas", action="store_true")
    pr.set_defaults(funcao=_resolver)
    pc = sub.add_parser("caminho", help="compara BFS, DFS, Dijkstra, A*, Bellman-Ford e Floyd-Warshall entre dois vértices")
    pc.add_argument("arquivo", nargs="?", help="instância de dados/ (omita ao usar --arestas)")
    pc.add_argument("origem", nargs="?")
    pc.add_argument("destino", nargs="?")
    pc.add_argument("--algoritmos", default="todos", help="lista separada por vírgula: bfs,dfs,dijkstra,a_estrela,bellman_ford,floyd_warshall")
    _adicionar_grafo_proprio(pc)
    pc.set_defaults(funcao=_caminho)
    pg = sub.add_parser("grafo", help="resumo do grafo: vértices, arcos, graus, conexidade e árvore geradora mínima")
    pg.add_argument("arquivo", nargs="?")
    pg.add_argument("--mostrar-agm", action="store_true", help="lista as arestas da árvore geradora mínima")
    _adicionar_grafo_proprio(pg)
    pg.set_defaults(funcao=_grafo)
    pb = sub.add_parser("benchmark", help="executa os experimentos e grava os CSV em resultados/")
    pb.add_argument("conjunto", nargs="?", default="todos", choices=["todos", "solomon", "cvrp_x", "ablacao", "escala", "grafo_viario", "prioridade", "exato", "kaggle_gh", "kaggle_entregas"])
    pb.add_argument("--saida", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados"))
    pb.add_argument("--iteracoes", type=int, default=10000)
    pb.add_argument("--rapido", action="store_true")
    pb.set_defaults(funcao=_benchmark)
    args = ap.parse_args(argv)
    if not getattr(args, "funcao", None):
        args = ap.parse_args(["interface"] + (argv or []))
    try:
        return args.funcao(args)
    except (ErroExplicado, CicloNegativo, ValueError) as e:
        mensagem, motivo, dica = explicar(e)
        sys.stderr.write("Erro: %s\n" % mensagem)
        if motivo:
            sys.stderr.write("Por quê: %s\n" % motivo)
        if dica:
            sys.stderr.write("O que fazer: %s\n" % dica)
        return 1
    except KeyboardInterrupt:
        sys.stderr.write("\nInterrompido pelo usuário.\n")
        return 130


if __name__ == "__main__":
    sys.exit(principal())
