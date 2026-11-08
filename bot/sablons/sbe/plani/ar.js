// ---------- AR set: sheet list, title block, roof plan, sections, specifications, details ----------
// project data comes from window.AR (plani/ar-config.json, filled in by the architect for each project)
const ARC = window.AR || null;
const AR_PARTS = {
  visp: "Vispārīgie rādītāji",
  plan: "Pirmā stāva plāns ar izmēriem",
  mebel: "Pirmā stāva plāns ar mēbeļu izvietojumu",
  jumts: "Jumta plāns",
  griez: "Griezumi 1-1 un 2-2",
  fas1: "Fasādes",
  fas2: "Fasādes",
  sienas: "Sienu specifikācija",
  logi: "Logu un durvju specifikācija",
  mezgli: "Logu montāžas mezgli",
};
// sheet number of a part ("AR-3"), or null when the part is not in this set
const arNo = k => { const i = ARC ? ARC.parts.indexOf(k) : -1; return i < 0 ? null : `AR-${i + 1}`; };
const arToday = () => { const d = new Date(), p = n => String(n).padStart(2, "0"); return `${p(d.getDate())}.${p(d.getMonth() + 1)}.${d.getFullYear()}`; };
const roofSeams = () => !ARC || (ARC.roof && ARC.roof.type) !== "sindeli";

// build-ups from the config override the drawing defaults (layers: [name, thickness mm, flags h=boards i=insulation m=membrane a=air])
const LAYERS = k => (ARC && ARC.layers && ARC.layers[k]) || null;
if (ARC) {
  const conv = ls => ls.filter(l => l[1] > 0).map(([n, t, f = ""]) => ({ t, name: n, hatch: f.includes("h"), ins: f.includes("i") }));
  if (LAYERS("S1")) { EXT_LAYERS.splice(0, EXT_LAYERS.length, ...conv(LAYERS("S1").layers)); EXT_SPEC.splice(0, EXT_SPEC.length, ...LAYERS("S1").layers.map(([n, t]) => [n, t ? String(t) : "-"])); }
  if (LAYERS("S2")) INT_LAYERS.splice(0, INT_LAYERS.length, ...conv(LAYERS("S2").layers));
  if (ARC.floor && ARC.floor.above != null) ROOF.plinth = ARC.floor.above;
  if (ARC.floor && ARC.floor.foundation === "stabi") ROOF.floorT = ARC.floor.floorT ?? (LAYERS("G1") ? LAYERS("G1").layers.reduce((s, l) => s + l[1], 0) : 300);
  // roof geometry from the config: pitch of the long slopes, hip = pitch of the end slopes (hipped roof), eave = wall top, overhang
  const rf = ARC.roof || {};
  ["pitch", "hip", "eave", "ov"].forEach(k => { if (rf[k] != null) ROOF[k] = rf[k]; });
  tan = Math.tan(ROOF.pitch * Math.PI / 180);
  if (LAYERS("J1")) ROOF.th = LAYERS("J1").layers.reduce((s, l) => s + l[1], 0);
}
const hipIns = v => ROOF.hip ? (v.D / 2 + ROOF.ov) * tan / Math.tan(ROOF.hip * Math.PI / 180) : 0;
const pitchTxt = () => ROOF.hip ? `${Math.round(ROOF.pitch)}° (gali ${ROOF.hip}°)` : `${Math.round(ROOF.pitch)}°`;
const roofGeo = v => {
  const eEdge = ROOF.eave - ROOF.ov * tan, thV = ROOF.th / Math.cos(ROOF.pitch * Math.PI / 180);
  return { eEdge, thV, ridgeTop: eEdge + thV + (v.D / 2 + ROOF.ov) * tan, ridgeU: ROOF.eave + (v.D / 2) * tan };
};
// facade names by axes as seen from outside: south 1-4, north 4-1, west A-B, east B-A
const sideAxes = (v, side) => {
  const ax = side === "south" || side === "north" ? v.axes.x : v.axes.y, f = ax[0][1], l = ax[ax.length - 1][1];
  return side === "south" || side === "west" ? `${f}-${l}` : `${l}-${f}`;
};

// title block after the office template: firm, object, people with dates, archive no., mark, stage, scale, sheet, sheets
function arTitle(svg, title, no, total, scale) {
  const tb = el("g", { "data-block": "title", transform: "translate(225 243)" }, svg), c = ARC.tb || {};
  const W = 185, LW = 75, L = (x1, y1, x2, y2, w = .25) => el("line", { x1, y1, x2, y2, stroke: C.ink, "stroke-width": w }, tb);
  el("rect", { width: W, height: 44, fill: "#fff", stroke: C.ink, "stroke-width": .5 }, tb);
  L(0, 22, W, 22, .35); L(LW, 0, LW, 44, .35);
  // firm with logo box
  // no logo given: the place stays empty (no box)
  if (c.logo) el("image", { x: 2.5, y: 2.5, width: 17, height: 17, href: c.logo, preserveAspectRatio: "xMidYMid meet" }, tb);
  (c.firm || []).forEach((t, i) => T_(tb, c.logo ? 22 : 2.5, 6 + i * 4, t, { fs: i ? 2.2 : 2.6, fw: i ? 400 : 600 }));
  // object
  (c.object || []).forEach((t, i) => T_(tb, LW + (W - LW) / 2, 7 + i * 5, t, { fs: i ? 2.8 : 3.4, fw: i ? 400 : 600, a: "middle" }));
  // people rows, dated automatically
  // row lines continue the right half's lines (30, 37), so both halves line up
  const RY = [22, 30, 37, 44], cols = [0, 16, 39, 56, LW];
  [30, 37].forEach(y => L(0, y, LW, y));
  cols.slice(1, -1).forEach(x => L(x, 22, x, 44));
  (c.people || []).slice(0, 3).forEach(([role, name], i) => {
    const y = (RY[i] + RY[i + 1]) / 2 + 1;
    T_(tb, 1.5, y, role + (role ? ":" : ""), { fs: 2.4 }); T_(tb, cols[1] + 1.5, y, name || "", { fs: 2.4 });
    if (role) T_(tb, cols[3] + 1.5, y, c.date || arToday(), { fs: 2.4 });
  });
  // sheet title and the data row
  L(LW, 30, W, 30); L(LW, 37, W, 37);
  T_(tb, LW + (W - LW) / 2, 27.3, title, { fs: 3.2, a: "middle", fw: 500 });
  const cw = [24, 18, 16, 18, 16, 18], cx = cw.reduce((a, w) => [...a, a[a.length - 1] + w], [LW]);
  cx.slice(1, -1).forEach(x => L(x, 30, x, 44));
  const heads = [["Arhīva reģ./", "Pasūtījuma Nr."], ["Rasējuma", "marka"], ["Stadija"], ["Mērogs"], ["Lapa"], ["Lapas"]];
  const vals = [c.archive || "", "AR", c.stage || "", scale, no, String(total)];
  heads.forEach((h, k) => {
    h.forEach((t, j) => T_(tb, cx[k] + 1.2, h.length > 1 ? 32.6 + j * 2.6 : 34.2, t, { fs: 2 }));
    T_(tb, (cx[k] + cx[k + 1]) / 2, 41.6, vals[k], { fs: 2.8, a: "middle", fw: k === 4 ? 600 : 400 });
  });
  return tb;
}

// notes with references only to sheets that exist in this set
const UNITS = "Visi izmēri norādīti milimetros, augstuma atzīmes norādītas metros.";
function arNotes(own) {
  const n = [];
  n.push("Par atzīmi ±0.000 pieņemts 1.stāva tīrās grīdas līmenis.", UNITS);
  own.forEach(t => n.push(t));
  if (arNo("griez")) n.push(`Griezumus 1-1; 2-2 skatīt lapā ${arNo("griez")}.`);
  if (arNo("sienas")) n.push(`Sienu specifikāciju skatīt lapā ${arNo("sienas")}.`);
  if (arNo("logi")) n.push(`Logu, durvju specifikāciju skatīt lapā ${arNo("logi")}.`);
  return n;
}
function notesBlock(svg, x, y, w, notes, title = "PIEZĪMES") {
  const g = el("g", { "data-block": "notes", transform: `translate(${x} ${y})` }, svg);
  T_(g, 0, 0, title, { fs: 3, fw: 600, ls: .3 });
  el("line", { x1: 0, y1: 2.2, x2: w, y2: 2.2, stroke: C.ink, "stroke-width": .3 }, g);
  let yy = 7.5;
  notes.forEach((t, i) => {
    const lines = wrap(t, Math.floor(w / 1.18));
    T_(g, 0, yy, `${i + 1}.`, { fs: 2.4, fill: "#333" });
    lines.forEach((l, j) => T_(g, 5, yy + j * 3.6, l, { fs: 2.4, fill: "#333" }));
    yy += lines.length * 3.6 + 1;
  });
  return g;
}
function wrap(t, n) {
  const out = []; let cur = "";
  String(t).split(" ").forEach(w => { if ((cur + " " + w).trim().length > n && cur) { out.push(cur); cur = w; } else cur = (cur + " " + w).trim(); });
  if (cur) out.push(cur);
  return out;
}
function sheetHeading(svg, x, y, w, title, scale = "M 1:100") {
  const g = el("g", {}, svg);
  T_(g, x, y, title, { fs: 4.2, fw: 600, ls: .3 });
  T_(g, x + title.length * 2.75 + 6, y, scale, { fs: 3.4, fill: "#444" });
  el("line", { x1: x, y1: y + 2, x2: x + w, y2: y + 2, stroke: C.ink, "stroke-width": .3 }, g);
}

