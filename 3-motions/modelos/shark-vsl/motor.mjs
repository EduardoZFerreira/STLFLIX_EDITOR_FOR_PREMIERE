// Motor dos motions STLFLIX 9:16 (HyperFrames). Extraído do build.mjs da VSL-Shark (corpo e leads usam o mesmo),
// sem mudar o HTML, o CSS nem as animações: só as cenas, a pasta, a faixa e a campanha viraram parâmetros.
// O código abaixo NÃO é recuado de propósito: os textos multilinha (HTML, CSS, runtime) vão para os arquivos gerados.
// As cenas vêm do plano-de-cenas.md (ver dsl.mjs). Uso: construir(cenas, { pasta, faixa, campanha, so })
import fs from "node:fs";
import path from "node:path";

// Cores e textos da campanha: 2-design-system/campanhas/<campanha>/campanha.json (ligada na pasta de trabalho).
// Sem o arquivo, valem os da BF26, e o resultado é idêntico ao motor original. A marca STLFLIX (fontes, branco,
// verde-limão de resultado e CTA) não muda com a campanha.
const CAMPANHA_PADRAO = {
  nome: "Black November 2026",
  logo: { arquivo: "logo-kv.png", texto: "Black November · Infinitas possibilidades para viver de impressão 3D" },
  cores: { degrade: ["#8DFB5E", "#2EE6A6", "#22C7F0", "#2F7BFF"], barra: "#2F7BFF", brilho: "#07EF2D" },
};
export function lerCampanha(pasta, campanha) {
  let c = {};
  try { c = JSON.parse(fs.readFileSync(path.join(pasta, campanha, "campanha.json"), "utf8")); } catch {}
  return { ...CAMPANHA_PADRAO, ...c, logo: { ...CAMPANHA_PADRAO.logo, ...(c.logo || {}) }, cores: { ...CAMPANHA_PADRAO.cores, ...(c.cores || {}) } };
}
const rgb = (hex) => { const h = hex.replace("#", ""); return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)).join(","); };
const degrade = (cores) => {                           // 4 cores: 0/32/64/100% como na BF26; outras quantidades, por igual
  const pos = cores.length === 4 ? [0, 32, 64, 100] : cores.map((_, i) => Math.round((100 * i) / Math.max(1, cores.length - 1)));
  return `linear-gradient(90deg, ${cores.map((c, i) => `${c} ${pos[i]}%`).join(", ")})`;
};

export function construir(cenas, { pasta, faixa = {}, campanha = "bf26", so = null } = {}) {
cenas = JSON.parse(JSON.stringify(cenas));            // o pós-processamento marca as peças: não mexe no original
const W = 1080, H = 1920;
const BAND = { top: 130, height: 430, side: 64, ...faixa };   // faixa acima da cabeça do apresentador
const CAMP = lerCampanha(pasta, campanha), DG = CAMP.cores.degrade;
const COR2 = DG[1] || DG[0], COR3 = DG[2] || DG[DG.length - 1];   // brilhos dos efeitos (fx): 2ª e 3ª cor do degradê
// número de resultado ([verde] no plano): o verde → azul da marca em qualquer campanha, salvo "resultado" no campanha.json
const RES = CAMP.cores.resultado || CAMPANHA_PADRAO.cores.degrade;
const NUM_BG = degrade(RES) === degrade(DG) ? "var(--grad-title)" : degrade(RES);
const GAP = 0.6;                                       // intervalo entre cenas no reel (facilita o corte)
for (const s of cenas) if (s.topo) s.fases.forEach((ph, pi) => { for (const e of ph.els) if (e.k === "title") e.imp = { label: ph.els.some((x) => x.k === "label"), icone: ph.els.some((x) => x.k === "ico"), caneta: true }; });   // caneta em todas as batidas (o usuário preferiu assim)

// Frases-tese: o título ganha peso (variable-axis-type do registry, na Sora variável: 200 → 700, palavra-chave 800).
const PESO = new Set([]);   // nesta VSL as frases-tese usam VX() direto
for (const s of cenas) if (PESO.has(s.id)) for (const ph of s.fases) for (const e of ph.els) if (e.k === "title") e.vax = true;

// ───────────────────────── HTML de cada peça ─────────────────────────
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const rich = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, '<span class="g">$1</span>');
const CHECK = '<svg class="ck" viewBox="0 0 24 24" width="30" height="30"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="#3DDC84" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>';

// Quebra explícita em até 2 linhas equilibradas; a palavra-chave (**...**) é uma unidade que nunca se parte.
// Linhas fixas são exigência dos efeitos que mudam a largura das letras (o texto não pode re-quebrar no meio).
function quebraLinhas(text, limite) {
  const unid = [];
  text.split(/\*\*/).forEach((p, i) => {
    if (!p.trim()) return;
    if (i % 2) unid.push({ t: p.trim(), kw: true });
    else p.trim().split(/\s+/).forEach((w) => {
      if (/^[\p{P}]+$/u.test(w) && unid.length) unid[unid.length - 1].pos = (unid[unid.length - 1].pos || "") + w;   // pontuação solta (ex.: aspas) gruda na anterior
      else unid.push({ t: w, kw: false });
    });
  });
  const len = (arr) => arr.map((u) => u.t + (u.pos || "")).join(" ").length;
  let linhas = [unid];
  if (len(unid) > limite && unid.length > 1) {
    let melhor = null;
    for (let i = 1; i < unid.length; i++) { const m = Math.max(len(unid.slice(0, i)), len(unid.slice(i))); if (!melhor || m < melhor.m) melhor = { i, m }; }
    linhas = [unid.slice(0, melhor.i), unid.slice(melhor.i)];
  }
  return { unid, linhas, len };
}
// Frase de impacto (cenas com título no topo): Sora grande, linhas explícitas (cada linha entra
// por conta própria), palavra-chave em gradiente e circulada à mão. O tamanho final é medido no navegador (runtime).
function impHTML(e, at, a) {
  const { unid, linhas, len } = quebraLinhas(e.text, 14);
  const maior = Math.max(...linhas.map(len));
  const teto = e.imp.icone ? (e.imp.label ? 92 : 104) : 140;   // com ícone na batida a frase encolhe para os três caberem na faixa
  const size = Math.min(linhas.length > 1 ? Math.min(teto, e.imp.label ? 100 : 118) : teto, Math.round(900 / (maior * 0.56)));
  const semKw = !unid.some((u) => u.kw) && e.circ !== false;   // sem palavra-chave: a frase toda é circulada, em branco (circ: false desliga)
  const html = linhas.map((l) => {
    const corpo = l.map((u) => (u.kw ? `<span class="kw"><span class="g">${esc(u.t)}</span></span>${esc(u.pos || "")}` : esc(u.t + (u.pos || "")))).join(" ");
    return `<span class="ln"><span class="lt"><span class="tt">${semKw ? `<span class="kw">${corpo}</span>` : corpo}</span></span></span>`;
  }).join("");
  return `<div class="el title imp" data-noanim="1"${e.imp.caneta ? ' data-caneta="1"' : ""} style="font-size:${size}px" ${a(at)}>${html}</div>`;
}

