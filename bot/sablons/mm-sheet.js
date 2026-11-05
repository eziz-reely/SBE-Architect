// ---------- MM Homes: KLIENTA PROJEKTS, one A3 portrait sheet per house model ----------
// left: ground floor plan + its room table, loft plan + its room table, 4 facades, notes
// right strip x 247..287: vertical MM Homes title block (brand, phase, model, key figures, address, revisions)
const MM_TXT = {
  lv: { plan: "1. STĀVA PLĀNS", loft: "MANSARDA PLĀNS", expl: "TELPU EKSPLIKĀCIJA", total: "Kopā", foot: "Apbūves laukums", fas: "FASĀDE ASĪS", notes: "PIEZĪMES",
        mat: "Fasāde: vertikāla koka apdare; jumts: valcprofila skārds RAL 7016; logi, durvis RAL 7016.", tone: "Fasāžu materiālu krāsu toņus saskaņot ar pasūtītāju.",
        f1: "1. stāvs", f2: "Mansards", tag: "MODULĀRAS MĀJAS", phase: "SKICES PROJEKTS", model: "MODELIS", obj: "OBJEKTA ADRESE", cont: "PIEZĪMES",
        contL: ["1. stāva plāns", "Mansarda plāns", "Fasādes", "Telpu eksplikācija", "Materiāli un toņi"], key: "GALVENIE RĀDĪTĀJI", kFoot: "Apbūves laukums", kNet: "Iekštelpu platība",
        kSize: "Gabarīti", kRidge: "Kores augstums", kCeil: "Griestu augstums", kPitch: "Jumta slīpums", matT: "MATERIĀLI UN TOŅI",
        mats: [["wood", "Fasāde: vertikāla koka apdare,", "krāsota tumši pelēka (antracīts)"], ["roof", "Jumts: valcprofila skārds", "RAL 7016"], ["#2f3438", "Notekas, notekcaurules", "RAL 7016"], ["#383E42", "Logi, durvis: rāmji", "RAL 7016"], ["#1d1d1d", "Cokols: metāla apdare,", "RAL 9005"]], rev: "REVĪZIJAS", rNr: "Nr.", rDate: "Datums", rDesc: "Apraksts",
        scale: "MĒROGS", fmt: "FORMĀTS", sheet: "LAPA", info: "Rasējums ir informatīvs un nav būvniecības dokuments. Izmēri precizējami ražošanas projektā." },
  en: { plan: "GROUND FLOOR PLAN", loft: "LOFT FLOOR PLAN", expl: "ROOM SCHEDULE", total: "Total", foot: "Building area", fas: "ELEVATION", notes: "NOTES",
        mat: "Facade: vertical timber cladding; roof: standing seam steel RAL 7016; windows, doors RAL 7016.", tone: "Facade colours to be agreed with the client.",
        f1: "Ground floor", f2: "Loft", tag: "MODULAR HOMES", phase: "SKETCH DESIGN", model: "MODEL", obj: "SITE ADDRESS", cont: "NOTES",
        contL: ["Ground floor plan", "Loft floor plan", "Elevations", "Room schedule", "Materials and colours"], key: "KEY FIGURES", kFoot: "Building area", kNet: "Floor area",
        kSize: "Footprint", kRidge: "Ridge height", kCeil: "Ceiling height", kPitch: "Roof pitch", matT: "MATERIALS AND COLOURS",
        mats: [["wood", "Facade: vertical timber cladding,", "painted dark grey (anthracite)"], ["roof", "Roof: standing seam steel", "RAL 7016"], ["#2f3438", "Gutters, downpipes", "RAL 7016"], ["#383E42", "Windows, doors: frames", "RAL 7016"], ["#1d1d1d", "Plinth: metal cladding,", "RAL 9005"]], rev: "REVISIONS", rNr: "No.", rDate: "Date", rDesc: "Description",
        scale: "SCALE", fmt: "SIZE", sheet: "SHEET", info: "This drawing is for information only and is not a construction document. Dimensions to be confirmed in the production project." },
};
const MM_DARK = "#36312D", MM_BEIGE = "#E0D4B5", MM_ACC = "#A8916A", MM_SOFT = "#F3F1EC", MM_GREY = "#6b6b6b";
const mmRooms = v => v ? v.rooms.filter(rm => !rm.void) : [];
const mmNum = (x, d = 2) => x.toFixed(d).replace(".", ",");

