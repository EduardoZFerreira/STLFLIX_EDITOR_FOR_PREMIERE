#!/usr/bin/env node
// Motions STLFLIX 9:16: do plano-de-cenas.md aos .mov transparentes (HyperFrames).
//
//   node 3-motions/motions.mjs validar --projeto <VSL> [--plano corpo]
//   node 3-motions/motions.mjs gerar   --projeto <VSL> [--plano corpo]          → pasta de trabalho do HyperFrames
//   node 3-motions/motions.mjs previa  --projeto <VSL> [--plano corpo]          → abre o Studio do HyperFrames
//   node 3-motions/motions.mjs render  --projeto <VSL> [--plano corpo] [--so B05H,B05I] [--por-parte 30]
//   node 3-motions/motions.mjs render  --projeto <VSL> [--plano corpo] --pendentes         → só as que faltam ou mudaram no plano
//   node 3-motions/motions.mjs validar --projeto <VSL> --arquivo 04-plano-de-cenas/rascunho-corpo.md   → qualquer comando com um plano avulso
//   node 3-motions/motions.mjs estado  --projeto <VSL>                                 → JSON de cada cena: pronto, falta, mudou (usado pelo painel)
//   (o modelo visual vem de motions.modelo no config.json; padrão "shark-vsl" → 3-motions/modelos/shark-vsl)
//   node 3-motions/motions.mjs migrar  --build <build.mjs antigo> --gatilhos <plano com frases> --saida <plano.md>
//
// O render sai em <projeto>/<pastas.motions> (um .mov por cena + LEIAME.txt) e a prévia sobre o quadro de
// referência em <pasta de trabalho>/renders/previa-cenas.mp4.
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";
import { lerPlano, cenaParaLinhas } from "./motor/dsl.mjs";

const KIT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DS = path.join(KIT, "2-design-system");
const PADRAO = { modelo: "shark-vsl", campanha: "bf26", faixa: { top: 130, height: 430, side: 64 }, referencia: "", hyperframes: "0.8.176" };

function args() {
  const [cmd, ...r] = process.argv.slice(2);
  const o = { cmd };
  for (let i = 0; i < r.length; i++) if (r[i].startsWith("--")) o[r[i].slice(2)] = r[i + 1] && !r[i + 1].startsWith("--") ? r[++i] : true;
  return o;
}

// --projeto aceita a pasta da VSL ou só o nome dela: as VSLs ficam onde o editor quiser e o kit anota o caminho
// em %LOCALAPPDATA%\STLFLIX_EDITOR\vsls.json (a mesma lista do stlflix, em 4-filmcraft/stlflix/vsls.py).
function resolverVsl(arg) {
  if (fs.existsSync(path.join(arg, "config.json"))) return arg;
  const lista = path.join(process.env.LOCALAPPDATA || os.homedir(), "STLFLIX_EDITOR", "vsls.json");
  let anotadas = [];
  try { anotadas = JSON.parse(fs.readFileSync(lista, "utf8")); } catch {}
  const dentro = path.join(KIT, "projetos");
  const doKit = fs.existsSync(dentro) ? fs.readdirSync(dentro).filter((n) => !/^[_.]/.test(n)).map((n) => path.join(dentro, n)) : [];
  const nome = path.basename(path.normalize(arg.trim())).toLowerCase();
  const achadas = [...new Set([...anotadas, ...doKit].map((p) => path.resolve(p)))]
    .filter((p) => path.basename(p).toLowerCase() === nome && fs.existsSync(path.join(p, "config.json")));
  if (achadas.length === 1) return achadas[0];
  if (achadas.length > 1) throw new Error(`há ${achadas.length} VSLs chamadas "${arg}": use o caminho (${achadas.join("; ")})`);
  throw new Error(`não achei a VSL "${arg}": use o caminho da pasta`);
}