// ---- wall-type marks (S1, S2) and section lines on the plan ----
function wallTags(g, v) {
  const tg = el("g", {}, g);
  (v.wallTags || []).forEach((w, i) => {
    const n0 = tg.childNodes.length, th = w.t === "S1" ? T : t, s = w.side || 1, ext = 420;
    const L = (x1, y1, x2, y2) => el("line", { x1, y1, x2, y2, stroke: C.ink, "stroke-width": 28 }, tg);
    if (w.o === "h") {
      const y0 = s > 0 ? w.y - 150 : w.y + th + 150, y1 = s > 0 ? w.y + th + ext : w.y - ext;
      L(w.x, y0, w.x, y1);
      T_(tg, w.x + 70, s > 0 ? y1 - 20 : y1 + 150, w.t, { fs: 180, fw: 600 });
    } else {
      const x0 = s > 0 ? w.x - 150 : w.x + th + 150, x1 = s > 0 ? w.x + th + ext : w.x - ext;
      L(x0, w.y, x1, w.y);
      T_(tg, x1 + (s > 0 ? 60 : -60), w.y + 60, w.t, { fs: 180, fw: 600, a: s > 0 ? "start" : "end" });
    }
    for (let k = n0; k < tg.childNodes.length; k++) tg.childNodes[k].setAttribute("data-tag", "s" + i);
  });
}
function sectionLines(g, v, ext = 2300) {
  const sg = el("g", {}, g);
  (v.sections || []).forEach(s => {
    const span = s.o === "v" ? v.D : v.W, a0 = -ext, a1 = span + ext;
    const P = (a, b = s.at) => s.o === "v" ? [b, a] : [a, b];
    const line = (p, q, sw, dash) => el("line", { x1: p[0], y1: p[1], x2: q[0], y2: q[1], stroke: C.ink, "stroke-width": sw, ...(dash ? { "stroke-dasharray": dash } : {}) }, sg);
    const SV = +(((window.AR && window.AR.projekts && window.AR.projekts.wall_style) || {}).section) || 1;   // griezuma līnijas veids 1-3
    line(P(a0), P(a1), SV === 2 ? 12 : 10, SV === 2 ? null : "380 110 50 110");
    [[a0, a0 + 550], [a1 - 550, a1]].forEach(([p, q]) => line(P(p), P(q), 38));
    if (SV === 3) {   // ArchiCAD veida zīme: trijstūris skata virzienā un aplis ar numuru
      [a0, a1].forEach(a => {
        const d = s.look, B = (u, w) => P(a + u, s.at + d * w), tri = [B(-380, 150), B(380, 150), B(0, 900)];
        el("polygon", { points: tri.map(t => t.join(",")).join(" "), fill: "#bdbdbd", stroke: C.ink, "stroke-width": 10 }, sg);
        const c = B(0, 1250); el("circle", { cx: c[0], cy: c[1], r: 340, fill: "#fff", stroke: C.ink, "stroke-width": 14 }, sg);
        T_(sg, c[0], c[1] + 95, s.n, { fs: 300, fw: 700, a: "middle" });
      });
      return;
    }
    // view arrows at both ends, number beyond the arrow head
    const dir = s.look;
    [a0, a1].forEach(a => {
      const p = P(a), q = P(a, s.at + dir * 520), hd = P(a, s.at + dir * 650);
      line(p, q, 14);
      const nx = s.o === "v" ? dir : 0, ny = s.o === "v" ? 0 : dir;
      el("path", { d: `M ${hd[0]} ${hd[1]} L ${q[0] - ny * 70} ${q[1] - nx * 70} L ${q[0] + ny * 70} ${q[1] + nx * 70} Z`, fill: C.ink }, sg);
      const tp = P(a, s.at + dir * 650), off = s.o === "v" ? [dir > 0 ? 60 : -60, 230] : [70, dir > 0 ? 250 : -60];
      T_(sg, tp[0] + off[0], tp[1] + off[1], s.n, { fs: 240, fw: 600, a: s.o === "v" && dir < 0 ? "end" : "start" });
    });
  });
}

// ---- legend of symbols on the dimensioned plan ----
function symbolLegend(svg, x, y, v) {
  const g = el("g", { "data-block": "wall-legend", transform: `translate(${x} ${y})` }, svg);
  const rows = [["ins", "Siltumizolācija"], ["S1", arNo("sienas") ? `Sienas tips (sk. lapu ${arNo("sienas")})` : "Sienas tips"], ["L-1", "Loga marka"], ["DK-1", "Durvju marka (DK kreisās, DL labās, ĀD ārdurvis)"]];
  if (v.sections && arNo("griez")) rows.push(["sec", "Griezuma līnija"]);
  rows.push(["lvl", "Augstuma atzīme"]);
  const RH = 5.2, W1 = 24, W = 118;
  T_(g, 0, 0, "PIEŅEMTIE APZĪMĒJUMI", { fs: 3, fw: 600, ls: .3 });
  el("rect", { x: 0, y: 3, width: W, height: rows.length * RH, fill: "none", stroke: C.ink, "stroke-width": .3 }, g);
  el("line", { x1: W1, y1: 3, x2: W1, y2: 3 + rows.length * RH, stroke: C.ink, "stroke-width": .2 }, g);
  rows.forEach(([k, label], i) => {
    const y0 = 3 + i * RH, cy = y0 + RH / 2;
    if (i) el("line", { x1: 0, y1: y0, x2: W, y2: y0, stroke: C.ink, "stroke-width": .15 }, g);
    T_(g, W1 + 2, cy + 1, label, { fs: 2.4 });
    if (k === "ins") {
      const id = "lgi"; el("rect", { x: 3, y: y0 + 1.2, width: 18, height: RH - 2.4 }, el("clipPath", { id }, g));
      el("rect", { x: 3, y: y0 + 1.2, width: 18, height: RH - 2.4, fill: "#fff", stroke: C.ink, "stroke-width": .2 }, g);
      el("path", { d: loops(3, y0 + 1.2, 1, 0, 0, 1, 18, RH - 2.4), ...INS, "stroke-width": .15, "clip-path": `url(#${id})` }, g);
    } else if (k === "S1") {
      el("line", { x1: 5, y1: cy, x2: 13, y2: cy, stroke: C.ink, "stroke-width": .3 }, g);
      T_(g, 14, cy + 1, "S1", { fs: 2.2, fw: 600 });
    } else if (k === "sec") {
      el("line", { x1: 4, y1: cy, x2: 16, y2: cy, stroke: C.ink, "stroke-width": .4 }, g);
      el("path", { d: `M 16 ${cy} L 16 ${cy - 2.2}`, stroke: C.ink, "stroke-width": .2 }, g);
      el("path", { d: `M 16 ${cy - 2.6} l -.6 1 h 1.2 z`, fill: C.ink }, g);
      T_(g, 17.3, cy - .4, "1", { fs: 2.2, fw: 600 });
    } else if (k === "lvl") T_(g, 12, cy + 1, "±0,000", { fs: 2.2, fw: 600, a: "middle" });
    else { const tw = k.length * .98 + .9; el("rect", { x: 12 - tw / 2, y: cy - 1.05, width: tw, height: 2.1, rx: .4, fill: "none", stroke: C.ink, "stroke-width": .06 }, g); T_(g, 12, cy + .52, k, { fs: 1.45, fw: 600, a: "middle" }); }
  });
  return g;
}

