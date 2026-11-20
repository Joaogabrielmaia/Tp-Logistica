"use strict";

const $ = (id) => document.getElementById(id);
const estado = { instancia: null, resultado: null, destaque: null, arquivo: null };
const COR_PRIORIDADE = { 1: "#d64545", 2: "#e0a030", 3: null };
const NOME_PRIORIDADE = { 1: "alta", 2: "média", 3: "baixa" };

function el(tag, attrs, filhos) {
  const e = document.createElement(tag);
  for (const k in attrs || {}) {
    if (k === "texto") e.textContent = attrs[k];
    else if (k === "estilo") e.style.cssText = attrs[k];
    else e.setAttribute(k, attrs[k]);
  }
  for (const f of filhos || []) e.append(f);
  return e;
}

function fmt(v, casas) {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return Number(v).toLocaleString("pt-BR", { minimumFractionDigits: casas === undefined ? 1 : casas, maximumFractionDigits: casas === undefined ? 1 : casas });
}

function corRota(i) {
  const escuro = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const h = (i * 137.508 + 20) % 360;
  return "hsl(" + h.toFixed(0) + "," + (escuro ? 70 : 68) + "%," + (escuro ? 62 : 44) + "%)";
}

function definirEstado(texto, ocupado) {
  const e = $("estado");
  e.textContent = texto;
  e.classList.toggle("ocupado", !!ocupado);
}

// Mostra o erro em três partes, como o servidor devolve: o que aconteceu, por quê e o que fazer.
function mostrarAviso(erro) {
  const a = $("aviso");
  if (!erro) {
    a.hidden = true;
    a.replaceChildren();
    return;
  }
  const msg = typeof erro === "string" ? erro : erro.message;
  const filhos = [el("b", { texto: msg })];
  if (erro.motivo) filhos.push(el("p", {}, [el("span", { texto: "Por quê: " }), erro.motivo]));
  if (erro.dica) filhos.push(el("p", {}, [el("span", { texto: "O que fazer: " }), erro.dica]));
  a.replaceChildren(...filhos);
  a.hidden = false;
}

async function chamar(caminho, corpo) {
  const opcoes = corpo === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(corpo) };
  let r, dados;
  try {
    r = await fetch(caminho, opcoes);
    dados = await r.json();
  } catch (e) {
    const erro = new Error("o servidor não respondeu");
    erro.motivo = "a página fala com o programa Python que roda no terminal; se ele foi encerrado (Ctrl+C) ou caiu, não há quem responda.";
    erro.dica = "rode de novo python main.py no terminal e recarregue a página.";
    throw erro;
  }
  if (!r.ok) {
    const erro = new Error(dados.erro || "erro " + r.status);
    erro.motivo = dados.motivo || "";
    erro.dica = dados.dica || "";
    throw erro;
  }
  return dados;
}

function configuracao() {
  const num = (id) => ($(id).value === "" ? null : Number($(id).value));
  return {
    arquivo: $("instancia").value,
    modo: document.querySelector("input[name=modo]:checked").value,
    prioridades: $("prioridades").checked,
    semente_prioridade: 1,
    capacidade: num("p-cap"),
    frota: num("p-frota"),
    distancia_maxima: num("p-dmax"),
    custo_fixo: num("p-fixo"),
    peso_prioridade: num("p-peso"),
    iteracoes: Number($("p-iter").value),
    tempo_limite: Number($("p-tempo").value),
    semente: Number($("p-semente").value),
  };
}

async function carregarLista(selecionar) {
  const lista = await chamar("/api/instancias");
  const sel = $("instancia");
  sel.replaceChildren();
  const grupos = {};
  for (const item of lista) (grupos[item.grupo] = grupos[item.grupo] || []).push(item);
  const nomes = { solomon: "Solomon (janelas de tempo, 100 clientes)", "cvrp-x": "CVRP-X (101 a 303 clientes)" };
  for (const g in grupos) {
    const og = el("optgroup", { label: nomes[g] || g });
    for (const it of grupos[g]) og.append(el("option", { value: it.arquivo, texto: it.nome }));
    sel.append(og);
  }
  sel.value = selecionar || (lista.find((x) => x.arquivo === "solomon/R101.vrp") || lista[0]).arquivo;
}

