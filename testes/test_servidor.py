import json
import threading
import unittest
import urllib.error
import urllib.request

from logistica.servidor import criar_servidor


class TesteApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servidor = criar_servidor(0)
        cls.porta = cls.servidor.server_address[1]
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()

    def chamar(self, caminho, corpo=None, bruto=None):
        dados = bruto if bruto is not None else (None if corpo is None else json.dumps(corpo).encode())
        req = urllib.request.Request("http://127.0.0.1:%d%s" % (self.porta, caminho), data=dados, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_lista_de_instancias(self):
        status, lista = self.chamar("/api/instancias")
        self.assertEqual(status, 200)
        self.assertEqual(len([i for i in lista if i["grupo"] != "enviadas e geradas"]), 368)

    def test_resolver_devolve_solucao_verificada(self):
        status, r = self.chamar("/api/resolver", {"arquivo": "solomon/C101.vrp", "iteracoes": 300})
        self.assertEqual(status, 200)
        self.assertTrue(r["verificacao"]["viavel"])
        atendidos = sorted(u for rota in r["rotas"] for u in rota["nos"])
        self.assertEqual(atendidos, list(range(1, 101)))
        for rota in r["rotas"]:
            self.assertLessEqual(rota["carga"], r["parametros"]["capacidade"] + 1e-9)
            self.assertEqual(len(rota["ordem_carregamento"]), len(rota["nos"]))
        self.assertAlmostEqual(sum(x["distancia"] for x in r["rotas"]), r["resultado"]["distancia"], places=6)

    def test_modo_viario_devolve_caminho_fisico(self):
        status, g = self.chamar("/api/gerar", {"n": 25, "semente": 2, "modo": "viario"})
        self.assertEqual(status, 200)
        status, r = self.chamar("/api/resolver", {"arquivo": g["arquivo"], "modo": "viario", "iteracoes": 200})
        self.assertEqual(status, 200)
        self.assertTrue(r["verificacao"]["viavel"])
        self.assertIn("arestas", r["instancia"])

    def test_entradas_invalidas(self):
        self.assertEqual(self.chamar("/api/resolver", {"arquivo": "../logistica/avaliacao.py"})[0], 400)
        self.assertEqual(self.chamar("/api/resolver", {"arquivo": "solomon/C101.vrp", "iteracoes": 10 ** 9})[0], 400)
        self.assertEqual(self.chamar("/api/resolver", {"arquivo": "solomon/C101.vrp", "capacidade": -5})[0], 400)
        self.assertEqual(self.chamar("/api/resolver", {"arquivo": "solomon/C101.vrp", "capacidade": 5})[0], 400)
        self.assertEqual(self.chamar("/api/resolver", {"arquivo": "solomon/C101.vrp", "modo": "x"})[0], 400)
        self.assertEqual(self.chamar("/api/resolver", bruto=b"{nao e json")[0], 400)
        self.assertEqual(self.chamar("/api/resolver", bruto=b"[1,2]")[0], 400)
        self.assertEqual(self.chamar("/api/gerar", {"n": 100000})[0], 400)
        self.assertEqual(self.chamar("/api/inexistente")[0], 404)

    def test_envio_de_arquivo(self):
        texto = open("dados/solomon/C101.vrp", encoding="utf-8").read()
        status, r = self.chamar("/api/enviar", {"nome": "minha", "conteudo": texto})
        self.assertEqual(status, 200)
        status, inst = self.chamar("/api/instancia", {"arquivo": r["arquivo"]})
        self.assertEqual((status, inst["n"]), (200, 100))
        self.assertEqual(self.chamar("/api/enviar", {"nome": "x", "conteudo": "lixo"})[0], 400)
        self.assertEqual(self.chamar("/api/enviar", {"nome": "x", "conteudo": ""})[0], 400)

    def test_pagina_estatica(self):
        req = urllib.request.urlopen("http://127.0.0.1:%d/" % self.porta)
        self.assertIn(b"Roteamento", req.read())
        self.assertEqual(self.chamar("/../main.py")[0], 404)


if __name__ == "__main__":
    unittest.main()
