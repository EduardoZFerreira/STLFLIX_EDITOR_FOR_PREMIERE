// Escrita à mão e círculo à mão para as cenas da VSL.
// Motor adaptado do bloco do registry `hw-write-title` (HyperFrames): letras Caveat "baked"
// (fx/caveat-pen.js) reveladas por traços de caneta no centro de cada letra, com a facilidade de
// velocidade da caneta (rápida nas retas, lenta nas curvas) e "boil" (tremulação de desenho animado).
// Tudo determinístico: posições são função do tempo da timeline, sem Math.random nem relógio.
(function () {
  var NS = "http://www.w3.org/2000/svg";
  function clamp(v, lo, hi) { return Math.min(hi, Math.max(lo, v)); }

  // um único onUpdate por timeline, com vários renderizadores (regra da família hw)
  window.hwOnUpdate = function (tl, fn) {
    if (!tl.__hwRenders) {
      tl.__hwRenders = [];
      var anterior = tl.eventCallback("onUpdate");
      tl.eventCallback("onUpdate", function () {
        if (anterior) anterior();
        for (var i = 0; i < tl.__hwRenders.length; i++) tl.__hwRenders[i]();
      });
    }
    tl.__hwRenders.push(fn);
    fn();
  };
  window.hwHash = function (n, seed) {
    var x = Math.sin(n * 127.1 + (seed || 1) * 311.7) * 43758.5453;
    return (x - Math.floor(x)) * 2 - 1;
  };
  // tremulação: pose sorteada a cada 3 quadros (frameDrop), igual ao bloco original
  window.hwBoil = function (tl, el, opts) {
    opts = opts || {};
    var amp = opts.amp != null ? opts.amp : 1.6, rot = opts.rot != null ? opts.rot : 0.5, seed = opts.seed || 1, drop = opts.frameDrop || 3;
    window.hwOnUpdate(tl, function () {
      var step = Math.floor((tl.time() * 30) / drop);
      gsap.set(el, { x: window.hwHash(step * 3, seed) * amp, y: window.hwHash(step * 3 + 1, seed) * amp, rotation: window.hwHash(step * 3 + 2, seed) * rot });
    });
  };
  // velocidade da caneta: função pura da geometria do traço (seek-safe)
  window.hwPenEase = function (pathEl) {
    var kCurve = 10, L = pathEl.getTotalLength();
    if (L <= 0) return { ease: function (t) { return t; }, inkTime: 1 };
    var PRE = 48, pts = [], i;
    for (i = 0; i <= PRE; i++) pts.push(pathEl.getPointAtLength((L * i) / PRE));
    var curv = [0];
    for (i = 1; i < PRE; i++) {
      var ax = pts[i].x - pts[i - 1].x, ay = pts[i].y - pts[i - 1].y, bx = pts[i + 1].x - pts[i].x, by = pts[i + 1].y - pts[i].y;
      var la = Math.hypot(ax, ay) || 1e-6, lb = Math.hypot(bx, by) || 1e-6;
      curv.push(Math.acos(clamp((ax * bx + ay * by) / (la * lb), -1, 1)) / ((la + lb) / 2));
    }
    curv.push(0);
    var mass = 0;
    for (i = 0; i < curv.length; i++) mass += curv[i];
    var N = Math.max(25, Math.min(75, Math.round(25 + mass * 18))), seg = L / N, times = [0], t = 0;
    for (i = 1; i <= N; i++) {
      var u = ((i - 0.5) / N) * PRE, i0 = Math.floor(u), f = u - i0;
      var c = curv[Math.min(i0, PRE)] * (1 - f) + curv[Math.min(i0 + 1, PRE)] * f;
      t += seg / Math.max(1 / (1 + kCurve * c * 14), 0.22);
      times.push(t);
    }
    for (i = 0; i <= N; i++) times[i] /= t;
    return {
      inkTime: t,
      ease: function (p) {
        if (p <= 0) return 0;
        if (p >= 1) return 1;
        var lo = 0, hi = N;
        while (hi - lo > 1) { var mid = (lo + hi) >> 1; if (times[mid] <= p) lo = mid; else hi = mid; }
        return (lo + (p - times[lo]) / (times[hi] - times[lo] || 1e-9)) / N;
      },
    };
  };

  // Escreve `text` dentro de `el` (substitui o conteúdo). opts: tl, at, size (px), ink, id (prefixo único), maxDur
  window.hwEscrever = function (el, text, o) {
    var table = window.__hwPenCaveat;
    if (!table) return o.at;
    var svg = document.createElementNS(NS, "svg");
    svg.setAttribute("class", "hw-svg");
    var g = document.createElementNS(NS, "g");
    var x = 0, strokes = [], fallbacks = [], gi = 0;
    for (var ci = 0; ci < text.length; ci++) {
      var ch = text[ci], gl = table.glyphs[ch];
      if (ch === " ") { x += 300; continue; }
      if (!gl) {
        // letra fora da tabela (ex.: acentos): Caveat de verdade, aparecendo por fade
        var ft = document.createElementNS(NS, "text");
        ft.setAttribute("x", x); ft.setAttribute("y", 0); ft.setAttribute("font-size", "1000");
        ft.setAttribute("style", "font-family: Caveat, cursive; font-weight: 700");
        ft.setAttribute("fill", o.ink);
        ft.textContent = ch;
        g.appendChild(ft);
        fallbacks.push({ el: ft, glyph: gi });
        x += 450; gi++;
        continue;
      }
      var gg = document.createElementNS(NS, "g");
      gg.setAttribute("transform", "translate(" + x + ",0)");
      var maskId = o.id + "-m" + gi, mask = document.createElementNS(NS, "mask");
      mask.setAttribute("id", maskId); mask.setAttribute("maskUnits", "userSpaceOnUse");
      mask.setAttribute("x", "-200"); mask.setAttribute("y", "-900"); mask.setAttribute("width", gl.adv + 400); mask.setAttribute("height", "1400");
      for (var si = 0; si < gl.strokes.length; si++) {
        var mp = document.createElementNS(NS, "path");
        mp.setAttribute("d", gl.strokes[si]); mp.setAttribute("fill", "none"); mp.setAttribute("stroke", "#fff");
        mp.setAttribute("stroke-width", Math.max(30, Math.round(gl.stem * 1.35)));
        mp.setAttribute("stroke-linecap", "round"); mp.setAttribute("stroke-linejoin", "round");
        mask.appendChild(mp);
        strokes.push({ path: mp, glyph: gi });
      }
      gg.appendChild(mask);
      var op = document.createElementNS(NS, "path");
      op.setAttribute("d", gl.outline); op.setAttribute("fill", o.ink); op.setAttribute("mask", "url(#" + maskId + ")");
      gg.appendChild(op);
      g.appendChild(gg);
      x += gl.adv; gi++;
    }
    svg.appendChild(g);
    var hU = table.meta.ascent - table.meta.descent, s = o.size / 1000;
    svg.setAttribute("width", Math.ceil(x * s)); svg.setAttribute("height", Math.ceil(hU * s));
    svg.setAttribute("viewBox", "0 " + -table.meta.ascent + " " + x + " " + hU);
    el.textContent = "";
    el.appendChild(svg);

    // traçado: um tween por traço, na ordem, com 60 ms de "caneta levantada" entre eles
    var tl = o.tl, lift = 0.06, metas = [], inkSum = 0, i;
    for (i = 0; i < strokes.length; i++) {
      var pe = window.hwPenEase(strokes[i].path), len = strokes[i].path.getTotalLength();
      metas.push({ pe: pe, len: len, st: { p: 0 } });
      inkSum += pe.inkTime;
      strokes[i].path.setAttribute("stroke-dasharray", len + " " + len);
    }
    var dur = clamp(0.4 + 0.045 * strokes.length, 0.9, o.maxDur || 1.6);
    var draw = Math.max(0.1, dur - lift * Math.max(0, strokes.length - 1)), t = o.at, inicioGlifo = {};
    for (i = 0; i < metas.length; i++) {
      var d = (metas[i].pe.inkTime / (inkSum || 1)) * draw;
      if (inicioGlifo[strokes[i].glyph] == null) inicioGlifo[strokes[i].glyph] = t;
      tl.to(metas[i].st, { p: 1, duration: d, ease: metas[i].pe.ease }, t);
      t += d + lift;
    }
    window.hwOnUpdate(tl, function () {
      for (var k = 0; k < metas.length; k++) {
        var m = metas[k];
        strokes[k].path.style.strokeDashoffset = m.len * (1 - m.st.p);
        strokes[k].path.style.opacity = m.st.p > 0 ? "1" : "0";
      }
    });
    for (i = 0; i < fallbacks.length; i++) {
      var tf = inicioGlifo[fallbacks[i].glyph + 1] != null ? inicioGlifo[fallbacks[i].glyph + 1] - 0.1 : t - 0.2;
      tl.fromTo(fallbacks[i].el, { opacity: 0 }, { opacity: 1, duration: 0.2, ease: "power2.out" }, tf);
    }
    return t - lift;
  };

  // Caneta marcador que desliza até `kw`, faz um laço à mão em volta e sai (adaptado do componente do registry
  // `cursor-annotate`): traço de espessura variável (grosso onde a caneta desacelera), tinta revelada sob a ponta.
  // Coordenadas locais à palavra (medida pela fonte), então funciona com a cena oculta na montagem.
  // o: tl, at, budget (s disponíveis), w, h (px da palavra), color, seed
  window.caAnotar = function (kw, o) {
    var w = o.w, h = o.h, tl = o.tl, seed = o.seed || 1;
    var PX = Math.round(w * 0.25 + 60), PY = Math.round(h * 0.6 + 40), W = w + PX * 2, H = h + PY * 2;
    var cx = PX + w / 2, cy = PY + h / 2;
    var rx = w / 2 + h * 0.2 + 12, ry = h * 0.46 + 6, tilt = (-4 + window.hwHash(3, seed) * 3) * Math.PI / 180;
    var fn = function (u) {   // laço: começa em cima à esquerda, passa um pouco do início e abre na saída
      var a = -2.55 + (Math.PI * 2 + 0.5) * u;
      var r = (1 + 0.035 * Math.sin(3 * a + 1.1 + seed)) * (1 + 0.08 * u);
      var ex = Math.cos(a) * rx * r, ey = Math.sin(a) * ry * r;
      return [cx + ex * Math.cos(tilt) - ey * Math.sin(tilt), cy + ex * Math.sin(tilt) + ey * Math.cos(tilt)];
    };
    var STEPS = 140, se = gsap.parseEase("sine.inOut"), pts = [], k;
    for (k = 0; k <= STEPS; k++) {
      var u = se(k / STEPS), p = fn(u), a0 = fn(Math.max(0, u - 1e-4)), b0 = fn(Math.min(1, u + 1e-4));
      var tlen = Math.hypot(b0[0] - a0[0], b0[1] - a0[1]) || 1;
      pts.push({ x: p[0], y: p[1], nx: -(b0[1] - a0[1]) / tlen, ny: (b0[0] - a0[0]) / tlen });
    }
    var top = 0;
    pts.forEach(function (q, i) { var A = pts[Math.max(0, i - 1)], B = pts[Math.min(STEPS, i + 1)]; q.speed = Math.hypot(B.x - A.x, B.y - A.y); top = Math.max(top, q.speed); });
    var sm = function (x) { return x * x * (3 - 2 * x); };
    pts.forEach(function (q, i) { var lift = 1 - sm(clamp((i / STEPS - 0.82) / 0.18, 0, 1)); q.w = 4 + (9 - 4) * (1 - q.speed / top) * lift; });
    var drawnTo = function (f) {
      var x = clamp(f, 0, 1) * STEPS, i = Math.floor(x), out = pts.slice(0, i + 1);
      if (i < STEPS && x > i) { var A = pts[i], B = pts[i + 1], m = x - i; out.push({ x: A.x + (B.x - A.x) * m, y: A.y + (B.y - A.y) * m, nx: A.nx + (B.nx - A.nx) * m, ny: A.ny + (B.ny - A.ny) * m, w: A.w + (B.w - A.w) * m }); }
      return out;
    };
    var outline = function (ps) {   // contorno preenchido de um traço de largura variável, pontas redondas
      if (ps.length < 2) return "";
      var side = function (q, dir) { var hh = (q.w / 2) * dir; return (q.x + q.nx * hh).toFixed(1) + " " + (q.y + q.ny * hh).toFixed(1); };
      var cap = function (q) { var r = (q.w / 2).toFixed(2); return " A" + r + " " + r + " 0 0 0 "; };
      var last = ps[ps.length - 1], d = "M" + side(ps[0], 1), i;
      for (i = 1; i < ps.length; i++) d += " L" + side(ps[i], 1);
      d += cap(last) + side(last, -1);
      for (i = ps.length - 2; i >= 0; i--) d += " L" + side(ps[i], -1);
      return d + cap(ps[0]) + side(ps[0], 1) + " Z";
    };
    // tinta
    var svg = document.createElementNS(NS, "svg");
    svg.setAttribute("class", "ca-ink"); svg.setAttribute("width", W); svg.setAttribute("height", H); svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    svg.style.left = -PX + "px"; svg.style.top = -PY + "px";
    var inkPath = document.createElementNS(NS, "path");
    inkPath.setAttribute("fill", o.color);
    svg.appendChild(inkPath);
    kw.appendChild(svg);
    // caneta (o desenho do componente original; a ponta fica na origem)
    var pen = document.createElement("div");
    pen.className = "ca-pen";
    pen.innerHTML = '<svg viewBox="-40 -200 240 240" width="230" height="230" style="position:absolute;left:-38px;top:-192px;overflow:visible"><g transform="rotate(-50)">' +
      '<path d="M0 0 L15 -5.5 L15 5.5 Z" fill="#1d1d22"/><path d="M3 -1.4 L15 -5.5 L15 5.5 L3 1.4 Z" fill="' + o.color + '"/>' +
      '<rect x="15" y="-7.5" width="14" height="15" rx="2" fill="#2a2a31"/><rect x="29" y="-9" width="62" height="18" rx="4" fill="#ffffff" stroke="#141414" stroke-width="2"/>' +
      '<rect x="36" y="-9" width="8" height="18" fill="' + o.color + '"/><rect x="91" y="-9.5" width="16" height="19" rx="6" fill="#1d1d22"/></g></svg>';
    kw.appendChild(pen);
    // tempos: desliza, desenha, levanta e sai — comprimidos para caber no tempo da batida
    var sq = clamp(o.budget / 1.9, 0.45, 1), tG = 0.4 * sq, tD = 1.0 * sq, tS = 0.5 * sq, T0 = o.at;
    var st = { g: 0, d: 0, s: 0 };
    tl.to(st, { g: 1, duration: tG, ease: "power3.out" }, T0);
    tl.to(st, { d: 1, duration: tD, ease: "none" }, T0 + tG);
    tl.to(st, { s: 1, duration: tS, ease: "power2.in" }, T0 + tG + tD + 0.04);
    var first = pts[0], fim = pts[STEPS];
    var de = { x: first.x + 230, y: first.y + 170 };                       // entra de baixo, à direita
    var away = { x: fim.x - cx, y: fim.y - cy }, al = Math.hypot(away.x, away.y) || 1;
    away = { x: away.x / al, y: away.y / al };
    window.hwOnUpdate(tl, function () {
      inkPath.setAttribute("d", st.d > 0 ? outline(drawnTo(st.d)) : "");
      var x, y;
      if (st.d <= 0) { x = de.x + (first.x - de.x) * st.g; y = de.y + (first.y - de.y) * st.g; }
      else if (st.s <= 0) { var dd = drawnTo(st.d), q = dd[dd.length - 1]; x = q.x; y = q.y; }
      else { x = fim.x + away.x * 320 * st.s; y = fim.y + away.y * 320 * st.s; }
      pen.style.transform = "translate(" + (x - PX).toFixed(1) + "px," + (y - PY).toFixed(1) + "px)";
      pen.style.opacity = st.g <= 0 ? "0" : String(1 - st.s);
    });
  };

  // Círculo feito à mão em volta de `kw` (elemento inline-block). Largura/altura vêm medidas pela fonte
  // (a cena pode estar oculta na montagem, quando offsetWidth ainda é zero). Devolve o <path> para animar o traço.
  window.hwCirculo = function (kw, seed, w, h) {
    var px = Math.round(h * 0.24 + 18), py = Math.round(h * 0.07 + 4);   // elipse larga e baixa: não invade a outra linha
    var W = w + px * 2, H = h + py * 2, cx = W / 2, cy = H / 2;
    var svg = document.createElementNS(NS, "svg");
    svg.setAttribute("class", "circ");
    svg.setAttribute("width", W); svg.setAttribute("height", H); svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    svg.style.left = -px + "px"; svg.style.top = -py + "px";
    var N = 72, ini = -2.5 + window.hwHash(1, seed) * 0.25, volta = Math.PI * 2 * 1.13, tilt = window.hwHash(2, seed) * 0.05, d = "";
    for (var i = 0; i <= N; i++) {
      var p = i / N, a = ini + volta * p;
      var rf = 1 + window.hwHash(i * 0.35, seed) * 0.025 + (p - 0.5) * 0.07;   // mão: raio oscila e a volta não fecha certinho
      var ex = Math.cos(a) * (cx - 5) * rf, ey = Math.sin(a) * (cy - 5) * rf;
      var X = cx + ex * Math.cos(tilt) - ey * Math.sin(tilt), Y = cy + ex * Math.sin(tilt) + ey * Math.cos(tilt);
      d += (i ? " L " : "M ") + X.toFixed(1) + " " + Y.toFixed(1);
    }
    var path = document.createElementNS(NS, "path");
    path.setAttribute("d", d); path.setAttribute("pathLength", "1");
    svg.appendChild(path);
    kw.appendChild(svg);
    return path;
  };
})();