async function visualizarInstancia() {
  mostrarAviso("");
  try {
    definirEstado("Carregando instância…", true);
    estado.instancia = await chamar("/api/instancia", configuracao());
    estado.resultado = null;
    estado.destaque = null;
    $("p-cap").placeholder = estado.instancia.capacidade;
    $("p-frota").placeholder = estado.instancia.frota;
    if (estado.instancia.inalcancaveis.length) mostrarAviso("A rede não conecta o depósito a: " + estado.instancia.inalcancaveis.slice(0, 8).join(", "));
    renderTudo();
    definirEstado("Instância " + estado.instancia.nome + " · " + estado.instancia.n + " clientes");
  } catch (e) {
    mostrarAviso(e);
    definirEstado("Erro");
  }
}

async function resolver() {
  mostrarAviso("");
  const botao = $("b-resolver");
  botao.disabled = true;
  definirEstado("Calculando rotas…", true);
  try {
    const r = await chamar("/api/resolver", configuracao());
    estado.resultado = r;
    estado.instancia = r.instancia;
    estado.destaque = null;
    renderTudo();
    definirEstado("Concluído em " + fmt(r.resultado.tempo, 2) + " s");
  } catch (e) {
    mostrarAviso(e);
    definirEstado("Erro");
  } finally {
    botao.disabled = false;
  }
}

function renderTudo() {
  renderKpis();
  renderMapa();
  renderTabela();
  renderCronograma();
  renderCarga();
  renderConvergencia();
}

function kpi(rotulo, valor, sub, classe) {
  return el("div", { class: "kpi " + (classe || "") }, [el("span", { texto: rotulo }), el("b", { texto: valor }), el("small", { texto: sub || "" })]);
}

function renderKpis() {
  const c = $("kpis");
  c.replaceChildren();
  const r = estado.resultado;
  if (!r) {
    const i = estado.instancia;
    if (!i) return;
    c.append(kpi("Clientes", String(i.n), i.tipo), kpi("Capacidade", fmt(i.capacidade, 0), "por veículo"), kpi("Frota", String(i.frota), "veículos disponíveis"));
    if (i.bks_custo) c.append(kpi("Melhor conhecida", fmt(i.bks_custo), (i.bks_veiculos || "?") + " veículos (referência)"));
    return;
  }
  const x = r.resultado;
  c.append(
    kpi("Distância total", fmt(x.distancia), x.gap_bks === null ? "custo " + fmt(x.custo) : "referência " + fmt(r.instancia.bks_custo)),
    kpi("Veículos", String(x.veiculos), "de " + r.parametros.frota + " disponíveis", x.viavel_frota ? "" : "ruim"),
    kpi("Utilização média", fmt(x.utilizacao_media * 100, 1) + "%", "da capacidade"),
    kpi("Diferença p/ referência", x.gap_bks === null ? "—" : (x.gap_bks >= 0 ? "+" : "") + fmt(x.gap_bks, 2) + "%", x.gap_bks === null ? "sem referência neste cenário" : "melhor solução conhecida"),
    kpi("Verificação independente", r.verificacao.viavel ? "Aprovada" : "Reprovada", r.verificacao.viavel ? "todas as restrições conferem" : r.verificacao.erros[0], r.verificacao.viavel ? "ok" : "ruim"),
    kpi("Tempo", fmt(x.tempo, 2) + " s", x.iteracoes + " iterações" + (x.interrompido ? " (limite de tempo atingido)" : "")),
  );
}

let transformacao = null;
let pontosTela = [];

