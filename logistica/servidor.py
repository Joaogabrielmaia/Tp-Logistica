import json
import mimetypes
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .servico import ErroRequisicao, Servico

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
LIMITE_CORPO = 8_000_000


def criar_servidor(porta=8000, host="127.0.0.1", dados=None, resultados=None):
    servico = Servico(dados or os.path.join(RAIZ, "dados"), resultados or os.path.join(RAIZ, "resultados"))

    class Manipulador(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _responder(self, codigo, corpo, tipo="application/json; charset=utf-8"):
            dados_bytes = corpo if isinstance(corpo, bytes) else json.dumps(corpo, ensure_ascii=False).encode("utf-8")
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(dados_bytes)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(dados_bytes)

        def _estatico(self, caminho):
            if caminho in ("", "/"):
                caminho = "/index.html"
            alvo = os.path.normpath(os.path.join(WEB, caminho.lstrip("/")))
            if os.path.commonpath([alvo, WEB]) != WEB or not os.path.isfile(alvo):
                self._responder(404, {"erro": "não encontrado"})
                return
            tipo = mimetypes.guess_type(alvo)[0] or "application/octet-stream"
            if tipo.startswith("text/") or tipo in ("application/javascript",):
                tipo += "; charset=utf-8"
            with open(alvo, "rb") as f:
                self._responder(200, f.read(), tipo)

        def do_GET(self):
            url = urlparse(self.path)
            if url.path == "/api/instancias":
                self._responder(200, servico.listar())
            elif url.path == "/api/desempenho":
                self._responder(200, servico.desempenho())
            elif url.path == "/api/saude":
                self._responder(200, {"ok": True})
            elif url.path.startswith("/api/"):
                self._responder(404, {"erro": "rota desconhecida"})
            else:
                self._estatico(url.path)

        def do_POST(self):
            url = urlparse(self.path)
            try:
                tamanho = int(self.headers.get("Content-Length", 0))
                if tamanho > LIMITE_CORPO:
                    raise ErroRequisicao("requisição grande demais")
                bruto = self.rfile.read(tamanho) if tamanho else b"{}"
                try:
                    corpo = json.loads(bruto.decode("utf-8") or "{}")
                except ValueError:
                    raise ErroRequisicao("JSON inválido")
                if not isinstance(corpo, dict):
                    raise ErroRequisicao("o corpo deve ser um objeto JSON")
                if url.path == "/api/instancia":
                    self._responder(200, servico.instancia(corpo))
                elif url.path == "/api/resolver":
                    self._responder(200, servico.resolver(corpo))
                elif url.path == "/api/gerar":
                    self._responder(200, {"arquivo": servico.gerar(corpo)})
                elif url.path == "/api/enviar":
                    self._responder(200, {"arquivo": servico.enviar(corpo)})
                elif url.path == "/api/caminho":
                    self._responder(200, servico.caminho(corpo))
                else:
                    self._responder(404, {"erro": "rota desconhecida"})
            except ErroRequisicao as e:
                self._responder(400, {"erro": str(e), "motivo": e.motivo, "dica": e.dica})
            except (ValueError, TypeError) as e:
                self._responder(400, {"erro": "parâmetros inválidos: " + str(e), "motivo": "algum campo veio vazio ou com texto no lugar de número.", "dica": "confira os campos numéricos da tela."})
            # Qualquer outra falha vira resposta 500 com o tipo do erro, para a página não ficar travada esperando.
            except Exception as e:
                self._responder(500, {"erro": "falha interna: " + type(e).__name__, "motivo": str(e)[:200], "dica": "recarregue a página; se repetir, rode o mesmo caso pela linha de comando para ver o detalhe."})

    servidor = ThreadingHTTPServer((host, porta), Manipulador)
    servidor.servico = servico
    return servidor


def executar(porta=8000, abrir_navegador=True):
    servidor = criar_servidor(porta)
    url = "http://127.0.0.1:%d/" % servidor.server_address[1]
    print("Interface em " + url + "  (Ctrl+C para encerrar)")
    if abrir_navegador:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()