function elHTML(e, at) {
  const a = (t) => `data-at="${(+t).toFixed(2)}"`;
  switch (e.k) {
    case "kicker": return `<div class="el kicker hf-tracking-in" data-noanim="1" ${a(at)}>${esc(e.text)}</div>`;
    case "label": return `<div class="el label" ${a(at)}>${esc(e.text)}</div>`;
    case "title": {
      if (e.imp) return impHTML(e, at, a);
      if (e.vax) {   // frase-tese com peso variável: linhas fixas, cada uma numa caixa que não quebra
        const { linhas } = quebraLinhas(e.text, 16);
        const html = linhas.map((l) => `<span class="vl">${l.map((u) => (u.kw ? `<span class="g">${esc(u.t)}</span>${esc(u.pos || "")}` : esc(u.t + (u.pos || "")))).join(" ")}</span>`).join("");
        return `<div class="el title vax" style="font-size:${e.vpx || 92}px" ${a(at)}>${html}</div>`;
      }
      const strike = e.strikeAt != null ? `<i class="line" ${a(at + e.strikeAt)}></i>` : "";
      return `<div class="el title t-${e.size || "md"}${e.wide ? " wide" : ""}${e.vax ? " vax" : ""}${e.strikeAt != null ? " struck" : ""}" ${a(at)}><span class="tx">${rich(e.text)}${strike}</span></div>`;
    }
    case "num": {
      const cls = `el num n-${e.size || "lg"}${e.grad ? " g" : ""}${e.lime ? " lime" : ""}${e.neg ? " neg" : ""}`;
      if (e.count) {
        const c = e.count;
        return `<div class="${cls}" ${a(at)}><span class="cnt" data-to="${c.to}" data-dec="${c.dec || 0}" data-pre="${esc(c.prefix || "")}" data-suf="${esc(c.suffix || "")}" ${a(at + 0.1)}>${esc((c.prefix || "") + "0" + (c.suffix || ""))}</span></div>`;
      }
      return `<div class="${cls}" ${a(at)}>${esc(e.text)}</div>`;
    }
    case "chips": {
      const step = e.step ?? 0.8, items = [];
      e.items.forEach((t, i) => {
        if (i && e.arrows) items.push(`<span class="arrow it" ${a(at + i * step - 0.15)}>→</span>`);
        const strike = e.strikeAt != null ? `<i class="line" ${a(at + e.strikeAt + i * 0.25)}></i>` : "";
        items.push(`<span class="chip it${e.dim ? " dim" : ""}${e.strikeAt != null ? " struck" : ""}" ${a(at + i * step)}>${e.check ? CHECK : ""}<span>${esc(t)}</span>${strike}</span>`);
      });
      return `<div class="el chips${e.cols === 2 ? " two" : ""}" ${a(at)} data-noanim="1">${items.join("")}</div>`;
    }
    case "row": {
      const step = e.step ?? 1;
      return `<div class="el row" ${a(at)} data-noanim="1">${e.items.map((it, i) => `<div class="cell it" ${a(at + i * step)}><div class="rn">${esc(it.n)}</div><div class="rl">${esc(it.l)}</div></div>`).join("")}</div>`;
    }
    case "people": {
      const step = e.step ?? 1;
      return `<div class="el row people" ${a(at)} data-noanim="1">${e.items.map((it, i) => `<div class="cell it" ${a(at + i * step)}><div class="pn">${esc(it.n)}</div><div class="rl">${esc(it.d)}</div></div>`).join("")}</div>`;
    }
    case "bars": {
      const step = e.step ?? 1;
      return `<div class="el bars" ${a(at)} data-noanim="1">${e.items.map((it, i) => `<div class="bar it" ${a(at + i * step)}><span class="bl">${esc(it.l)}</span><span class="track"><i class="fill${i === 0 ? "" : " alt"}" data-f="${it.f}" ${a(at + i * step + 0.2)}></i></span><span class="bv">${esc(it.v)}</span></div>`).join("")}</div>`;
    }
    case "conta": {
      const step = e.step ?? 2;
      return `<div class="el conta" ${a(at)} data-noanim="1"><div class="cw">${e.lines.map((t, i) => `<div class="cl it" ${a(at + i * step)}>${esc(t)}</div>`).join("")}</div></div>`;
    }
    case "stack": {
      const step = e.step ?? 1;
      return `<div class="el stack${e.small ? " small" : ""}" ${a(at)} data-noanim="1">${e.items.map((it, i) => `<div class="sr it struck" ${a(at + i * step)}><span class="tx"><b>${esc(it.v)}</b>${it.l ? `<em>${esc(it.l)}</em>` : ""}${e.strikeAt ? `<i class="line" ${a(at + e.strikeAt[i])}></i>` : ""}</span></div>`).join("")}</div>`;
    }
    case "dots": return `<div class="el dots" ${a(at)} data-noanim="1">${Array.from({ length: e.n }, (_, i) => `<i class="dot it" ${a(at + i * 0.45)}></i>`).join("")}</div>`;
    case "cta": return `<div class="el cta" ${a(at)}><span class="btn">${esc(e.text)}<i class="shine"></i></span><span class="down">↓</span><i class="tri"></i></div>`;
    case "ico": return `<div class="el ico" data-noanim="1" ${a(at)} style="height:${e.h || 170}px"><img src="${campanha}/${e.nome}.png" alt=""></div>`;
    case "icos": return `<div class="el icos" data-noanim="1" ${a(at)}>${e.nomes.map((nm, i) => `<div class="ico" ${a(at + i * (e.step ?? 0.25))} style="height:${e.h || 120}px"><img src="${campanha}/${nm}.png" alt=""></div>`).join("")}</div>`;
    case "logo": return `<div class="el logo" data-noanim="1" ${a(at)}><img src="${campanha}/${CAMP.logo.arquivo}" alt="${esc(CAMP.logo.texto)}" style="width:${e.w || 940}px"></div>`;
    case "x3d": return `<div class="el x3d" ${a(at)} data-noanim="1">${e.linhas.map(([t, cor, px], i) => `<div class="xl xl-${cor} it" data-t="${esc(t)}" style="font-size:${px}px" ${a(at + i * 0.35)}><span class="xf">${esc(t)}</span></div>`).join("")}</div>`;
  }
  throw new Error("peça desconhecida: " + e.k);
}