// ---- roof plan ----
function roofPlan(parent, v) {
  const g = el("g", { "data-block": "plan" }, parent), ov = ROOF.ov, W = v.W, Dd = v.D;
  const box = [-ov, -ov, W + 2 * ov, Dd + 2 * ov];
  // axes
  const dash = { stroke: C.axis, "stroke-width": 7, "stroke-dasharray": "300 60 40 60" };
  const bub = (cx, cy, n) => { el("circle", { cx, cy, r: 300, fill: "#fff", stroke: C.ink, "stroke-width": 12 }, g); T_(g, cx, cy + 92, n, { a: "middle", fs: 260, fw: 500 }); };
  v.axes.x.forEach(([x, n]) => { el("line", { x1: x, y1: -2700, x2: x, y2: Dd + 3150, ...dash }, g); bub(x, -3000, n); bub(x, Dd + 3450, n); });
  v.axes.y.forEach(([y, n]) => { el("line", { x1: -2700, y1: y, x2: W + 2850, y2: y, ...dash }, g); bub(-3000, y, n); bub(W + 3150, y, n); });
  // roof surface with its covering
  const cid = "roofclip"; el("rect", { x: box[0], y: box[1], width: box[2], height: box[3] }, el("clipPath", { id: cid }, g));
  el("rect", { x: box[0], y: box[1], width: box[2], height: box[3], fill: "#fff" }, g);
  // roof faces; covering runs parallel (shingle rows) or across (seams) to each face's eave
  const hi = hipIns(v), r0 = -ov + hi, r1 = W + ov - hi, ym = Dd / 2;
  const faces = ROOF.hip ? [[[-ov, -ov], [W + ov, -ov], [r1, ym], [r0, ym], "x"], [[-ov, Dd + ov], [W + ov, Dd + ov], [r1, ym], [r0, ym], "x"], [[-ov, -ov], [r0, ym], [-ov, Dd + ov], "y"], [[W + ov, -ov], [r1, ym], [W + ov, Dd + ov], "y"]]
    : [[[-ov, -ov], [W + ov, -ov], [W + ov, ym], [-ov, ym], "x"], [[-ov, ym], [W + ov, ym], [W + ov, Dd + ov], [-ov, Dd + ov], "x"]];
  faces.forEach((fc, fi) => {
    const dir = fc.pop(), fid = `${cid}-f${fi}`;
    el("polygon", { points: fc.map(p => p.join(",")).join(" ") }, el("clipPath", { id: fid }, g));
    const cg = el("g", { "clip-path": `url(#${fid})` }, g), along = (dir === "x") !== roofSeams();
    const [a0, a1, b0, b1] = along ? [-ov, Dd + ov, -ov, W + ov] : [-ov, W + ov, -ov, Dd + ov];
    const L = (p, q0, q1, sw, col) => el("line", along ? { x1: q0, y1: p, x2: q1, y2: p, stroke: col, "stroke-width": sw } : { x1: p, y1: q0, x2: p, y2: q1, stroke: col, "stroke-width": sw }, cg);
    if (roofSeams()) for (let p = a0 + 265; p < a1; p += 530) L(p, b0, b1, 6, "#666");
    else for (let p = a0, r = 0; p < a1; p += 340, r++) {
      L(p, b0, b1, 5, "#888");
      for (let q = b0 + (r % 2 ? 170 : 0); q < b1; q += 340) el("line", along ? { x1: q, y1: p, x2: q, y2: p + 120, stroke: "#999", "stroke-width": 4 } : { x1: p, y1: q, x2: p + 120, y2: q, stroke: "#999", "stroke-width": 4 }, cg);
    }
  });
  el("rect", { x: box[0], y: box[1], width: box[2], height: box[3], fill: "none", stroke: C.ink, "stroke-width": 22 }, g);
  el("line", { x1: r0, y1: ym, x2: r1, y2: ym, stroke: C.ink, "stroke-width": 22 }, g);
  if (ROOF.hip) [[-ov, -ov], [-ov, Dd + ov]].forEach(([x, y]) => { el("line", { x1: x, y1: y, x2: r0, y2: ym, stroke: C.ink, "stroke-width": 22 }, g); el("line", { x1: W - x, y1: y, x2: r1, y2: ym, stroke: C.ink, "stroke-width": 22 }, g); });
  // outer walls below, dashed
  el("polygon", { points: v.poly.map(p => p.join(",")).join(" "), fill: "none", stroke: C.ink, "stroke-width": 12, "stroke-dasharray": "160 90" }, g);
  // slope arrows (down the slope), pitch
  [[Dd / 4, -1], [Dd * 3 / 4, 1]].forEach(([y, s]) => [W * .3, W * .7].forEach(x => {
    const y0 = y - s * 700, y1 = y + s * 700;
    el("rect", { x: x - 330, y: y - 400, width: 660, height: 800, fill: "#fff" }, g);
    el("line", { x1: x - 180, y1: y0, x2: x - 180, y2: y1, stroke: C.ink, "stroke-width": 10 }, g);
    el("path", { d: `M ${x - 180} ${y1 + s * 140} L ${x - 250} ${y1} L ${x - 110} ${y1} Z`, fill: C.ink }, g);
    T_(g, x + 120, y + 60, `${Math.round(ROOF.pitch)}°`, { a: "middle", fs: 210, fw: 600, tr: `rotate(-90 ${x + 120} ${y})` });
  }));
  // end slopes of a hipped roof: arrows toward the end eaves
  if (ROOF.hip) [[-ov + hi * .5, -1], [W + ov - hi * .5, 1]].forEach(([x, s]) => {
    const y = Dd / 2 + 420, x0 = x - s * 500, x1 = x + s * 500;
    el("rect", { x: x - 600, y: y - 330, width: 1200, height: 560, fill: "#fff" }, g);
    el("line", { x1: x0, y1: y, x2: x1, y2: y, stroke: C.ink, "stroke-width": 10 }, g);
    el("path", { d: `M ${x1 + s * 140} ${y} L ${x1} ${y - 70} L ${x1} ${y + 70} Z`, fill: C.ink }, g);
    T_(g, x, y - 90, `${ROOF.hip}°`, { a: "middle", fs: 210, fw: 600 });
  });
  // gutters along both eaves, downpipes in the corners; leaders 1 = gutter, 2 = downpipe
  // gutter outline closed: hipped roof = one ring round the eaves, gable = lines with end caps
  if (ROOF.hip) el("rect", { x: -ov - 150, y: -ov - 150, width: W + 2 * ov + 300, height: Dd + 2 * ov + 300, fill: "none", stroke: C.ink, "stroke-width": 8 }, g);
  [-ov, Dd + ov].forEach((y, k) => {
    const yo = y + (k ? 150 : -150);
    if (!ROOF.hip) el("path", { d: `M ${-ov} ${y} V ${yo} H ${W + ov} V ${y}`, fill: "none", stroke: C.ink, "stroke-width": 8 }, g);
    [-ov + 140, W + ov - 140].forEach(x => el("circle", { cx: x, cy: y + (k ? 75 : -75), r: 60, fill: "#fff", stroke: C.ink, "stroke-width": 10 }, g));
  });
  const leader = (x, y, tx, ty, n) => { el("line", { x1: x, y1: y, x2: tx, y2: ty, stroke: C.ink, "stroke-width": 6 }, g); el("line", { x1: tx, y1: ty, x2: tx + 260, y2: ty, stroke: C.ink, "stroke-width": 6 }, g); T_(g, tx + 130, ty - 50, n, { a: "middle", fs: 210, fw: 600 }); };
  leader(W * .55, -ov - 150, W * .55 + 350, -ov - 700, "1");
  leader(W * .45, Dd + ov + 150, W * .45 + 350, Dd + ov + 700, "1");
  leader(-ov + 140, -ov - 75, -ov + 520, -ov - 700, "2");
  leader(W + ov - 140, Dd + ov + 75, W + ov - 520 - 260, Dd + ov + 700, "2");
  // dimensions incl. overhangs
  const dg = el("g", {}, g);
  if (ROOF.hip) chainCad(dg, [-ov, r0, r1, W + ov], "x", -1250);
  chainCad(dg, [-ov, ...v.axes.x.map(a => a[0]), W + ov], "x", Dd + 1250);
  const ax = v.axes.x.map(a => a[0]), ay = v.axes.y.map(a => a[0]);
  chainCad(dg, [Math.min(...ax), Math.max(...ax)], "x", Dd + 1850);   // total between the outer axes
  chainCad(dg, [-ov, W + ov], "x", Dd + 2450);
  if (ay.length > 2) chainCad(dg, ay, "y", W + 1350);
  chainCad(dg, [Math.min(...ay), Math.max(...ay)], "y", W + (ay.length > 2 ? 1950 : 1350));
  chainCad(dg, [-ov, 0, Dd / 2, Dd, Dd + ov], "y", -1250);
  chainCad(dg, [-ov, Dd + ov], "y", -1850);
  if (arNo("griez")) sectionLines(g, v);
  return g;
}

