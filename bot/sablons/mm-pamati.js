// ---------- MM Homes: PAMATU UN KOMUNIKĀCIJU PLĀNS (stabveida pamati) ----------
// Dati: model.json projekts.pamatu_plans (redaktorā cilne Māja → Konstrukcijas → Pamatu plāns)
//   skice / ar: lapa skiču projektā / AR daļā; skati: { stabi, vainags, kopa }
//   d: staba diametrs, uz: uzlaide uz iekšu no C24 karkasa ārmalas, nx / ny: kolonas / rindas (tukšs = solis ≤ 1200)
//   stu: papildu stabi perimetra malējos laidumos, mov: { atslēga: [dx, dy] }, del: [atslēga], ext: [[x, y]] papildu stabi
//   vb / vh: vainaga dēlis (platums guļus × biezums), kom: [{ n, c, side, x, y, sym }] komunikāciju pievadi
// Koordinātas mm no ass 1 (rietumi) un ass A (ziemeļi), tāpat kā plānā.
const PAM_TXT = {
  lv: { title: "Pamatu un komunikāciju plāns", stabi: "STABU PLĀNS", vainags: "VAINAGA PLĀNS", kopa: "STABI UN 1. STĀVA PLĀNOJUMS", outer: "STABU ĀRĒJAIS IZMĒRS",
        count: "STABU SKAITS", post: "Stabveida pamati", uz: "uzlaide", rim: "Vainags C24", perim: "perimetrs", mid: "starplikas", pcs: "gab.",
        n1: "Izmēri pa stabu centriem, mm. Stabu malējā ārmala pret C24 karkasa ārmalu", n2: "Vainaga ārmala pa C24 karkasa ārmalu, stūri 45°. Starplikas pa stabu centriem.",
        n3: "Komunikāciju ievadu vietas precizēt objektā.", sheet: "PAMATU PLĀNS" },
  en: { title: "Foundation and services plan", stabi: "POST PLAN", vainags: "RIM BEAM PLAN", kopa: "POSTS AND GROUND FLOOR LAYOUT", outer: "POSTS OUTER SIZE",
        count: "NUMBER OF POSTS", post: "Post foundation", uz: "inset", rim: "Rim beam C24", perim: "perimeter", mid: "joists", pcs: "pcs",
        n1: "Dimensions to post centres, mm. Outer post edge relative to C24 frame outer face", n2: "Rim beam outer edge on the C24 frame outer face, 45° corners. Joists on post centres.",
        n3: "Service entry points to be confirmed on site.", sheet: "FOUNDATION PLAN" },
};
const PAM_KOM = [
  { n: "Ūdens ievads", c: "#1f5fd6", side: "n", fx: .62, fy: .18, sym: "ievads" },
  { n: "Kanalizācija", c: "#7a4a2a", side: "e", fx: .94, fy: .22, sym: "kan" },
  { n: "Elektrības ievads", c: "#d62828", side: "w", fx: .1, fy: .55, sym: "ievads" },
];
const pamPP = () => (window.AR && AR.projekts && AR.projekts.pamatu_plans) || null;
const pamOn = where => { const P = (window.AR && AR.projekts) || {}, PP = pamPP(); return !!(PP && PP[where] && P.pamati !== "platne" && pamViews(PP).length); };
const pamViews = PP => ["stabi", "vainags", "kopa"].filter(k => (PP.skati || { stabi: true })[k]);
// C24 karkasa ārmala no fasādes: ārsienas slāņi pirms karkasa (apdare, latojums)
function pamC24() {
  const PP = pamPP() || {};
  if (PP.c24 != null) return +PP.c24;
  const S = (window.AR && AR.layers && AR.layers.S1 && AR.layers.S1.layers) || [];
  const i = S.findIndex(l => /karkas/i.test(l[0]));
  return i > 0 ? S.slice(0, i).reduce((a, l) => a + (+l[1] || 0), 0) : 71;
}
// stabu izkārtojums: režģis pa centriem + perimetra malējo laidumu papildu stabi + pārbīdes + papildu stabi
function pamLayout(v, PP) {
  const d = +PP.d || 120, uz = PP.uzOn ? (PP.uz != null ? +PP.uz : 10) : 0, off = pamC24();   // uzlaide tikai ar ķeksīti
  const x0 = off, y0 = off, x1 = v.W - off, y1 = v.D - off;
  const cx0 = x0 + uz + d / 2, cx1 = x1 - uz - d / 2, cy0 = y0 + uz + d / 2, cy1 = y1 - uz - d / 2;
  const auto = L => Math.max(2, Math.ceil(L / 1200) + 1);
  const nx = Math.max(2, Math.round(+PP.nx) || auto(cx1 - cx0)), ny = Math.max(2, Math.round(+PP.ny) || auto(cy1 - cy0));
  const sx = (cx1 - cx0) / (nx - 1), sy = (cy1 - cy0) / (ny - 1);
  const GX = [...Array(nx)].map((_, i) => cx0 + i * sx), GY = [...Array(ny)].map((_, j) => cy0 + j * sy);
  const pts = [], seen = new Set(), mov = PP.mov || {}, del = new Set(PP.del || []);
  // visas rindas (rmov) vai kolonas (cmov) pārbīde: [dx, dy]
  const RM = j => (PP.rmov || {})[j] || [0, 0], CM = i => (PP.cmov || {})[i] || [0, 0];
  const add = (key, x, y, kind, o = [0, 0]) => { if (seen.has(key) || del.has(key)) return; seen.add(key); const m = mov[key] || [0, 0]; pts.push({ key, x: x + o[0] + m[0], y: y + o[1] + m[1], x0: x, y0: y, kind, moved: !!(m[0] || m[1]) }); };
  GY.forEach((y, j) => GX.forEach((x, i) => add(`${i},${j}`, x, y, "g", [RM(j)[0] + CM(i)[0], RM(j)[1] + CM(i)[1]])));
  if (PP.stu !== false) {
    const bx = nx > 2 ? [0, nx - 2] : [0], by = ny > 2 ? [0, ny - 2] : [0];
    [0, ny - 1].forEach(j => bx.forEach(i => add(`a${i},${j}`, (GX[i] + GX[i + 1]) / 2, GY[j], "h", [RM(j)[0] + (CM(i)[0] + CM(i + 1)[0]) / 2, RM(j)[1]])));
    [0, nx - 1].forEach(i => by.forEach(j => add(`b${i},${j}`, GX[i], (GY[j] + GY[j + 1]) / 2, "h", [CM(i)[0], CM(i)[1] + (RM(j)[1] + RM(j + 1)[1]) / 2])));
  }
  // papildu stabi: [x, y] brīvi vai { c: [i, j], t, o } laukuma vidū starp 4 stabiem (piem. kamīnam), ar krustu un atsauci
  const cells = [];
  (PP.ext || []).forEach((q, n) => {
    if (Array.isArray(q)) return add(`e${n}`, q[0], q[1], "e");
    const i = Math.max(0, Math.min(nx - 2, q.c[0])), j = Math.max(0, Math.min(ny - 2, q.c[1])), P4 = [[i, j], [i + 1, j], [i + 1, j + 1], [i, j + 1]].map(([a, b]) => pts.find(p => p.key === `${a},${b}`) || { x: GX[a], y: GY[b] });
    const cx = P4.reduce((a, p) => a + p.x, 0) / 4, cy = P4.reduce((a, p) => a + p.y, 0) / 4, o = q.o || [0, 0];
    add(`e${n}`, cx + o[0], cy + o[1], "e"); cells.push({ key: `e${n}`, P4, x: cx + o[0], y: cy + o[1], t: q.t == null ? "Papildu stabs kamīnam" : q.t });
  });
  const GXv = GX.map((x, i) => x + CM(i)[0]);   // vainaga starplikas seko kolonu pārbīdei
  return { d, uz, off, x0, y0, x1, y1, nx, ny, sx, sy, GX, GY, GXv, pts, cells, cx0, cx1, cy0, cy1 };
}