function projeto(pasta) {
  const p = path.resolve(pasta), arq = path.join(p, "config.json");
  if (!fs.existsSync(arq)) throw new Error(`não achei ${arq}: copie projetos/_MODELO-VSL e preencha o config.json`);
  const cfg = JSON.parse(fs.readFileSync(arq, "utf8"));
  const cam = (rel) => (path.isAbsolute(rel) ? rel : path.join(p, rel));
  const mv = { ...PADRAO, ...(cfg.motions || {}) };
  mv.faixa = { ...PADRAO.faixa, ...(mv.faixa || {}) };
  return { pasta: p, cfg, cam, mv };
}

function planoDe(proj, chave) {
  const pl = proj.cfg.plano_de_cenas || "04-plano-de-cenas/plano-de-cenas.md";
  if (typeof pl === "string") return { chave: chave || "corpo", arquivo: proj.cam(pl) };
  const k = chave || Object.keys(pl)[0];
  if (!pl[k]) throw new Error(`sem plano "${k}" em plano_de_cenas (tem: ${Object.keys(pl).join(", ")})`);
  return { chave: k, arquivo: proj.cam(pl[k]) };
}

// ───── o que já foi renderizado ─────
// <pasta de motions>/.registro-render.json guarda a impressão de cada cena no momento do render: se o editor muda a
// descrição no plano depois, a impressão muda e a cena aparece como "mudou" (o nome e a frase-gatilho não contam).
const REGISTRO = ".registro-render.json";
const pastaMotions = (proj) => proj.cam((proj.cfg.pastas || {}).motions || "05-motions");

function impressao(proj, cena) {
  const { id, nome, ...visual } = cena;
  return crypto.createHash("sha1").update(JSON.stringify([visual, proj.mv.modelo, proj.mv.campanha, proj.mv.faixa])).digest("hex").slice(0, 12);
}

function lerRegistro(proj) {
  try { return JSON.parse(fs.readFileSync(path.join(pastaMotions(proj), REGISTRO), "utf8")); } catch { return {}; }
}

function movsDaPasta(pasta) {                 // código → arquivo, como o arquivos_motion do stlflix (pastas "_…" são backup)
  const out = {};
  const andar = (d) => {
    if (!fs.existsSync(d)) return;
    const itens = fs.readdirSync(d, { withFileTypes: true });
    for (const e of itens) if (e.isFile() && /\.mov$/i.test(e.name)) { const id = e.name.split("-")[0].split(".")[0]; if (!(id in out)) out[id] = path.join(d, e.name); }
    for (const e of itens) if (e.isDirectory() && !e.name.startsWith("_")) andar(path.join(d, e.name));
  };
  andar(pasta);
  return out;
}

function situacao(proj, todas) {
  const movs = movsDaPasta(pastaMotions(proj)), reg = lerRegistro(proj);
  return todas.map((c) => {
    const imp = c.cena ? impressao(proj, c.cena) : null;
    const estado = !c.cena ? "so-encaixe" : !movs[c.id] ? "falta" : reg[c.id] && reg[c.id].impressao !== imp ? "mudou" : "pronto";
    return { c, estado, mov: movs[c.id] || null };
  });
}

function estado(proj) {
  const pl = proj.cfg.plano_de_cenas || "04-plano-de-cenas/plano-de-cenas.md";
  const planos = (typeof pl === "string" ? [null] : Object.keys(pl)).map((k) => {
    const { chave, arquivo } = planoDe(proj, k);
    if (!fs.existsSync(arquivo)) return { chave, arquivo, existe: false, erros: [], cenas: [] };
    const { todas, erros } = cenasDoPlano(arquivo);
    erros.push(...iconesQueFaltam(proj, todas));
    return { chave, arquivo, existe: true, erros, cenas: situacao(proj, todas).map(({ c, estado, mov }) => ({
      id: c.id, nome: c.nome, gatilho: c.gatilho, bloco: c.bloco, blocoTitulo: c.blocoTitulo, estado, mov,
      linhas: c.cena ? cenaParaLinhas(c.cena).map((l) => l.trim()) : [] })) };
  });
  process.stdout.write(JSON.stringify({ planos, pasta: pastaMotions(proj) }));
}