function renderMapa() {
  const cv = $("mapa");
  const caixa = cv.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  cv.width = Math.max(10, caixa.width * dpr);
  cv.height = Math.max(10, caixa.height * dpr);
  const ctx = cv.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const W = caixa.width, H = caixa.height;
  ctx.clearRect(0, 0, W, H);
  const i = estado.instancia;
  if (!i) return;
  const cs = getComputedStyle(document.documentElement);
  const texto = cs.getPropertyValue("--texto").trim();
  const borda = cs.getPropertyValue("--borda").trim();
  const xs = i.nos.map((n) => n.x), ys = i.nos.map((n) => n.y);
  const minx = Math.min(...xs), maxx = Math.max(...xs), miny = Math.min(...ys), maxy = Math.max(...ys);
  const pad = 36;
  const esc = Math.min((W - 2 * pad) / Math.max(1, maxx - minx), (H - 2 * pad) / Math.max(1, maxy - miny));
  const ox = (W - esc * (maxx - minx)) / 2, oy = (H - esc * (maxy - miny)) / 2;
  const tx = (x) => ox + (x - minx) * esc, ty = (y) => H - (oy + (y - miny) * esc);
  transformacao = { tx, ty };
  if (i.arestas) {
    ctx.strokeStyle = borda;
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (const [u, v] of i.arestas) {
      ctx.moveTo(tx(i.nos[u].x), ty(i.nos[u].y));
      ctx.lineTo(tx(i.nos[v].x), ty(i.nos[v].y));
    }
    ctx.stroke();
  }
  const r = estado.resultado;
  const rotaDe = {};
  if (r) {
    r.rotas.forEach((rt, k) => rt.nos.forEach((u) => (rotaDe[u] = k)));
    r.rotas.forEach((rt, k) => {
      const ativa = estado.destaque === null || estado.destaque === k;
      ctx.globalAlpha = ativa ? 1 : 0.12;
      ctx.strokeStyle = corRota(k);
      ctx.lineWidth = estado.destaque === k ? 3.4 : 2;
      ctx.lineJoin = "round";
      ctx.beginPath();
      rt.caminho.forEach(([x, y], j) => (j ? ctx.lineTo(tx(x), ty(y)) : ctx.moveTo(tx(x), ty(y))));
      ctx.stroke();
    });
    ctx.globalAlpha = 1;
  }
  pontosTela = [];
  for (const n of i.nos) {
    const px = tx(n.x), py = ty(n.y);
    pontosTela.push({ id: n.id, px, py });
    if (n.id === 0) continue;
    const k = rotaDe[n.id];
    const ativa = estado.destaque === null || estado.destaque === k;
    ctx.globalAlpha = r && !ativa ? 0.2 : 1;
    const raio = n.prioridade === 1 ? 5.5 : n.prioridade === 2 ? 4.5 : 3.6;
    ctx.beginPath();
    ctx.arc(px, py, raio, 0, Math.PI * 2);
    ctx.fillStyle = r && k !== undefined ? corRota(k) : "#8a93a6";
    ctx.fill();
    const aro = COR_PRIORIDADE[n.prioridade];
    if (aro) {
      ctx.lineWidth = 2;
      ctx.strokeStyle = aro;
      ctx.beginPath();
      ctx.arc(px, py, raio + 2.2, 0, Math.PI * 2);
      ctx.stroke();
    }
  }
  ctx.globalAlpha = 1;
  const d = i.nos[0];
  ctx.fillStyle = texto;
  ctx.fillRect(tx(d.x) - 7, ty(d.y) - 7, 14, 14);
  ctx.fillStyle = cs.getPropertyValue("--superficie").trim();
  ctx.fillRect(tx(d.x) - 3, ty(d.y) - 3, 6, 6);
  const lg = $("legenda");
  lg.replaceChildren(
    el("span", {}, [el("i", { estilo: "background:" + texto + ";border-radius:2px" }), "Depósito"]),
    el("span", {}, [el("i", { estilo: "border:2px solid #d64545" }), "Prioridade alta"]),
    el("span", {}, [el("i", { estilo: "border:2px solid #e0a030" }), "Média"]),
  );
}

function dica(ev) {
  const i = estado.instancia, d = $("dica");
  if (!i) return;
  const caixa = $("mapa").getBoundingClientRect();
  const mx = ev.clientX - caixa.left, my = ev.clientY - caixa.top;
  let melhor = null, dist = 14;
  for (const p of pontosTela) {
    const dd = Math.hypot(p.px - mx, p.py - my);
    if (dd < dist) { dist = dd; melhor = p; }
  }
  if (!melhor) { d.hidden = true; return; }
  const n = i.nos[melhor.id];
  const linhas = [melhor.id === 0 ? "Depósito" : "Cliente " + n.id];
  if (melhor.id !== 0) {
    linhas.push("Demanda " + fmt(n.demanda, 0) + " · serviço " + fmt(n.servico, 0));
    linhas.push("Janela [" + fmt(n.inicio, 0) + ", " + (n.fim === null ? "∞" : fmt(n.fim, 0)) + "]");
    linhas.push("Prioridade " + NOME_PRIORIDADE[n.prioridade]);
    const r = estado.resultado;
    if (r) {
      r.rotas.forEach((rt, k) => {
        const idx = rt.nos.indexOf(n.id);
        if (idx >= 0) linhas.push("Rota " + (k + 1) + " · chegada " + fmt(rt.chegadas[idx], 1) + " · início " + fmt(rt.inicios[idx], 1));
      });
    }
  }
  d.replaceChildren(...linhas.map((t, k) => el(k ? "div" : "b", { texto: t })));
  d.hidden = false;
  d.style.left = Math.min(mx + 14, caixa.width - 270) + "px";
  d.style.top = Math.max(4, my - 10) + "px";
}