// ---- zīmēšanas palīgi (modeļa mm, k = lapas mm uz modeļa mm) ----
function pamDim(g, k, pts, at, horiz, o = {}) {   // mērķēde: punkti pa ass virzienu, līnija pozīcijā at
  const s = 1 / k, col = o.col || C.ink, sw = .16 * s, fs = (o.fs || 2.1) * s, tk = .9 * s;
  const xs = [...new Set(pts.map(p => Math.round(p * 10) / 10))].sort((a, b) => a - b);
  if (xs.length < 2) return;
  const L = (a1, b1, a2, b2, w = sw) => el("line", horiz ? { x1: a1, y1: b1, x2: a2, y2: b2, stroke: col, "stroke-width": w } : { x1: b1, y1: a1, x2: b2, y2: a2, stroke: col, "stroke-width": w }, g);
  L(xs[0] - 1.2 * s, at, xs[xs.length - 1] + 1.2 * s, at);
  xs.forEach(x => { L(x - tk, at + tk, x + tk, at - tk, .3 * s); if (o.ext != null) L(x, o.ext, x, at + (o.ext > at ? 1.2 * s : -1.2 * s)); });
  for (let i = 0; i + 1 < xs.length; i++) {
    const a = xs[i], b = xs[i + 1], m = (a + b) / 2, t = o.label && xs.length === 2 ? o.label : String(Math.round(b - a)), sm = (b - a) * k < t.length * 1.15 * (o.fs || 2.1) / 2.1 + 1;
    const off = (o.side || -1) * (sm && i % 2 ? 3.6 : .9) * s;
    if (horiz) T_(g, m, at + off + (o.side > 0 ? fs * .8 : 0), t, { fs, a: "middle", fill: col, fw: o.fw });
    else T_(g, 0, 0, t, { fs, a: "middle", fill: col, fw: o.fw, tr: `translate(${at + off + (o.side > 0 ? fs * .8 : 0)} ${m}) rotate(-90)` });
  }
}
function pamAxes(g, v, k, ext) {   // asis 1..n, A..n ar apļiem
  const s = 1 / k, dash = { stroke: C.axis, "stroke-width": .18 * s, "stroke-dasharray": `${4 * s} ${1 * s} ${.6 * s} ${1 * s}` };
  const bub = (cx, cy, n) => { el("circle", { cx, cy, r: 2.8 * s, fill: "#fff", stroke: C.ink, "stroke-width": .2 * s }, g); T_(g, cx, cy + 1.1 * s, n, { a: "middle", fs: 3 * s, fw: 500 }); };
  (v.axes.x || []).forEach(([x, n]) => { el("line", { x1: x, y1: -ext.n, x2: x, y2: v.D + ext.s, ...dash }, g); bub(x, -ext.n - 2.8 * s, n); });
  (v.axes.y || []).forEach(([y, n]) => { el("line", { x1: -ext.w, y1: y, x2: v.W + ext.e, y2: y, ...dash }, g); bub(-ext.w - 2.8 * s, y, n); });
}
function pamPosts(g, L, k, tag) {
  const s = 1 / k;
  L.pts.forEach(p => el("circle", { cx: p.x, cy: p.y, r: L.d / 2, fill: "#8a8d90", stroke: C.ink, "stroke-width": .2 * s, ...(tag ? { "data-pst": p.key } : {}) }, g));
}
function pamCells(g, L, k) {   // laukuma vidus stabs: raustīts krusts pār laukumu un atsauce ar tekstu
  const s = 1 / k;
  L.cells.forEach(c => {
    const st = { stroke: "#2e8b57", "stroke-width": .2 * s, "stroke-dasharray": `${1.4 * s} ${.9 * s}` };
    el("line", { x1: c.P4[0].x, y1: c.P4[0].y, x2: c.P4[2].x, y2: c.P4[2].y, ...st }, g);
    el("line", { x1: c.P4[1].x, y1: c.P4[1].y, x2: c.P4[3].x, y2: c.P4[3].y, ...st }, g);
    if (!c.t) return;
    const ex = Math.max(c.x, L.x1) + 6 * s, ey = c.y - 6 * s, w = (c.t.length * 1.05 + 2) * s;
    el("polyline", { points: `${c.x} ${c.y} ${Math.max(c.x, L.x1) + 2 * s} ${ey} ${ex} ${ey}`, fill: "none", stroke: "#2e8b57", "stroke-width": .2 * s }, g);
    el("rect", { x: ex, y: ey - 1.6 * s, width: w, height: 3.2 * s, fill: "#fff", stroke: "#2e8b57", "stroke-width": .2 * s }, g);
    T_(g, ex + w / 2, ey + .65 * s, c.t.toUpperCase(), { fs: 1.75 * s, a: "middle", fw: 600, fill: "#2e8b57" });
  });
}
function pamContour(g, L, k, dash) {
  el("rect", { x: L.x0, y: L.y0, width: L.x1 - L.x0, height: L.y1 - L.y0, fill: "none", stroke: C.ink, "stroke-width": .3 / k, ...(dash ? { "stroke-dasharray": `${2 / k} ${1 / k}` } : {}) }, g);
}