// room table: dark header, numbered rows, total
function mmTable(svg, x, y, w, title, sub, rooms, L, foot) {
  const g = el("g", { "data-block": "schedule", transform: `translate(${x} ${y})` }, svg), RH = 5;
  el("rect", { width: w, height: 6.5, fill: MM_DARK }, g);
  T_(g, 2, 4.4, title, { fs: 2.4, fw: 700, ls: .45, fill: "#fff" });
  T_(g, w - 2, 4.4, sub, { fs: 2.1, a: "end", fill: "#d9d4ca" });
  let yy = 6.5;
  rooms.forEach((rm, i) => {
    if (i % 2) el("rect", { y: yy, width: w, height: RH, fill: MM_SOFT }, g);
    const nm = L === "en" ? (rm.en || rm.n) : rm.n;
    el("circle", { cx: 3.6, cy: yy + RH / 2, r: 1.75, fill: "none", stroke: MM_ACC, "stroke-width": .25 }, g);
    T_(g, 3.6, yy + RH / 2 + .75, String(i + 1), { fs: 1.9, a: "middle", fw: 600 });
    T_(g, 7, yy + RH / 2 + .8, nm, { fs: nm.length > 24 ? 1.9 : 2.2 });
    T_(g, w - 2, yy + RH / 2 + .8, mmNum(area(rm)) + " m²", { fs: 2.2, a: "end" });
    yy += RH;
  });
  el("line", { x1: 0, y1: yy, x2: w, y2: yy, stroke: MM_DARK, "stroke-width": .35 }, g);
  T_(g, 2, yy + 3.8, MM_TXT[L].total, { fs: 2.3, fw: 700 });
  T_(g, w - 2, yy + 3.8, mmNum(rooms.reduce((a, rm) => a + area(rm), 0)) + " m²", { fs: 2.3, a: "end", fw: 700 });
  yy += RH + .5;
  if (foot) { T_(g, 2, yy + 3.3, MM_TXT[L].foot, { fs: 2, fill: MM_GREY }); T_(g, w - 2, yy + 3.3, mmNum(foot) + " m²", { fs: 2, a: "end", fill: MM_GREY }); yy += RH; }
  el("rect", { width: w, height: yy, fill: "none", stroke: MM_DARK, "stroke-width": .3 }, g);
  return yy;
}