function renderTabela() {
  const tb = document.querySelector("#tab-rotas tbody");
  tb.replaceChildren();
  const r = estado.resultado;
  if (!r) {
    tb.append(el("tr", {}, [el("td", { colspan: 5, class: "vazio", texto: "Calcule as rotas para ver o detalhamento." })]));
    return;
  }
  r.rotas.forEach((rt, k) => {
    const tr = el("tr", { class: estado.destaque === k ? "sel" : "" }, [
      el("td", {}, [el("span", { class: "chip", estilo: "background:" + corRota(k) })]),
      el("td", { texto: "#" + rt.indice }),
      el("td", { texto: String(rt.nos.length) }),
      el("td", {}, [el("span", { class: "barra" }, [el("i", { estilo: "width:" + Math.min(100, rt.utilizacao * 100) + "%" })]), fmt(rt.carga, 0) + "/" + fmt(r.parametros.capacidade, 0)]),
      el("td", { texto: fmt(rt.distancia) }),
    ]);
    tr.addEventListener("click", () => {
      estado.destaque = estado.destaque === k ? null : k;
      renderMapa();
      renderTabela();
    });
    tb.append(tr);
  });
}

function svg(tag, attrs, filhos) {
  const e = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const k in attrs || {}) e.setAttribute(k, attrs[k]);
  for (const f of filhos || []) e.append(f);
  return e;
}

function svgTexto(x, y, t, extra) {
  const e = svg("text", Object.assign({ x, y }, extra || {}));
  e.textContent = t;
  return e;
}

function vazio(alvo, msg) {
  alvo.replaceChildren(el("div", { class: "vazio", texto: msg }));
}