// 1) stabu plāns ar izmēriem
function pamViewStabi(g, v, L, k, tx) {
  const s = 1 / k, A = v.axes.x.map(a => a[0]), B = v.axes.y.map(a => a[0]);
  pamAxes(g, v, k, { n: 26 * s, s: 6 * s, w: 26 * s, e: 6 * s });
  pamContour(g, L, k);
  // režģa līnijas pa stabu centriem
  const gl = { stroke: "#9a9a9a", "stroke-width": .12 * s, "stroke-dasharray": `${2.2 * s} ${1.2 * s}` };
  L.GX.forEach(x => el("line", { x1: x, y1: L.y0 - 2 * s, x2: x, y2: L.y1 + 2 * s, ...gl }, g));
  L.GY.forEach(y => el("line", { x1: L.x0 - 2 * s, y1: y, x2: L.x1 + 2 * s, y2: y, ...gl }, g));
  // diagonāles pa malējo stabu centriem
  const P = key => L.pts.find(p => p.key === key);
  const c = [P("0,0"), P(`${L.nx - 1},0`), P(`${L.nx - 1},${L.ny - 1}`), P(`0,${L.ny - 1}`)];
  [[c[0], c[2], .3], [c[1], c[3], .7]].forEach(([a, b, f]) => {
    if (!a || !b) return;
    el("line", { x1: a.x, y1: a.y, x2: b.x, y2: b.y, stroke: "#5b7fa8", "stroke-width": .15 * s, "stroke-dasharray": `${1.2 * s} ${.8 * s}` }, g);
    const mx = a.x + (b.x - a.x) * f, my = a.y + (b.y - a.y) * f, ang = Math.atan2(b.y - a.y, b.x - a.x) * 180 / Math.PI, an = ang > 90 || ang < -90 ? ang + 180 : ang;
    const t = String(Math.round(Math.hypot(b.x - a.x, b.y - a.y))), w = t.length * 1.15 * s + 1.2 * s;
    const tg = el("g", { transform: `translate(${mx} ${my}) rotate(${an})` }, g);
    el("rect", { x: -w / 2, y: -2.6 * s, width: w, height: 2.4 * s, fill: "#fff" }, tg);
    T_(tg, 0, -.8 * s, t, { fs: 2.1 * s, a: "middle", fill: "#2f5b8a" });
  });
  pamCells(g, L, k);
  pamPosts(g, L, k, true);
  // mērķēdes: augšā un kreisajā pusē (no āra uz iekšu: asis, stabu ārējais izmērs, stabi pa centriem)
  const top = L.pts.filter(p => Math.abs(p.y0 - L.cy0) < 1).map(p => p.x), left = L.pts.filter(p => Math.abs(p.x0 - L.cx0) < 1).map(p => p.y);
  const ox0 = L.cx0 - L.d / 2, ox1 = L.cx1 + L.d / 2, oy0 = L.cy0 - L.d / 2, oy1 = L.cy1 + L.d / 2;
  pamDim(g, k, A, -19 * s, true, { ext: -21 * s, fw: 600 });
  pamDim(g, k, [ox0, ox1], -13 * s, true, { label: `${Math.round(ox1 - ox0)} ${tx.outer}`, ext: L.y0 });
  pamDim(g, k, top, -7 * s, true, { ext: L.y0 });
  pamDim(g, k, B, -19 * s, false, { ext: -21 * s, fw: 600 });
  pamDim(g, k, [oy0, oy1], -13 * s, false, { label: `${Math.round(oy1 - oy0)} ${tx.outer}`, ext: L.x0 });
  pamDim(g, k, left, -7 * s, false, { ext: L.x0 });
  // pārbīdītie stabi: mēri līdz kaimiņiem rindā un kolonā
  L.pts.filter(p => p.moved).forEach(p => {
    const row = L.pts.filter(q => Math.abs(q.y0 - p.y0) < 1).map(q => q.x).sort((a, b) => a - b), col = L.pts.filter(q => Math.abs(q.x0 - p.x0) < 1).map(q => q.y).sort((a, b) => a - b);
    const nb = (arr, v0) => { const i = arr.indexOf(v0); return arr.slice(Math.max(0, i - 1), i + 2); };
    if (p.x !== p.x0) pamDim(g, k, nb(row, p.x), p.y + 3.2 * s, true, { col: "#d9480f", fs: 1.9 });
    if (p.y !== p.y0) pamDim(g, k, nb(col, p.y), p.x + 3.2 * s, false, { col: "#d9480f", fs: 1.9 });
  });
}