function iconesQueFaltam(proj, todas) {      // ícone com nome errado sai como imagem quebrada no motion, sem aviso
  const pasta = path.join(DS, "campanhas", proj.mv.campanha);
  const tem = fs.existsSync(pasta) ? fs.readdirSync(pasta).filter((n) => n.endsWith(".png")).map((n) => n.slice(0, -4)) : [];
  const erros = [];
  for (const c of todas) for (const f of (c.cena ? c.cena.fases : [])) for (const e of f.els) {
    for (const nome of e.k === "ico" ? [e.nome] : e.k === "icos" ? e.nomes : []) {
      if (!tem.includes(nome)) erros.push(`linha ${c.linha}: ${c.id} usa o ícone "${nome}", que não existe na campanha ${proj.mv.campanha} (tem: ${tem.filter((n) => n !== "logo-kv").join(", ")})`);
    }
  }
  return erros;
}

function cenasDoPlano(arquivo) {
  if (!fs.existsSync(arquivo)) throw new Error(`ainda não existe o plano de cenas: ${arquivo} (tem um exemplo na mesma pasta)`);
  const { cenas, erros } = lerPlano(fs.readFileSync(arquivo, "utf8"));
  const geraveis = cenas.filter((c) => c.cena).map((c) => c.cena);
  return { todas: cenas, geraveis, erros };
}

function ligar(destino, alvo) {                       // junção no Windows (não precisa de admin), symlink nos outros
  if (fs.existsSync(destino)) return;
  fs.symlinkSync(alvo, destino, process.platform === "win32" ? "junction" : "dir");
}

function pastaDeTrabalho(proj, chave) {
  const w = path.join(proj.pasta, "motions-hf", chave);
  fs.mkdirSync(w, { recursive: true });
  ligar(path.join(w, "assets"), path.join(DS, "STLFLIX"));
  ligar(path.join(w, "vendor"), path.join(DS, "vendor", "gsap", "3.14.2"));
  ligar(path.join(w, "fx"), path.join(DS, "fx"));
  ligar(path.join(w, proj.mv.campanha), path.join(DS, "campanhas", proj.mv.campanha));
  const ver = proj.mv.hyperframes;
  fs.writeFileSync(path.join(w, "package.json"), JSON.stringify({ name: `motions-${chave}`, private: true, type: "module",
    scripts: { dev: `npx --yes hyperframes@${ver} preview`, render: `npx --yes hyperframes@${ver} render` } }, null, 2));
  fs.writeFileSync(path.join(w, "hyperframes.json"), JSON.stringify({ $schema: "https://hyperframes.heygen.com/schema/hyperframes.json",
    paths: { blocks: "compositions", components: "compositions/components", assets: "assets" }, media: { autoProxy: true } }, null, 2));
  fs.writeFileSync(path.join(w, "meta.json"), JSON.stringify({ id: `motions-${chave}`, name: `motions-${chave}` }));
  const ref = path.join(w, "referencia-enquadramento.png");
  const fonte = proj.mv.referencia ? proj.cam(proj.mv.referencia) : "";
  if (fonte && fs.existsSync(fonte)) fs.copyFileSync(fonte, ref);
  else if (!fs.existsSync(ref)) {                      // sem quadro do apresentador: fundo cinza só para a prévia
    spawnSync("ffmpeg", ["-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x2a2d36:s=1080x1920", "-frames:v", "1", ref]);
  }
  return w;
}

const slug = (s) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 48);

function sh(cmd, argv, opts = {}) {
  if (process.platform === "win32" && cmd === "npx") { argv = ["/d", "/s", "/c", "npx", ...argv]; cmd = "cmd"; }   // npx é .cmd no Windows
  const r = spawnSync(cmd, argv, { stdio: opts.log ? ["ignore", fs.openSync(opts.log, "w"), fs.openSync(opts.log, "a")] : "inherit",
    cwd: opts.cwd });
  if (r.status !== 0) throw new Error(`${cmd} ${argv.slice(0, 3).join(" ")} falhou${opts.log ? ` (ver ${opts.log})` : ""}`);
}