// vertical title block, x 247..287
function mmTitleBlock(svg, v, lf, L) {
  const tx = MM_TXT[L], P = (window.AR && window.AR.projekts) || {}, X = 247, W = 40, cx = X + W / 2;
  const g = el("g", { "data-block": "title" }, svg);
  const lab = (y, t) => { T_(g, X + 3, y, t, { fs: 1.8, fw: 700, ls: .35, fill: MM_ACC }); el("line", { x1: X + 3, y1: y + 1.2, x2: X + W - 3, y2: y + 1.2, stroke: "#d6d0c4", "stroke-width": .2 }, g); };
  // brand
  if (window.MM_LOGO) {   // īstais MM logo (modelu-bots/LOGO.png): tumši brūns fons, bēšs M
    el("rect", { x: X, y: 10, width: W, height: 58, fill: MM_DARK }, g);
    el("image", { href: window.MM_LOGO, x: X + 2, y: 11, width: W - 4, height: (W - 4) * 433 / 486, preserveAspectRatio: "xMidYMid slice" }, g);
    T_(g, cx, 54.5, "HOMES", { fs: 4.2, fw: 600, a: "middle", fill: MM_BEIGE, ls: 2.2 });
    T_(g, cx, 62, tx.tag, { fs: 1.8, a: "middle", fill: "#b9ad93", ls: .6 });
  } else {
    el("rect", { x: X, y: 10, width: W, height: 58, fill: MM_DARK }, g);
    T_(g, cx, 38, "MM", { fs: 17, fw: 700, a: "middle", fill: "#fff", ls: .5 });
    el("line", { x1: cx - 9, y1: 43, x2: cx + 9, y2: 43, stroke: MM_ACC, "stroke-width": .6 }, g);
    T_(g, cx, 50, "HOMES", { fs: 4.2, fw: 600, a: "middle", fill: "#fff", ls: 2.2 });
    T_(g, cx, 57.5, tx.tag, { fs: 1.8, a: "middle", fill: "#cfc8bb", ls: .6 });
  }
  // phase
  el("rect", { x: X + 3, y: 73, width: W - 6, height: 7, rx: 3.5, fill: "none", stroke: MM_ACC, "stroke-width": .45 }, g);
  T_(g, cx, 77.8, tx.phase, { fs: 2.3, fw: 700, a: "middle", ls: .5, fill: MM_DARK });
  // model
  lab(88, tx.model);
  if (P.modela_nosaukums) {   // modeļa vārds (piem. Freya) un zem tā MM + m²
    T_(g, X + 3, 97, P.modela_nosaukums, { fs: P.modela_nosaukums.length > 9 ? 4.6 : 6.2, fw: 700, fill: MM_DARK });
    T_(g, X + 3, 102.5, P.modelis || "", { fs: 2.6, fw: 600, fill: MM_ACC, ls: .4 });
  } else T_(g, X + 3, 98, P.modelis || v.short || "", { fs: 6.2, fw: 700, fill: MM_DARK });
  // key figures
  const I = P.ievade || {}, foot = polyArea(v.poly), net = [...mmRooms(v), ...mmRooms(lf)].reduce((a, rm) => a + area(rm), 0);
  lab(108, tx.key);
  const kv = [[tx.kFoot, mmNum(foot) + " m²"], [tx.kNet, mmNum(net) + " m²"], [tx.kSize, `${Math.round(v.W)} × ${Math.round(v.D)}`],
    [tx.kRidge, I.augstums ? mmNum(I.augstums / 1000) + " m" : "–"], [tx.kCeil, mmNum((v.ceiling || 2200) / 1000) + " m"], [tx.kPitch, (P.pitch || 25) + "°"],
    ...(P.raditaji || []).map(r => L === "en" && r.length > 2 ? [r[2], r[3] || r[1]] : r)];   // papildu rādītāji: [nosaukums, vērtība, EN nosaukums, EN vērtība]
  let ky = 114;
  kv.forEach(([k, val]) => {
    T_(g, X + 3, ky, k, { fs: 1.9, fill: MM_GREY });
    T_(g, X + 3, ky + 4, val, { fs: 3, fw: 600, fill: MM_DARK });
    ky += 8.2;
  });
  // address
  ky += 1;
  if ((P.adrese || []).length) {   // bez adreses (--bez-adreses): sadaļu nerāda
    lab(ky, tx.obj);
    P.adrese.forEach((l, i) => T_(g, X + 3, ky + 5.5 + i * 3.6, l, { fs: 2.3, fill: MM_DARK }));
    ky += 7 + P.adrese.length * 3.6 + 6;
  }
  lab(ky, tx.cont);
  // projekta piezīmes (pamati u.c.): model.json projekts.piezimes, EN: piezimes_en
  let ny = ky + 5.5;
  ((L === "en" ? P.piezimes_en : P.piezimes) || P.piezimes || []).forEach(t => {
    const ls = wrap(t, 25);
    T_(g, X + 3, ny, "—", { fs: 2.1, fill: MM_ACC });
    ls.forEach((l, j) => T_(g, X + 6.5, ny + j * 3.2, l, { fs: 2.1, fill: MM_DARK }));
    ny += ls.length * 3.2 + 1.2;
  });

  // vertical watermark in the free space between the notes and the info note (left out when it does not fit)
  { const wm = (P.modela_nosaukums || P.modelis || v.short || "") + "  ·  " + tx.phase, top = ny + 4, bot = 326, fs = Math.min(5.5, (bot - top) / (wm.length * 0.95));
    if (fs >= 3) T_(g, 0, 0, wm, { fs, fw: 700, ls: fs * .22, fill: "#e9e5dc", tr: `translate(${cx + fs * .35} ${(top + bot) / 2}) rotate(-90)`, a: "middle" }); }
  // info note
  const info = wrap(tx.info, 27);
  info.forEach((l, i) => T_(g, X + 3, 344 - (info.length - 1 - i) * 2.8, l, { fs: 1.75, fill: MM_GREY }));
  // revisions
  lab(350, tx.rev);
  const ry = 355;
  T_(g, X + 3, ry, tx.rNr, { fs: 1.7, fill: MM_GREY }); T_(g, X + 10, ry, tx.rDate, { fs: 1.7, fill: MM_GREY }); T_(g, X + 23, ry, tx.rDesc, { fs: 1.7, fill: MM_GREY });
  T_(g, X + 3, ry + 4, P.revizija || "00", { fs: 2.2, fw: 700 });
  T_(g, X + 10, ry + 4, P.datums || "", { fs: 2.1 });
  wrap(L === "en" ? (P.rev_apraksts_en || P.rev_apraksts || "") : (P.rev_apraksts || ""), 10).forEach((l, i) => T_(g, X + 23, ry + 4 + i * 2.8, l, { fs: 1.9 }));
  // bottom cells: scale / size / sheet
  el("line", { x1: X, y1: 372, x2: X + W, y2: 372, stroke: C.ink, "stroke-width": .35 }, g);
  [[tx.scale, "1:100"], [tx.fmt, "A3"], [tx.sheet, P.lapa || "1/1"]].forEach(([k, val], i) => {
    const x = X + i * W / 3;
    if (i) el("line", { x1: x, y1: 372, x2: x, y2: 386, stroke: C.ink, "stroke-width": .2 }, g);
    T_(g, x + W / 6, 377, k, { fs: 1.6, a: "middle", fill: MM_GREY, ls: .2 });
    T_(g, x + W / 6, 383, val, { fs: 2.8, fw: 700, a: "middle" });
  });
  el("rect", { x: X, y: 386, width: W, height: 24, fill: MM_DARK }, g);
  if (window.MM_LOGO) el("image", { href: window.MM_LOGO, x: X + W - 15, y: 389, width: 13, height: 13 * 433 / 486 }, g);
  T_(g, X + 3, 393, "REV. " + (P.revizija || "00"), { fs: 2.6, fw: 700, fill: MM_ACC, ls: .4 });
  T_(g, X + 3, 398.5, P.datums || "", { fs: 2.2, fill: "#fff" });
  T_(g, X + 3, 405, "MM Homes", { fs: 2.2, fw: 600, fill: MM_BEIGE, ls: .3 });
}