// 2) vainaga plāns
function pamRim(L) {
  const PP = pamPP() || {}, b = +PP.vb || 145, h = +PP.vh || 45;
  const mids = L.GXv.slice(1, -1);
  return { b, h, mids, lx: L.x1 - L.x0, ly: L.y1 - L.y0, lm: L.y1 - L.y0 - 2 * b };
}
function pamViewVainags(g, v, L, k, tx) {
  const s = 1 / k, R = pamRim(L), A = v.axes.x.map(a => a[0]);
  pamAxes(g, v, k, { n: 20 * s, s: 6 * s, w: 14 * s, e: 6 * s });
  el("rect", { x: 0, y: 0, width: v.W, height: v.D, fill: "none", stroke: "#b5b5b5", "stroke-width": .15 * s, "stroke-dasharray": `${1.5 * s} ${1 * s}` }, g);
  pamPosts(g, L, k, false);
  const wood = { fill: "rgba(222,196,150,.55)", stroke: C.ink, "stroke-width": .22 * s };
  const { x0, y0, x1, y1 } = L, b = R.b;
  [[[x0, y0], [x1, y0], [x1 - b, y0 + b], [x0 + b, y0 + b]], [[x1, y0], [x1, y1], [x1 - b, y1 - b], [x1 - b, y0 + b]],
   [[x1, y1], [x0, y1], [x0 + b, y1 - b], [x1 - b, y1 - b]], [[x0, y1], [x0, y0], [x0 + b, y0 + b], [x0 + b, y1 - b]]]
    .forEach(q => el("polygon", { points: q.map(p => p.join(" ")).join(" "), ...wood }, g));
  R.mids.forEach(x => el("rect", { x: x - b / 2, y: y0 + b, width: b, height: y1 - y0 - 2 * b, ...wood }, g));
  // marķējums V1 (perimetrs W-A), V2 (perimetrs Z-D), V3 (starplikas)
  const tag = (x, y, t) => { el("circle", { cx: x, cy: y, r: 2 * s, fill: "#fff", stroke: C.ink, "stroke-width": .18 * s }, g); T_(g, x, y + .75 * s, t, { fs: 1.9 * s, a: "middle", fw: 600 }); };
  tag((x0 + x1) / 2 + (R.mids.length % 2 ? L.sx / 2 : 0), y0 + b / 2, "V1"); tag((x0 + x1) / 2 + (R.mids.length % 2 ? L.sx / 2 : 0), y1 - b / 2, "V1");
  tag(x0 + b / 2, (y0 + y1) / 2, "V2"); tag(x1 - b / 2, (y0 + y1) / 2, "V2");
  R.mids.forEach((x, i) => { if (i % 2 === 0 || R.mids.length < 4) tag(x, (y0 + y1) / 2 + (i % 2 ? 4 * s : 0), "V3"); });
  pamDim(g, k, A, -14 * s, true, { ext: -16 * s, fw: 600 });
  pamDim(g, k, [x0, x1], -8 * s, true, { ext: y0 });
  pamDim(g, k, [x0, ...R.mids, x1], -3 * s, true, { ext: y0, fs: 1.9 });
  pamDim(g, k, [y0, y1], -8 * s, false, { ext: x0 });
  pamDim(g, k, [y0, y0 + b, y1 - b, y1], -3 * s, false, { ext: x0, fs: 1.9 });
}

