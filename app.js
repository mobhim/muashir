/* مؤشّر · motion and interaction. Every figure comes from data.js (written by the pipeline). */
(function () {
  "use strict";
  const D = window.MUASHIR;
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  if (!D) { document.body.insertAdjacentHTML("afterbegin", '<p style="padding:2rem">تعذّر تحميل بيانات الدراسة. شغّل python -m muashir.pipeline ثم حدّث الصفحة.</p>'); return; }

  /* ?still=1 shows everything at rest (for printing and screenshots) */
  const STILL = new URLSearchParams(location.search).has("still") || matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (STILL) document.documentElement.classList.add("still");
  const EASE = "cubic-bezier(.16,1,.3,1)";
  const C = { gold: "#d9b24a", hi: "#f4d98a", cream: "#f3ead3", up: "#46d39a", dn: "#ff6b6b", faint: "rgba(243,234,211,.62)", grid: "rgba(255,255,255,.08)", mute: "rgba(243,234,211,.8)" };
  const NS = "http://www.w3.org/2000/svg";

  /* ───── formatting ───── */
  const minus = (s) => s.replace("-", "−");
  const F = {
    pct: (v, d = 2) => (v == null ? "—" : minus((v >= 0 ? "+" : "") + (v * 100).toFixed(d) + "%")),
    pct0: (v) => (v == null ? "—" : Math.round(v * 100) + "%"),
    int: (v) => (v == null ? "—" : Number(v).toLocaleString("en-US")),
    num: (v, d = 1) => (v == null ? "—" : minus(Number(v).toFixed(d))),
    raw: (v) => (v == null ? "—" : String(v)),
  };
  const get = (p) => p.split(".").reduce((o, k) => (o == null ? o : o[k]), D);
  $$("[data-v]").forEach((n) => { const v = get(n.dataset.v); if (v != null) n.textContent = F[n.dataset.f || "raw"](v); });
  const cls = (v) => (v == null ? "" : v < 0 ? "dn" : "up");
  const arDate = (iso) => new Date(iso).toLocaleDateString("ar-SA-u-ca-gregory-nu-latn", { year: "numeric", month: "long", day: "numeric" });
  const byT = Object.fromEntries(D.companies.map((c) => [c.t, c]));
  const COMP = ["نمو الربحية السنوي", "التغير عن الربع السابق", "مفاجأة المحللين", "استمرارية النمو", "عائد الأرباح", "عائد التوزيعات", "هدوء أمام السوق"];

  /* ───── tiny SVG toolkit ───── */
  function el(tag, attrs, kids) {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs || {}) if (attrs[k] != null) n.setAttribute(k, attrs[k]);
    (kids || []).forEach((k) => n.appendChild(typeof k === "string" ? document.createTextNode(k) : k));
    return n;
  }
  const txt = (s, x, y, a) => el("text", Object.assign({ x, y }, a), [s]);
  const rtl = (s, x, y, a) => txt(s, x, y, Object.assign({ direction: "rtl", "text-anchor": "start" }, a));
  const scale = (d0, d1, r0, r1) => (v) => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);
  const ticks = (lo, hi, step) => { const o = []; for (let v = Math.ceil(lo / step - 1e-9) * step; v <= hi + 1e-9; v += step) o.push(Math.round(v * 1e6) / 1e6); return o; };
  const svg = (w, h) => el("svg", { viewBox: `0 0 ${w} ${h}`, width: w, height: h, "aria-hidden": "true" });
  const anim = (node, frames, opt) => (STILL ? null : node.animate(frames, Object.assign({ easing: EASE, fill: "backwards" }, opt)));
  const drawOn = (path, dur, delay) => { path.setAttribute("pathLength", 1); path.style.strokeDasharray = 1; anim(path, [{ strokeDashoffset: 1 }, { strokeDashoffset: 0 }], { duration: dur, delay: delay || 0 }); };
  const grow = (rect, origin, delay) => { rect.style.transformBox = "fill-box"; rect.style.transformOrigin = origin; anim(rect, [{ transform: origin.includes("left") || origin.includes("right") ? "scaleX(0)" : "scaleY(0)" }, { transform: "none" }], { duration: 900, delay: delay || 0 }); };
  const mounts = {};
  function mount(id, draw) {
    const host = document.getElementById(id); if (!host) return;
    let last = 0;
    const run = (force) => { const w = Math.round(host.clientWidth); if (!w || (w === last && !force)) return; last = w; host.replaceChildren(draw(w)); };
    new ResizeObserver(() => run(false)).observe(host);
    mounts[id] = () => run(true);
    run(false);
  }

  /* ───── moving background: drifting gold price lines ───── */
  (function () {
    const cv = $("#bg"), ctx = cv.getContext("2d");
    let W = 0, H = 0, raf = 0, t0 = performance.now();
    const lines = Array.from({ length: 7 }, (_, i) => ({ y: 0.18 + i * 0.115, a: 18 + i * 7, f: 0.0016 + i * 0.00037, s: 0.00006 + i * 0.000017, p: i * 1.9, w: i % 3 === 0 ? 1.6 : 1, o: i % 3 === 0 ? 0.5 : 0.2 }));
    function size() { const d = Math.min(devicePixelRatio || 1, 1.5); W = innerWidth; H = innerHeight; cv.width = W * d; cv.height = H * d; ctx.setTransform(d, 0, 0, d, 0, 0); }
    function frame(now) {
      const t = now - t0;
      ctx.clearRect(0, 0, W, H);
      ctx.strokeStyle = "rgba(255,255,255,.035)"; ctx.lineWidth = 1; ctx.beginPath();
      for (let x = (-(t * 0.012) % 90); x < W; x += 90) { ctx.moveTo(x, 0); ctx.lineTo(x, H); }
      for (let y = 60; y < H; y += 90) { ctx.moveTo(0, y); ctx.lineTo(W, y); }
      ctx.stroke();
      lines.forEach((l) => {
        ctx.beginPath();
        for (let x = -10; x <= W + 10; x += 12) {
          const u = x * l.f + t * l.s * 12 + l.p;
          const y = H * l.y - (x / W) * H * 0.12 + Math.sin(u) * l.a + Math.sin(u * 2.7 + l.p) * l.a * 0.42 + Math.sin(u * 6.1) * l.a * 0.16;
          x === -10 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.strokeStyle = `rgba(217,178,74,${l.o})`; ctx.lineWidth = l.w; ctx.stroke();
        if (l.w > 1) { ctx.strokeStyle = "rgba(217,178,74,.07)"; ctx.lineWidth = 9; ctx.stroke(); }
      });
      if (!STILL) raf = requestAnimationFrame(frame);
    }
    size(); frame(performance.now());
    addEventListener("resize", () => { size(); if (STILL) frame(performance.now()); });
    document.addEventListener("visibilitychange", () => { cancelAnimationFrame(raf); if (!document.hidden && !STILL) raf = requestAnimationFrame(frame); });
  })();

  /* ───── word split (Arabic-safe) and heading reveals ───── */
  function split(node) {
    const words = node.textContent.trim().split(/\s+/);
    node.setAttribute("aria-label", node.textContent.trim());
    node.innerHTML = words.map((w) => `<span class="w" aria-hidden="true">${w}</span>`).join(" ");
    return $$(".w", node);
  }
  const wordsIn = (ws, base) => ws.forEach((w, i) => anim(w, [{ opacity: 0, transform: "translateY(.3em)", filter: "blur(10px)" }, { opacity: 1, transform: "none", filter: "blur(0)" }], { duration: 700, delay: (base || 0) + i * 80 }));

  /* ───── loader, then the hero entrance ───── */
  const heroWords = split($("#hero-title"));
  function enter() {
    wordsIn(heroWords, 80);
    $$(".hero .in").forEach((n, i) => { n.style.opacity = 1; anim(n, [{ opacity: 0, transform: "translateY(.8rem)" }, { opacity: 1, transform: "none" }], { duration: 700, delay: 260 + i * 90 }); });
  }
  (function () {
    const L = $("#loader"), pct = $("#loader-pct");
    if (STILL) { L.remove(); $$(".hero .in").forEach((n) => (n.style.opacity = 1)); return; }
    const start = performance.now(), dur = 1150;
    (function tick(now) {
      const k = Math.min(1, (now - start) / dur); pct.textContent = Math.round(k * 100);
      if (k < 1) requestAnimationFrame(tick); else { L.classList.add("gone"); enter(); setTimeout(() => L.remove(), 800); }
    })(start);
    setTimeout(() => { if (L.isConnected && !L.classList.contains("gone")) { L.classList.add("gone"); enter(); } }, 2600);   // never trap the page behind the loader
  })();

  /* ───── odometer numbers ───── */
  function odo(node) {
    const raw = node.textContent.trim(), fs = parseFloat(getComputedStyle(node).fontSize), lh = Math.round(fs * 1.3);
    node.setAttribute("aria-label", raw);
    const box = document.createElement("span"); box.className = "odo-box"; box.setAttribute("aria-hidden", "true"); box.style.setProperty("--lh", lh + "px");
    const reels = [];
    raw.split("").forEach((ch) => {
      if (/\d/.test(ch)) {
        const r = document.createElement("span"); r.className = "reelc"; const col = document.createElement("span"); col.className = "col";
        for (let k = 0; k < 20; k++) { const d = document.createElement("span"); d.textContent = k % 10; col.appendChild(d); }
        r.appendChild(col); box.appendChild(r); reels.push({ col, d: +ch });
      } else { const s = document.createElement("span"); s.className = "ch"; s.textContent = ch; box.appendChild(s); }
    });
    node.textContent = ""; node.appendChild(box);
    const rest = () => reels.forEach((r) => { r.col.style.transition = "none"; r.col.style.transform = `translateY(-${(10 + r.d) * lh}px)`; });
    const roll = () => reels.forEach((r, i) => { r.col.style.transition = "none"; r.col.style.transform = "translateY(0)"; void r.col.offsetHeight; r.col.style.transition = `transform ${950 + i * 110}ms ${EASE} ${i * 50}ms`; r.col.style.transform = `translateY(-${(10 + r.d) * lh}px)`; });
    return { node, rest, roll };
  }
  const odos = $$(".odo").map(odo);
  if (STILL) odos.forEach((o) => o.rest());
  else { const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { io.unobserve(e.target); e.target._o.roll(); } }), { threshold: 0.6 }); odos.forEach((o) => { o.node._o = o; io.observe(o.node); }); }

  /* ───── gauge ───── */
  function gauge(host, value, label) {
    const R = 52, CIRC = 2 * Math.PI * R, ARC = CIRC * 0.75, s = el("svg", { viewBox: "0 0 140 140", "aria-hidden": "true" });
    const mk = (stroke, w) => el("circle", { cx: 70, cy: 70, r: R, fill: "none", stroke, "stroke-width": w, "stroke-linecap": "round", "stroke-dasharray": `${ARC} ${CIRC}`, transform: "rotate(135 70 70)" });
    const fill = mk(C.gold, 9); fill.style.filter = "drop-shadow(0 0 6px rgba(217,178,74,.6))";
    const to = ARC * (1 - Math.max(0, Math.min(100, value)) / 100);
    fill.setAttribute("stroke-dashoffset", to);
    const n = txt("0", 70, 79, { "text-anchor": "middle", "font-size": 34, "font-weight": 800, fill: C.cream });
    s.append(mk(C.grid, 9), fill, n, txt(label || "من 100", 70, 100, { "text-anchor": "middle", "font-size": 10, fill: C.faint }));
    host.replaceChildren(s);
    if (STILL) { n.textContent = F.num(value, 0); return; }
    fill.animate([{ strokeDashoffset: ARC }, { strokeDashoffset: to }], { duration: 1300, easing: EASE });
    const t0 = performance.now(); (function tick(now) { const k = Math.min(1, (now - t0) / 1200), e = 1 - Math.pow(1 - k, 4); n.textContent = Math.round(value * e); if (k < 1) requestAnimationFrame(tick); })(t0);
  }

  /* ───── story charts ───── */
  mount("c-buckets", (W) => {
    const H = Math.max(240, Math.min(360, W * 0.56)), m = { l: 44, r: 8, t: 26, b: 44 }, v = D.buckets.reaction;
    const lo = Math.min(0, ...v) - 0.002, hi = Math.max(0, ...v) + 0.002, y = scale(lo, hi, H - m.b, m.t), band = (W - m.l - m.r) / v.length, bw = Math.min(band * 0.6, 90), s = svg(W, H);
    ticks(lo, hi, 0.005).forEach((t) => { s.append(el("line", { x1: m.l, x2: W - m.r, y1: y(t), y2: y(t), stroke: t === 0 ? C.faint : C.grid }), txt(F.pct(t, 1), m.l - 8, y(t) + 4, { class: "axis", "text-anchor": "end" })); });
    v.forEach((val, i) => {
      const cx = m.l + band * (i + 0.5), col = i === 0 ? C.dn : i === v.length - 1 ? C.up : "rgba(243,234,211,.35)";
      const r = el("rect", { x: cx - bw / 2, width: bw, y: Math.min(y(val), y(0)), height: Math.max(1, Math.abs(y(val) - y(0))), fill: col, rx: 5 });
      grow(r, val >= 0 ? "center bottom" : "center top", i * 110);
      const lab = txt(F.pct(val), cx, val >= 0 ? y(val) - 8 : y(val) + 19, { class: "val", "text-anchor": "middle", fill: i === 0 ? C.dn : i === v.length - 1 ? C.up : C.cream });
      anim(lab, [{ opacity: 0 }, { opacity: 1 }], { duration: 500, delay: 500 + i * 110 });
      s.append(r, lab, txt(String(i + 1), cx, H - m.b + 20, { "text-anchor": "middle", "font-size": 14, "font-weight": 600 }));
      const sub = i === 0 ? "الأدنى درجة" : i === v.length - 1 ? "الأعلى درجة" : "";
      if (sub) s.append(txt(sub, cx, H - m.b + 37, { class: "axis", "text-anchor": "middle" }));
    });
    return s;
  });
  const LINES = [["5", C.up, "الأعلى درجة"], ["3", "rgba(243,234,211,.45)", "الوسط"], ["1", C.dn, "الأدنى درجة"]];
  mount("c-path", (W) => {
    const days = D.path.days, narrow = W < 480, H = Math.max(240, Math.min(380, W * 0.6)), m = { l: 42, r: narrow ? 10 : 92, t: narrow ? 28 : 12, b: 30 };
    const all = LINES.flatMap(([b]) => D.path.buckets[b]), lo = Math.min(...all) - 0.003, hi = Math.max(...all) + 0.003;
    const x = scale(days[0], days[days.length - 1], m.l, W - m.r), y = scale(lo, hi, H - m.b, m.t), s = svg(W, H);
    s.append(el("rect", { x: x(-1), width: x(1) - x(-1), y: m.t, height: H - m.b - m.t, fill: "rgba(217,178,74,.16)" }));
    ticks(lo, hi, 0.01).forEach((t) => { s.append(el("line", { x1: m.l, x2: W - m.r, y1: y(t), y2: y(t), stroke: t === 0 ? C.faint : C.grid }), txt(F.pct(t, 0), m.l - 8, y(t) + 4, { class: "axis", "text-anchor": "end" })); });
    ticks(days[0], days[days.length - 1], 20).forEach((t) => s.append(txt(t === 0 ? "يوم الإعلان" : minus((t > 0 ? "+" : "") + t), x(t), H - m.b + 19, { class: "axis", "text-anchor": "middle", fill: t === 0 ? C.hi : null })));
    LINES.forEach(([b, col, name], k) => {
      const pts = D.path.buckets[b];
      const p = el("path", { d: "M" + pts.map((v, i) => `${x(days[i]).toFixed(1)} ${y(v).toFixed(1)}`).join(" L"), fill: "none", stroke: col, "stroke-width": b === "3" ? 1.6 : 2.8, "stroke-linejoin": "round", "stroke-linecap": "round" });
      if (b !== "3") p.style.filter = `drop-shadow(0 0 5px ${col})`;
      drawOn(p, 2200, k * 150); s.append(p);
      const tc = b === "3" ? C.mute : col;
      const lab = narrow ? rtl(name, W - m.r - k * 88, 14, { "font-size": 12, "font-weight": 600, fill: tc }) : txt(name, W - m.r + 8, y(pts[pts.length - 1]) + 4, { "font-size": 12, "font-weight": 600, fill: tc });
      anim(lab, [{ opacity: 0 }, { opacity: 1 }], { duration: 600, delay: 1700 }); s.append(lab);
    });
    return s;
  });
  mount("c-measures", (W) => {
    const rows = [["نموذج السوق: يطرح تفوق السهم السابق", D.windows.drift_60.spread, C.cream], ["عائد السهم ناقص عائد السوق", D.measures.market_adjusted, C.gold], ["عائد السهم ناقص بيتا × عائد السوق", D.measures.beta_adjusted, C.gold], ["العائد الخام", D.measures.raw_return, C.gold]];
    const rh = 58, m = { l: 12, r: 12, t: 6, b: 52 }, H = m.t + rows.length * rh + m.b, pa = D.prior_alpha.spread;
    const lo = Math.min(0, ...rows.map((r) => r[1].lo)) - (W < 520 ? 0.03 : 0.018), hi = Math.max(...rows.map((r) => r[1].hi), pa) + 0.012, x = scale(lo, hi, m.l, W - m.r), s = svg(W, H);
    ticks(lo, hi, 0.02).forEach((t) => s.append(el("line", { x1: x(t), x2: x(t), y1: m.t, y2: H - m.b, stroke: t === 0 ? C.faint : C.grid }), txt(F.pct(t, 0), x(t), H - m.b + 17, { class: "axis", "text-anchor": "middle" })));
    s.append(el("line", { x1: x(pa), x2: x(pa), y1: m.t, y2: H - m.b + 24, stroke: C.dn, "stroke-width": 1.5, "stroke-dasharray": "5 4" }), rtl(`تفوقها قبل الإعلان ⁦${F.pct(pa)}⁩`, Math.min(W - m.r, x(pa) + 120), H - m.b + 42, { "font-size": 12, "font-weight": 600, fill: C.dn }));
    rows.forEach(([name, sp, col], i) => {
      const top = m.t + i * rh, cy = top + 38;
      const r = el("rect", { x: Math.min(x(0), x(sp.mean)), width: Math.max(2, Math.abs(x(sp.mean) - x(0))), y: cy - 7, height: 14, fill: col, rx: 4 }); grow(r, "left center", i * 120);
      const near = Math.min(x(0), x(sp.lo)) - m.l < 60;
      s.append(rtl(name, W - m.r, top + 18, { "font-size": W < 480 ? 12 : 14, "font-weight": 600 }), r, el("line", { x1: x(sp.lo), x2: x(sp.hi), y1: cy, y2: cy, stroke: C.faint }),
        txt(F.pct(sp.mean), near ? x(sp.hi) + 8 : Math.min(x(0), x(sp.lo)) - 8, cy + 5, { class: "val", "text-anchor": near ? "start" : "end", fill: col }));
    });
    return s;
  });
  $$("details").forEach((d) => d.addEventListener("toggle", () => { if (d.open && mounts["c-measures"] && d.contains($("#c-measures"))) mounts["c-measures"](); }));

  /* ───── the sticky stage follows the step being read ───── */
  const chips = $("#chips"); chips.innerHTML = COMP.map((n) => `<li><i></i>${n}</li>`).join("");
  const scenes = $$(".scene"), steps = $$(".step");
  let cur = -1, chipTimer = 0;
  function playScore() {
    clearTimeout(chipTimer);
    const items = $$("li", chips); items.forEach((li) => li.classList.remove("done"));
    gauge($("#g-stage"), D.buckets.score[4], "متوسط الأعلى درجة");
    if (STILL) { items.forEach((li) => li.classList.add("done")); return; }
    let k = 0; (function next() { if (k < items.length) { items[k++].classList.add("done"); chipTimer = setTimeout(next, 170); } else chipTimer = setTimeout(() => { if (cur === 0) playScore(); }, 4200); })();
  }
  function show(i) {
    if (i === cur) return; cur = i;
    scenes.forEach((s, j) => s.classList.toggle("on", j === i)); steps.forEach((s, j) => s.classList.toggle("on", j === i));
    if (i === 0) playScore(); else clearTimeout(chipTimer);
    if (i === 1 && mounts["c-buckets"]) mounts["c-buckets"]();
    if (i === 2 && mounts["c-path"]) mounts["c-path"]();
  }
  const sio = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) show(+e.target.dataset.step); }), { rootMargin: "-45% 0px -45% 0px" });
  steps.forEach((s) => sio.observe(s)); show(0);

  /* ───── leaderboard ───── */
  const rowsEl = $("#rows"), sectorsEl = $("#sectors");
  const SORTS = { score: { f: (v) => F.num(v, 1), lo: 0, hi: 100 }, react: { f: F.pct, div: true }, drift: { f: F.pct, div: true }, up: { f: F.pct0, lo: 0, hi: 1 } };
  let sortKey = "score", sector = "الكل";
  const sectors = ["الكل"].concat(Array.from(new Set(D.companies.map((c) => c.sector))));
  sectorsEl.innerHTML = sectors.map((s) => `<button type="button" aria-pressed="${s === sector}">${s}</button>`).join("");
  rowsEl.innerHTML = D.companies.map((c) => `<li data-t="${c.t}"><button type="button" class="row" aria-label="${c.name}، افتح البطاقة"><span class="rk"></span><span class="nm"><b>${c.name}</b><span>${c.sector} · <span class="num">${c.t}</span> · <span class="num">${c.n}</span> إعلان</span></span><span class="bar"><i></i></span><span class="vl"></span></button></li>`).join("");
  function board(first) {
    const S = SORTS[sortKey], items = $$("li", rowsEl), before = new Map(items.map((li) => [li, li.getBoundingClientRect().top]));
    const span = S.div ? Math.max(...D.companies.map((c) => Math.abs(c[sortKey]))) : 0;
    const order = D.companies.slice().sort((a, b) => b[sortKey] - a[sortKey]);
    let rank = 0;
    order.forEach((c) => {
      const li = $(`li[data-t="${c.t}"]`, rowsEl), on = sector === "الكل" || c.sector === sector, v = c[sortKey];
      li.hidden = !on; rowsEl.appendChild(li); if (!on) return;
      $(".rk", li).textContent = ++rank; const vl = $(".vl", li); vl.textContent = S.f(v); vl.className = "vl" + (S.div ? " " + cls(v) : "");
      const bar = $(".bar", li), i = $("i", bar); let u = $("u", bar);
      if (S.div) { if (!u) { u = document.createElement("u"); bar.appendChild(u); } u.style.left = "50%"; const w = (Math.abs(v) / span) * 50; i.className = v < 0 ? "neg" : "pos"; i.style.left = (v < 0 ? 50 - w : 50) + "%"; i.style.width = w + "%"; }
      else { if (u) u.remove(); i.className = ""; i.style.left = "0"; i.style.width = ((v - S.lo) / (S.hi - S.lo)) * 100 + "%"; }
    });
    if (first || STILL) return;
    items.forEach((li) => { if (li.hidden) return; const dy = before.get(li) - li.getBoundingClientRect().top; if (dy) li.animate([{ transform: `translateY(${dy}px)` }, { transform: "none" }], { duration: 700, easing: EASE }); });
  }
  board(true);
  $("#sort").addEventListener("click", (e) => { const b = e.target.closest("button"); if (!b) return; sortKey = b.dataset.sort; $$("#sort button").forEach((x) => x.setAttribute("aria-pressed", String(x === b))); board(); });
  sectorsEl.addEventListener("click", (e) => { const b = e.target.closest("button"); if (!b) return; sector = b.textContent; $$("button", sectorsEl).forEach((x) => x.setAttribute("aria-pressed", String(x === b))); board(); });
  rowsEl.addEventListener("click", (e) => { const li = e.target.closest("li"); if (li) openSheet(li.dataset.t, e.target.closest("button")); });

  /* ───── radar and timelines (shared by the duel and the company sheet) ───── */
  function radar(W, sets) {
    const H = Math.min(W, 360), cx = W / 2, cy = H / 2 + 4, R = Math.min(W, H) / 2 - 58, n = COMP.length, s = svg(W, H);
    const pt = (i, r) => [cx + Math.sin((i / n) * 2 * Math.PI) * r, cy - Math.cos((i / n) * 2 * Math.PI) * r];
    [0.25, 0.5, 0.75, 1].forEach((k) => s.append(el("polygon", { points: COMP.map((_, i) => pt(i, R * k).join(",")).join(" "), fill: "none", stroke: C.grid })));
    COMP.forEach((name, i) => { const [x, y] = pt(i, R + 14), a = Math.sin((i / n) * 2 * Math.PI); s.append(el("line", { x1: cx, y1: cy, x2: pt(i, R)[0], y2: pt(i, R)[1], stroke: C.grid }), txt(name, x, y + 4, { "font-size": W < 360 ? 9.5 : 11, fill: C.mute, "text-anchor": Math.abs(a) < 0.2 ? "middle" : a > 0 ? "start" : "end" })); });
    sets.forEach(([vals, col], k) => { const p = el("polygon", { points: vals.map((v, i) => pt(i, R * ((v == null ? 50 : v) / 100)).join(",")).join(" "), fill: col, "fill-opacity": 0.16, stroke: col, "stroke-width": 2, "stroke-linejoin": "round" }); p.style.transformBox = "fill-box"; p.style.transformOrigin = "center"; anim(p, [{ transform: "scale(.2)", opacity: 0 }, { transform: "none", opacity: 1 }], { duration: 900, delay: k * 140 }); s.append(p); });
    return s;
  }
  const allDates = D.companies.flatMap((c) => c.events.map((e) => +new Date(e[0]))), T0 = Math.min(...allDates), T1 = Math.max(...allDates);
  function timeline(W, sets, onPick) {
    const H = Math.max(200, Math.min(280, W * 0.42)), m = { l: 30, r: 10, t: 10, b: 26 }, x = scale(T0, T1, m.l, W - m.r), y = scale(0, 100, H - m.b, m.t), s = svg(W, H);
    [0, 25, 50, 75, 100].forEach((t) => s.append(el("line", { x1: m.l, x2: W - m.r, y1: y(t), y2: y(t), stroke: t === 50 ? C.faint : C.grid }), txt(String(t), m.l - 7, y(t) + 4, { class: "axis", "text-anchor": "end" })));
    const y0 = new Date(T0).getFullYear(), y1 = new Date(T1).getFullYear(), step = W < 520 ? 2 : 1;
    for (let yr = y0; yr <= y1; yr += step) s.append(txt(String(yr), x(+new Date(yr, 0, 1)), H - m.b + 18, { class: "axis", "text-anchor": "start" }));
    sets.forEach(([c, col], k) => {
      const p = el("path", { d: "M" + c.events.map((e) => `${x(+new Date(e[0])).toFixed(1)} ${y(e[1]).toFixed(1)}`).join(" L"), fill: "none", stroke: col, "stroke-width": onPick ? 1.2 : 2.2, "stroke-linejoin": "round", opacity: onPick ? 0.5 : 1 });
      drawOn(p, 1600, k * 200); s.append(p);
      if (!onPick) return;
      c.events.forEach((e, i) => {
        const up = e[3] != null && e[3] >= 0;
        const g = el("g", { class: "dot", transform: `translate(${x(+new Date(e[0])).toFixed(1)},${y(e[1]).toFixed(1)})`, tabindex: 0, role: "button", "aria-label": `${arDate(e[0])}، الدرجة ${e[1]}، ${up ? "ارتفع" : "انخفض"}` },
          [el("circle", { r: 12, fill: "transparent" }), el("path", { d: up ? "M0,-6 L6,5 L-6,5 Z" : "M0,6 L6,-5 L-6,-5 Z", fill: up ? C.up : C.dn })]);
        const go = () => { $$(".dot.on", s).forEach((d) => d.classList.remove("on")); g.classList.add("on"); onPick(i); };
        g.addEventListener("pointerenter", go); g.addEventListener("focus", go); g.addEventListener("click", go);
        if (i === c.events.length - 1) g.classList.add("on");
        anim(g, [{ opacity: 0 }, { opacity: 1 }], { duration: 400, delay: 300 + i * 22 }); s.append(g);
      });
    });
    return s;
  }

  /* ───── arena: a live head-to-head that plays ready matchups until the visitor takes over ───── */
  const arena = $("#arena"), racesEl = $("#races"), verdictEl = $("#verdict"), dock = $("#dock"), presetsEl = $("#presets"), playBtn = $("#play");
  const sorted = D.companies.slice().sort((a, b) => b.score - a.score);
  const PRESETS = [["1120", "1180"], ["2222", "2010"], ["7010", "7020"], ["2280", "2050"], ["4190", "4003"], ["1150", "1010"]].filter((p) => byT[p[0]] && byT[p[1]]);
  const short = (c) => c.name.replace(/^(مصرف|بنك|البنك|مجموعة|شركة)\s+/, "");
  const METRICS = [["الدرجة", "score", (v) => F.num(v, 1), 100], ["يوم الإعلان", "react", F.pct, 0], ["بعد 60 يوم", "drift", F.pct, 0], ["ارتفع يوم الإعلان", "up", F.pct0, 1]];
  let A = byT[PRESETS[0][0]], B = byT[PRESETS[0][1]], slot = "b", playing = !STILL, pi = 0, timer = 0;
  const sideHTML = (c, tag) => `<span class="side-tag">${tag}</span><b class="side-name">${c.name}</b><small>${c.sector} · <span class="num">${c.t}</span> · <span class="num">${c.n}</span> إعلان</small><span class="side-g"></span>`;
  function fill(which, c, animate) {
    const node = $(`.side.${which}`, arena), dir = which === "a" ? 1 : -1;
    const put = () => { node.innerHTML = sideHTML(c, which === "a" ? "الأولى" : "الثانية"); gauge($(".side-g", node), c.score, "متوسط الدرجة"); node.setAttribute("aria-label", `${c.name}. اضغط ثم اختر شركة بدلها`); };
    if (!animate || STILL) return put();
    node.animate([{ opacity: 1, transform: "none", filter: "blur(0)" }, { opacity: 0, transform: `translateX(${dir * 2}rem) scale(.94)`, filter: "blur(12px)" }], { duration: 240, easing: "ease-in", fill: "forwards" }); setTimeout(() => { node.getAnimations().forEach((x) => x.cancel());
      put(); node.animate([{ opacity: 0, transform: `translateX(${dir * -2}rem) scale(.94)`, filter: "blur(12px)" }, { opacity: 1, transform: "none", filter: "blur(0)" }], { duration: 640, easing: EASE });
    }, 240);   // a timer, not onfinish: the swap must happen even if the animation is throttled
  }
  function races() {
    let wa = 0, wb = 0;
    racesEl.innerHTML = METRICS.map(([name, k, f, cap]) => {
      const a = A[k], b = B[k], top = cap || Math.max(Math.abs(a), Math.abs(b)) || 1; if (a > b) wa++; else if (b > a) wb++;
      return `<div class="metric"><p><b class="num ${a > b ? "win" : ""}">${f(a)}</b><span>${name}</span><b class="num ${b > a ? "win" : ""}">${f(b)}</b></p><div class="track2"><span><i data-w="${Math.min(100, (Math.abs(b) / top) * 100)}"></i></span><span><i data-w="${Math.min(100, (Math.abs(a) / top) * 100)}"></i></span></div></div>`;
    }).join("");
    $$(".metric", racesEl).forEach((m, i) => {
      $$("i", m).forEach((bar) => { bar.style.width = STILL ? bar.dataset.w + "%" : "0%"; if (!STILL) setTimeout(() => (bar.style.width = bar.dataset.w + "%"), 240 + i * 240); });
      anim(m, [{ opacity: 0, transform: "translateY(.6rem)" }, { opacity: 1, transform: "none" }], { duration: 520, delay: 120 + i * 240 });
    });
    verdictEl.innerHTML = wa === wb ? `تعادل <b class="num">${wa}–${wb}</b>` : `<b>${(wa > wb ? A : B).name}</b> تتقدم في <b class="num">${Math.max(wa, wb)}</b> من <b class="num">${METRICS.length}</b>`;
    verdictEl.className = "verdict" + (wa === wb ? "" : wa > wb ? " wa" : " wb");
    anim(verdictEl, [{ opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0)" }], { duration: 600, delay: 240 + METRICS.length * 240 });
  }
  function marks() {
    $$("button", dock).forEach((b) => (b.dataset.in = b.dataset.t === A.t ? "a" : b.dataset.t === B.t ? "b" : ""));
    $$("button", presetsEl).forEach((b, i) => b.setAttribute("aria-pressed", String(PRESETS[i][0] === A.t && PRESETS[i][1] === B.t)));
    $$(".side", arena).forEach((s) => s.setAttribute("aria-pressed", String(!playing && s.dataset.slot === slot)));
  }
  function setPair(a, b, animate) {
    const ca = a !== A, cb = b !== B; A = a; B = b;
    if (ca || !animate) fill("a", A, animate);
    if (cb || !animate) fill("b", B, animate);
    races(); marks();
    $("#duel-names").innerHTML = `<span>${A.name}</span><i>×</i><span>${B.name}</span>`;
    if (mounts["c-radar"]) { mounts["c-radar"](); mounts["c-duel"](); }
  }
  function stop() { playing = false; clearTimeout(timer); playBtn.setAttribute("aria-pressed", "false"); playBtn.classList.remove("run"); $("span", playBtn).textContent = "شغّل العرض"; marks(); }
  function tickPlay() {
    clearTimeout(timer); if (!playing) return;
    playBtn.classList.remove("run"); void playBtn.offsetWidth; playBtn.classList.add("run");
    timer = setTimeout(() => { pi = (pi + 1) % PRESETS.length; setPair(byT[PRESETS[pi][0]], byT[PRESETS[pi][1]], true); tickPlay(); }, 6500);
  }
  function choose(t) {
    const c = byT[t]; if (!c || c === A || c === B) return; stop();
    if (slot === "a") { setPair(c, B, true); slot = "b"; } else { setPair(A, c, true); slot = "a"; }
    marks();
  }
  dock.innerHTML = sorted.map((c) => `<button type="button" data-t="${c.t}" aria-label="${c.name}، الدرجة ${F.num(c.score, 0)}"><b>${short(c)}</b><span class="num">${F.num(c.score, 0)}</span></button>`).join("");
  presetsEl.innerHTML = PRESETS.map((p) => `<button type="button" aria-pressed="false">${short(byT[p[0]])} × ${short(byT[p[1]])}</button>`).join("");
  dock.addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) choose(b.dataset.t); });
  dock.addEventListener("wheel", (e) => { if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) { dock.scrollLeft += e.deltaY; e.preventDefault(); } }, { passive: false });
  presetsEl.addEventListener("click", (e) => { const b = e.target.closest("button"); if (!b) return; stop(); pi = $$("button", presetsEl).indexOf(b); setPair(byT[PRESETS[pi][0]], byT[PRESETS[pi][1]], true); });
  arena.addEventListener("click", (e) => { const s = e.target.closest(".side"); if (!s) return; stop(); slot = s.dataset.slot; marks(); });
  playBtn.addEventListener("click", () => { if (playing) return stop(); playing = true; playBtn.setAttribute("aria-pressed", "true"); $("span", playBtn).textContent = "أوقف العرض"; marks(); tickPlay(); });
  document.addEventListener("visibilitychange", () => { if (document.hidden) clearTimeout(timer); else if (playing) tickPlay(); });
  mount("c-radar", (W) => radar(W, [[A.comp, C.cream], [B.comp, C.gold]]));
  mount("c-duel", (W) => timeline(W, [[A, C.cream], [B, C.gold]]));
  setPair(A, B, false);
  if (playing) { playBtn.setAttribute("aria-pressed", "true"); $("span", playBtn).textContent = "أوقف العرض"; setTimeout(tickPlay, 2400); } else stop();
  function compareWith(t) { const c = byT[t]; if (!c) return; stop(); if (c !== A && c !== B) { setPair(A, c, true); slot = "a"; marks(); } scrollTo({ top: 0, behavior: STILL ? "auto" : "smooth" }); }

  /* ───── quiz ───── */
  const pool = D.companies.flatMap((c) => c.events.filter((e) => e[3] != null && e[6] != null && Math.abs(e[3]) > 0.004).map((e) => ({ c, e })));
  const top = D.companies.flatMap((c) => c.events.filter((e) => e[2] === 5 && e[3] != null)), topUp = top.filter((e) => e[3] > 0).length / top.length;
  const qc = $("#quiz-card"), qs = $("#quiz-score"); let q = null, right = 0, total = 0, streak = 0;
  function ask() {
    q = pool[Math.floor(Math.random() * pool.length)]; const { c, e } = q, beat = e[5] - e[6];
    qc.innerHTML = `<div><h3>${c.name}</h3><p class="quiz-meta">${c.sector} · ${arDate(e[0])}</p><div class="quiz-facts"><span>الربحية المعلنة<b class="num">${F.num(e[5], 2)}</b></span><span>المتوقعة<b class="num">${F.num(e[6], 2)}</b></span><span>${beat >= 0 ? "فوق التوقعات" : "تحت التوقعات"}<b class="num ${cls(beat)}">${minus((beat >= 0 ? "+" : "") + beat.toFixed(2))}</b></span></div></div><div class="quiz-gauge" id="q-gauge"></div><div class="quiz-act"><button type="button" class="btn go-up" data-g="1">▲ ارتفع</button><button type="button" class="btn go-dn" data-g="-1">▼ نزل</button></div>`;
    gauge($("#q-gauge"), e[1], "درجة الإعلان");
    anim(qc, [{ opacity: 0, transform: "translateY(.8rem)", filter: "blur(6px)" }, { opacity: 1, transform: "none", filter: "blur(0)" }], { duration: 600 });
  }
  qc.addEventListener("click", (ev) => {
    const b = ev.target.closest("button"); if (!b) return;
    if (b.dataset.next) return ask();
    const g = +b.dataset.g, { e } = q, ok = g > 0 === e[3] > 0; total++; if (ok) { right++; streak++; } else streak = 0;
    $(".quiz-act", qc).outerHTML = `<p class="quiz-result ${ok ? "up" : "dn"}">${ok ? "صح." : "لا."} السهم ${e[3] > 0 ? "ارتفع" : "نزل"} <span class="num">${(Math.abs(e[3]) * 100).toFixed(2)}%</span> ${e[3] > 0 ? "فوق" : "تحت"} المتوقع في ثلاثة أيام.</p><div class="quiz-act"><button type="button" class="btn solid" data-next="1">إعلان ثاني</button></div>`;
    qs.innerHTML = `أصبت <b class="num">${right}</b> من <b class="num">${total}</b>${streak > 1 ? ` · <b class="num">${streak}</b> صح ورا بعض` : ""}. للمقارنة: الإعلانات الأعلى درجة ارتفعت في <b class="num">${F.pct0(topUp)}</b> من المرات.`;
    $("[data-next]", qc).focus();
  });
  ask();

  /* ───── company sheet ───── */
  const sheet = $("#sheet"), back = $("#sheet-back"); let lastFocus = null;
  function openSheet(t, from) {
    const c = byT[t]; if (!c) return; lastFocus = from || document.activeElement;
    const rows = c.events.slice().reverse().slice(0, 6);
    sheet.innerHTML = `<button type="button" class="sheet-x" aria-label="إغلاق"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6 6 18"/></svg></button>
      <div class="sheet-top"><div><h3 id="sheet-name">${c.name}</h3><p class="meta">${c.sector} · <span class="num">${c.t}</span></p><button type="button" class="btn ghost sheet-cmp" data-cmp="${c.t}">قارنها في الحلبة</button></div><div id="s-gauge"></div></div>
      <dl class="figs"><div><dt>إعلانات في العينة</dt><dd>${c.n}</dd></div><div><dt>يوم الإعلان</dt><dd class="${cls(c.react)}">${F.pct(c.react)}</dd></div><div><dt>بعد 60 يوم</dt><dd class="${cls(c.drift)}">${F.pct(c.drift)}</dd></div><div><dt>نسبة الارتفاع يوم الإعلان</dt><dd>${F.pct0(c.up)}</dd></div><div><dt>بيتا</dt><dd>${F.num(c.beta, 2)}</dd></div><div><dt>أعلى درجة</dt><dd>${F.num(Math.max(...c.events.map((e) => e[1])), 1)}</dd></div></dl>
      <h4>درجة كل إعلان</h4><div class="chart" id="s-line"></div><p class="readout" id="s-read" aria-live="polite"></p>
      <h4>وين قوتها</h4><div class="chart" id="s-radar"></div>
      <h4>آخر الإعلانات</h4><table class="evs"><thead><tr><th>التاريخ</th><th>الدرجة</th><th>يوم الإعلان</th><th>بعد 60 يوم</th></tr></thead><tbody>${rows.map((e) => `<tr><td>${e[0]}</td><td>${F.num(e[1], 1)}</td><td class="${cls(e[3])}">${F.pct(e[3])}</td><td class="${cls(e[4])}">${e[4] == null ? "—" : F.pct(e[4])}</td></tr>`).join("")}</tbody></table>`;
    sheet.hidden = false; back.hidden = false; void sheet.offsetWidth; sheet.classList.add("on"); back.classList.add("on"); document.body.style.overflow = "hidden";
    gauge($("#s-gauge"), c.score, "متوسط الدرجة");
    const read = $("#s-read"), pick = (i) => { const e = c.events[i]; read.innerHTML = `<span>${arDate(e[0])}</span><span>الدرجة <b>${F.num(e[1], 1)}</b></span><span>يوم الإعلان <b class="${cls(e[3])}">${F.pct(e[3])}</b></span><span>بعد 60 يوم <b class="${cls(e[4])}">${e[4] == null ? "لم تكتمل" : F.pct(e[4])}</b></span>`; };
    pick(c.events.length - 1);
    mount("s-line", (W) => timeline(W, [[c, C.gold]], pick)); mount("s-radar", (W) => radar(W, [[c.comp, C.gold]]));
    $(".sheet-x", sheet).focus();
    const u = new URL(location.href); u.searchParams.set("c", c.t); history.replaceState(null, "", u);
  }
  function closeSheet() {
    if (sheet.hidden) return; sheet.classList.remove("on"); back.classList.remove("on"); document.body.style.overflow = "";
    setTimeout(() => { sheet.hidden = true; back.hidden = true; }, 450);
    const u = new URL(location.href); u.searchParams.delete("c"); history.replaceState(null, "", u);
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  back.addEventListener("click", closeSheet);
  sheet.addEventListener("click", (e) => { const cmp = e.target.closest("[data-cmp]"); if (cmp) { lastFocus = null; closeSheet(); compareWith(cmp.dataset.cmp); } else if (e.target.closest(".sheet-x")) closeSheet(); });

  /* ───── search palette ───── */
  const pBack = $("#palette-back"), qIn = $("#q"), pList = $("#palette-list"); let act = 0;
  function results() {
    const term = qIn.value.trim().toLowerCase(), hit = D.companies.filter((c) => !term || c.name.toLowerCase().includes(term) || c.t.includes(term) || c.sector.includes(term)).slice(0, 40);
    act = Math.min(act, Math.max(0, hit.length - 1));
    pList.innerHTML = hit.length ? hit.map((c, i) => `<button type="button" data-t="${c.t}" class="${i === act ? "act" : ""}"><b>${c.name}</b><small>${c.sector} · <span class="num">${c.t}</span></small></button>`).join("") : "<p>ما لقينا شركة بهالاسم أو الرمز في العينة. جرّب جزء من الاسم.</p>";
    const a = $(".act", pList); if (a) a.scrollIntoView({ block: "nearest" });
  }
  function openPal(from) { lastFocus = from || document.activeElement; pBack.hidden = false; void pBack.offsetWidth; pBack.classList.add("on"); qIn.value = ""; act = 0; results(); qIn.focus(); }
  function closePal() { if (pBack.hidden) return; pBack.classList.remove("on"); setTimeout(() => (pBack.hidden = true), 350); }
  $$("[data-open-search]").forEach((b) => b.addEventListener("click", () => openPal(b)));
  qIn.addEventListener("input", () => { act = 0; results(); });
  pBack.addEventListener("click", (e) => { const b = e.target.closest("button[data-t]"); if (b) { closePal(); openSheet(b.dataset.t, lastFocus); } else if (e.target === pBack) closePal(); });
  addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openPal(); return; }
    if (e.key === "Escape") { closePal(); closeSheet(); return; }
    if (pBack.hidden) return;
    const n = $$("button", pList).length; if (!n) return;
    if (e.key === "ArrowDown") { e.preventDefault(); act = (act + 1) % n; results(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); act = (act - 1 + n) % n; results(); }
    else if (e.key === "Enter") { e.preventDefault(); const b = $(".act", pList); if (b) { closePal(); openSheet(b.dataset.t, lastFocus); } }
  });

  /* ───── scroll reveals, spotlight, nav ───── */
  $$("h2.split").forEach((h) => { const ws = split(h); if (STILL) return; ws.forEach((w) => (w.style.opacity = 0)); new IntersectionObserver((es, io) => es.forEach((e) => { if (e.isIntersecting) { io.disconnect(); ws.forEach((w) => (w.style.opacity = "")); wordsIn(ws, 0); } }), { rootMargin: "0px 0px -12% 0px" }).observe(h); });
  const rvs = $$(".stat, .board-bar, .rows li, .duel-card, .quiz-card, .lead, details");
  rvs.forEach((n, i) => { n.classList.add("rv"); n.style.setProperty("--d", Math.min(i % 8, 7) * 60 + "ms"); });
  if (STILL) rvs.forEach((n) => n.classList.add("on"));
  else { const rio = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { rio.unobserve(e.target); e.target.classList.add("on"); } }), { rootMargin: "0px 0px -8% 0px" }); rvs.forEach((n) => rio.observe(n)); }
  addEventListener("pointermove", (e) => { const s = e.target.closest && e.target.closest(".spot"); if (!s) return; const r = s.getBoundingClientRect(); s.style.setProperty("--mx", e.clientX - r.left + "px"); s.style.setProperty("--my", e.clientY - r.top + "px"); }, { passive: true });
  const nav = $("#nav"); let lastY = 0;
  addEventListener("scroll", () => { const y = scrollY; nav.classList.toggle("hide", y > lastY && y > 500); lastY = y; }, { passive: true });
  const links = $$(".nav nav a"), spy = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) links.forEach((a) => (a.getAttribute("href") === "#" + e.target.id ? a.setAttribute("aria-current", "true") : a.removeAttribute("aria-current"))); }), { rootMargin: "-40% 0px -55% 0px" });
  $$("main > section[id]").forEach((s) => spy.observe(s));

  const want = new URLSearchParams(location.search).get("c"); if (want && byT[want]) setTimeout(() => openSheet(want), STILL ? 0 : 1500);
})();