const CSS = `
__ROOT__ { position: absolute; inset: 0; overflow: hidden; font-family: var(--font-title);
  --grad-title: ${degrade(DG)};
  --accent: ${CAMP.cores.barra}; }   /* Black: só verde → azul (sem violeta/rosa); barrinha no azul da campanha */
.band { position: absolute; left: ${BAND.side}px; right: ${BAND.side}px; top: ${BAND.top}px; height: ${BAND.height}px; }
.phase { font-family: var(--font-title); position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 14px; text-align: center;
  text-shadow: 0 2px 18px rgba(0,0,0,.55), 0 1px 3px rgba(0,0,0,.5); }
.topo { position: absolute; left: 0; right: 0; top: 24px; display: flex; flex-direction: column; align-items: center; gap: 14px; text-align: center; text-shadow: 0 2px 18px rgba(0,0,0,.55), 0 1px 3px rgba(0,0,0,.5); }
.phase.sob { top: 100px; }
/* título pequeno (topo e dentro das cenas): tracking-in (componente do registry) — Inter em caixa alta, branco, letras se aproximando.
   Verde-lima fica reservado para resultado (números) e CTA. */
.kicker.hf-tracking-in { font: 700 36px/1.2 var(--font-body); text-transform: uppercase; color: #fff;
  letter-spacing: var(--hf-tracking-value, .6em); text-shadow: 0 2px 12px rgba(0,0,0,.6), 0 0 2px rgba(0,0,0,.35); }
/* frase de impacto: Sora, palavra-chave circulada à mão */
.title.imp { font-family: var(--font-title); font-weight: 700; letter-spacing: 0; line-height: 1.12; max-width: 952px; }   /* .title.imp vence o espaçamento negativo do .title (o colorama desenha sem ele) */
.imp .ln { display: block; white-space: nowrap; }
.imp .lt { position: relative; display: inline-block; }
.imp .ln + .ln { margin-top: .16em; }
.imp + .label { margin-top: 30px; }
.imp .kw { position: relative; display: inline-block; }
.imp .circ, .imp .ca-ink { position: absolute; overflow: visible; pointer-events: none; }
.imp .ca-ink path { filter: drop-shadow(0 2px 6px rgba(0,0,0,.45)); }
.imp .ca-pen { position: absolute; left: 0; top: 0; width: 0; height: 0; pointer-events: none; filter: drop-shadow(0 6px 10px rgba(0,0,0,.45)); }
.imp .circ path { fill: none; stroke: var(--cta); stroke-width: 7; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 1; stroke-dashoffset: 1;
  filter: drop-shadow(0 2px 6px rgba(0,0,0,.45)); }
/* palavra-chave da frase de impacto: camada branca por cima do gradiente, que some (--branco 1 → 0) */
/* frase-tese: Sora variável, começa fina e ganha peso */
@font-face { font-family: "Plus Jakarta Sans"; src: url("fx/plus-jakarta-sans-variable-latin.woff2") format("woff2"); font-weight: 200 800; font-display: block; }   /* guia BF26: título de impacto */
@font-face { font-family: "Sora Var"; src: url("fx/sora-variable-latin.woff2") format("woff2"); font-weight: 100 800; font-display: block; }
.title.vax { font-family: "Sora Var", var(--font-title); font-weight: 200; font-size: 92px; line-height: 1.1; letter-spacing: 0; max-width: 952px; }
.vax .vl { display: block; white-space: nowrap; }
.imp .g, .vax .g { --branco: 0; background-image: linear-gradient(rgba(255,255,255,var(--branco)), rgba(255,255,255,var(--branco))), var(--grad-title); }
.accent { display: none; width: 140px; height: 10px; border-radius: 5px; background: var(--accent); box-shadow: 0 2px 12px rgba(0,0,0,.4); margin-bottom: 8px; flex: 0 0 auto; }
.kicker { font: 600 34px/1.2 var(--font-body); letter-spacing: .14em; text-transform: uppercase; color: rgba(246,250,254,.85); }
.title { font-weight: 700; color: var(--text); letter-spacing: -.03em; line-height: 1.08; max-width: 952px; }
.t-sm { font-size: 58px; } .t-md { font-size: 74px; } .t-lg { font-size: 100px; } .t-xl { font-size: 150px; }
.wide { letter-spacing: .08em; }
.tx { position: relative; display: inline-block; }
.num { white-space: nowrap; font-weight: 700; color: var(--text); letter-spacing: -.04em; line-height: .95; font-variant-numeric: tabular-nums; }
.num.lime { background: ${NUM_BG}; -webkit-background-clip: text; background-clip: text; color: transparent; text-shadow: none;
  filter: drop-shadow(0 2px 12px rgba(0,0,0,.45)); }   /* sem glow colorido: as bordas ficavam marcadas */
.num.lime .cnt { background: inherit; -webkit-background-clip: text; background-clip: text; }
.n-lg { font-size: 160px; } .n-md { font-size: 116px; }
.neg { color: var(--no); }
.label { font: 600 42px/1.2 var(--font-body); color: rgba(246,250,254,.88); max-width: 952px; }
.g { background: var(--grad-title); -webkit-background-clip: text; background-clip: text; color: transparent; text-shadow: none; filter: drop-shadow(0 2px 12px rgba(0,0,0,.45)); }
.num.g .cnt { background: inherit; -webkit-background-clip: text; background-clip: text; }
.chips { display: flex; flex-wrap: wrap; justify-content: center; align-items: center; gap: 14px 14px; max-width: 952px; }
.chips.two { display: grid; grid-template-columns: repeat(2, auto); justify-content: center; }
.chip { position: relative; display: inline-flex; align-items: center; gap: 10px; padding: 12px 28px; border-radius: 999px; border: 2px solid rgba(246,250,254,.55);
  font: 600 38px/1.15 var(--font-body); color: var(--text); white-space: nowrap; }
.chip .ck { flex: 0 0 auto; filter: drop-shadow(0 1px 4px rgba(0,0,0,.4)); }
.chip.dim { color: rgba(246,250,254,.7); border-color: rgba(246,250,254,.3); }
.arrow { font: 600 40px var(--font-body); color: rgba(246,250,254,.7); }
.line { position: absolute; left: -4%; right: -4%; top: 52%; height: 4px; border-radius: 2px; background: var(--no); transform-origin: left center; transform: scaleX(0); display: block; }
.row { display: flex; justify-content: center; align-items: flex-start; gap: 52px; }
.cell { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.rn { font: 700 92px/1 var(--font-title); letter-spacing: -.04em; color: var(--text); }
.pn { font: 700 64px/1.05 var(--font-title); letter-spacing: -.03em; color: var(--text); }
.rl { font: 600 34px/1.2 var(--font-body); color: rgba(246,250,254,.85); max-width: 320px; }
.bars { display: flex; flex-direction: column; gap: 22px; width: 900px; }
.bar { display: grid; grid-template-columns: 150px 1fr 170px; align-items: center; gap: 22px; }
.bl { font: 600 36px var(--font-body); color: var(--text); text-align: right; }
.bv { font: 700 56px var(--font-title); color: var(--text); text-align: left; letter-spacing: -.03em; }
.track { position: relative; height: 22px; border-radius: 11px; background: rgba(246,250,254,.18); overflow: hidden; }
.fill { position: absolute; inset: 0; background: var(--text); transform-origin: left center; transform: scaleX(0); display: block; border-radius: 11px; }
.fill.alt { background: var(--grad-title); }
.conta { height: 210px; overflow: hidden; width: 952px; -webkit-mask-image: linear-gradient(to bottom, transparent 0, #000 30%, #000 100%); mask-image: linear-gradient(to bottom, transparent 0, #000 30%, #000 100%); }
.cw { display: flex; flex-direction: column; justify-content: flex-end; min-height: 210px; }
.cl { font: 600 44px/70px var(--font-body); color: var(--text); white-space: nowrap; }
.stack { display: flex; flex-direction: column; align-items: center; gap: 10px; }
.sr b { font: 700 74px/1.05 var(--font-title); letter-spacing: -.03em; color: var(--text); }
.sr em { font: 600 34px var(--font-body); font-style: normal; color: rgba(246,250,254,.8); margin-left: 18px; }
.stack.small .sr b { font-size: 54px; }
.dots { display: flex; gap: 22px; margin-top: 8px; }
.dot { display: block; width: 26px; height: 26px; border-radius: 50%; border: 3px solid rgba(246,250,254,.8); }
.cta { display: flex; flex-direction: column; align-items: center; gap: 18px; }
.btn { display: inline-block; padding: 30px 64px; border-radius: 999px; background: var(--grad-title); color: #0d0e14; font: 700 54px/1 var(--font-title); letter-spacing: -.01em; text-shadow: none;
  box-shadow: 0 6px 18px rgba(0,0,0,.4); }   /* sem glow colorido: o brilho grande dava banding no degradê */
.down { font: 700 64px/1 var(--font-body); color: var(--cta); }
/* ── efeitos da Black (cenas fx) ── */
.shine, .tri { display: none; }
.fx .num.lime { position: relative; }
.fx .down { display: none; }
.fx .tri { display: block; width: 0; height: 0; border-left: 44px solid transparent; border-right: 44px solid transparent; border-top: 56px solid ${COR2};
  filter: drop-shadow(0 3px 8px rgba(0,0,0,.5)); }
.fx .btn { position: relative; overflow: hidden; box-shadow: 0 6px 18px rgba(0,0,0,.4); }
.fx .shine { display: block; position: absolute; top: -40%; bottom: -40%; left: -40%; width: 30%; transform: skewX(-22deg);
  background: linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,.85), rgba(255,255,255,0)); }
.dust { position: absolute; left: -${BAND.side}px; top: -110px; width: ${W}px; height: 600px; pointer-events: none; }
/* tipo 3D da campanha: camada de trás = extrusão + glow, da frente = gradiente */
/* assets oficiais (kit BF26): objeto com sombra curta e brilho verde só embaixo */
.ico { position: relative; display: flex; justify-content: center; align-items: flex-end; flex: 0 0 auto; }
.ico img { height: 100%; width: auto; display: block; position: relative; z-index: 1; filter: drop-shadow(0 10px 14px rgba(0,0,0,.45)); }
.ico::after { content: ""; position: absolute; left: 50%; bottom: -4%; width: 72%; height: 16%; transform: translateX(-50%); z-index: 0;
  background: radial-gradient(ellipse at center, rgba(${rgb(CAMP.cores.brilho)},.5), rgba(${rgb(CAMP.cores.brilho)},0) 70%); filter: blur(6px); display: none; }   /* brilho verde desligado: sem glow colorido */
.icos { display: flex; justify-content: center; align-items: flex-end; gap: 28px; margin-top: 10px; }
.logo img { display: block; height: auto; filter: drop-shadow(0 16px 26px rgba(0,0,0,.5)); }
.x3d { display: flex; flex-direction: column; align-items: center; gap: 0; }
.xl { position: relative; font-family: "Plus Jakarta Sans", "Sora Var", var(--font-title); font-weight: 800; text-transform: uppercase; line-height: 1.02; letter-spacing: -.02em; white-space: nowrap; }
.xl .xf { position: relative; z-index: 1; display: block; }
.xl::before { content: attr(data-t); position: absolute; left: 0; right: 0; top: 0; text-align: center; z-index: 0; }   /* extrusão: pseudo-elemento atrás da face */
.xl .xf { -webkit-background-clip: text; background-clip: text; color: transparent; text-shadow: none; }
.xl-azul::before { color: #1a56d6; text-shadow: 0 1px 0 #1a56d6, 0 2px 0 #1951cc, 0 3px 0 #174cc1, 0 4px 0 #1647b7, 0 5px 0 #1442ac, 0 6px 0 #133da2, 0 7px 0 #123898, 0 8px 0 #10348d, 0 9px 0 #0f2f83, 0 10px 0 #0e2a79, 0 11px 0 #0c256e, 0 12px 0 #0b2064, 0 13px 0 #091b59, 0 14px 0 #08164f, 0 22px 22px rgba(0,0,0,.55); }
.xl-azul .xf { background-image: linear-gradient(180deg, #b8f6ff 0%, #5fd6ff 26%, #2f9bff 58%, #1f62ec 100%); }
.xl-verde::before { color: #11a83a; text-shadow: 0 1px 0 #11a83a, 0 2px 0 #10a038, 0 3px 0 #0f9835, 0 4px 0 #0e9133, 0 5px 0 #0d8930, 0 6px 0 #0c812e, 0 7px 0 #0b792b, 0 8px 0 #0a7229, 0 9px 0 #096a26, 0 10px 0 #086224, 0 11px 0 #075a21, 0 12px 0 #06531f, 0 13px 0 #054b1c, 0 14px 0 #04431a, 0 22px 22px rgba(0,0,0,.55); }
.xl-verde .xf { background-image: linear-gradient(180deg, #e2ff9e 0%, #8ff76a 26%, #2fe84f 58%, #0fbf3c 100%); }
`;