// 3) stabi + 1. stāva plānojums (raustīts) + komunikāciju pievadi
function pamKom(v) {
  const PP = pamPP() || {};
  return (PP.kom || PAM_KOM.map(q => ({ n: q.n, c: q.c, side: q.side, x: Math.round(v.W * q.fx / 10) * 10, y: Math.round(v.D * q.fy / 10) * 10, sym: q.sym })));
}
function pamViewKopa(g, v, L, k, tx) {
  const s = 1 / k, A = v.axes.x.map(a => a[0]), B = v.axes.y.map(a => a[0]);
  const KM = pamKom(v), cnt = { n: 0, s: 0, w: 0, e: 0 };
  KM.forEach(q => cnt[q.side] = (cnt[q.side] || 0) + 1);
  const ext = { n: (14 + 7 * cnt.n) * s, s: (6 + 7 * cnt.s) * s, w: (14 + 7 * cnt.w) * s, e: (6 + 7 * cnt.e) * s };
  pamAxes(g, v, k, ext);
  // sienas: ārējā kontūra un telpu iekšējās virsmas, tušētas
  const dl = { fill: "none", stroke: "#555", "stroke-width": .2 * s, "stroke-dasharray": `${1.6 * s} ${.9 * s}` };
  el("polygon", { points: (v.poly || [[0, 0], [v.W, 0], [v.W, v.D], [0, v.D]]).map(p => p.join(" ")).join(" "), ...dl }, g);
  if (!AR.projekts.tikai_pamati) (v.rooms || []).forEach(rm => (rm.r || []).forEach(q => el("rect", { x: q[0], y: q[1], width: q[2], height: q[3], ...dl }, g)));
  if (!AR.projekts.tikai_pamati) (v.rooms || []).filter(rm => !rm.void).forEach(rm => { const q = rm.r[0]; if (q) T_(g, q[0] + q[2] / 2, q[1] + q[3] / 2, rm.n, { fs: 1.7 * s, a: "middle", fill: "#888" }); });
  pamContour(g, L, k, true);
  pamCells(g, L, k);
  pamPosts(g, L, k, true);
  pamDim(g, k, A, -8 * s, true, { ext: -10 * s, fw: 600 });
  pamDim(g, k, B, -8 * s, false, { ext: -10 * s, fw: 600 });
  // komunikācijas: līnija no ārpuses līdz galapunktam, simbols, nosaukums krāsainā rāmī, piesaiste asīm
  const used = { n: 0, s: 0, w: 0, e: 0 };
  KM.forEach(q => {
    const c = q.c || "#1f5fd6", sd = q.side || "n", lane = 12 * s + 7 * s * used[sd]++, x = +q.x || 0, y = +q.y || 0;
    const out = sd === "n" ? [x, -lane - 4 * s] : sd === "s" ? [x, v.D + lane + 4 * s] : sd === "w" ? [-lane - 4 * s, y] : [v.W + lane + 4 * s, y];
    el("line", { x1: out[0], y1: out[1], x2: x, y2: y, stroke: c, "stroke-width": .55 * s }, g);
    if (q.sym === "kan") el("circle", { cx: x, cy: y, r: 1.1 * s, fill: c, stroke: C.ink, "stroke-width": .12 * s }, g);
    else if (q.sym === "kolektors") el("rect", { x: x - 2 * s, y: y - 1.2 * s, width: 4 * s, height: 2.4 * s, fill: c, stroke: C.ink, "stroke-width": .12 * s }, g);
    else el("rect", { x: x - 1.6 * s, y: y - .7 * s, width: 3.2 * s, height: 1.4 * s, fill: c }, g);
    const lw = (String(q.n || "").length * 1.05 + 2) * s, horiz = sd === "n" || sd === "s";
    const lx = horiz ? out[0] + .8 * s : sd === "w" ? out[0] - lw : out[0], ly = horiz ? (sd === "n" ? out[1] - 3 * s : out[1]) : out[1] - 3.2 * s;
    el("rect", { x: lx, y: ly, width: lw, height: 3 * s, fill: "#fff", stroke: c, "stroke-width": .2 * s }, g);
    T_(g, lx + lw / 2, ly + 2.15 * s, String(q.n || "").toUpperCase(), { fs: 1.75 * s, a: "middle", fw: 600, fill: c });
    // piesaiste: gar sienu no abām asīm, dziļums no tuvākās ass
    if (horiz) {
      const ay = sd === "n" ? -lane + 2.5 * s : v.D + lane - 2.5 * s;
      pamDim(g, k, [A[0], x, A[A.length - 1]], ay, true, { col: c, fs: 1.9, side: sd === "n" ? -1 : 1 });
      pamDim(g, k, [sd === "n" ? B[0] : B[B.length - 1], y], x + 2.5 * s, false, { col: c, fs: 1.9, side: 1 });
    } else {
      const ax = sd === "w" ? -lane + 2.5 * s : v.W + lane - 2.5 * s;
      pamDim(g, k, [B[0], y, B[B.length - 1]], ax, false, { col: c, fs: 1.9, side: sd === "w" ? -1 : 1 });
      pamDim(g, k, [sd === "w" ? A[0] : A[A.length - 1], x], y - 2.5 * s, true, { col: c, fs: 1.9 });
    }
  });
}