function modelSheet(v) {
  const L = window.MM_LANG || "lv", tx = MM_TXT[L];
  const lf = V.find(x => x.id === "A" && x.rev === v.rev + 1);
  const svg = el("svg", { viewBox: "0 0 297 420", class: "a3", role: "img", "aria-label": v.short || "Modelis" });
  el("rect", { width: 297, height: 420, fill: "#fff" }, svg);
  el("rect", { x: 20, y: 10, width: 267, height: 400, fill: "none", stroke: C.ink, "stroke-width": .5 }, svg);
  el("line", { x1: 247, y1: 10, x2: 247, y2: 410, stroke: C.ink, "stroke-width": .35, "data-block": "title-strip" }, svg);
  const k = .01, w = v.W * k, d = v.D * k;
  const PX = 49, TX = Math.max(168, PX + w + 26), TW = 241 - TX;   // plan origin x, room tables column (moves right for long houses)

  // 1) ground floor: furniture, inner and outer dimensions, axes close to the outer chain; client mode = no element marks
  const PY = 41;
  cadPlan(el("g", { "data-block": "plan", transform: `translate(${PX} ${PY}) scale(${k})` }, svg), v, { furniture: true, axes: true, levels: true, tag: "-a3", tags: false, axOff: 1650 });
  let y = PY + d + 29;
  sheetHeading(svg, 26, y, 215, tx.plan);
  mmTable(svg, TX, PY - 12, TW, tx.expl, tx.f1, mmRooms(v), L, polyArea(v.poly));

  // 2) loft: tie paši ārējie izmēri (garums, platums) kā 1. stāvam; sava telpu tabula blakus
  if (lf) {
    const LY = y + 27;
    cadPlan(el("g", { "data-block": "loft", transform: `translate(${PX} ${LY}) scale(${k})` }, svg), lf, { furniture: true, axes: true, levels: true, tag: "-loft", tags: false, axOff: 1650 });
    mmTable(svg, TX, LY - 8, TW, tx.expl, tx.f2, mmRooms(lf), L);
    y = LY + d + 27;
    sheetHeading(svg, 26, y, 215, tx.loft);
  }

  // 3) four facades, two rows; long side left, gable right
  const row1 = y + 50, row2 = row1 + 77, gx = Math.min(60 + w + 36, 229 - d);
  const fas = (side, x, yy) => elevation(el("g", { "data-block": "elev-" + side, transform: `translate(${x} ${yy}) scale(${k})` }, svg), v, side, { levels: x < 100, noScale: x >= 100, ground: x < 100 && 46 + w + 36 > gx ? 600 : 0, title: `${tx.fas} ${sideAxes(v, side)}` });
  fas("south", 46, row1); fas("west", gx, row1);
  fas("north", 46, row2); fas("east", gx, row2);

  // 4) materials and colour tones (client project: no notes block)
  const keep = ARC.materials;
  const PR = ARC.projekts || {}, plate = PR.pamati === "platne";
  ARC.materials = tx.mats.map(m => m[0] === "wood" && PR.tonis_lv ? ["wood", ...(L === "en" ? PR.tonis_en : PR.tonis_lv)]
    : m[0] === "#1d1d1d" && plate ? ["#9b9c98", ...(L === "en" ? ["Plinth: foundation slab,", "concrete"] : ["Cokols: pamatu plātne,", "betons"])]
    : m[0] === "#383E42" && PR.logi ? [PR.logi_hex || m[0], m[1], PR.logi]
    : m[0] === "#1d1d1d" && PR.cokols ? [PR.cokols_hex || m[0], m[1], PR.cokols] : m);
  if (PR.sturi) ARC.materials.push(["#F2F0EA", ...(L === "en" ? [`Corner boards ${PR.sturi} mm,`, "white"] : [`Stūru dēļi ${PR.sturi} mm,`, "balti"])]);
  const mg = materials(svg, 26, row2 + 31, true);
  ARC.materials = keep;
  mg.querySelector("text").textContent = tx.matT;
  el("line", { x1: 0, y1: 2.2, x2: 215, y2: 2.2, stroke: C.ink, "stroke-width": .3 }, mg);
  T_(mg, 156, 9, tx.tone, { fs: 2.1, fill: MM_GREY });

  mmTitleBlock(svg, v, lf, L);
  return svg;
}