async function carregarModelo(nome) {          // cada modelo visual é uma pasta em 3-motions/modelos/<nome>/motor.mjs
  const arq = path.join(KIT, "3-motions", "modelos", nome, "motor.mjs");
  if (!fs.existsSync(arq)) throw new Error(`modelo "${nome}" não existe (há: ${fs.readdirSync(path.join(KIT, "3-motions", "modelos")).join(", ")})`);
  return (await import(pathToFileURL(arq).href)).construir;
}

function render(construir, proj, chave, cenas, { so, porParte = 30 }) {
  const w = pastaDeTrabalho(proj, chave);
  const alvo = so ? cenas.filter((c) => so.includes(c.id)) : cenas;
  if (!alvo.length) throw new Error("nenhuma cena para renderizar");
  const imps = new Map(cenas.map((c) => [c.id, impressao(proj, c)]));   // antes do motor, que pode mexer nas cenas
  const R = path.join(w, "renders"), partes = path.join(R, "partes"), saidaCenas = path.join(R, "cenas");
  for (const d of [partes, saidaCenas]) fs.mkdirSync(d, { recursive: true });
  const fonte = path.join(R, "_fonte-etiqueta.ttf");     // Arial Bold do Windows (licença não permite pôr no kit)
  if (!fs.existsSync(fonte) && fs.existsSync("C:/Windows/Fonts/arialbd.ttf")) fs.copyFileSync("C:/Windows/Fonts/arialbd.ttf", fonte);
  const ver = proj.mv.hyperframes, opt = { pasta: w, faixa: proj.mv.faixa, campanha: proj.mv.campanha };
  const previas = [], feitos = [];
  for (let i = 0, k = 1; i < alvo.length; i += porParte, k++) {
    const grupo = alvo.slice(i, i + porParte).map((c) => c.id);
    console.log(`parte ${k}: ${grupo.length} cenas (${grupo[0]}…${grupo[grupo.length - 1]})`);
    const { lista } = construir(cenas, { ...opt, so: grupo });
    let idx = fs.readFileSync(path.join(w, "index.html"), "utf8");      // reel transparente: sem referência nem etiquetas
    idx = idx.replace('<img id="fundo" class="clip"', '<img id="fundo" data-hidden class="clip"').replaceAll('class="tag clip"', 'data-hidden class="tag clip"');
    fs.writeFileSync(path.join(w, "index.html"), idx);
    const parte = path.join(partes, `parte-${k}.mov`);
    sh("npx", ["--yes", `hyperframes@${ver}`, "render", "--format", "mov", "-o", parte], { cwd: w, log: path.join(R, `render-parte-${k}.log`) });
    for (const s of lista) {                                             // ProRes é intra-frame: -c copy corta exato no quadro
      const nome = `${s.id}-${slug(s.nome)}.mov`;
      sh("ffmpeg", ["-v", "error", "-y", "-ss", String(s.inicio), "-i", parte, "-t", String(s.dur), "-c", "copy", path.join(saidaCenas, nome)]);
      feitos.push({ ...s, arquivo: nome });
    }
    const filtro = path.join(partes, `previa-filtro-${k}.txt`);
    const dt = lista.map((s) => `drawtext=fontfile='renders/_fonte-etiqueta.ttf':text='${s.id}':x=40:y=h-90:fontsize=40:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=12:enable='between(t,${s.inicio},${(s.inicio + s.dur).toFixed(2)})'`).join(",\n");
    fs.writeFileSync(filtro, "[0:v]scale=1080:1920,setsar=1[bg];\n[bg][1:v]overlay=format=auto:shortest=1,\n" + dt + ",\nformat=yuv420p[v]\n");
    const previa = path.join(partes, `previa-${k}.mp4`);
    sh("ffmpeg", ["-v", "error", "-y", "-loop", "1", "-framerate", "30", "-i", "referencia-enquadramento.png", "-i", parte,
      "-/filter_complex", filtro, "-map", "[v]", "-c:v", "libx264", "-crf", "21", "-preset", "medium", "-movflags", "+faststart", previa], { cwd: w });
    previas.push(previa);
    fs.rmSync(parte);
  }
  construir(cenas, opt);                                                 // devolve o index.html de revisão completo
  fs.rmSync(path.join(w, "cenas-teste.json"), { force: true });
  const lst = path.join(partes, "previas.txt");
  fs.writeFileSync(lst, previas.map((p) => `file '${p.replace(/\\/g, "/")}'`).join("\n"));
  sh("ffmpeg", ["-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", path.join(R, "previa-cenas.mp4")]);
  for (const p of previas) fs.rmSync(p);
  // entrega: .mov na pasta de motions do projeto + LEIAME. A versão anterior de cada cena não é sobrescrita:
  // vai para "_motions anteriores (dd-mm HHhMM)", e o registro guarda a impressão do que foi renderizado agora.
  const destino = pastaMotions(proj);
  fs.mkdirSync(destino, { recursive: true });
  const agora = new Date(), dd = (n) => String(n).padStart(2, "0");
  const backup = path.join(destino, `_motions anteriores (${dd(agora.getDate())}-${dd(agora.getMonth() + 1)} ${dd(agora.getHours())}h${dd(agora.getMinutes())})`);
  const refeitos = new Set(feitos.map((f) => f.id));
  for (const n of fs.readdirSync(destino)) {
    if (/\.mov$/i.test(n) && refeitos.has(n.split("-")[0].split(".")[0])) {
      fs.mkdirSync(backup, { recursive: true });
      fs.renameSync(path.join(destino, n), path.join(backup, n));
    }
  }
  for (const f of feitos) fs.copyFileSync(path.join(saidaCenas, f.arquivo), path.join(destino, f.arquivo));
  const reg = lerRegistro(proj);
  for (const f of feitos) reg[f.id] = { impressao: imps.get(f.id), arquivo: f.arquivo, quando: agora.toISOString() };
  fs.writeFileSync(path.join(destino, REGISTRO), JSON.stringify(reg, null, 1));
  const leiame = path.join(destino, "LEIAME.txt");
  const antigas = fs.existsSync(leiame) ? fs.readFileSync(leiame, "utf8").split(/\r?\n/).filter((l) => /^[A-Z]{1,3}\d/.test(l)) : [];
  const linhas = new Map(antigas.map((l) => [l.split(/\s+/)[0], l]));
  for (const f of feitos) linhas.set(f.id, `${f.id.padEnd(6)} ${String(f.dur).padStart(4)} s  ${f.nome}`);
  fs.writeFileSync(leiame, [`Motions ${proj.cfg.nome || ""} · ProRes 4444 com transparência, 1080x1920, 30 fps`,
    "Já posicionados na faixa acima da cabeça: colocar na V2 em escala 200 (python -m stlflix ... motions --aplicar).", "",
    ...[...linhas.values()].sort()].join("\r\n") + "\r\n");
  return { feitos, destino, previa: path.join(R, "previa-cenas.mp4") };
}