function renderCronograma() {
  const alvo = $("cronograma");
  const r = estado.resultado;
  if (!r) return vazio(alvo, "Calcule as rotas para ver a linha do tempo de cada veículo.");
  const linha = 26, esq = 56, dir = 16, topo = 26;
  const W = 1000, H = topo + r.rotas.length * linha + 28;
  const fimDeposito = r.instancia.nos[0].fim;
  const tmax = Math.max(...r.rotas.map((x) => x.retorno), fimDeposito || 0) * 1.02 || 1;
  const sx = (t) => esq + (t / tmax) * (W - esq - dir);
  const raiz = svg("svg", { viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": "Cronograma por veículo" });
  const passo = Math.pow(10, Math.floor(Math.log10(tmax / 6))) * (tmax / 6 / Math.pow(10, Math.floor(Math.log10(tmax / 6))) > 5 ? 5 : tmax / 6 / Math.pow(10, Math.floor(Math.log10(tmax / 6))) > 2 ? 2 : 1);
  for (let t = 0; t <= tmax; t += passo) {
    raiz.append(svg("line", { x1: sx(t), x2: sx(t), y1: topo - 4, y2: H - 24, stroke: "currentColor", "stroke-opacity": 0.1 }));
    raiz.append(svgTexto(sx(t), topo - 10, String(Math.round(t)), { "text-anchor": "middle" }));
  }
  r.rotas.forEach((rt, k) => {
    const y = topo + k * linha;
    const cor = corRota(k);
    raiz.append(svgTexto(esq - 8, y + 15, "Rota " + rt.indice, { "text-anchor": "end" }));
    raiz.append(svg("line", { x1: sx(0), x2: sx(rt.retorno), y1: y + 11, y2: y + 11, stroke: cor, "stroke-opacity": 0.35, "stroke-width": 1 }));
    rt.nos.forEach((u, j) => {
      const n = r.instancia.nos[u];
      if (n.fim !== null) raiz.append(svg("rect", { x: sx(n.inicio), y: y + 2, width: Math.max(1.5, sx(n.fim) - sx(n.inicio)), height: 18, rx: 3, fill: cor, "fill-opacity": 0.16 }));
      const espera = rt.inicios[j] - rt.chegadas[j];
      if (espera > 0.01) raiz.append(svg("rect", { x: sx(rt.chegadas[j]), y: y + 8, width: Math.max(1, sx(rt.inicios[j]) - sx(rt.chegadas[j])), height: 6, fill: "#8a93a6", "fill-opacity": 0.55 }));
      const barra = svg("rect", { x: sx(rt.inicios[j]), y: y + 5, width: Math.max(2, sx(rt.inicios[j] + n.servico) - sx(rt.inicios[j])), height: 12, rx: 2, fill: cor, stroke: COR_PRIORIDADE[n.prioridade] || "none", "stroke-width": 1.6 });
      const tt = svg("title");
      tt.textContent = "Cliente " + u + " · janela [" + fmt(n.inicio, 0) + ", " + (n.fim === null ? "∞" : fmt(n.fim, 0)) + "] · chegada " + fmt(rt.chegadas[j]) + " · início " + fmt(rt.inicios[j]) + " · prioridade " + NOME_PRIORIDADE[n.prioridade];
      barra.append(tt);
      raiz.append(barra);
    });
  });
  raiz.append(svgTexto(esq, H - 8, "Tempo. Faixa clara: janela de tempo do cliente · barra: atendimento · cinza: espera · contorno colorido: prioridade alta/média."));
  alvo.replaceChildren(raiz);
}

function renderCarga() {
  const alvo = $("carga"), carreg = $("carregamento");
  const r = estado.resultado;
  carreg.replaceChildren();
  if (!r) return vazio(alvo, "Calcule as rotas para ver a ocupação de cada veículo.");
  const W = 1000, H = 300, esq = 50, base = H - 40, topo = 20;
  const raiz = svg("svg", { viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": "Utilização da capacidade por veículo" });
  const n = r.rotas.length, larg = (W - esq - 16) / n;
  const ymax = Math.max(1.05, ...r.rotas.map((x) => x.utilizacao));
  const sy = (v) => base - (v / ymax) * (base - topo);
  [0, 0.25, 0.5, 0.75, 1].forEach((v) => {
    raiz.append(svg("line", { x1: esq, x2: W - 8, y1: sy(v), y2: sy(v), stroke: "currentColor", "stroke-opacity": v === 1 ? 0.5 : 0.1, "stroke-dasharray": v === 1 ? "5 4" : "0" }));
    raiz.append(svgTexto(esq - 6, sy(v) + 4, Math.round(v * 100) + "%", { "text-anchor": "end" }));
  });
  r.rotas.forEach((rt, k) => {
    const x = esq + k * larg + larg * 0.15, w = larg * 0.7;
    const b = svg("rect", { x, y: sy(rt.utilizacao), width: w, height: base - sy(rt.utilizacao), rx: 3, fill: corRota(k) });
    const tt = svg("title");
    tt.textContent = "Rota " + rt.indice + ": carga " + fmt(rt.carga, 0) + " de " + fmt(r.parametros.capacidade, 0) + " (" + fmt(rt.utilizacao * 100) + "%)";
    b.append(tt);
    raiz.append(b);
    if (n <= 40) raiz.append(svgTexto(x + w / 2, base + 14, String(rt.indice), { "text-anchor": "middle" }));
  });
  raiz.append(svgTexto(esq, H - 6, "Rotas · linha tracejada: capacidade do veículo (100%)"));
  alvo.replaceChildren(raiz);
  const corpo = el("tbody");
  r.rotas.forEach((rt, k) => {
    corpo.append(el("tr", {}, [
      el("td", {}, [el("span", { class: "chip", estilo: "background:" + corRota(k) }), " #" + rt.indice]),
      el("td", { texto: rt.ordem_carregamento.join(" → ") }),
    ]));
  });
  carreg.append(
    el("h3", { texto: "Ordem de carregamento (primeiro a entrar → último a entrar; o último entregue entra primeiro)" }),
    el("div", { class: "rolagem", estilo: "max-height:280px" }, [el("table", {}, [el("thead", {}, [el("tr", {}, [el("th", { texto: "Veículo" }), el("th", { texto: "Clientes na ordem de carregamento" })])]), corpo])]),
  );
}

function renderConvergencia() {
  const alvo = $("convergencia"), et = $("etapas");
  et.replaceChildren();
  const r = estado.resultado;
  if (!r) return vazio(alvo, "Calcule as rotas para ver a evolução do custo.");
  const h = r.resultado.historico;
  if (h.length < 2) {
    vazio(alvo, "Sem iterações de otimização neste cálculo.");
  } else {
    const W = 1000, H = 300, esq = 70, topo = 16, base = H - 36;
    const raiz = svg("svg", { viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": "Convergência do custo" });
    const xmax = h[h.length - 1][0];
    const ys = h.map((p) => p[1]);
    const ymin = Math.min(...ys), ymax = Math.max(...ys);
    const sx = (v) => esq + (v / xmax) * (W - esq - 12);
    const sy = (v) => base - ((v - ymin) / Math.max(1e-9, ymax - ymin)) * (base - topo);
    for (let k = 0; k <= 4; k++) {
      const v = ymin + ((ymax - ymin) * k) / 4;
      raiz.append(svg("line", { x1: esq, x2: W - 12, y1: sy(v), y2: sy(v), stroke: "currentColor", "stroke-opacity": 0.1 }));
      raiz.append(svgTexto(esq - 6, sy(v) + 4, fmt(v, 0), { "text-anchor": "end" }));
    }
    raiz.append(svg("polyline", { points: h.map((p) => sx(p[0]) + "," + sy(p[1])).join(" "), fill: "none", stroke: "var(--marca)", "stroke-width": 2 }));
    raiz.append(svgTexto(esq, H - 8, "Iterações (0 a " + xmax + ") · melhor custo encontrado"));
    alvo.replaceChildren(raiz);
  }
  const corpo = el("tbody");
  for (const e of r.resultado.etapas) {
    corpo.append(el("tr", {}, [el("td", { texto: e.etapa }), el("td", { texto: fmt(e.distancia) }), el("td", { texto: fmt(e.custo) }), el("td", { texto: String(e.veiculos) }), el("td", { texto: fmt(e.tempo, 2) + " s" })]));
  }
  et.append(
    el("h3", { texto: "Contribuição de cada etapa do solver" }),
    el("div", { class: "rolagem" }, [el("table", {}, [el("thead", {}, [el("tr", {}, ["Etapa", "Distância", "Custo", "Veículos", "Tempo acumulado"].map((t) => el("th", { texto: t })))]), corpo])]),
  );
}

const TITULOS = {
  solomon: "Instâncias Solomon: solver contra a melhor solução conhecida",
  cvrp_x: "Instâncias CVRP-X: solver contra a melhor solução conhecida",
  ablacao: "Ablação: contribuição de cada componente (distância)",
  escala: "Escalabilidade do solver em instâncias sintéticas",
  grafo_viario: "Grafo completo contra rede viária (Dijkstra)",
  prioridade: "Efeito do peso de prioridade",
  exato: "Solver exato contra heurística (instâncias pequenas)",
  kaggle_gh: "Kaggle: instâncias Gehring-Homberger (200 a 1000 clientes)",
  kaggle_entregas: "Kaggle: entregas de e-commerce e efeito da prioridade",
};

async function renderDesempenho() {
  const alvo = $("desempenho");
  try {
    const dados = await chamar("/api/desempenho");
    const nomes = Object.keys(dados);
    if (!nomes.length) return vazio(alvo, "Nenhum experimento registrado em resultados/. Execute: python main.py benchmark");
    alvo.replaceChildren();
    for (const nome of nomes) {
      const linhas = dados[nome];
      if (!linhas.length) continue;
      const cols = Object.keys(linhas[0]);
      const corpo = el("tbody");
      for (const l of linhas) corpo.append(el("tr", {}, cols.map((c) => el("td", { texto: l[c] }))));
      alvo.append(el("h3", { texto: TITULOS[nome] || nome }), el("div", { class: "rolagem" }, [el("table", {}, [el("thead", {}, [el("tr", {}, cols.map((c) => el("th", { texto: c })))]), corpo])]));
    }
  } catch (e) {
    vazio(alvo, e.message);
  }
}

function trocarAba(nome) {
  document.querySelectorAll(".abas button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.aba === nome)));
  document.querySelectorAll(".aba").forEach((s) => (s.hidden = s.id !== "aba-" + nome));
  if (nome === "mapa") renderMapa();
  if (nome === "desempenho") renderDesempenho();
  if (nome === "caminhos") renderCaminho();
}

async function gerar() {
  try {
    const corpo = { n: Number($("g-n").value), semente: Number($("g-semente").value), capacidade: Number($("g-cap").value), agrupada: $("g-agrupada").checked, janelas: $("g-janelas").checked, modo: document.querySelector("input[name=modo]:checked").value };
    const r = await chamar("/api/gerar", corpo);
    await carregarLista(r.arquivo);
    await visualizarInstancia();
  } catch (e) {
    mostrarAviso(e);
  }
}

function enviar(ev) {
  const arq = ev.target.files[0];
  if (!arq) return;
  const leitor = new FileReader();
  leitor.onload = async () => {
    try {
      const ext = (arq.name.match(/\.[^.]+$/) || [".vrp"])[0].toLowerCase();
      const r = await chamar("/api/enviar", { nome: arq.name.replace(/\.[^.]+$/, ""), extensao: ext, conteudo: leitor.result });
      await carregarLista(r.arquivo);
      await visualizarInstancia();
    } catch (e) {
      mostrarAviso(e);
    }
  };
  leitor.readAsText(arq);
}

// Aba Caminhos: roda BFS, DFS, Dijkstra, A*, Bellman-Ford e Floyd-Warshall entre dois vértices, no grafo da
// instância selecionada (no modo escolhido no painel) ou num grafo digitado como lista de arestas.
const consulta = { resultado: null, linha: null };

async function calcularCaminho() {
  mostrarAviso("");
  const proprio = $("c-proprio").checked;
  const corpo = Object.assign(configuracao(), { origem: $("c-origem").value.trim(), destino: $("c-destino").value.trim(), proprio, arestas: $("c-arestas").value, dirigido: $("c-dirigido").checked });
  definirEstado("Calculando caminhos…", true);
  try {
    consulta.resultado = await chamar("/api/caminho", corpo);
    const ok = consulta.resultado.linhas.filter((l) => l.indices);
    consulta.linha = (ok.find((l) => l.algoritmo === "dijkstra") || ok.find((l) => l.algoritmo === "bellman_ford") || ok[0] || {}).algoritmo || null;
    definirEstado("Caminhos calculados");
  } catch (e) {
    consulta.resultado = null;
    definirEstado("Erro");
    mostrarAviso(e);
  }
  renderCaminho();
}

function renderCaminho() {
  const r = consulta.resultado;
  const info = $("c-info"), tabela = $("c-tabela"), desenho = $("c-desenho");
  if (!r) {
    info.replaceChildren();
    tabela.replaceChildren();
    vazio(desenho, "Informe origem e destino e clique em Calcular caminho.");
    return;
  }
  const g = r.resumo;
  info.replaceChildren(
    el("p", { texto: r.grafo }),
    el("p", { texto: g.vertices + " vértices · " + g.arcos + " arcos · " + (g.fortemente_conexo ? "fortemente conexo" : "não é fortemente conexo") + " · " + g.componentes_fracas + " componente(s) · árvore geradora mínima " + fmt(g.agm_peso, 2) + (g.tem_peso_negativo ? " · tem peso negativo" : "") })
  );
  const corpo = el("tbody");
  for (const l of r.linhas) {
    const caminho = l.caminho ? l.caminho.join(" → ") : "—";
    const tr = el("tr", { class: l.algoritmo === consulta.linha ? "sel" : "" }, [
      el("td", {}, [el("b", { texto: l.nome }), el("small", { texto: l.garante })]),
      el("td", { texto: l.custo === null ? "—" : fmt(l.custo, 2) }),
      el("td", { texto: l.arcos === null ? "—" : String(l.arcos) }),
      el("td", { texto: l.tempo_ms === null ? "—" : fmt(l.tempo_ms, 2) }),
      el("td", { class: "c-caminho" }, [caminho.length > 140 ? caminho.slice(0, 137) + "…" : caminho, l.observacao ? el("small", { texto: l.observacao }) : ""]),
    ]);
    if (l.indices) tr.addEventListener("click", () => { consulta.linha = l.algoritmo; renderCaminho(); });
    corpo.append(tr);
  }
  tabela.replaceChildren(
    el("div", { class: "rolagem" }, [el("table", { class: "t-caminhos" }, [el("thead", {}, [el("tr", {}, ["Algoritmo", "Custo", "Arcos", "Tempo (ms)", "Caminho"].map((t) => el("th", { texto: t })))]), corpo])]),
    el("p", { class: "c-conclusao", texto: r.conclusao ? "Conclusão: " + r.conclusao : "" })
  );
  desenharCaminho(desenho, r);
}

function desenharCaminho(alvo, r) {
  const W = 760, H = 460, pad = 34;
  const xs = r.nos.map((n) => n.x), ys = r.nos.map((n) => n.y);
  const minx = Math.min(...xs), maxx = Math.max(...xs), miny = Math.min(...ys), maxy = Math.max(...ys);
  const esc = Math.min((W - 2 * pad) / Math.max(1e-9, maxx - minx || 1), (H - 2 * pad) / Math.max(1e-9, maxy - miny || 1));
  const ox = (W - esc * (maxx - minx)) / 2, oy = (H - esc * (maxy - miny)) / 2;
  const px = (i) => ox + (r.nos[i].x - minx) * esc, py = (i) => H - (oy + (r.nos[i].y - miny) * esc);
  const raiz = svg("svg", { viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": "Grafo com o caminho destacado" });
  const poucos = r.nos.length <= 30;
  if (r.arestas) {
    const vistos = new Set();
    for (const [u, v, p] of r.arestas) {
      const chave = Math.min(u, v) + "-" + Math.max(u, v);
      raiz.append(svg("line", { x1: px(u), y1: py(u), x2: px(v), y2: py(v), stroke: "var(--borda)", "stroke-width": poucos ? 1.6 : 1 }));
      if (poucos && !vistos.has(chave)) {
        vistos.add(chave);
        raiz.append(svgTexto((px(u) + px(v)) / 2 + 4, (py(u) + py(v)) / 2 - 4, fmt(p, Number.isInteger(p) ? 0 : 1), { style: "font-size:13px" }));
      }
    }
  }
  const linha = r.linhas.find((l) => l.algoritmo === consulta.linha);
  if (linha && linha.indices && linha.indices.length > 1) {
    const pts = linha.indices.map((i) => px(i) + "," + py(i)).join(" ");
    raiz.append(svg("polyline", { points: pts, fill: "none", stroke: "var(--destaque)", "stroke-width": 4, "stroke-linejoin": "round", "stroke-linecap": "round" }));
  }
  const noCaminho = new Set(linha && linha.indices ? linha.indices : []);
  r.nos.forEach((n, i) => {
    const pontaO = n.rotulo === String(r.origem), pontaD = n.rotulo === String(r.destino);
    const raio = pontaO || pontaD ? 8 : poucos ? 6 : noCaminho.has(i) ? 4 : 2.5;
    raiz.append(svg("circle", { cx: px(i), cy: py(i), r: raio, fill: pontaO || pontaD ? "var(--destaque)" : noCaminho.has(i) ? "var(--marca)" : "var(--suave)" }));
    if (poucos || pontaO || pontaD) raiz.append(svgTexto(px(i) + 9, py(i) - 9, n.rotulo, { style: "font-size:15px;font-weight:650;fill:var(--texto)" }));
  });
  alvo.replaceChildren(raiz, el("p", { class: "c-legenda", texto: linha ? "Destacado: " + linha.nome + " (clique em outra linha da tabela para trocar)." : "Nenhum algoritmo encontrou caminho." }));
}

async function iniciar() {
  document.querySelectorAll(".abas button").forEach((b) => b.addEventListener("click", () => trocarAba(b.dataset.aba)));
  $("b-resolver").addEventListener("click", resolver);
  $("b-gerar").addEventListener("click", gerar);
  $("arquivo").addEventListener("change", enviar);
  $("b-caminho").addEventListener("click", calcularCaminho);
  $("c-proprio").addEventListener("change", () => ($("c-texto").hidden = !$("c-proprio").checked));
  $("instancia").addEventListener("change", visualizarInstancia);
  document.querySelectorAll("input[name=modo]").forEach((r) => r.addEventListener("change", visualizarInstancia));
  $("prioridades").addEventListener("change", visualizarInstancia);
  $("mapa").addEventListener("mousemove", dica);
  $("mapa").addEventListener("mouseleave", () => ($("dica").hidden = true));
  window.addEventListener("resize", () => renderMapa());
  try {
    await carregarLista();
    await visualizarInstancia();
  } catch (e) {
    mostrarAviso(e);
  }
}

iniciar();