// ---- building sections ----
function section(parent, v, s) {
  const g = el("g", {}, parent), span = s.o === "v" ? v.D : v.W, ov = ROOF.ov, { eEdge, thV, ridgeTop } = roofGeo(v);
  const P = (u, z) => `${u},${-z}`, CEIL = v.ceiling || 2500, fl = (LAYERS("G1") || { layers: [["", 300]] }).layers;
  const flT = fl.reduce((a, l) => a + l[1], 0), pl = ROOF.plinth;
  // rooms crossed by the cut, as intervals along u
  const cut = v.rooms.flatMap((rm, i) => rm.r.filter(q => s.o === "v" ? q[0] < s.at && q[0] + q[2] > s.at : q[1] < s.at && q[1] + q[3] > s.at)
    .map(q => ({ i, a: s.o === "v" ? q[1] : q[0], b: s.o === "v" ? q[1] + q[3] : q[0] + q[2] }))).sort((p, q) => p.a - q.a);
  const iv = []; cut.forEach(c => { const l = iv[iv.length - 1]; if (l && c.a <= l.b + 1 && l.i === c.i) l.b = Math.max(l.b, c.b); else iv.push({ ...c }); });
  const open = i => (v.openRooms || []).includes(i);
  // building outline along the cut (recessed outline: terrace / porch parts stay open)
  const xs = [];
  v.poly.forEach((p, i) => { const q = v.poly[(i + 1) % v.poly.length];
    if (s.o === "v" && p[1] === q[1] && (p[0] - s.at) * (q[0] - s.at) < 0) xs.push(p[1]);
    if (s.o === "h" && p[0] === q[0] && (p[1] - s.at) * (q[1] - s.at) < 0) xs.push(p[0]); });
  xs.sort((a, b) => a - b);
  const bld = []; for (let i = 0; i + 1 < xs.length; i += 2) bld.push([xs[i], xs[i + 1]]);
  const inB = u => bld.some(([p, q]) => u > p && u < q);
  const fcp = "fc-" + Math.random().toString(36).slice(2, 8), fcl = el("clipPath", { id: fcp }, g);
  bld.forEach(([p, q]) => el("rect", { x: p - 10, y: -10, width: q - p + 20, height: pl + 20 }, fcl));
  const fg = el("g", { "clip-path": `url(#${fcp})` }, g);
  // ground and floor build-up
  { let d = ""; for (let x = -1400; x < span + 1400 - 260; x += 200) d += `M ${x} ${pl + 260} L ${x + 260} ${pl} `; el("path", { d, stroke: "#666", "stroke-width": 8, fill: "none" }, g); }
  el("line", { x1: -1600, y1: pl, x2: span + 1600, y2: pl, stroke: C.ink, "stroke-width": 40 }, g);
  bld.forEach(([p, q]) => el("rect", { x: p, y: 0, width: q - p, height: flT, fill: fl.some(l => (l[2] || "").includes("c")) ? "url(#concrete)" : "#fff", stroke: C.ink, "stroke-width": 14 }, g));
  if (ROOF.floorT) bld.forEach(([p, q]) => { const n = Math.max(1, Math.round((q - p) / 2000)); for (let i = 0; i <= n; i++) { const u = p + 100 + (q - p - 200) * i / n; el("rect", { x: u - 100, y: flT, width: 200, height: pl - flT, fill: "url(#concrete)", stroke: C.ink, "stroke-width": 10 }, g); } });
  // dark grey metal plinth at the outer faces, 40 mm above the ground
  if (ROOF.floorT) bld.forEach(([p, q]) => [p - 25, q].forEach(xx => el("rect", { x: xx, y: flT - 60, width: 25, height: pl - 40 - flT + 60, fill: "#3a3f43" }, g)));
  let z = 0; fl.forEach(([n, th, f = ""]) => { if (f.includes("i")) el("rect", { x: 0, y: z, width: span, height: th, fill: "#fff", stroke: C.ink, "stroke-width": 6 }, fg), el("path", { d: loops(0, z, 1, 0, 0, 1, span, th), ...INS, "stroke-width": 5 }, fg); z += th; el("line", { x1: 0, y1: z, x2: span, y2: z, stroke: C.ink, "stroke-width": 5 }, fg); });
  // roof: cut across the slope (1-1) or along the ridge (2-2)
  // insulation loops clipped to a shape (walls, roof)
  const insShape = (pts, ...bands) => {
    const id = "si-" + Math.random().toString(36).slice(2, 8);
    el("polygon", { points: pts }, el("clipPath", { id }, g));
    el("polygon", { points: pts, fill: "#fff", stroke: C.ink, "stroke-width": 14 }, g);
    bands.forEach(b => el("path", { d: loops(...b), ...INS, "stroke-width": 5, "clip-path": `url(#${id})` }, g));
  };
  const insRect = (x, y, w, h) => insShape([P(x, -y), P(x + w, -y), P(x + w, -y - h), P(x, -y - h)].join(" "), [x, y, 0, 1, 1, 0, h, w]);
  const ca = Math.cos(ROOF.pitch * Math.PI / 180), sa = Math.sin(ROOF.pitch * Math.PI / 180), Ls = (v.D / 2 + ov) / ca + 400;
  if (s.o === "v") {
    const zb = u => ROOF.eave + Math.min(u, span - u) * tan;
    insShape([P(-ov, eEdge), P(span / 2, zb(span / 2)), P(span + ov, eEdge), P(span + ov, eEdge + thV), P(span / 2, ridgeTop), P(-ov, eEdge + thV)].join(" "),
      [-ov - 200 * ca, -eEdge + 200 * sa, ca, -sa, -sa, -ca, Ls, ROOF.th], [span + ov + 200 * ca, -eEdge + 200 * sa, -ca, -sa, sa, -ca, Ls, ROOF.th]);
    el("polyline", { points: [P(-ov - 20, eEdge + thV + 10), P(span / 2, ridgeTop + 10), P(span + ov + 20, eEdge + thV + 10)].join(" "), fill: "none", stroke: "#40464b", "stroke-width": 30 }, g);
  } else if (ROOF.hip) {
    const d = s.at, zb = ROOF.eave + Math.min(d, v.D - d) * tan, a = ROOF.hip * Math.PI / 180, tH = Math.tan(a), cH = Math.cos(a), sH = Math.sin(a);
    const thH = ROOF.th / cH, zE = ROOF.eave - ov * tH, uB = (zb - ROOF.eave) / tH, ins = (ridgeTop - zE - thH) / tH;
    el("polygon", { points: [P(-ov, zE + thH), P(-ov + ins, ridgeTop), P(span + ov - ins, ridgeTop), P(span + ov, zE + thH), P(span - uB, zb + thV), P(uB, zb + thV)].join(" "), fill: "#f1f1ef", stroke: C.thin, "stroke-width": 8 }, g);
    const Lh = (uB + ov) / cH + 400;
    insShape([P(-ov, zE), P(uB, zb), P(span - uB, zb), P(span + ov, zE), P(span + ov, zE + thH), P(span - uB, zb + thV), P(uB, zb + thV), P(-ov, zE + thH)].join(" "),
      [-ov - 200 * cH, -zE + 200 * sH, cH, -sH, -sH, -cH, Lh, ROOF.th], [span + ov + 200 * cH, -zE + 200 * sH, -cH, -sH, sH, -cH, Lh, ROOF.th], [uB, -(zb + thV), 1, 0, 0, 1, span - 2 * uB, thV]);
    // end walls up to the eave
    [[0, T], [span - T, span]].forEach(([u0, u1]) => insRect(u0, -ROOF.eave, u1 - u0, ROOF.eave));
  } else {
    const d = s.at, zb = ROOF.eave + Math.min(d, v.D - d) * tan;
    el("polygon", { points: [P(-ov, zb), P(-ov, ridgeTop), P(span + ov, ridgeTop), P(span + ov, zb)].join(" "), fill: "#f1f1ef", stroke: C.thin, "stroke-width": 8 }, g);
    if (roofSeams()) for (let u = -ov + 265; u < span + ov; u += 530) el("line", { x1: u, y1: -ridgeTop, x2: u, y2: -(zb + thV), stroke: "#999", "stroke-width": 5 }, g);
    insShape([P(-ov, zb), P(span + ov, zb), P(span + ov, zb + thV), P(-ov, zb + thV)].join(" "), [-ov, -(zb + thV), 1, 0, 0, 1, span + 2 * ov, thV]);
    // gable walls continue up to the roof
    [[0, T], [span - T, span]].forEach(([u0, u1]) => insRect(u0, -zb, u1 - u0, zb));
  }
  // walls between the rooms crossed; outer walls up to the roof underside
  const zRoof = u => s.o === "v" ? ROOF.eave + Math.min(u, span - u) * tan : ROOF.eave + Math.min(s.at, v.D - s.at) * tan;
  const gaps = []; let prev = 0; iv.forEach(c => { if (c.a - prev > 20) gaps.push([prev, c.a]); prev = c.b; }); if (span - prev > 20) gaps.push([prev, span]);
  gaps.flatMap(([a, b]) => bld.map(([p, q]) => [Math.max(a, p), Math.min(b, q)]).filter(([p, q]) => q - p > 20)).forEach(([a, b]) => {
    if (!inB((a + b) / 2)) return;
    const bbox = a < 1 || b > span - 1, outer = bbox || !inB(a - 30) || !inB(b + 30), top = bbox ? zRoof(a < 1 ? 0 : span) : outer ? ROOF.eave : CEIL;
    if (s.o === "h" && bbox) return;
    insRect(a, -top, b - a, top);
    if (!outer) return;
    // windows / doors in the outer walls on the cut
    const wsec = v.windows.filter(w => (s.o === "v" ? w.o === "h" && w.x < s.at && w.x + w.len > s.at && (a < 1 ? w.y === 0 : w.y > 0) : w.o === "v" && w.y < s.at && w.y + w.len > s.at && (a < 1 ? w.x === 0 : w.x > 0)));
    wsec.forEach(w => {
      el("rect", { x: a - 5, y: -w.head, width: b - a + 10, height: w.head - w.sill, fill: "#fff" }, g);
      el("rect", { x: a + (b - a) * .25, y: -w.head, width: (b - a) * .3, height: w.head - w.sill, fill: "url(#glass)", stroke: C.ink, "stroke-width": 8 }, g);
      [w.sill, w.head].forEach(zz => el("line", { x1: a, y1: -zz, x2: b, y2: -zz, stroke: C.ink, "stroke-width": 10 }, g));
    });
  });
  // ceilings in rooms that are not open to the roof; room names
  iv.forEach(c => {
    if (!open(c.i)) el("rect", { x: c.a, y: -CEIL - 60, width: c.b - c.a, height: 60, fill: "#d9d9d6", stroke: C.ink, "stroke-width": 8 }, g);
    const nm = FULL[v.rooms[c.i].n] || v.rooms[c.i].n;
    if (c.b - c.a > nm.length * 110) T_(g, (c.a + c.b) / 2, -1100, nm, { a: "middle", fs: 190 });
    T_(g, (c.a + c.b) / 2, -1400, String(c.i + 1), { a: "middle", fs: 190, fw: 600 });
  });
  // levels on the left
  const lvl = (zz, label, above = 0) => {
    const lx = -ov - 1200, up = above ? 1 : zz < 0 ? -1 : 1, ty = -zz - up * 210;
    el("line", { x1: lx, y1: -zz, x2: -ov - 150, y2: -zz, stroke: C.ink, "stroke-width": 7 }, g);
    el("path", { d: `M ${lx} ${-zz} L ${lx - 130} ${ty} L ${lx + 130} ${ty} Z`, fill: C.ink }, g);
    el("line", { x1: lx - 130 - label.length * 152, y1: ty, x2: lx - 130, y2: ty, stroke: C.ink, "stroke-width": 10 }, g);
    T_(g, lx - 140, up > 0 ? ty - 45 : ty + 225, label, { a: "end", fs: 250, fw: 600 });
  };
  [ridgeTop, ROOF.eave, CEIL, 0, -pl].forEach(zz => lvl(zz, lv(Math.round(zz))));
  if (ROOF.floorT) lvl(-ROOF.floorT, lv(-ROOF.floorT), 1);
  // height chain on the right
  chainCad(el("g", { transform: `translate(${span + ov + 900} 0)` }, g), [pl, 0, -CEIL, -ROOF.eave, -Math.round(ridgeTop)], "y", 0);
  // axes under the section
  const ax = s.o === "v" ? v.axes.y : v.axes.x;
  ax.forEach(([a, n]) => {
    el("line", { x1: a, y1: pl + 80, x2: a, y2: 1150, stroke: C.axis, "stroke-width": 7, "stroke-dasharray": "200 50 30 50" }, g);
    el("circle", { cx: a, cy: 1450, r: 300, fill: "#fff", stroke: C.ink, "stroke-width": 12 }, g);
    T_(g, a, 1540, n, { a: "middle", fs: 250, fw: 500 });
  });
  const name = `GRIEZUMS ${s.n}-${s.n}`;
  T_(g, -ov, 2450, name, { fs: 330, fw: 600, ls: 20 });
  T_(g, -ov + name.length * 262 + 350, 2450, "M 1:100", { fs: 260, fill: "#444" });
  el("line", { x1: -ov, y1: 2560, x2: span + ov, y2: 2560, stroke: C.ink, "stroke-width": 12 }, g);
  return g;
}

// ---- material hatches (units = real mm; u = paper mm per unit, keeps line weights constant) ----
const MEMB = { d: { stroke: "#1f6fd1" }, v: { stroke: "#d0312d", dash: [3, 1.2] }, r: { stroke: "#5b5f62", dash: [2.4, .8, .5, .8] } };
// layers whose name contains a key word (set in the editor, projekts.layer_marks) are drawn as a coloured line
const MARK_DEF = [{ k: "membrān", c: "#1f6fd1", d: 1 }, { k: "plēve", c: "#1f6fd1", d: 1 }, { k: "folij", c: "#1f6fd1", d: 1 }];
const markOf = name => { const L = ((window.AR && window.AR.projekts && window.AR.projekts.layer_marks) || MARK_DEF), n = String(name || "").toLowerCase(); const r = L.find(q => q.k && n.includes(String(q.k).toLowerCase())); return r ? { stroke: r.c || "#1f6fd1", ...(r.d ? { dash: [3, 1.2] } : {}) } : null; };
function membLine(g, x1, y1, x2, y2, f, u, ov) {
  const m = ov || MEMB[f[1]] || { stroke: C.ink, dash: [3, 1.2] };
  el("line", { x1, y1, x2, y2, stroke: m.stroke, "stroke-width": .6 / u, ...(m.dash ? { "stroke-dasharray": m.dash.map(k => k / u).join(" ") } : {}) }, g);
}
function hatchBox(g, bx, by, bw, bh, f, u, clip) {
  // Arka-B / ArchiCAD fills; u = drawing units per paper mm (1 / scale)
  const o = clip ? { "clip-path": `url(#${clip})` } : {}, vert = bw < bh, L = vert ? bh : bw, t = vert ? bw : bh;
  // point at a along the layer, b across it (0 = first face)
  const P = (a, b) => vert ? `${(bx + b).toFixed(2)} ${(by + a).toFixed(2)}` : `${(bx + a).toFixed(2)} ${(by + b).toFixed(2)}`;
  const path = (d, st) => el("path", { d, fill: "none", ...st, ...o }, g);
  if (f.includes("h")) {
    // boards: light grey with fine diagonal grain
    el("rect", { x: bx, y: by, width: bw, height: bh, fill: "#d9d9d9", stroke: "none", ...o }, g);
    let d = ""; for (let a = -t; a < L; a += .45 / u) d += `M ${P(a, t)} L ${P(a + t * 1.6, 0)} `;
    path(d, { stroke: "#b5b5b5", "stroke-width": .08 / u });
  }
  if (f.includes("o")) {
    // OSB / durelis: sparse thin slashes across the board
    let d = ""; for (let a = 2 / u; a < L; a += 7 / u) d += `M ${P(a, t)} L ${P(a + t * 1.2, 0)} `;
    path(d, { stroke: "#555", "stroke-width": .1 / u });
  }
  if (f.includes("l")) {
    // battens: dense lines across the layer
    let d = ""; for (let a = .3 / u; a < L; a += .6 / u) d += `M ${P(a, 0)} L ${P(a, t)} `;
    path(d, { stroke: "#777", "stroke-width": .06 / u });
  }
  if (f.includes("k")) {
    // gypsum board: sparse fine dots
    let d = ""; const r = .1 / u;
    for (let a = 1.5 / u, j = 0; a < L; a += 3.2 / u, j++) { const b = t * (j % 3 === 0 ? .3 : j % 3 === 1 ? .7 : .5); d += `M ${P(a - r, b)} L ${P(a + r, b)} `; }
    path(d, { stroke: "#555", "stroke-width": 2 * r, "stroke-linecap": "round" });
  }
}

