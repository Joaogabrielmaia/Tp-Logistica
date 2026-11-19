import argparse
import os
import sys

from .leitor import ler_instancia
from .modelo import Parametros
from .solver import resolver
from .verificador import verificar


def _resolver(args):
    inst = ler_instancia(args.arquivo, modo=args.modo)
    if args.prioridades:
        inst = inst.com_prioridades(args.semente_prioridade)
    par = Parametros(
        capacidade=args.capacidade or inst.capacidade,
        frota_maxima=args.frota or inst.frota,
        distancia_maxima=args.distancia_maxima,
        custo_fixo_veiculo=args.custo_fixo,
        peso_prioridade=args.peso_prioridade,
    )
    res = resolver(inst, par, iteracoes=args.iteracoes, semente=args.semente, tempo_limite=args.tempo_limite)
    rel = verificar(inst, par, res.rotas, res.custo)
    print("Instância: %s (%d clientes, modo %s)" % (inst.nome, inst.n, inst.modo))
    for e in res.etapas:
        print("  %-20s distância %10.2f  veículos %3d  (%.2fs)" % (e["etapa"], e["distancia"], e["veiculos"], e["tempo"]))
    print("Distância final: %.2f | veículos: %d | custo: %.2f" % (res.distancia, res.veiculos, res.custo))
    if res.interrompido:
        print("Limite de tempo atingido: a solução mostrada é a melhor encontrada até o prazo.")
    if inst.bks_custo and par.custo_fixo_veiculo == 0 and par.peso_prioridade == 0:
        print("Melhor conhecida: %.2f | diferença: %+.2f%%" % (inst.bks_custo, (res.distancia / inst.bks_custo - 1) * 100))
    print("Verificação independente: %s" % ("aprovada" if rel.viavel else "REPROVADA"))
    for erro in rel.erros:
        print("  - " + erro)
    if args.mostrar_rotas:
        for i, r in enumerate(res.rotas, 1):
            print("Rota %d: %s" % (i, " ".join(map(str, r))))
    return 0 if rel.viavel else 1


def _benchmark(args):
    from . import benchmark
    return benchmark.executar(args.conjunto, args.saida, args.iteracoes, args.rapido)


def _interface(args):
    from .servidor import executar
    executar(args.porta, not args.sem_navegador)
    return 0


def principal(argv=None):
    ap = argparse.ArgumentParser(prog="main.py", description="Roteamento e carga de veículos com grafos")
    sub = ap.add_subparsers(dest="comando")
    pi = sub.add_parser("interface", help="abre a interface gráfica no navegador")
    pi.add_argument("--porta", type=int, default=8000)
    pi.add_argument("--sem-navegador", action="store_true")
    pi.set_defaults(funcao=_interface)
    pr = sub.add_parser("resolver", help="resolve uma instância pela linha de comando")
    pr.add_argument("arquivo")
    pr.add_argument("--modo", choices=["completo", "viario"], default="completo")
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
    pb = sub.add_parser("benchmark", help="executa os experimentos e grava os CSV em resultados/")
    pb.add_argument("conjunto", nargs="?", default="todos", choices=["todos", "solomon", "cvrp_x", "ablacao", "escala", "grafo_viario", "prioridade", "exato", "kaggle_gh", "kaggle_entregas"])
    pb.add_argument("--saida", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados"))
    pb.add_argument("--iteracoes", type=int, default=20000)
    pb.add_argument("--rapido", action="store_true")
    pb.set_defaults(funcao=_benchmark)
    args = ap.parse_args(argv)
    if not getattr(args, "funcao", None):
        args = ap.parse_args(["interface"] + (argv or []))
    return args.funcao(args)


if __name__ == "__main__":
    sys.exit(principal())
