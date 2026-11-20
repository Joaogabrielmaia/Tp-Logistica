import os
import sys
import threading

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from playwright.sync_api import sync_playwright

from logistica.servidor import criar_servidor

OUT = os.path.join(RAIZ, "relatorio", "figuras")


def topo(pagina):
    # o clique em "Calcular rotas" rola a página; volta ao topo para o cabeçalho aparecer no print
    pagina.evaluate("window.scrollTo(0, 0)")
    pagina.wait_for_timeout(200)


def capturar():
    os.makedirs(OUT, exist_ok=True)
    servidor = criar_servidor(0)
    porta = servidor.server_address[1]
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        pagina = navegador.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5, color_scheme="light")
        pagina.goto("http://127.0.0.1:%d/" % porta)
        pagina.wait_for_timeout(1000)
        pagina.select_option("#instancia", "kaggle/ecommerce/entregas_200.csv")
        pagina.wait_for_timeout(800)
        pagina.fill("#p-peso", "0.01")
        pagina.select_option("#p-iter", "5000")
        pagina.click("#b-resolver")
        pagina.wait_for_selector(".kpi.ok", timeout=120000)
        pagina.wait_for_timeout(500)
        topo(pagina)
        pagina.screenshot(path=os.path.join(OUT, "tela_mapa.png"))
        for aba in ("cronograma", "carga", "convergencia"):
            pagina.click("button[data-aba=%s]" % aba)
            pagina.wait_for_timeout(400)
            topo(pagina)
            pagina.screenshot(path=os.path.join(OUT, "tela_%s.png" % aba))
        pagina.click("button[data-aba=mapa]")
        pagina.check("input[name=modo][value=viario]")
        pagina.wait_for_timeout(1200)
        pagina.click("summary:has-text('Gerar instância sintética')")
        pagina.fill("#g-n", "45")
        pagina.fill("#g-semente", "3")
        pagina.click("#b-gerar")
        pagina.wait_for_timeout(1500)
        pagina.fill("#p-peso", "0")
        pagina.wait_for_timeout(800)
        pagina.click("#b-resolver")
        pagina.wait_for_selector(".kpi.ok", timeout=120000)
        pagina.wait_for_timeout(500)
        topo(pagina)
        pagina.screenshot(path=os.path.join(OUT, "tela_viario.png"))
        pagina.click("button[data-aba=caminhos]")
        pagina.fill("#c-origem", "0")
        pagina.fill("#c-destino", "30")
        pagina.click("#b-caminho")
        pagina.wait_for_function("document.getElementById('estado').innerText === 'Caminhos calculados'", timeout=60000)
        pagina.wait_for_timeout(400)
        topo(pagina)
        pagina.screenshot(path=os.path.join(OUT, "tela_caminhos.png"))
        navegador.close()
    servidor.shutdown()


if __name__ == "__main__":
    capturar()