// ---- build-up sample at 1:10 with numbered layers and a table ----
function buildUp(svg, x, y, id, spec) {
  const g = el("g", { "data-block": "spec-" + id, transform: `translate(${x} ${y})` }, svg), ls = spec.layers;
  const tot = ls.reduce((a, l) => a + l[1], 0);
  T_(g, 0, 0, `${id} – ${spec.name.toUpperCase()}, ${tot} mm`, { fs: 3.4, fw: 600, ls: .2 });
  el("line", { x1: 0, y1: 2, x2: 182, y2: 2, stroke: C.ink, "stroke-width": .3 }, g);
  const sc = .1, Lx = 46, top = 9, d = el("g", { transform: `translate(0 ${top}) scale(${sc})` }, g);
  let yy = 0; const memb = [];
  const mids = ls.map(([n, th, f = ""]) => {
    if (th > 0) {
      el("rect", { x: 0, y: yy, width: Lx / sc, height: th, fill: f.includes("a") ? "#fff" : f.includes("c") ? "url(#concrete)" : "#fff", stroke: C.thin, "stroke-width": 4 }, d);
      const cid = "bu-" + id + "-" + Math.round(yy * 10); el("rect", { x: 0, y: yy, width: Lx / sc, height: th }, el("clipPath", { id: cid }, d));
      if (f.includes("i")) el("path", { d: loops(0, yy, 1, 0, 0, 1, Lx / sc, th), ...INS, "stroke-width": 1.6, "clip-path": `url(#${cid})` }, d);
      if (f.includes("g")) for (let k = 0; k < Lx / sc; k += 40) el("circle", { cx: k + 20, cy: yy + th / 2 + ((k / 40) % 2 ? 8 : -8), r: 9, fill: "none", stroke: "#888", "stroke-width": 2 }, d);
      hatchBox(d, 0, yy, Lx / sc, th, f, sc, cid);
    } else memb.push([yy, f, markOf(n)]);
    if (th > 0 && markOf(n)) memb.push([yy + th / 2, f, markOf(n)]);
    const m = top + (yy + th / 2) * sc; yy += th; return m;
  });
  // membranes on top of the layer outlines, so the colour line stays visible
  memb.forEach(([yy, f, ov]) => membLine(d, 0, yy, Lx / sc, yy, f, sc, ov));
  el("rect", { x: 0, y: 0, width: Lx / sc, height: tot, fill: "none", stroke: C.ink, "stroke-width": 8 }, d);
  // side marks: ⊕ warm side (iekšpuse / telpa), ⊖ cold side (ārpuse / grunts)
  const side = (cy, lab) => {
    const warm = /iekš|telp/.test(lab), cx = Lx / 2, r = 1.5;
    el("circle", { cx, cy, r, fill: "#fff", stroke: C.ink, "stroke-width": .2 }, g);
    el("path", { d: `M ${cx - .8} ${cy} H ${cx + .8}` + (warm ? ` M ${cx} ${cy - .8} V ${cy + .8}` : ""), stroke: C.ink, "stroke-width": .25, fill: "none" }, g);
  };
  side(top - 2.3, spec.top || "ārpuse");
  side(top + tot * sc + 2.3, spec.bottom || "iekšpuse");
  // leaders fan out to evenly spaced numbers, then the table
  const RH = 4.6, ty0 = top + 2, nx = Lx + 9;
  mids.forEach((m, i) => {
    const ly = ty0 + i * RH + RH / 2;
    el("polyline", { points: `${Lx * .6},${m} ${Lx + 3},${m} ${nx - 2.2},${ly}`, fill: "none", stroke: C.ink, "stroke-width": .15 }, g);
    el("circle", { cx: Lx * .6, cy: m, r: .35, fill: C.ink }, g);
    el("circle", { cx: nx, cy: ly, r: 2, fill: "#fff", stroke: C.ink, "stroke-width": .2 }, g);
    T_(g, nx, ly + .8, String(i + 1), { fs: 2.2, a: "middle" });
  });
  const tx = nx + 4, TW = 182 - tx;
  el("rect", { x: tx, y: ty0 - RH, width: TW, height: (ls.length + 2) * RH, fill: "none", stroke: C.ink, "stroke-width": .3 }, g);
  T_(g, tx + 2, ty0 - RH / 2 + .9, "SLĀNIS", { fs: 2, ls: .4, fw: 500 }); T_(g, tx + TW - 2, ty0 - RH / 2 + .9, "mm", { fs: 2, a: "end", fw: 500 });
  ls.forEach(([n, th], i) => {
    const yr = ty0 + i * RH;
    el("line", { x1: tx, y1: yr, x2: tx + TW, y2: yr, stroke: C.ink, "stroke-width": i ? .1 : .25 }, g);
    T_(g, tx + 2, yr + RH / 2 + .9, `${i + 1}. ${n}`, { fs: 2.3 }); T_(g, tx + TW - 2, yr + RH / 2 + .9, th ? String(th) : "–", { fs: 2.3, a: "end" });
  });
  const yt = ty0 + ls.length * RH;
  el("line", { x1: tx, y1: yt, x2: tx + TW, y2: yt, stroke: C.ink, "stroke-width": .25 }, g);
  T_(g, tx + 2, yt + RH / 2 + .9, "Kopā" + (spec.u ? `, U ≈ ${spec.u} W/m²K` : ""), { fs: 2.3, fw: 600 }); T_(g, tx + TW - 2, yt + RH / 2 + .9, String(tot), { fs: 2.3, a: "end", fw: 600 });
  el("line", { x1: tx + TW - 14, y1: ty0 - RH, x2: tx + TW - 14, y2: yt + RH, stroke: C.ink, "stroke-width": .15 }, g);
  return g;
}