// skatu izvietojums apgabalā: visiem skatiem lapā vienādas malas, tāpēc asis sakrīt; mērogs lielākais standarta vai brīvs (maksimāli liels)
const PAM_PAD = { stabi: [30, 8, 32, 10], vainags: [24, 8, 20, 10], kopa: [0, 0, 0, 0] };   // [augša, apakša, kreisā, labā] lapas mm (asis, ķēdes)
const PAM_SC = [20, 25, 50, 75, 100, 125, 150, 200, 250, 300, 400];
function pamPad(v, key) {
  const lab = Math.max(0, ...((pamPP() || {}).ext || []).filter(q => !Array.isArray(q)).map(q => (q.t == null ? 21 : q.t.length) * 1.05 + 10));
  const p = pamPad0(v, key); if (key !== "vainags") p[3] = Math.max(p[3], lab); return p;
}
function pamPad0(v, key) {
  if (key !== "kopa") return PAM_PAD[key].slice();
  const KM = pamKom(v), cnt = { n: 0, s: 0, w: 0, e: 0 }; KM.forEach(q => cnt[q.side] = (cnt[q.side] || 0) + 1);
  const lw = sd => Math.max(0, ...KM.filter(q => q.side === sd).map(q => String(q.n || "").length * 1.05 + 2));
  return [20 + 7 * cnt.n, 10 + 7 * cnt.s, 20 + 7 * cnt.w + lw("w"), 10 + 7 * cnt.e + lw("e")];
}
function pamPlace(v, views, R, free) {   // R = [x, y, w, h]
  const HD = 9, pd = [0, 1, 2, 3].map(i => Math.max(...views.map(k => pamPad(v, k)[i])));
  const cw = k => pd[2] + pd[3] + v.W * k, ch = k => pd[0] + pd[1] + v.D * k + HD;
  let best = null;
  for (let cols = 1; cols <= views.length; cols++) {
    const rows = Math.ceil(views.length / cols);
    // lielākais k, kas ietilpst: (R.w - cols*(pd+pd)) / (cols*W) un tāpat augstumam
    const kmax = Math.min((R[2] - cols * (pd[2] + pd[3])) / (cols * v.W), (R[3] - rows * (pd[0] + pd[1] + HD)) / (rows * v.D));
    if (kmax <= 0) continue;
    const sc = free ? 1 / kmax : PAM_SC.find(d => 1 / d <= kmax + 1e-9) || 1 / kmax;
    if (!best || sc < best.sc) best = { sc, k: 1 / sc, cols, rows };
  }
  if (!best) best = { sc: 500, k: 1 / 500, cols: 1, rows: views.length };
  const W1 = cw(best.k), H1 = ch(best.k), gx = (R[2] - best.cols * W1) / best.cols, gy = (R[3] - best.rows * H1) / best.rows;
  const pos = views.map((key, i) => { const c = i % best.cols, r = Math.floor(i / best.cols), cx = R[0] + c * (W1 + gx) + gx / 2, cy = R[1] + r * (H1 + gy) + gy / 2;
    return { key, x: cx + pd[2], y: cy + pd[0], hx: cx, hy: cy + pd[0] + v.D * best.k + pd[1] + 6, w: W1 - 4 }; });
  return { ...best, pos };
}
// lapu sadalījums: PP.lapas = [["stabi", "vainags"], ["kopa"]]; tikai ieslēgtie skati, tukšās lapas izmet
function pamSheetsOf(PP) {
  const on = pamViews(PP), L = (PP.lapas || [on]).map(a => a.filter(k => on.includes(k))).filter(a => a.length);
  const rest = on.filter(k => !L.flat().includes(k)); if (rest.length) L.push(rest);
  return L;
}
function pamTitle(views, L0) { const T = PAM_TXT[L0]; return views.length === 3 ? T.title : views.map(k => T[k].toLowerCase()).join(L0 === "en" ? " and " : " un ").replace(/^./, c => c.toUpperCase()); }
function pamDraw(svg, v, R, views) {
  const L0 = window.MM_LANG === "en" ? "en" : "lv", tx = PAM_TXT[L0], PP = pamPP() || {}, Lay = pamLayout(v, PP), Rm = pamRim(Lay);
  const pl = pamPlace(v, views, R, !!PP.brivs), sct = PP.brivs ? (L0 === "en" ? "not to scale" : "bez mēroga") : "M 1:" + pl.sc;
  window.MM_PAM = { nx: Lay.nx, ny: Lay.ny, sx: Math.round(Lay.sx), sy: Math.round(Lay.sy), n: Lay.pts.length, d: Lay.d, uz: Lay.uz, c24: Lay.off, sc: Math.round(pl.sc) };
  window.MM_SCALE = Math.round(pl.sc); window.MM_SCALE_TXT = PP.brivs ? "–" : null;
  pl.pos.forEach(p => {
    const g = el("g", { "data-block": "pam-" + p.key, transform: `translate(${p.x} ${p.y}) scale(${pl.k})` }, svg);
    ({ stabi: pamViewStabi, vainags: pamViewVainags, kopa: pamViewKopa })[p.key](g, v, Lay, pl.k, tx);
    sheetHeading(svg, p.hx, p.hy, Math.min(p.w, 215), tx[p.key], sct);
  });
  return Lay;
}

