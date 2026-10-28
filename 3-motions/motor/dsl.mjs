// Linguagem do plano de cenas → cenas do motor (e o caminho de volta, para migrar build.mjs antigos).
//
//   ## Bloco 05 · Luan
//   - **B05H** · Quase R$ 5 mil com 1 impressora — "o Luan achou um produto com potencial"
//     duração: 7 · poeira: 0-7                       ← opções da cena (poeira, barra: não, fx: não)
//     topo: O PRODUTO QUE O LUAN ACHOU               ← título fixo no alto; as batidas viram frases de impacto
//     > 0.3 | kicker: O PRODUTO QUE O LUAN ACHOU | número: R$ 5 mil [verde, conta] | legenda: quase isso, com 1 impressora
//     > 3.6 lenta | frase: Ninguém compra de **loja sem estrela**
//     tela: anotações livres para quem revisa         ← qualquer outra linha recuada é ignorada
//
// Batida: "> [segundo] [lenta] | peça | peça ...". Sem o segundo, as batidas se distribuem sozinhas pela duração.
// Peça: "tipo: texto [opções]". **palavra** = destaque em gradiente.
//   kicker · título · frase (peso variável) · número · legenda · ícone · ícones · logo · cta · chips · json
//   opções: tamanho=grande|médio|pequeno · largo · risca=1.4 · px=110 · atraso=0.4 · verde · negativo · gradiente
//           conta (ou conta=5, antes="R$ ", depois=" mil", dec=1) · altura=150 · passo=0.25 · largura=940
//           chips: check · setas · colunas=2 · apagado

const TAM = { grande: "lg", "médio": "md", medio: "md", pequeno: "sm", lg: "lg", md: "md", sm: "sm" };
const TAM_INV = { lg: "grande", md: "médio", sm: "pequeno" };
const CENA = /^\s*[-*]\s*\*\*\s*([A-Z]{1,3}\d+[A-Z]*\d*)\s*(?:·\s*([^*]*?))?\s*\*\*\s*(?:·\s*(.*?))?\s*[—–-]{1,2}\s*["“](.+?)["”]\s*$/;
const BLOCO = /^#{2,3}\s*(?:Bloco|BLOCO|Lead|LEAD)\s+([0-9A-Z]+)\s*(?:·\s*(.*))?$/;

export const tamanhoAuto = (txt) => (txt.replace(/\*\*/g, "").length <= 13 ? "lg" : "md");   // TT() do motor

// "R$ 5 mil" → { to: 5, prefix: "R$ ", suffix: " mil" } · "47.500" → { to: 47500 } · "1,5 mil" → dec 1
export function contaDoTexto(txt) {
  const m = txt.match(/^(\D*?)(\d[\d.]*(?:,\d+)?)(.*)$/);
  if (!m) return null;
  const [, pre, num, suf] = m;
  const dec = num.includes(",") ? num.split(",")[1].length : 0;
  const to = Number(num.replace(/\./g, "").replace(",", "."));
  const c = { to };
  if (pre) c.prefix = pre;
  if (suf) c.suffix = suf;
  if (dec) c.dec = dec;
  return c;
}

function opcoes(str) {
  const o = {};
  const re = /\s*([\wáéíóúâêôãõç-]+)(?:\s*=\s*("(?:[^"\\]|\\.)*"|[^,\]]+))?\s*(?:,|$)/gy;
  let m;
  while ((m = re.exec(str)) && m[0]) {
    let v = m[2] === undefined ? true : m[2].trim();
    if (typeof v === "string" && v.startsWith('"')) v = JSON.parse(v);
    else if (typeof v === "string" && /^-?\d+(\.\d+)?$/.test(v)) v = Number(v);
    o[m[1].toLowerCase()] = v;
  }
  return o;
}