// ───────────────────────── runtime (timeline a partir dos data-at) ─────────────────────────
const RUNTIME = `
(function (ID, DUR) {
  // montada depois que as fontes carregam (o ajuste de tamanho e a caneta medem o texto); registra no fim
  var monta = function () {
  var R = document.getElementById("r-" + ID);
  var q = function (s) { return R.querySelectorAll(s); };
  var tl = gsap.timeline({ paused: true });
  var at = function (el) { return parseFloat(el.getAttribute("data-at")); };
  // frase de impacto: mede pela fonte (a cena pode estar oculta agora, então o layout ainda mede zero),
  // ajusta o tamanho, entra com headline-slam + soft-blur-in e a caneta circula a palavra-chave
  var cvm = document.createElement("canvas").getContext("2d");
  var larg = function (txt, px) { cvm.font = "700 " + px + "px Sora"; return cvm.measureText(txt).width; };
  q(".imp").forEach(function (el, n) {
    var t0 = at(el), lts = el.querySelectorAll(".lt"), px = parseFloat(el.style.fontSize), maior = 0;
    lts.forEach(function (lt) { maior = Math.max(maior, larg(lt.textContent.trim(), px)); });
    if (maior > 900) { px = Math.floor(px * 900 / maior); el.style.fontSize = px + "px"; }
    var alt = Math.round(px * 1.12);
    // caneta (cursor-annotate) circula a palavra-chave; o tempo cabe antes da batida sair
    var ph = el.closest(".phase"), saida = ph && ph.getAttribute("data-out") ? parseFloat(ph.getAttribute("data-out")) : DUR - 0.6;
    if (el.getAttribute("data-caneta")) el.querySelectorAll(".kw").forEach(function (kw, i) {
      var ini = t0 + 1.0 + i * 0.15;
      window.caAnotar(kw, { tl: tl, at: ini, budget: saida - 0.1 - ini, w: Math.round(larg(kw.textContent.trim(), px)), h: alt, color: "#FFFFFF", seed: n * 7 + i + 3 });
    });
    // headline-slam (registry): cada linha cai de 1,6× e pousa com expo.out; soft-blur-in (registry): desfocada até pousar
    lts.forEach(function (lt, i) {
      tl.fromTo(lt, { scale: 1.6, opacity: 0, filter: "blur(14px)" }, { scale: 1, opacity: 1, filter: "blur(0px)", duration: 0.5, ease: "expo.out" }, t0 + i * 0.14);
    });
    // pouso da última linha: tremor de 3 quadros (o "impacto" do headline-slam)
    var pouso = t0 + (lts.length - 1) * 0.14 + 0.22, Q = 1 / 30;
    tl.to(el, { x: 7, y: -4, duration: Q, ease: "power2.out" }, pouso);
    tl.to(el, { x: -5, y: 3, duration: Q, ease: "power2.out" }, pouso + Q);
    tl.to(el, { x: 0, y: 0, duration: Q, ease: "power2.out" }, pouso + 2 * Q);
    // a palavra-chave sai do branco para o gradiente verde → azul
    el.querySelectorAll(".g").forEach(function (g) { tl.fromTo(g, { "--branco": 1 }, { "--branco": 0, duration: 0.45, ease: "power1.inOut" }, pouso + 0.25); });
  });
  // variable-axis-type: a frase entra fina e "engorda" (expo.out); a palavra-chave vai mais longe e ganha a cor
  q(".vax").forEach(function (el) {
    var t0 = at(el), vpx = parseFloat(el.style.fontSize) || 92, vmaior = 0;
    // mede cada linha no peso final (800, o mais largo) e reduz o tamanho se precisar — o texto não re-quebra no meio
    el.querySelectorAll(".vl").forEach(function (vl) { cvm.font = '800 ' + vpx + 'px "Sora Var"'; vmaior = Math.max(vmaior, cvm.measureText(vl.textContent).width); });
    if (vmaior > 930) el.style.fontSize = Math.floor(vpx * 930 / vmaior) + "px";
    tl.fromTo(el, { fontWeight: 200 }, { fontWeight: 700, duration: 1.1, ease: "expo.out" }, t0 + 0.35);
    el.querySelectorAll(".g").forEach(function (g) {
      tl.fromTo(g, { fontWeight: 200, "--branco": 1 }, { fontWeight: 800, "--branco": 0, duration: 1.1, ease: "expo.out" }, t0 + 0.55);
    });
  });
  q(".phase").forEach(function (ph) {
    var t0 = parseFloat(ph.getAttribute("data-at")), out = ph.getAttribute("data-out"), slow = ph.getAttribute("data-slow") === "1";
    var bar = ph.querySelector(".accent");
    if (bar) tl.fromTo(bar, { scaleX: 0 }, { scaleX: 1, duration: 0.4, ease: "power3.out" }, t0);
    if (out) tl.to(ph, { opacity: 0, y: -24, duration: 0.32, ease: "power2.in" }, parseFloat(out));
    ph.querySelectorAll(".el").forEach(function (el) {
      if (el.getAttribute("data-noanim") === "1") return;
      tl.fromTo(el, { opacity: 0, y: slow ? 34 : 26 }, { opacity: 1, y: 0, duration: slow ? 0.8 : 0.45, ease: "power3.out" }, at(el));
    });
  });
  // tracking-in em todo título pequeno: as letras chegam afastadas e se aproximam até o espaçamento final, subindo de leve
  q(".kicker.hf-tracking-in").forEach(function (kk) {
    // trava as quebras de linha como ficam no espaçamento final: sem isso, o texto reflui enquanto o espaçamento diminui
    kk.style.setProperty("--hf-tracking-value", "0.16em");
    var pal = kk.textContent.split(" ").filter(Boolean), linhas = [], topo = null;
    kk.textContent = "";
    pal.forEach(function (w, i) { var s = document.createElement("span"); s.textContent = w; s.style.display = "inline"; kk.appendChild(s); if (i < pal.length - 1) kk.appendChild(document.createTextNode(" ")); });
    var spans = kk.querySelectorAll("span");
    spans.forEach(function (s, i) { if (s.offsetTop !== topo) { linhas.push([]); topo = s.offsetTop; } linhas[linhas.length - 1].push(pal[i]); });
    kk.textContent = "";
    var maxCh = 1, larg = 0;
    linhas.forEach(function (l) { var d = document.createElement("span"); d.style.cssText = "display:block;white-space:nowrap"; d.textContent = l.join(" "); kk.appendChild(d); maxCh = Math.max(maxCh, d.textContent.length); });
    for (var c = 0; c < kk.children.length; c++) larg = Math.max(larg, kk.children[c].getBoundingClientRect().width);
    var ini = Math.max(0.16, Math.min(0.6, 0.16 + (940 - larg) / (maxCh * parseFloat(getComputedStyle(kk).fontSize))));   // a linha mais larga nunca passa da tela
    tl.fromTo(kk, { opacity: 0, y: 10, "--hf-tracking-value": ini + "em" }, { opacity: 1, y: 0, "--hf-tracking-value": "0.16em", duration: 0.9, ease: "power3.out" }, kk.hasAttribute("data-at") ? at(kk) : 0.3);
  });
  q(".it").forEach(function (el) { tl.fromTo(el, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.4, ease: "power3.out" }, at(el)); });
  q(".cnt").forEach(function (el) {
    var to = parseFloat(el.getAttribute("data-to")), dec = parseInt(el.getAttribute("data-dec"), 10), pre = el.getAttribute("data-pre"), suf = el.getAttribute("data-suf");
    var o = { v: 0 };
    var fmt = function (v) { return pre + v.toLocaleString("pt-BR", { minimumFractionDigits: dec, maximumFractionDigits: dec }) + suf; };
    tl.to(o, { v: to, duration: 1.3, ease: "power2.out", onUpdate: function () { el.textContent = fmt(o.v); } }, at(el));
  });
  q(".line").forEach(function (el) { tl.fromTo(el, { scaleX: 0 }, { scaleX: 1, duration: 0.4, ease: "power2.inOut" }, at(el)); });
  q(".line").forEach(function (el) { var host = el.closest(".struck"); if (host) tl.to(host, { opacity: 0.55, duration: 0.3 }, at(el) + 0.3); });
  q(".fill").forEach(function (el) { tl.fromTo(el, { scaleX: 0 }, { scaleX: parseFloat(el.getAttribute("data-f")), duration: 1.0, ease: "power3.out" }, at(el)); });
  q(".dot").forEach(function (el) { tl.to(el, { backgroundColor: "#F6FAFE", duration: 0.25 }, at(el) + 0.3); });
  q(".conta").forEach(function (box) {
    var lines = box.querySelectorAll(".cl"), cw = box.querySelector(".cw");
    lines.forEach(function (ln, i) { if (i >= 3) tl.to(cw, { y: -70 * (i - 2), duration: 0.45, ease: "power3.out" }, at(ln) - 0.05); });
  });
  var fx = R.querySelector(".band").classList.contains("fx");
  q(".cta .btn").forEach(function (btn) {
    var t = at(btn.parentNode) + 0.2;
    tl.fromTo(btn, { scale: 0.85 }, { scale: 1, duration: 0.6, ease: "power3.out" }, t);
    if (fx) {
      // seta flutuando em seno até o fim + reflexo varrendo o botão de tempos em tempos
      var tri = btn.parentNode.querySelector(".tri"), sh = btn.querySelector(".shine");
      var reps = Math.max(1, Math.floor((DUR - 0.6 - (t + 0.8)) / 1.1));
      tl.fromTo(tri, { y: 0 }, { y: 24, duration: 1.1, ease: "sine.inOut", yoyo: true, repeat: reps }, t + 0.8);
      for (var k = t + 1.0; k < DUR - 1.2; k += 2.8) tl.fromTo(sh, { x: 0, xPercent: 0, skewX: -22 }, { x: 0, xPercent: 520, skewX: -22, duration: 0.8, ease: "power2.inOut" }, k);
      return;
    }
    var down = btn.parentNode.querySelector(".down");
    for (var k2 = 0; k2 < 3; k2++) tl.fromTo(down, { y: 0 }, { y: 14, duration: 0.35, ease: "power2.inOut", yoyo: true, repeat: 1 }, t + 1.2 + k2 * 1.4);
  });
  // ícones e logo: entram com mola (back.out) e flutuam em seno até o fim da cena
  q(".ico, .logo").forEach(function (el, i) {
    var t = at(el), img = el.querySelector("img"), logo = el.classList.contains("logo");
    tl.fromTo(el, { opacity: 0, scale: logo ? 0.82 : 0.55, y: logo ? 0 : 24 }, { opacity: 1, scale: 1, y: 0, duration: logo ? 0.8 : 0.6, ease: logo ? "back.out(1.6)" : "back.out(1.9)" }, t);
    var ini = t + 0.7, voltas = Math.max(0, Math.floor((DUR - 0.6 - ini) / 1.3));
    if (voltas > 0) tl.fromTo(img, { y: 0 }, { y: logo ? -6 : -9, duration: 1.3, ease: "sine.inOut", yoyo: true, repeat: voltas - 1 + (voltas % 2) }, ini + (i % 3) * 0.2);
  });
  // tipo 3D entra com um "pop"
  q(".xl").forEach(function (el) { tl.fromTo(el, { scale: 0.8 }, { scale: 1, duration: 0.75, ease: "back.out(1.8)" }, at(el)); });
  // poeira subindo: posição é função do tempo (determinística), desenhada a cada atualização da timeline
  q(".dust").forEach(function (cv) {
    var de = parseFloat(cv.getAttribute("data-de")), ate = parseFloat(cv.getAttribute("data-ate")), s = parseInt(cv.getAttribute("data-seed"), 10) >>> 0;
    var ctx = cv.getContext("2d"), Wc = cv.width, Hc = cv.height, L = Hc + 160;
    var rnd = function () { s = (s + 0x6D2B79F5) | 0; var r = Math.imul(s ^ (s >>> 15), 1 | s); r = (r + Math.imul(r ^ (r >>> 7), 61 | r)) ^ r; return ((r ^ (r >>> 14)) >>> 0) / 4294967296; };
    var P = [];
    for (var i = 0; i < 90; i++) { var big = rnd() < 0.25; P.push({ x: rnd() * Wc, y0: rnd() * L, v: big ? 28 + rnd() * 36 : 45 + rnd() * 80, r: big ? 5 + rnd() * 9 : 1.3 + rnd() * 2.2, big: big, ph: rnd() * 6.283, dr: (rnd() - 0.5) * 26, al: big ? 0.2 + rnd() * 0.2 : 0.55 + rnd() * 0.4 }); }
    var draw = function (t) {
      ctx.clearRect(0, 0, Wc, Hc);
      if (t <= de || t >= ate) return;
      var env = Math.min(1, (t - de) / 1.2, (ate - t) / 0.8);
      ctx.globalCompositeOperation = "lighter";
      for (var i = 0; i < P.length; i++) {
        var p = P[i];
        var y = Hc + 80 - ((p.y0 + p.v * (t - de)) % L);            // sobe e recomeça embaixo
        var x = p.x + Math.sin(p.ph + t * 0.6) * p.dr;
        var edge = Math.max(0, Math.min(1, y / 90, (Hc - 40 - y) / 160)); // some antes de chegar no cabelo do Hugo
        var A = p.al * env * edge * (0.65 + 0.35 * Math.sin(p.ph * 3 + t * 2.4));
        if (A < 0.01) continue;
        if (p.big) {
          var g = ctx.createRadialGradient(x, y, 0, x, y, p.r);
          g.addColorStop(0, "rgba(110,185,255," + A + ")"); g.addColorStop(1, "rgba(40,124,255,0)");
          ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, p.r, 0, 6.283); ctx.fill();
        } else {
          ctx.fillStyle = "rgba(90,200,255," + (A * 0.22) + ")"; ctx.beginPath(); ctx.arc(x, y, p.r * 3, 0, 6.283); ctx.fill();
          ctx.fillStyle = "rgba(205,240,255," + A + ")"; ctx.beginPath(); ctx.arc(x, y, p.r, 0, 6.283); ctx.fill();
        }
      }
    };
    var o = { t: 0 };
    tl.fromTo(o, { t: 0 }, { t: DUR, duration: DUR, ease: "none", onUpdate: function () { draw(o.t); } }, 0);
    draw(0);
  });
  tl.to(R.querySelector(".band"), { opacity: 0, y: -24, duration: 0.45, ease: "power2.in" }, DUR - 0.55);
  window.__timelines[ID] = tl;
  };
  // carrega explicitamente as fontes medidas (cenas ocultas não disparam o download sozinhas)
  if (document.fonts && document.fonts.load) Promise.all([document.fonts.load("700 100px Sora"), document.fonts.load('200 100px "Sora Var"'), document.fonts.load('800 100px "Plus Jakarta Sans"')]).then(function () { return document.fonts.ready; }).then(monta, monta);
  else monta();
})(__ID__, __DUR__);
`;