// ---- window / door outside views for the specification ----
// windows: panes as seen from INSIDE; ĀD from outside; interior doors from the swing side (DK hinge left)
function openingView(g, x, y, w, h, kind, door, sc, hl = true, PN = null, cas = 0) {
  const W = w * sc, H = h * sc, f = 60 * sc;
  const R = (x0, y0, ww, hh, o = {}) => el("rect", { x: x0, y: y0, width: ww, height: hh, fill: "none", stroke: C.ink, "stroke-width": .1, ...o }, g);
  const dsh = { fill: "none", stroke: C.ink, "stroke-width": .15, "stroke-dasharray": "1 .6" };
  if (door) R(x - W / 2, y - H, W, H, { "stroke-width": .12 });
  if (door) {
    const x0 = x - W / 2 + f, lw = W - 2 * f, top = y - H + f, left = door === "ĀD" ? hl : door !== "DL";
    if (door === "ĀD") {
      R(x - W / 2, y - H, W, H, { fill: C.ral, "stroke-width": .12 });   // frame / casing in the door colour
      R(x0, top, lw, H - f, { fill: C.ral });
      // as on the facade: narrow glass strip on the hinge side, long bar handle opposite
      R(left ? x0 + 120 * sc : x0 + lw - 280 * sc, y - 1950 * sc, 160 * sc, 1800 * sc, { fill: "url(#glass)" });
      R(left ? x0 + lw - 260 * sc : x0 + 220 * sc, y - 1600 * sc, 40 * sc, 1100 * sc, { fill: "#b9bcbe", "stroke-width": .1 });
    } else {
      // lacquered wood casing and leaf, lever handle with rosette on the lock side
      R(x - W / 2, y - H, W, H, { fill: "#c9ad85", "stroke-width": .12 });
      R(x0, top, lw, H - f, { fill: "#dcc6a3" });
      const hx = left ? x0 + lw - 70 * sc : x0 + 70 * sc, hy = y - 1050 * sc, dir = left ? -1 : 1;
      el("circle", { cx: hx, cy: hy, r: 28 * sc, fill: "#d9d9d9", stroke: C.ink, "stroke-width": .1 }, g);
      el("line", { x1: hx, y1: hy, x2: hx + dir * 140 * sc, y2: hy, stroke: C.ink, "stroke-width": .45, "stroke-linecap": "round" }, g);
    }
    // opening symbol: lines meet at the handle side
    sashSym(g, x0, top, lw, H - f, { turn: left ? "l" : "r" }, door === "ĀD" ? { ...dsh, stroke: "#e8e8e8" } : dsh);
    return;
  }
  // window: same ArchiCAD style as on the facade (frame, sash, glass contours), without casing and sill
  PN = PN || PANES(kind, hl, false);
  const fw = 70 * sc, sw = 55 * sc, r = 18 * sc, x0 = x - W / 2, top = y - H, fc = colHex(WINC().inn);
  const ln = { stroke: C.ink, "stroke-width": .1 }, thin = { stroke: C.ink, "stroke-width": .06 };
  R(x0, top, W, H, { fill: fc, ...ln });
  R(x0 + r, top + r, W - 2 * r, H - 2 * r, { fill: "none", ...thin });
  const panes = PN.length, avail = W - fw * (panes + 1), gy = top + fw, gh = H - 2 * fw;
  for (let k = 0, gx = x0 + fw; k < panes; k++) {
    const pw = avail * (PN[k].f ?? 1 / panes); if (k) gx += avail * (PN[k - 1].f ?? 1 / panes) + fw;
    const p = PN[k], sash = p.turn || p.tilt || p.slide, i = sash ? sw : 25 * sc;
    if (k) R(gx - fw, gy, fw, gh, { fill: fc, ...thin });   // mullion
    if (sash) R(gx, gy, pw, gh, { fill: fc, ...ln });
    const a0 = gx + i, a1 = gx + pw - i, b0 = gy + i, b1 = gy + gh - i;
    R(a0, b0, a1 - a0, b1 - b0, { fill: "#8fadbb", ...thin });
    const sh = Math.min(330 * sc, (b1 - b0) * .25), sv = Math.min(190 * sc, (a1 - a0) * .15);
    el("polygon", { points: `${a0},${b0} ${a1},${b0} ${a1},${b1} ${a1 - sv},${b1} ${a1 - sv},${b0 + sh} ${a0},${b0 + sh}`, fill: "rgba(20,40,52,.38)" }, g);
    sashSym(g, sash ? gx : a0, sash ? gy : b0, sash ? pw : a1 - a0, sash ? gh : b1 - b0, p, { ...dsh, stroke: "#111" });
    if (p.slide) el("path", { d: `M ${gx + pw * .2} ${gy + gh / 2} H ${gx + pw * .8} m -1 -.6 l 1 .6 l -1 .6`, fill: "none", stroke: "#111", "stroke-width": .2 }, g);
  }
}
function openingTable(svg, x, y, title, cols, isDoor) {
  const g = el("g", { "data-block": "tbl-" + (isDoor ? "d" : "l"), transform: `translate(${x} ${y})` }, svg);
  const LW = 27, CW = Math.min(30, (378 - LW) / cols.length), W = LW + CW * cols.length;
  const rows = [["Apzīmējums", 6], ["Daudzums", 6], [isDoor ? "Skats" : "Skats no iekšpuses", 33], ["Ailes izmēri", 6], [isDoor ? "Durvju izmēri" : "Loga izmēri", 6], ["Apraksts", 15], ["Krāsa", 6], [isDoor ? "Ud" : "Uw", 6]];
  const H = rows.reduce((a, r) => a + r[1], 0) + 7;
  el("rect", { width: W, height: H, fill: "none", stroke: C.ink, "stroke-width": .35 }, g);
  T_(g, W / 2, 5, title, { fs: 3.2, fw: 600, a: "middle" });
  el("line", { x1: 0, y1: 7, x2: W, y2: 7, stroke: C.ink, "stroke-width": .3 }, g);
  el("line", { x1: LW, y1: 7, x2: LW, y2: H, stroke: C.ink, "stroke-width": .2 }, g);
  cols.forEach((c, k) => k && el("line", { x1: LW + k * CW, y1: 7, x2: LW + k * CW, y2: H, stroke: C.ink, "stroke-width": .2 }, g));
  const maxW = Math.max(...cols.map(c => c.w)), maxH = Math.max(...cols.map(c => c.h)), sc = Math.min((CW - 6) / maxW, 27 / maxH);
  let yy = 7;
  rows.forEach(([lab, rh], ri) => {
    if (ri) el("line", { x1: 0, y1: yy, x2: W, y2: yy, stroke: C.ink, "stroke-width": .15 }, g);
    T_(g, 1.5, yy + (ri === 2 || ri === 5 ? 3.6 : rh / 2 + 1), lab, { fs: 2.4 });
    cols.forEach((c, k) => {
      const cx = LW + k * CW + CW / 2, v = [c.mark, String(c.n), null, `${c.w}*${c.h}(h)`, `${c.w - 20}*${c.h - (isDoor ? 20 : 50)}(h)`, c.desc, c.color, c.u][ri];
      if (ri === 2) openingView(g, cx, yy + rh - 3, c.w, c.h, c.kind, c.door, sc, c.hl, c.panes && mirrorPanes(c.panes), c.cas);
      else if (ri === 5) wrap(v, Math.floor(CW / 1.05)).slice(0, 4).forEach((l, j) => T_(g, LW + k * CW + 1.2, yy + 3 + j * 2.9, l, { fs: 1.95 }));
      else if (ri === 6 && v.length > CW / 1.25) v.split(", ").slice(0, 2).forEach((l, j) => T_(g, cx, yy + 2.6 + j * 2.5, l, { fs: 1.95, a: "middle" }));
      else T_(g, cx, yy + rh / 2 + 1, v, { fs: ri === 0 ? 2.6 : 2.3, fw: ri === 0 ? 600 : 400, a: "middle" });
    });
    yy += rh;
  });
  return g;
}

// ---- window installation details at 1:5 ----
const DET_ITEMS = ["Logs, rāmis ar 3-stiklu paketi", "PU putu blīvējums", "Difūzijas (tvaika caurlaidīga) lenta", "Tvaika izolācijas lenta", "Palodzes profils 30 mm", "Skārda palodze RAL 7016, slīpums ≥ 5°", "Iekšējā palodze", "Skārda nolaide virs loga RAL 7016", "Apmales dēlis 21 mm", "Ailes apdare"];
let DET_LIST = [];
const detLegend = n => { let i = DET_LIST.indexOf(n); if (i < 0) { DET_LIST.push(n); i = DET_LIST.length - 1; } return i + 1; };
function winDetail(svg, x, y, kind, label) {
  const g = el("g", { "data-block": "det-" + kind, transform: `translate(${x} ${y})` }, svg), sc = .2;
  const ls = (LAYERS("S1") || { layers: EXT_SPEC.map(([n, t]) => [n, t === "-" ? 0 : +t]) }).layers;
  // a = across the wall from outside, b = into the wall body from the opening edge
  const M = kind === "sill" ? (a, b) => [a * sc, b * sc] : kind === "head" ? (a, b) => [a * sc, -b * sc] : (a, b) => [-b * sc + 70, a * sc];
  const poly = (pts, o = {}) => el("polygon", { points: pts.map(p => M(...p).join(",")).join(" "), fill: "#fff", stroke: C.ink, "stroke-width": .2, ...o }, g);
  const pl = (pts, o = {}) => el("polyline", { points: pts.map(p => M(...p).join(",")).join(" "), fill: "none", stroke: C.ink, "stroke-width": .2, ...o }, g);
  const BM = 330;
  let a = 0, studA = 0, studT = 0;
  const marks = [];
  ls.forEach(([n, th, f = ""], li) => {
    if (th > 0) {
      poly([[a, 0], [a + th, 0], [a + th, BM], [a, BM]], { fill: f.includes("a") ? "#fff" : "#fff" });
      if (f.includes("i")) {
        const id = "wd-" + kind + a; el("polygon", { points: [[a, 0], [a + th, 0], [a + th, BM], [a, BM]].map(p => M(...p).join(",")).join(" ") }, el("clipPath", { id }, g));
        const [x0, y0] = M(a, 0), [x1, y1] = M(a + th, BM);
        const bx = Math.min(x0, x1), by = Math.min(y0, y1), bw = Math.abs(x1 - x0), bh = Math.abs(y1 - y0);
        const along = kind === "jamb";
        el("path", { d: along ? loops(bx, by, 1, 0, 0, 1, bw, bh) : loops(bx, by, 0, 1, 1, 0, bh, bw), ...INS, "stroke-width": .12, "clip-path": `url(#${id})` }, g);
        if (th > studT) { studT = th; studA = a; }
      }
      if (/[hkol]/.test(f)) {
        const id = "wh-" + kind + a; el("polygon", { points: [[a, 0], [a + th, 0], [a + th, BM], [a, BM]].map(p => M(...p).join(",")).join(" ") }, el("clipPath", { id }, g));
        const [x0, y0] = M(a, 0), [x1, y1] = M(a + th, BM), bx = Math.min(x0, x1), by = Math.min(y0, y1), bw = Math.abs(x1 - x0), bh = Math.abs(y1 - y0);
        hatchBox(g, bx, by, bw, bh, f, 1, id);
      }
      marks.push([n, a + th / 2, 70 + li * 26]);
    } else {
      const [x0, y0] = M(a, -60), [x1, y1] = M(a, BM);
      membLine(g, x0, y0, x1, y1, f, 1); marks.push([n, a, 70 + li * 26]);
    }
    a += th;
  });
  const Wt = a;
  // framing member at the opening edge, drawn as cut timber
  poly([[studA, 0], [studA + studT, 0], [studA + studT, 45], [studA, 45]], { fill: "#efe7d6" });
  pl([[studA, 0], [studA + studT, 45]], { "stroke-width": .12 }); pl([[studA + studT, 0], [studA, 45]], { "stroke-width": .12 });
  // break line at the end of the wall body
  pl([[-15, BM], [Wt * .45, BM], [Wt * .5, BM - 12], [Wt * .55, BM + 12], [Wt * .6, BM], [Wt + 15, BM]], { "stroke-width": .25 });
  // window frame in the insulation zone, foam joint, glazing
  const f0 = studA + 14, f1 = f0 + 82, jb = kind === "sill" ? 50 : 20;
  poly([[f0, -jb], [f1, -jb], [f1, -jb - 85], [f0, -jb - 85]], { fill: "#e9ecee", "stroke-width": .3 });
  pl([[f0 + 12, -jb - 6], [f1 - 12, -jb - 6]], { "stroke-width": .12 }); pl([[f0 + 12, -jb - 30], [f1 - 12, -jb - 30]], { "stroke-width": .12 });
  [0, 18, 36].forEach(k => pl([[f0 + 23 + k, -jb - 85], [f0 + 23 + k, -jb - 240]], { "stroke-width": .25 }));
  pl([[f0 - 10, -jb - 250], [f1 + 10, -jb - 230]], { "stroke-width": .2 });
  poly([[f0, 0], [f1, 0], [f1, kind === "sill" ? -20 : -jb], [f0, kind === "sill" ? -20 : -jb]], { fill: "#f6efc9" });
  if (kind === "sill") poly([[f0, -20], [f1, -20], [f1, -50], [f0, -50]], { fill: "#dfe3e6" });
  // tapes: outside vapour-open, inside vapour-tight
  pl([[f0 - 3, -jb - 40], [f0 - 3, -4], [studA - 10, -4], [studA - 10, 60]], { stroke: "#2f6fb0", "stroke-width": .45 });
  pl([[f1 + 3, -jb - 40], [f1 + 3, -4], [studA + studT + 2, -4], [studA + studT + 2, 60]], { stroke: "#c0392b", "stroke-width": .45 });
  // outside: metal sill / head flashing / trim board; inside: window board / reveal lining
  if (kind === "sill") {
    pl([[f0 + 6, -50], [-45, -26], [-45, 2]], { "stroke-width": .45 });
    poly([[f1, -25], [Wt + 25, -25], [Wt + 25, 0], [f1, 0]], { fill: "#efe7d6" });
  } else {
    if (kind === "head") pl([[f0 + 10, -4], [-35, -4], [-35, -22]], { "stroke-width": .45 });
    else poly([[0, -60], [21, -60], [21, 90], [0, 90]], { fill: "#efe7d6" });
    poly([[f1, 0], [Wt, 0], [Wt, -13], [f1, -13]], { fill: "#eee" });
  }
  // numbered leaders to a column of numbers beside the detail; the numbers refer to one shared legend
  const items = [...marks.map(m => [m[0], m[1], m[2]]),
    [DET_ITEMS[0], (f0 + f1) / 2, -jb - 40], [DET_ITEMS[1], (f0 + f1) / 2, kind === "sill" ? -10 : -jb / 2],
    [DET_ITEMS[2], f0 - 3, -jb - 20], [DET_ITEMS[3], f1 + 3, -jb - 20],
    ...(kind === "sill" ? [[DET_ITEMS[4], (f0 + f1) / 2, -35], [DET_ITEMS[5], -20, -26], [DET_ITEMS[6], Wt - 10, -12]]
      : kind === "head" ? [[DET_ITEMS[7], -20, -4], [DET_ITEMS[9], Wt - 10, -6]] : [[DET_ITEMS[8], 10, 40], [DET_ITEMS[9], Wt - 10, -6]])];
  const pts = items.map(([n, ia, ib]) => [detLegend(n), ...M(ia, ib)]).sort((p, q) => kind === "jamb" ? p[1] - q[1] : p[2] - q[2]);
  pts.forEach(([no, px, py], i) => {
    const [lx, ly] = kind === "jamb" ? [-8 + i * 7.2, -14] : [76, -58 + i * 4.4];
    el("circle", { cx: px, cy: py, r: .35, fill: C.ink }, g);
    el("line", { x1: px, y1: py, x2: lx, y2: ly + (kind === "jamb" ? 1.9 : 0), stroke: C.ink, "stroke-width": .1 }, g);
    if (kind !== "jamb") el("line", { x1: lx - 1.9, y1: ly, x2: lx - 1.9, y2: ly, stroke: C.ink }, g);
    el("circle", { cx: lx, cy: ly, r: 1.9, fill: "#fff", stroke: C.ink, "stroke-width": .2 }, g);
    T_(g, lx, ly + .8, String(no), { fs: 2, a: "middle" });
  });
  T_(g, kind === "jamb" ? -8 : -10, kind === "jamb" ? -24 : -70, label, { fs: 3.4, fw: 600, ls: .2 });
  T_(g, (kind === "jamb" ? -8 : -10) + label.length * 2.2 + 6, kind === "jamb" ? -24 : -70, "M 1:5", { fs: 3, fill: "#444" });
  return g;
}