function migrar(o) {
  // build.mjs antigo → cenas (avalia só a parte das cenas) + frases-gatilho de um plano existente → plano completo
  const src = fs.readFileSync(o.build, "utf8").split("\n");
  const fim = src.findIndex((l) => /^for \(const s of cenas\) if \(s\.topo\)/.test(l));
  const tmp = path.join(path.dirname(path.resolve(o.saida)), `.migrar-${Date.now()}.mjs`);
  fs.writeFileSync(tmp, src.slice(0, fim).join("\n").replace(/^import fs from "node:fs";/m, "") + "\nexport default cenas;\n");
  return import("file:///" + tmp.replace(/\\/g, "/")).then(({ default: cenas }) => {
    fs.rmSync(tmp);
    const gat = o.gatilhos ? lerPlano(fs.readFileSync(o.gatilhos, "utf8")).cenas : [];
    const porId = new Map(gat.map((c) => [c.id, c]));
    const blocoDe = (id) => id.match(/^[A-Z]+(\d+)/)?.[1];
    const out = [`# Plano de cenas — migrado de ${path.basename(path.dirname(path.resolve(o.build)))}`];
    let atual = null;
    for (const c of cenas) {
      const g = porId.get(c.id);
      const b = g?.bloco || blocoDe(c.id);
      if (b !== atual) { out.push("", `## Bloco ${String(b).padStart(2, "0")}${g?.blocoTitulo ? " · " + g.blocoTitulo : ""}`); atual = b; }
      out.push("", `- **${c.id}** · ${c.nome} — "${g ? g.gatilho : "ESCREVA A FRASE-GATILHO"}"`, ...cenaParaLinhas(c));
    }
    fs.writeFileSync(o.saida, out.join("\n") + "\n");
    console.log(`✓ ${cenas.length} cenas → ${o.saida} (${cenas.filter((c) => !porId.has(c.id)).length} sem frase-gatilho)`);
  });
}