function sceneFile(s) {
  const phases = s.fases.map((ph, pi) => {
    const next = s.fases[pi + 1];
    let t = ph.at;
    const els = ph.els.map((e, ei) => {
      const at = ph.at + (e.d != null ? e.d : ei * 0.15);
      t = Math.max(t, at);
      return elHTML(e, at);
    }).join("\n          ");
    const out = next ? ` data-out="${(next.at - 0.35).toFixed(2)}"` : "";
    return `<div class="phase${s.topo ? " sob" : ""}" data-at="${ph.at}"${out}${ph.slow ? ' data-slow="1"' : ""}>
          ${s.topo || s.barra === false ? "" : '<i class="accent"></i>'}
          ${els}
        </div>`;
  }).join("\n        ");
  const id = `cena-${s.id.toLowerCase()}`;
  return `<!doctype html>
<html lang="pt-BR">
  <head><meta charset="UTF-8" /></head>
  <body>
    <template>
      <link rel="stylesheet" href="assets/tokens.css" />
      <style>${CSS.replace("__ROOT__", "#r-" + id)}</style>
      <!-- ${s.id} · ${esc(s.nome)} · ${s.dur} s — gerado por build.mjs a partir de plano-de-cenas.md -->
      <div id="r-${id}" data-composition-id="${id}" data-width="${W}" data-height="${H}">
        <div class="band${s.fx === false ? "" : " fx"}">
        ${s.poeira ? `<canvas class="dust" width="${W}" height="600" data-de="${s.poeira[0]}" data-ate="${s.poeira[1]}" data-seed="${[...s.id].reduce((h, ch) => (h * 31 + ch.charCodeAt(0)) >>> 0, 7)}"></canvas>` : ""}
        ${s.topo ? `<div class="topo"><i class="accent"></i><div class="kicker hf-tracking-in">${esc(s.topo)}</div></div>` : ""}
        ${phases}
        </div>
      </div>
      <script>${RUNTIME.replace("__ID__", JSON.stringify(id)).replace("__DUR__", String(s.dur))}</script>
    </template>
  </body>
</html>
`;
}