// ---------- the AR sheets ----------
function arSheets(v) {
  // ridge level given (eave → ridge from the client's drawing): long-slope pitch follows from it
  const rg = (ARC.roof || {}).ridge;
  if (rg) {
    const top = a => { const tn = Math.tan(a * Math.PI / 180); return ROOF.eave - ROOF.ov * tn + ROOF.th / Math.cos(a * Math.PI / 180) + (v.D / 2 + ROOF.ov) * tn; };
    let lo = 1, hi = 60; for (let i = 0; i < 60; i++) { const m = (lo + hi) / 2; if (top(m) < rg) lo = m; else hi = m; }
    ROOF.pitch = (lo + hi) / 2; tan = Math.tan(ROOF.pitch * Math.PI / 180);
  }
  const total = ARC.parts.length, out = [];
  const sheet = (k, title, scale) => { const svg = el("svg", { viewBox: "0 0 420 297", class: "a3", role: "img", "aria-label": title });
    el("rect", { width: 420, height: 297, fill: "#fff" }, svg);
    el("rect", { x: 20, y: 10, width: 390, height: 277, fill: "none", stroke: C.ink, "stroke-width": .5 }, svg);
    arTitle(svg, title, arNo(k), total, scale); svg.dataset.part = k; return svg; };
  const { ridgeTop } = roofGeo(v), H = ridgeTop + ROOF.plinth;
  const net = v.rooms.reduce((a, rm) => a + area(rm), 0), foot = polyArea(v.poly);
  const LR = v.W + 2 * ROOF.ov, BR = v.D + 2 * ROOF.ov, hi = hipIns(v);
  const roofA = ((LR - hi) * BR / Math.cos(ROOF.pitch * Math.PI / 180) + (ROOF.hip ? hi * BR / Math.cos(ROOF.hip * Math.PI / 180) : 0)) / 1e6;
  const fasT = side2 => `Fasādes asīs ${sideAxes(v, side2[0])} un ${sideAxes(v, side2[1])}`;
  const titles = { fas1: fasT(["south", "west"]), fas2: fasT(["north", "east"]) };
  ARC.parts.forEach(k => {
    const title = titles[k] || AR_PARTS[k];
    if (k === "plan" || k === "mebel") {
      const dims = k === "plan", other = dims ? arNo("mebel") : arNo("plan");
      const own = [v.ceilingNote || "Griestu augstums istabās 2500 mm, virtuvē un viesistabā atvērts līdz jumtam.", "Izmēri līdz konstrukcijas virsmai.", ...(v.planNotes || [])];
      if (other) own.push(dims ? `Mēbeļu izvietojumu skatīt lapā ${other}.` : `Izmērus un marķējumu skatīt lapā ${other}.`);
      const svg = planSheet(v, { sheetEl: sheet(k, title, "1:100"), furniture: !dims, tags: dims, wallTags: dims, wallLegend: false, sections: dims && !!arNo("griez"), symbols: dims, notes: arNotes(own), markTables: dims && !arNo("logi"), heading: dims ? "1. STĀVA PLĀNS AR IZMĒRIEM" : "1. STĀVA PLĀNS AR MĒBELĒM", tag: "-" + k });
      out.push(svg); return;
    }
    const svg = sheet(k, title, k === "mezgli" ? "1:5" : k === "sienas" ? "1:10" : k === "visp" || k === "logi" ? "-" : "1:100");
    if (k === "visp") {
      const tbl = (x, y, w, head, rows, c1) => {
        const g = el("g", { "data-block": "t-" + head.slice(0, 4), transform: `translate(${x} ${y})` }, svg), RH = 5.6;
        el("rect", { width: w, height: (rows.length + 1) * RH, fill: "none", stroke: C.ink, "stroke-width": .4 }, g);
        T_(g, w / 2, RH / 2 + 1.1, head, { fs: 3.1, fw: 700, ls: 1, a: "middle" });
        rows.forEach(([a, b], i) => {
          const yy = (i + 1) * RH; el("line", { x1: 0, y1: yy, x2: w, y2: yy, stroke: C.ink, "stroke-width": i ? .15 : .3 }, g);
          T_(g, 1.8, yy + RH / 2 + 1, a, { fs: 2.7 }); T_(g, c1 + 1.8, yy + RH / 2 + 1, b, { fs: 2.7 });
        });
        el("line", { x1: c1, y1: RH, x2: c1, y2: (rows.length + 1) * RH, stroke: C.ink, "stroke-width": .2 }, g);
        return (rows.length + 1) * RH;
      };
      const d = ARC.data || {}, tb = ARC.tb || {};
      const h1 = tbl(26, 22, 180, "OBJEKTA DATI", [["Objekts", (tb.object || [])[0] || ""], ["Adrese", d.adrese || ""], ["Kadastra apzīmējums", d.kadastrs || ""], ["Pasūtītājs", d.pasutitajs || ""], ["Būvniecības veids", d.veids || ""], ["Būves lietošanas veids", d.lietosana || ""], ["Stadija", tb.stage || ""]], 52);
      const fl = ARC.floor || {}, roofTxt = roofSeams() ? "valcprofila skārds" : "bitumena šindeļi";
      tbl(26, 22 + h1 + 8, 180, "GALVENIE RĀDĪTĀJI", [["Apbūves laukums", `${f2(foot)} m²`], ["Kopējā platība", `${f2(net)} m²`], ["Būvtilpums", `≈ ${Math.round(foot * (ROOF.plinth + ROOF.eave) / 1000 + v.D * (v.D / 2 * tan) * (v.W / 2 - (ROOF.hip ? v.D / 2 * tan / Math.tan(ROOF.hip * Math.PI / 180) / 3 : 0)) / 1e9)} m³`],
        ["Stāvu skaits", String(d.stavi || 1)], ["Ēkas augstums (no zemes līdz korei)", `${(H / 1000).toFixed(2).replace(".", ",")} m`], ["Jumta slīpums, segums", `${pitchTxt()}, ${roofTxt}`],
        ["Pamati", fl.foundation === "stabi" ? "stabveida pamati" : "siltināta pamatu plātne"], ["Ārsienas", `${(LAYERS("S1") || { name: "koka karkasa" }).name}, ${T} mm`], ["Ugunsnoturības pakāpe", d.ugunsnoturiba || ""]], 70);
      const list = ARC.parts.map(p => [arNo(p), titles[p] || AR_PARTS[p]]);
      tbl(222, 22, 182, "LAPU SARAKSTS", list, 20);
      notesBlock(svg, 222, 22 + (list.length + 1) * 5.6 + 12, 182, ARC.general || []);
    }
    if (k === "jumts") {
      roofPlan(el("g", { transform: "translate(57 50) scale(0.01)" }, svg), v);
      sheetHeading(svg, 26, 197, 199, "JUMTA PLĀNS");
      const r = ARC.roof || {};
      const notes = [`Jumta materiāls – ${roofSeams() ? "valcprofila skārds" : "bitumena šindeļi"}, krāsas tonis ${r.color || "RAL 7016"}${r.texture ? ` (${r.texture})` : ""}.`, `Ēkas jumta platība ≈ ${Math.round(roofA)} m².`, `Jumta slīpums ${pitchTxt()}, pārkare ${ROOF.ov} mm.`,
        `Lietus ūdens novadīšanai paredzēta ${r.gutter || "pusapaļa noteku sistēma, skārds ar PU pārklājumu"}, krāsas tonis ${r.color || "RAL 7016"}: 1 – tekne ${r.tekne || 125} mm, 2 – notekcaurule ${r.noteka || 90} mm.`];
      if (arNo("griez")) notes.push(`Griezumus 1-1; 2-2 skatīt lapā ${arNo("griez")}.`);
      notesBlock(svg, 252, 22, 152, [notes[0], UNITS, ...notes.slice(1)]);
    }
    if (k === "griez") {
      const [s1, s2] = v.sections;
      section(el("g", { "data-block": "sec-2", transform: "translate(52 122) scale(0.01)" }, svg), v, s2);
      section(el("g", { "data-block": "sec-1", transform: "translate(52 222) scale(0.01)" }, svg), v, s1);
      const fl = ARC.floor || {};
      notesBlock(svg, 232, 168, 172, [...arNotes([]).slice(0, 1), `Grīdas konstrukcija: ${fl.foundation === "stabi" ? "uz stabveida pamatiem" : "siltināta pamatu plātne"}, grīdas pīrāgs ${(LAYERS("G1") || { layers: [] }).layers.reduce((a, l) => a + l[1], 0)} mm${arNo("sienas") ? `, sk. lapu ${arNo("sienas")}` : ""}.`, `Ēkas augstums no zemes līdz korei ${(H / 1000).toFixed(2).replace(".", ",")} m.`, v.ceilingNote || "Griestu augstums istabās 2500 mm, virtuvē un viesistabā atvērts līdz jumtam.", "Griezumu vietas skatīt lapā " + (arNo("plan") || arNo("jumts") || "") + "."]);
    }
    if (k === "fas1" || k === "fas2") {
      const [a, b] = k === "fas1" ? ["south", "west"] : ["north", "east"];
      elevation(el("g", { "data-block": "elev-" + a, transform: `translate(52 150) scale(0.01)` }, svg), v, a, { levels: true, title: `FASĀDE ASĪS ${sideAxes(v, a)}` });
      elevation(el("g", { "data-block": "elev-" + b, transform: `translate(266 150) scale(0.01)` }, svg), v, b, { levels: true, title: `FASĀDE ASĪS ${sideAxes(v, b)}` });
      materials(svg, 30, 196, false);
      const fl = ARC.floor || {};
      notesBlock(svg, 118, 196, 100, [...arNotes([]).slice(0, 2), "Fasāžu materiālu krāsu toņus saskaņot ar pasūtītāju.", ...(arNo("logi") ? [`Logu, durvju specifikāciju skatīt lapā ${arNo("logi")}.`] : [])]);
    }
    if (k === "sienas") {
      const specs = ["S1", "S2", "G1", "J1"].filter(LAYERS);
      specs.forEach((id, i) => buildUp(svg, i % 2 ? 222 : 26, 22 + Math.floor(i / 2) * 112, id, { ...LAYERS(id), top: id === "G1" ? "telpa" : id === "S2" ? "iekšpuse" : "ārpuse", bottom: id === "G1" ? "grunts" : "iekšpuse" }));
      if (arNo("plan")) T_(svg, 26, 282, `Sienu tipu S1, S2 novietojumu skatīt lapā ${arNo("plan")}.`, { fs: 2.6, fill: "#333" });
    }
    if (k === "logi") {
      const mk = marks(v), w = ARC.win || {};
      const KD = { tilt: "vēramais-gāžamais", turn: "vēramais", hopper: "gāžamais", casement2: "divvērtņu, abas vērtnes vēramas", casement2t: "divvērtņu, abas vērtnes vēramas, viena gāžama", slide2: "pacelšanas-bīdāmais", fixed: "neverams (vitrīna)" };
      const wins = mk.types.filter(r => r.mark[0] === "L").map(r => {
        const src = v.windows.find((x, i) => mk.win[i] === r.mark);
        return { mark: r.mark, n: r.n, w: r.w, h: r.h, kind: src.kind, panes: r.panes, desc: `Stikla pakešu logs, ${w.mat || "PVC"} konstrukcija, ${src.parts ? `${src.parts.length}-daļīgs: ` + src.parts.map(p => `${KD[p.kind].replace(" (vitrīna)", "")} ${p.len} mm`).join(" + ") : KD[src.kind + (src.kind === "casement2" && src.tilt ? "t" : "")]}${r.sill ? "" : ", līdz grīdai"}.`, cas: r.cas, color: WINC().inn === WINC().out ? WINC().out : `ārā ${WINC().out}, iekšā ${WINC().inn}`, u: `${w.uw || "0,9"} W/m²K` };
      });
      (v.gableWins || []).length && wins.push({ mark: `L-${wins.length + 1}`, n: v.gableWins.length, w: v.gableWins[0].u1 - v.gableWins[0].u0, h: 1500, kind: "fixed", desc: `Stikla pakešu logs, ${w.mat || "PVC"} konstrukcija, neverams, augšmala pa jumta slīpumu (frontonā).`, cas: (w.casing || 0), color: WINC().inn === WINC().out ? WINC().out : `ārā ${WINC().out}, iekšā ${WINC().inn}`, u: `${w.uw || "0,9"} W/m²K` });
      const doors = mk.types.filter(r => r.mark[0] !== "L").map(r => ({ mark: r.mark, n: r.n, w: r.w, h: r.h, hl: r.hl, door: r.mark.split("-")[0], desc: r.mark[0] === "Ā" ? `Ārdurvis, ${w.doorMat || "koka-alumīnija"} konstrukcija, ar stikla paketi, siltinātas, ar garo rokturi.` : `Iekšdurvis, ${w.intDoor || "koka, lakotas"}, ar kārbu, apmalēm un rokturi, vērtne ${r.mark.startsWith("DK") ? "kreisā" : "labā"}.`, color: r.mark[0] === "Ā" ? (w.color || "RAL 7016") : (w.intDoorColor || "koks, lakots"), u: r.mark[0] === "Ā" ? `${w.ud || "1,1"} W/m²K` : "–" }));
      openingTable(svg, 26, 16, "LOGU SPECIFIKĀCIJA", wins, false);
      openingTable(svg, 26, 116, "DURVJU SPECIFIKĀCIJA", doors, true);
      notesBlock(svg, 26, 217, 190, ["Logi un iekšdurvis doti skatā no iekšpuses, ārdurvis skatā no ārpuses; vēršanās virziens un eņģes puse (kreisā/labā) noteikta skatā no iekšpuses. Fasādēs logi skatā no ārpuses. Vēršanās simbola līnijas saiet roktura pusē.", "Logu, durvju materiālu, krāsu, furnitūru, vēršanās virzienu pirms izgatavošanas saskaņot ar pasūtītāju.", "Apzīmējums „DK” – kreisās durvis, „DL” – labās durvis, „ĀD” – ārdurvis.", `Specifikācijas skatīt kopā ar stāva plānu${arNo("plan") ? ` (${arNo("plan")})` : ""} un fasāžu lapām${arNo("fas1") ? ` (${[arNo("fas1"), arNo("fas2")].filter(Boolean).join(", ")})` : ""}.`]);
    }
    if (k === "mezgli") {
      DET_LIST = (LAYERS("S1") || { layers: EXT_SPEC }).layers.map(l => l[0]);
      winDetail(svg, 40, 92, "sill", "1. PALODZES MEZGLS");
      winDetail(svg, 145, 92, "head", "2. AUGŠAS MEZGLS");
      winDetail(svg, 40, 200, "jamb", "3. SĀNU MEZGLS");
      notesBlock(svg, 252, 22, 152, DET_LIST.map((n, i) => n), "APZĪMĒJUMI");
      notesBlock(svg, 252, 150, 152, ["Logu montāžu veikt saskaņā ar ražotāja instrukciju (RAL montāža: ārā tvaika caurlaidīga, iekšā tvaika necaurlaidīga lenta).", "Logu rāmi stiprināt ar montāžas skrūvēm vai enkurplāksnēm pie karkasa, solis ≤ 700 mm.", "Mezgli doti principiāli, precizēt pēc izvēlētā loga profila." + (arNo("logi") ? ` Logu specifikāciju skatīt lapā ${arNo("logi")}.` : "")]);
    }
    out.push(svg);
  });
  return out;
}