// Amostra de uma campanha: 3 cenas de teste (degradê, barra, número, ícones, logo, CTA) renderizadas num projeto
// temporário; a prévia e um quadro de cada cena ficam em 2-design-system/campanhas/<campanha>/_amostra (fora do git).
async function amostra(o) {
  const id = o.campanha;
  if (!id || id === true) throw new Error("use --campanha <pasta em 2-design-system/campanhas>");
  const pasta = path.join(DS, "campanhas", id);
  if (!fs.existsSync(pasta)) throw new Error(`a campanha "${id}" não existe em 2-design-system/campanhas`);
  const icones = fs.readdirSync(pasta).filter((n) => n.endsWith(".png") && !n.startsWith("logo")).map((n) => n.slice(0, -4)).slice(0, 3);
  const temLogo = fs.existsSync(path.join(pasta, "logo-kv.png"));
  const tmp = path.join(os.tmpdir(), "stlflix-amostra", id);
  fs.rmSync(tmp, { recursive: true, force: true });
  fs.mkdirSync(path.join(tmp, "04-plano-de-cenas"), { recursive: true });
  const ref = o.referencia && o.referencia !== true ? path.resolve(o.referencia) : "";
  fs.writeFileSync(path.join(tmp, "config.json"), JSON.stringify({ nome: `Amostra ${id}`, motions: { campanha: id, referencia: ref } }));
  fs.writeFileSync(path.join(tmp, "04-plano-de-cenas", "plano-de-cenas.md"), [
    "## Bloco 01 · Amostra da campanha", "",
    '- **A01A** · Título e palavra-chave — "amostra da campanha cena um"',
    "  duração: 6",
    "  > 0.3 | kicker: AMOSTRA DA CAMPANHA | título: Viver de **impressão 3D** | legenda: o degradê da campanha na palavra-chave",
    "  > 3.2 | frase: Uma ideia por **batida**", "",
    '- **A01B** · Número e ícones — "amostra da campanha cena dois"',
    "  duração: 6",
    "  topo: A BARRA E O TÍTULO DO TOPO",
    "  > 0.3 | número: R$ 5 mil [verde, conta] | legenda: verde só para resultado",
    ...(icones.length ? [`  > 3.2 | ícones: ${icones.join(", ")} [altura=120] | legenda: ícones da campanha`] : []), "",
    '- **A01C** · Logo e CTA — "amostra da campanha cena três"',
    "  duração: 6 · poeira: 0-6",
    ...(temLogo ? ["  > 0.3 | logo"] : ["  > 0.3 | título: (campanha sem logo-kv.png)"]),
    "  > 3.0 | cta: QUERO AGORA", "",
  ].join("\n"));
  const proj = projeto(tmp);
  const { todas, geraveis, erros } = cenasDoPlano(path.join(tmp, "04-plano-de-cenas", "plano-de-cenas.md"));
  erros.push(...iconesQueFaltam(proj, todas));
  if (erros.length) throw new Error(erros.join("; "));
  const r = render(await carregarModelo(proj.mv.modelo), proj, "amostra", geraveis, {});
  const saida = path.join(pasta, "_amostra");
  fs.rmSync(saida, { recursive: true, force: true });
  fs.mkdirSync(saida, { recursive: true });
  fs.copyFileSync(r.previa, path.join(saida, "previa.mp4"));
  for (const f of r.feitos) {              // um quadro de cada batida de cada cena (as batidas começam em 0,3 e ~3 s)
    [2.2, 5.2].forEach((t, k) => sh("ffmpeg", ["-v", "error", "-y", "-ss", String(f.inicio + Math.min(t, f.dur - 0.3)), "-i", r.previa,
      "-frames:v", "1", "-q:v", "3", path.join(saida, `${f.id}-${k + 1}.jpg`)]));
  }
  console.log(`✓ amostra da campanha ${id}: ${path.join(saida, "previa.mp4")} (+ ${r.feitos.length * 2} quadros em ${saida})`);
}