// ───────────────────────── reel (index.html) e lista ─────────────────────────
fs.mkdirSync(path.join(pasta, "compositions"), { recursive: true });
for (const f of fs.readdirSync(path.join(pasta, "compositions"))) if (f.startsWith("cena-")) fs.unlinkSync(path.join(pasta, "compositions", f));
let t = 0;
const hosts = [], tags = [], lista = [];
const SO = so;   // só essas cenas no reel (render por partes / teste)
for (const s of cenas) {
  const id = `cena-${s.id.toLowerCase()}`;
  fs.writeFileSync(path.join(pasta, "compositions", `${id}.html`), sceneFile(s));
  if (SO && !SO.includes(s.id)) continue;
  hosts.push(`      <div id="h-${id}" data-composition-id="${id}" data-composition-src="compositions/${id}.html" data-start="${t.toFixed(2)}" data-duration="${s.dur}" data-track-index="1" data-width="${W}" data-height="${H}"></div>`);
  tags.push(`      <div id="tag-${id}" class="tag clip" data-start="${t.toFixed(2)}" data-duration="${s.dur}" data-track-index="2">${s.id} · ${esc(s.nome)}</div>`);
  lista.push({ id: s.id, nome: s.nome, inicio: +t.toFixed(2), dur: s.dur });
  t += s.dur + GAP;
}
const total = +(t - GAP).toFixed(2);
fs.writeFileSync(path.join(pasta, "index.html"), `<!doctype html>
<html lang="pt-BR" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=${W}, height=${H}" />
    <script src="vendor/gsap.min.js"></script>
    <!-- efeito do registry adaptado (cursor-annotate) — ver fx/ -->
    <script src="fx/hw-pen.js"></script>
    <link rel="stylesheet" href="assets/tokens.css" />
    <style>
      html, body { margin: 0; width: ${W}px; height: ${H}px; overflow: hidden; background: transparent; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; }
      #fundo { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
      .tag { position: absolute; left: 24px; bottom: 24px; font: 600 24px var(--font-body); color: rgba(255,255,255,.7); background: rgba(0,0,0,.45); padding: 6px 12px; border-radius: 6px; }
    </style>
  </head>
  <body>
    <!-- Reel de revisão: as ${cenas.length} cenas em sequência sobre o quadro de referência do Hugo.
         Trilha 0 = referência (só revisão) · Trilha 1 = cenas · Trilha 2 = etiquetas (só revisão) -->
    <div id="root" data-composition-id="main" data-start="0" data-duration="${total}" data-width="${W}" data-height="${H}">
      <img id="fundo" class="clip" src="referencia-enquadramento.png" data-start="0" data-duration="${total}" data-track-index="0" alt="" />
${hosts.join("\n")}
${tags.join("\n")}
    </div>
    <script>window.__timelines["main"] = gsap.timeline({ paused: true });</script>
  </body>
</html>
`);
fs.writeFileSync(path.join(pasta, SO ? "cenas-teste.json" : "cenas.json"), JSON.stringify({ total, cenas: lista }, null, 1));
return { total, lista };

}