// materials legend (shared by the facade sheets)
function materials(svg, x, y, twoCols) {
  const lg = el("g", { "data-block": "materials", transform: `translate(${x} ${y})` }, svg);
  T_(lg, 0, 0, "MATERIĀLI", { fs: 3.2, fw: 600, ls: .3 });
  const r = (ARC && ARC.roof) || {}, seam = roofSeams();
  const mats = (ARC && ARC.materials) ? ARC.materials.map(([k, a, b]) => [k === "roof" ? (seam ? "#40464b" : "url(#shingle)") : k, a, b]) : [["wood", "Fasāde: vertikāla koka apdare,", "krāsota tumši pelēka (antracīts)"], [seam ? "#40464b" : "url(#shingle)", seam ? "Jumts: valcprofila skārds" : "Jumts: bitumena šindeļi,", r.color || "RAL 7016"], ["#2f3438", "Notekas, notekcaurules", r.color || "RAL 7016"], [C.ral, "Logi, durvis: rāmji", "RAL 7016"], ["#9b9c98", "Cokols: pamatu plātne,", "betons"]];
  mats.forEach(([f, a, b], i) => {
    const yy = twoCols ? 7 + (i % 3) * 11 : 6 + i * 11, xx = twoCols ? Math.floor(i / 3) * 78 : 0;
    const sw = el("g", { transform: `translate(${xx} ${yy})` }, lg);
    if (f === "wood") { const cid2 = "swm-" + x + i; el("rect", { width: 10, height: 7 }, el("clipPath", { id: cid2 }, sw)); boards(el("g", { transform: "scale(0.01)" }, el("g", { "clip-path": `url(#${cid2})` }, sw)), 0, 1000, 0, 700); }
    else if (f.startsWith("url")) el("rect", { width: 1000, height: 700, fill: f, transform: "scale(0.01)" }, sw);
    else el("rect", { width: 10, height: 7, fill: f }, sw);
    el("rect", { width: 10, height: 7, fill: "none", stroke: C.ink, "stroke-width": .2 }, sw);
    T_(sw, 13, 2.9, a, { fs: 2.4 }); T_(sw, 13, 6.1, b, { fs: 2.4, fill: "#444" });
  });
  return lg;
}

// bitumen shingle pattern for roofs (elevation units mm)
{
  const p = el("pattern", { id: "shingle", patternUnits: "userSpaceOnUse", width: 680, height: 340 }, defs);
  el("rect", { width: 680, height: 340, fill: "#45474a" }, p);
  [[0, 170], [170, 0]].forEach(([yy, xx]) => el("path", { d: `M 0 ${yy} H 680 M ${xx} ${yy} V ${yy + 170} M ${xx + 340} ${yy} V ${yy + 170}`, stroke: "#2a2c2e", "stroke-width": 10 }, p));
}