// skiču projekts: A3 stāvus, tas pats MM rakstlaukums
function pamSheet(v, views) {
  const svg = el("svg", { viewBox: "0 0 297 420", class: "a3", role: "img", "aria-label": pamTitle(views, "lv"), "data-part": "pamati" });
  el("rect", { width: 297, height: 420, fill: "#fff" }, svg);
  el("rect", { x: 20, y: 10, width: 267, height: 400, fill: "none", stroke: C.ink, "stroke-width": .5 }, svg);
  el("line", { x1: 247, y1: 10, x2: 247, y2: 410, stroke: C.ink, "stroke-width": .35, "data-block": "title-strip" }, svg);
  pamDraw(svg, v, [26, 16, 216, 336], views);
  pamSpec(svg, v, 26, 356, 215, true);
  mmTitleBlock(svg, v, null, window.MM_LANG === "en" ? "en" : "lv");
  window.MM_SCALE_TXT = null;
  return svg;
}
// klienta lapa + ieslēgtās pamatu lapas; lapu numuri 1/n .. n/n
function mmSheets(pv) {
  const P = AR.projekts, only = !!P.tikai_pamati;   // projekts "Tikai stabu plāns": klienta lapas nav
  if (!pamOn("skice")) return only ? [pamSheet(pv, ["stabi"])] : [modelSheet(pv)];
  const keep = P.lapa, SH = pamSheetsOf(pamPP()), n = SH.length + (only ? 0 : 1), out = [];
  if (!only) { P.lapa = `1/${n}`; out.push(modelSheet(pv)); }
  SH.forEach((views, i) => { P.lapa = `${out.length + 1}/${n}`; out.push(pamSheet(pv, views)); });
  P.lapa = keep;
  return out;
}
// AR daļa: A3 guļus, AR rakstlaukums; daļas pam1, pam2, pam3 = pamatu lapas pēc sadalījuma
["pam1", "pam2", "pam3"].forEach((k, i) => { const PP = pamPP(); const SH = PP ? pamSheetsOf(PP) : []; AR_PARTS[k] = SH[i] ? pamTitle(SH[i], "lv") : PAM_TXT.lv.title; });
function pamArSheet(v, k, mk) {
  const PP = pamPP() || {}, views = pamSheetsOf(PP)[+k.slice(3) - 1] || ["stabi"];
  const pl = pamPlace(v, views, [26, 16, 378, 222], !!PP.brivs);
  const svg = mk(PP.brivs ? "-" : "1:" + pl.sc);
  pamDraw(svg, v, [26, 16, 378, 222], views);
  pamSpec(svg, v, 26, 246, 194, false);
  window.MM_SCALE = 100; window.MM_SCALE_TXT = null;
  return svg;
}