async function main() {
  const o = args();
  if (o.cmd === "migrar") return migrar(o);
  if (o.cmd === "amostra") return amostra(o);
  if (!o.projeto) throw new Error("use --projeto <VSL> (o nome ou a pasta)");
  const proj = projeto(resolverVsl(o.projeto));
  if (o.cmd === "estado") return estado(proj);
  // --arquivo: um plano avulso (ex.: o rascunho que o Claude escreveu), a partir da raiz do kit ou da pasta da VSL
  const { chave, arquivo } = o.arquivo
    ? { chave: o.plano || "rascunho", arquivo: fs.existsSync(o.arquivo) ? path.resolve(o.arquivo) : proj.cam(o.arquivo) }
    : planoDe(proj, o.plano);
  const { todas, geraveis, erros } = cenasDoPlano(arquivo);
  erros.push(...iconesQueFaltam(proj, todas));
  if (o.cmd === "validar" || erros.length) {
    console.log(`${todas.length} cenas em ${arquivo} · ${geraveis.length} com descrição de motion`);
    const sem = todas.filter((c) => !c.cena).map((c) => c.id);
    if (sem.length) console.log(`  · sem descrição (só encaixe): ${sem.slice(0, 15).join(", ")}${sem.length > 15 ? " …" : ""}`);
    for (const e of erros) console.log("  ✗", e);
    if (erros.length) process.exit(1);
    if (o.cmd === "validar") return console.log("  ✓ plano ok");
  }
  const construir = await carregarModelo(proj.mv.modelo);
  if (o.cmd === "gerar" || o.cmd === "previa") {
    const w = pastaDeTrabalho(proj, chave);
    const { total } = construir(geraveis, { pasta: w, faixa: proj.mv.faixa, campanha: proj.mv.campanha });
    console.log(`✓ ${geraveis.length} cenas geradas em ${w} (reel de ${Math.floor(total / 60)} min ${Math.round(total % 60)} s)`);
    if (o.cmd === "previa") sh("npx", ["--yes", `hyperframes@${proj.mv.hyperframes}`, "preview"], { cwd: w });
    return;
  }
  if (o.cmd === "render") {
    let so = o.so ? String(o.so).split(",").map((s) => s.trim()) : null;
    if (o.pendentes) {
      so = situacao(proj, todas).filter((s) => s.estado === "falta" || s.estado === "mudou").map((s) => s.c.id);
      if (!so.length) return console.log("✓ nada pendente: todos os motions do plano estão renderizados e em dia");
      console.log(`${so.length} pendentes (faltam ou mudaram no plano): ${so.join(", ")}`);
    }
    const r = render(construir, proj, chave, geraveis, { so, porParte: Number(o["por-parte"]) || 30 });
    console.log(`✓ ${r.feitos.length} motions em ${r.destino}\n  prévia: ${r.previa}`);
    return;
  }
  throw new Error(`comando desconhecido: ${o.cmd} (validar, gerar, previa, render, estado, migrar)`);
}

main().catch((e) => { console.error("✗ " + e.message); process.exit(1); });