function peca(token, erros, onde) {
  const m = token.match(/^\s*([\wáéíóúâêôãõç-]+)\s*(?::\s*(.*?))?\s*(?:\[(.*)\])?\s*$/);
  if (!m) { erros.push(`${onde}: peça ilegível "${token}"`); return null; }
  const tipo = m[1].toLowerCase(), txt = (m[2] || "").replace(/\\\|/g, "|"), o = opcoes(m[3] || "");
  const d = o.atraso !== undefined ? { d: o.atraso } : {};
  switch (tipo) {
    case "kicker": return { k: "kicker", text: txt, ...d };
    case "legenda": return { k: "label", text: txt, ...d };
    case "cta": return { k: "cta", text: txt, ...d };
    case "título": case "titulo": {
      const e = { k: "title", text: txt, size: o.tamanho ? TAM[o.tamanho] : tamanhoAuto(txt), ...d };
      if (o.largo) e.wide = true;
      if (o.risca !== undefined) e.strikeAt = o.risca;
      if (!e.size) erros.push(`${onde}: tamanho "${o.tamanho}" não existe (grande, médio, pequeno)`);
      return e;
    }
    case "frase": {
      const e = { k: "title", text: txt, vax: true, ...d };
      if (o.px !== undefined) e.vpx = o.px;
      return e;
    }
    case "número": case "numero": {
      const e = { k: "num", text: txt, ...d };
      if (o.tamanho) e.size = TAM[o.tamanho];
      if (o.verde) e.lime = true;
      if (o.negativo) e.neg = true;
      if (o.gradiente) e.grad = true;
      if (o.conta !== undefined) {
        const c = o.conta === true ? contaDoTexto(txt) : { to: o.conta };
        if (!c) erros.push(`${onde}: não sei contar "${txt}" (use conta=NÚMERO)`);
        else {
          if (o.antes !== undefined) c.prefix = o.antes;
          if (o.depois !== undefined) c.suffix = o.depois;
          if (o.dec !== undefined) c.dec = o.dec;
          e.count = c;
        }
      }
      return e;
    }
    case "ícone": case "icone": {
      const e = { k: "ico", nome: txt, ...d };
      if (o.altura !== undefined) e.h = o.altura;
      return e;
    }
    case "ícones": case "icones": {
      const e = { k: "icos", nomes: txt.split(",").map((s) => s.trim()).filter(Boolean), ...d };
      if (o.altura !== undefined) e.h = o.altura;
      if (o.passo !== undefined) e.step = o.passo;
      return e;
    }
    case "logo": {
      const e = { k: "logo", ...d };
      if (o.largura !== undefined) e.w = o.largura;
      return e;
    }
    case "chips": {
      const e = { k: "chips", items: txt.split(";").map((s) => s.trim()).filter(Boolean), ...d };
      if (o.passo !== undefined) e.step = o.passo;
      if (o.check) e.check = true;
      if (o.setas) e.arrows = true;
      if (o.colunas !== undefined) e.cols = o.colunas;
      if (o.risca !== undefined) e.strikeAt = o.risca;
      if (o.apagado) e.dim = true;
      return e;
    }
    case "json": try { return JSON.parse(txt); } catch { erros.push(`${onde}: json inválido`); return null; }
  }
  erros.push(`${onde}: tipo de peça desconhecido "${tipo}"`);
  return null;
}

function dividir(linha) {                                  // separa por " | " (aceita "\|" dentro do texto)
  return linha.split(/(?<!\\)\|/).map((s) => s.trim()).filter((s) => s.length);
}

function distribuir(cena) {                                // batidas sem segundo: espalha pela duração
  const t0 = cena.topo ? 0.6 : 0.3, n = cena.fases.length;
  const passo = n > 1 ? Math.min(3.4, Math.max(1.6, (cena.dur - t0 - 2.2) / (n - 1))) : 0;
  cena.fases.forEach((f, i) => { if (f.at === undefined) f.at = +(t0 + i * passo).toFixed(2); });
}

// → { cenas: [{ id, nome, gatilho, bloco, linha, cena|null }], erros }
export function lerPlano(texto) {
  const cenas = [], erros = [];
  let bloco = null, blocoTitulo = "", atual = null;
  texto.split(/\r?\n/).forEach((linha, k) => {
    const onde = `linha ${k + 1}`;
    const b = linha.match(BLOCO);
    if (b) { bloco = b[1].replace(/^0+(?=\d)/, ""); blocoTitulo = (b[2] || "").trim(); atual = null; return; }
    const c = linha.match(CENA);
    if (c) {
      atual = { id: c[1], nome: (c[2] || c[3] || "").trim().replace(/^·\s*/, ""), gatilho: c[4].trim(), bloco, blocoTitulo, linha: k + 1,
                cena: { id: c[1], nome: (c[2] || c[3] || "").trim(), fases: [] } };
      cenas.push(atual);
      return;
    }
    if (!atual || !/^\s+\S/.test(linha)) { if (/^\S/.test(linha)) atual = null; return; }
    const l = linha.trim();
    if (/^topo\s*:/i.test(l)) { atual.cena.topo = l.replace(/^topo\s*:\s*/i, ""); return; }
    if (/^dura[çc][ãa]o\s*:/i.test(l)) {
      for (const par of l.split(/\s+·\s+/)) {
        const [chave, ...resto] = par.split(":");
        const v = resto.join(":").trim(), k2 = chave.trim().toLowerCase();
        if (/^dura/.test(k2)) atual.cena.dur = Number(v.replace(/\s*s$/, "").replace(",", "."));
        else if (k2 === "poeira") { const [a, z] = v.split("-").map(Number); atual.cena.poeira = [a, z]; }
        else if (k2 === "barra" && /^n[ãa]o$/i.test(v)) atual.cena.barra = false;
        else if (k2 === "fx" && /^n[ãa]o$/i.test(v)) atual.cena.fx = false;
        else erros.push(`${onde}: opção de cena desconhecida "${par}"`);
      }
      return;
    }
    if (l.startsWith(">")) {
      const partes = dividir(l.slice(1));
      const fase = { els: [] };
      let cab = partes[0] || "";
      const mt = cab.match(/^(\d+(?:[.,]\d+)?)?\s*(lenta)?\s*$/i);
      if (mt) {                                           // "0.3", "3.8 lenta" ou só "lenta"
        if (mt[1]) fase.at = Number(mt[1].replace(",", "."));
        if (mt[2]) fase.slow = true;
        partes.shift();
      }
      for (const p of partes) { const e = peca(p, erros, `${onde} (${atual.id})`); if (e) fase.els.push(e); }
      atual.cena.fases.push(fase);
    }
  });
  for (const c of cenas) {
    if (!c.cena.fases.length) { c.cena = null; continue; }       // cena só com gatilho: serve para encaixe, não para gerar
    if (!c.cena.dur) erros.push(`linha ${c.linha}: ${c.id} sem "duração:"`);
    distribuir(c.cena);
    if (c.cena.fases.some((f, i, a) => i && f.at <= a[i - 1].at)) erros.push(`linha ${c.linha}: ${c.id} tem batidas fora de ordem`);
    if (c.cena.fases.some((f) => f.at >= c.cena.dur)) erros.push(`linha ${c.linha}: ${c.id} tem batida depois do fim (${c.cena.dur} s)`);
  }
  return { cenas, erros };
}