// specifikācija (stabi, vainaga dēļi ar tekošajiem metriem un m³) un automātiskās piezīmes lapas apakšā
function pamSpec(svg, v, x, y, w, mm) {
  const L0 = window.MM_LANG === "en" ? "en" : "lv", EN = L0 === "en", PP = pamPP() || {}, Lay = pamLayout(v, PP), R = pamRim(Lay);
  const HEAD = mm ? MM_DARK : C.ink, SOFT = mm ? MM_SOFT : "#f2f2f2", g = el("g", { "data-block": "pam-spec", transform: `translate(${x} ${y})` }, svg);
  const tw = Math.round(w * .56), nw = w - tw - 5, RH = 4.4, f = n => n.toFixed(2).replace(".", EN ? "." : ",");
  const sec = `${R.h}×${R.b}`, rows = [
    ["P1", (EN ? "Post foundation Ø" : "Stabveida pamati Ø") + Lay.d, String(Lay.pts.length), "–", "–"],
    ["V1", (EN ? `Rim beam C24 ${sec}, perimeter W–E` : `Vainags C24 ${sec}, perimetrs R–A`), "2", String(Math.round(R.lx)), f(2 * R.lx / 1000)],
    ["V2", (EN ? `Rim beam C24 ${sec}, perimeter N–S` : `Vainags C24 ${sec}, perimetrs Z–D`), "2", String(Math.round(R.ly)), f(2 * R.ly / 1000)],
    ...(R.mids.length ? [["V3", (EN ? `Joists C24 ${sec}, on post centres` : `Starplikas C24 ${sec}, pa stabu centriem`), String(R.mids.length), String(Math.round(R.lm)), f(R.mids.length * R.lm / 1000)]] : []),
  ];
  const lm = (2 * R.lx + 2 * R.ly + R.mids.length * R.lm) / 1000, m3 = lm * R.b * R.h / 1e6;
  // tabula
  const ca = ["start", "start", "end", "end", "end"], cxx = [1.6, 10.5, tw - 31, tw - 15, tw - 1.6];
  el("rect", { width: tw, height: 6, fill: HEAD }, g);
  T_(g, 1.6, 4.1, EN ? "SPECIFICATION" : "SPECIFIKĀCIJA", { fs: 2.3, fw: 700, ls: .4, fill: "#fff" });
  const hd = EN ? ["Mark", "Description", "Pcs", "L, mm", "Total, m"] : ["Poz.", "Nosaukums", "Gab.", "L, mm", "Kopā, m"];
  let yy = 6;
  hd.forEach((t, i) => T_(g, cxx[i], yy + 3.2, t, { fs: 1.7, fill: "#666", a: ca[i] }));
  yy += 4.2; el("line", { x1: 0, y1: yy, x2: tw, y2: yy, stroke: HEAD, "stroke-width": .2 }, g);
  rows.forEach((r, i) => {
    if (i % 2) el("rect", { y: yy, width: tw, height: RH, fill: SOFT }, g);
    r.forEach((t, j) => T_(g, cxx[j], yy + RH / 2 + .75, t, { fs: j === 1 ? 1.95 : 2, fw: j === 0 ? 700 : 400, a: ca[j] }));
    yy += RH;
  });
  el("line", { x1: 0, y1: yy, x2: tw, y2: yy, stroke: HEAD, "stroke-width": .35 }, g);
  T_(g, 1.6, yy + 3.6, EN ? `Rim beam total: ${f(lm)} m · ${m3.toFixed(3).replace(".", EN ? "." : ",")} m³` : `Vainags kopā: ${f(lm)} m · ${m3.toFixed(3).replace(".", ",")} m³`, { fs: 2.1, fw: 700 });
  T_(g, tw - 1.6, yy + 3.6, EN ? `posts: ${Lay.pts.length} pcs` : `stabi: ${Lay.pts.length} gab.`, { fs: 2.1, fw: 700, a: "end" });
  yy += 5.5;
  el("rect", { width: tw, height: yy, fill: "none", stroke: HEAD, "stroke-width": .3 }, g);
  // piezīmes no izvēlēm
  const N = [EN ? "Dimensions in mm, to post centres unless noted." : "Izmēri mm, pa stabu centriem, ja nav norādīts citādi.",
    Lay.uz ? (EN ? `Posts set ${Lay.uz} mm in from the C24 frame outer face, so the battens are not crushed.` : `Stabi novietoti ar uzlaidi ${Lay.uz} mm uz iekšu no C24 karkasa ārmalas, lai nesaspiestu latojumu.`)
      : (EN ? "Outer post edge flush with the C24 frame outer face." : "Stabu ārmala vienā līnijā ar C24 karkasa ārmalu."),
    EN ? `Rim beam C24 ${sec} laid flat on the posts, outer edge on the C24 frame outer face, corners mitred 45°; joists N–S on post centres.` : `Vainags C24 ${sec} guļus uz stabiem, ārmala pa C24 karkasa ārmalu, stūri 45°; starplikas Z–D virzienā pa stabu centriem.`,
    ...(Lay.pts.some(p => p.moved) ? [EN ? "Shifted posts are dimensioned in orange." : "Pārbīdītie stabi atzīmēti ar oranžiem izmēriem."] : []),
    ...(Lay.cells.length ? [(EN ? "Additional posts: " : "Papildu stabi: ") + Lay.cells.map(c => c.t || (EN ? "additional post" : "papildu stabs")).join("; ") + "."] : []),
    ...((pamViews(PP).includes("kopa")) ? [EN ? "Service entry points to be confirmed on site." : "Komunikāciju ievadu vietas precizēt objektā."] : []),
    ...String(PP.piez || "").split("\n").map(t => t.trim()).filter(Boolean)];
  const nx = tw + 5;
  el("rect", { x: nx, width: nw, height: 6, fill: HEAD }, g);
  T_(g, nx + 1.6, 4.1, EN ? "NOTES" : "PIEZĪMES", { fs: 2.3, fw: 700, ls: .4, fill: "#fff" });
  let ny = 10.2; const cpl = Math.floor((nw - 6) / 1.02);
  N.forEach((t, i) => { const ls = wrap(t, cpl); T_(g, nx + 1.4, ny, `${i + 1}.`, { fs: 1.95, fw: 700, fill: mm ? MM_ACC : C.ink }); ls.forEach((l, j) => T_(g, nx + 5, ny + j * 2.75, l, { fs: 1.95 })); ny += ls.length * 2.75 + .9; });
  el("rect", { x: nx, width: nw, height: Math.max(yy, ny), fill: "none", stroke: HEAD, "stroke-width": .3 }, g);
  return Math.max(yy, ny);
}