// ───── caminho de volta: cena do motor → linhas do plano (migração de build.mjs) ─────
const q = (s) => JSON.stringify(s);
function opcStr(pares) { return pares.length ? ` [${pares.join(", ")}]` : ""; }

function pecaStr(e) {
  const d = e.d !== undefined ? [`atraso=${e.d}`] : [];
  const esc = (t) => String(t).replace(/\|/g, "\\|");
  switch (e.k) {
    case "kicker": return `kicker: ${esc(e.text)}${opcStr(d)}`;
    case "label": return `legenda: ${esc(e.text)}${opcStr(d)}`;
    case "cta": return `cta: ${esc(e.text)}${opcStr(d)}`;
    case "title": {
      if (e.vax) return `frase: ${esc(e.text)}${opcStr([...(e.vpx !== undefined ? [`px=${e.vpx}`] : []), ...d])}`;
      const o = [];
      if ((e.size || "md") !== tamanhoAuto(e.text)) o.push(`tamanho=${TAM_INV[e.size || "md"]}`);
      if (e.wide) o.push("largo");
      if (e.strikeAt !== undefined) o.push(`risca=${e.strikeAt}`);
      return `título: ${esc(e.text)}${opcStr([...o, ...d])}`;
    }
    case "num": {
      const o = [];
      if (e.size) o.push(`tamanho=${TAM_INV[e.size]}`);
      if (e.lime) o.push("verde");
      if (e.neg) o.push("negativo");
      if (e.grad) o.push("gradiente");
      if (e.count) {
        const auto = contaDoTexto(e.text);
        if (auto && JSON.stringify(auto) === JSON.stringify(e.count)) o.push("conta");
        else {
          o.push(`conta=${e.count.to}`);
          if (e.count.prefix) o.push(`antes=${q(e.count.prefix)}`);
          if (e.count.suffix) o.push(`depois=${q(e.count.suffix)}`);
          if (e.count.dec) o.push(`dec=${e.count.dec}`);
        }
      }
      return `número: ${esc(e.text)}${opcStr([...o, ...d])}`;
    }
    case "ico": return `ícone: ${e.nome}${opcStr([...(e.h !== undefined ? [`altura=${e.h}`] : []), ...d])}`;
    case "icos": return `ícones: ${e.nomes.join(", ")}${opcStr([...(e.h !== undefined ? [`altura=${e.h}`] : []), ...(e.step !== undefined ? [`passo=${e.step}`] : []), ...d])}`;
    case "logo": return `logo${opcStr([...(e.w !== undefined ? [`largura=${e.w}`] : []), ...d])}`;
  }
  return `json: ${JSON.stringify(e)}`;
}

export function cenaParaLinhas(cena) {
  const out = [];
  const op = [`duração: ${cena.dur}`];
  if (cena.poeira) op.push(`poeira: ${cena.poeira[0]}-${cena.poeira[1]}`);
  if (cena.barra === false) op.push("barra: não");
  if (cena.fx === false) op.push("fx: não");
  out.push("  " + op.join(" · "));
  if (cena.topo) out.push(`  topo: ${cena.topo}`);
  for (const f of cena.fases) out.push(`  > ${f.at}${f.slow ? " lenta" : ""} | ${f.els.map(pecaStr).join(" | ")}`);
  return out;
}
