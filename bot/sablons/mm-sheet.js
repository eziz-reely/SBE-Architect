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
let MM_TBLN = 0;
function mmTable(svg, x, y, w, title, sub, rooms, L, foot, outs) {
  const ti = MM_TBLN++, TO = ((((window.AR && AR.projekts) || {}).tblOff) || {})[(window.MODEL_SHEET ? "" : "ar:") + ti] || [0, 0];   // eksplikācijas tabulu var pabīdīt (projekts.tblOff, lapas mm); atslēga = tabulas kārtas nr.
  const g = el("g", { "data-block": "schedule", "data-tbl": ti, transform: `translate(${x + TO[0]} ${y + TO[1]})` }, svg), RH = 5;
  el("rect", { width: w, height: 6.5, fill: MM_DARK }, g);
  T_(g, 2, 4.4, title, { fs: 2.4, fw: 700, ls: .45, fill: "#fff" });
  T_(g, w - 2, 4.4, sub, { fs: 2.1, a: "end", fill: "#d9d4ca" });
  let yy = 6.5;
  rooms.forEach((rm, i) => {
    if (i % 2) el("rect", { y: yy, width: w, height: RH, fill: MM_SOFT }, g);
    const nm = L === "en" ? (rm.en || rm.n) : rm.n;
    el("circle", { cx: 3.6, cy: yy + RH / 2, r: 1.75, fill: "none", stroke: MM_ACC, "stroke-width": .25 }, g);
    T_(g, 3.6, yy + RH / 2 + .75, String(i + 1), { fs: 1.9, a: "middle", fw: 600 });
    T_(g, 7, yy + RH / 2 + .8, nm, { fs: 2.2 });
    T_(g, w - 2, yy + RH / 2 + .8, mmNum(area(rm)) + " m²", { fs: 2.2, a: "end" });
    yy += RH;
  });
  el("line", { x1: 0, y1: yy, x2: w, y2: yy, stroke: MM_DARK, "stroke-width": .35 }, g);
  T_(g, 2, yy + 3.8, MM_TXT[L].total, { fs: 2.3, fw: 700 });
  T_(g, w - 2, yy + 3.8, mmNum(rooms.reduce((a, rm) => a + area(rm), 0)) + " m²", { fs: 2.3, a: "end", fw: 700 });
  yy += RH + .5;
  (outs || []).forEach((o, i) => {   // ārtelpas (lievenis, terases): netiek skaitītas kopējā platībā; terases pakāpiens (up) šeit nav
    const nm = o.name || (L === "en" ? "Terrace" : "Terase");
    el("circle", { cx: 3.6, cy: yy + RH / 2, r: 1.75, fill: "none", stroke: MM_GREY, "stroke-width": .25 }, g);
    T_(g, 3.6, yy + RH / 2 + .75, String(rooms.length + 1 + i), { fs: 1.9, a: "middle", fw: 600, fill: MM_GREY });
    T_(g, 7, yy + RH / 2 + .8, nm + (L === "en" ? " (outdoor)" : " (ārtelpa)"), { fs: 2.2, fill: MM_GREY });
    T_(g, w - 2, yy + RH / 2 + .8, mmNum(polyArea(o.poly)) + " m²", { fs: 2.2, a: "end", fill: MM_GREY });
    yy += RH;
  });
  if (foot) { T_(g, 2, yy + 3.3, MM_TXT[L].foot, { fs: 2, fill: MM_GREY }); T_(g, w - 2, yy + 3.3, mmNum(foot) + " m²", { fs: 2, a: "end", fill: MM_GREY }); yy += RH; }
  el("rect", { width: w, height: yy, fill: "none", stroke: MM_DARK, "stroke-width": .3 }, g);
  return yy;
}

// vertical title block, x 247..287
function mmTitleBlock(svg, v, lf, L) {
  const tx = MM_TXT[L], P = (window.AR && window.AR.projekts) || {}, X = 247, W = 40, cx = X + W / 2;
  const g = el("g", { "data-block": "title" }, svg);
  const lab = (y, t) => { T_(g, X + 3, y, t, { fs: 1.8, fw: 700, ls: .35, fill: MM_ACC }); el("line", { x1: X + 3, y1: y + 1.2, x2: X + W - 3, y2: y + 1.2, stroke: "#d6d0c4", "stroke-width": .2 }, g); };
  // brand: projekts.logo = savs attēls (data URL) vai "none" (bez logo, tumšais lauks paliek)
  const OWN = P.logo && P.logo !== "none" ? P.logo : null, NOLOGO = P.logo === "none";
  if (OWN || NOLOGO) {
    el("rect", { x: X, y: 10, width: W, height: 58, fill: MM_DARK }, g);
    if (OWN) el("image", { href: OWN, x: X + 4, y: 14, width: W - 8, height: 50, preserveAspectRatio: "xMidYMid meet" }, g);
  } else if (window.MM_LOGO) {   // īstais MM logo (modelu-bots/LOGO.png): tumši brūns fons, bēšs M
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
  const NONAME = P.modela_nosaukums === "";
  let SH = NONAME ? -20 : 0;   // nosaukums izdzēsts: nav ne "MODELIS", ne vārda
  if (!NONAME) lab(88, tx.model);
  if (!NONAME && P.modela_nosaukums) {   // modeļa vārds (piem. Freya) un zem tā MM + m²
    // nosaukums nedrīkst iziet ārpus rakstlaukuma (34 mm): garu vārdu burtu izmēru samazina, ļoti garu pārlauž divās rindās
    const nmT = String(P.modela_nosaukums), AVAIL = W - 6, cw = .56, one = Math.min(6.2, AVAIL / (nmT.length * cw));
    let lines = [nmT], nfs = one;
    if (one < 4.2 && nmT.includes(" ")) {
      const sp = [...nmT].map((c, i) => c === " " ? i : -1).filter(i => i >= 0).sort((p, q) => Math.abs(p - nmT.length / 2) - Math.abs(q - nmT.length / 2))[0];
      lines = [nmT.slice(0, sp), nmT.slice(sp + 1)]; nfs = Math.min(5.2, AVAIL / (Math.max(lines[0].length, lines[1].length) * cw));
    }
    lines.forEach((ln, i) => T_(g, X + 3, 97 + i * (nfs * 1.2), ln, { fs: nfs, fw: 700, fill: MM_DARK }));
    SH += (lines.length - 1) * (nfs * 1.2);   // otra rinda pabīda zemāk esošos laukus
    T_(g, X + 3, 102.5 + (lines.length - 1) * (nfs * 1.2), P.modelis || "", { fs: 2.6, fw: 600, fill: MM_ACC, ls: .4 });
  } else if (!NONAME) T_(g, X + 3, 98, P.modelis || v.short || "", { fs: 6.2, fw: 700, fill: MM_DARK });
  // key figures
  const I = P.ievade || {}, foot = polyArea(v.poly), net = [...mmRooms(v), ...mmRooms(lf)].reduce((a, rm) => a + area(rm), 0);
  lab(108 + SH, tx.key);
  const kv = [[tx.kFoot, mmNum(foot) + " m²"], [tx.kNet, mmNum(net) + " m²"], [tx.kSize, `${Math.round(v.W)} × ${Math.round(v.D)}`],
    [tx.kRidge, I.augstums ? mmNum(I.augstums / 1000) + " m" : "–"], [tx.kCeil, mmNum((v.ceiling || 2200) / 1000) + " m"], [tx.kPitch, (P.pitch || 25) + "°"],
    ...(P.raditaji || []).map(r => L === "en" && r.length > 2 ? [r[2], r[3] || r[1]] : r)].filter(r => !P.tikai_pamati || r[0] === tx.kFoot || r[0] === tx.kSize);   // tikai stabu plāns: laukums un gabarīti   // papildu rādītāji: [nosaukums, vērtība, EN nosaukums, EN vērtība]
  let ky = 114 + SH;
  kv.forEach(([k, val]) => {
    T_(g, X + 3, ky, k, { fs: 1.9, fill: MM_GREY });
    T_(g, X + 3, ky + 4, val, { fs: 3, fw: 600, fill: MM_DARK });
    ky += 8.2;
  });
  // address
  ky += 1;
  if ((P.adrese || []).length) {   // bez adreses (--bez-adreses): sadaļu nerāda
    lab(ky, tx.obj);
    const AD = [];   // adrese nedrīkst iziet ārpus rakstlaukuma: pārlauž pa vārdiem (≈ 29 rakstzīmes rindā)
    P.adrese.forEach(l => { let cur = ""; String(l).split(/\s+/).forEach(w => { if (cur && (cur + " " + w).length > 29) { AD.push(cur); cur = w; } else cur = cur ? cur + " " + w : w; }); if (cur) AD.push(cur); });
    AD.forEach((l, i) => T_(g, X + 3, ky + 5.5 + i * 3.6, l, { fs: 2.3, fill: MM_DARK }));
    ky += 7 + AD.length * 3.6 + 6;
  }
  lab(ky, tx.cont);
  // projekta piezīmes (pamati u.c.): model.json projekts.piezimes, EN: piezimes_en
  let ny = ky + 5.5;
  ((L === "en" ? P.piezimes_en : P.piezimes) || P.piezimes || []).filter(t => !(P.notes_off || []).includes(t)).forEach(t => {   // notes_off: lietotāja nodzēstās piezīmes (redaktora sadaļa "Piezīmes lapā")
    const ls = wrap(t, 25), gn = el("g", { "data-note": t }, g);
    T_(gn, X + 3, ny, "—", { fs: 2.1, fill: MM_ACC });
    ls.forEach((l, j) => T_(gn, X + 6.5, ny + j * 3.2, l, { fs: 2.1, fill: MM_DARK }));
    ny += ls.length * 3.2 + 1.2;
  });

  // vertical watermark in the free space between the notes and the info note (left out when it does not fit)
  { const wm = (P.modela_nosaukums || P.modelis || v.short || "") + "  ·  " + tx.phase, top = ny + 4, bot = 326, fs = Math.min(5.5, (bot - top) / (wm.length * 0.95));
    if (fs >= 3 && !NONAME) T_(g, 0, 0, wm, { fs, fw: 700, ls: fs * .22, fill: "#e9e5dc", tr: `translate(${cx + fs * .35} ${(top + bot) / 2}) rotate(-90)`, a: "middle" }); }
  // info note
  const info = wrap(tx.info, 27);
  info.forEach((l, i) => T_(g, X + 3, 344 - (info.length - 1 - i) * 2.8, l, { fs: 1.75, fill: MM_GREY }));
  // revisions
  lab(350, tx.rev);
  const ry = 355;
  T_(g, X + 3, ry, tx.rNr, { fs: 1.7, fill: MM_GREY }); T_(g, X + 10, ry, tx.rDate, { fs: 1.7, fill: MM_GREY }); if (P.rev_apraksts) T_(g, X + 23, ry, tx.rDesc, { fs: 1.7, fill: MM_GREY });
  T_(g, X + 3, ry + 4, P.revizija || "00", { fs: 2.2, fw: 700 });
  T_(g, X + 10, ry + 4, P.datums || "", { fs: 2.1 });
  wrap(L === "en" ? (P.rev_apraksts_en || P.rev_apraksts || "") : (P.rev_apraksts || ""), 10).forEach((l, i) => T_(g, X + 23, ry + 4 + i * 2.8, l, { fs: 1.9 }));
  // bottom cells: scale / size / sheet
  el("line", { x1: X, y1: 372, x2: X + W, y2: 372, stroke: C.ink, "stroke-width": .35 }, g);
  [[tx.scale, window.MM_SCALE_TXT || ("1:" + (window.MM_SCALE || 100))], [tx.fmt, "A3"], [tx.sheet, P.lapa || "1/1"]].forEach(([k, val], i) => {
    const x = X + i * W / 3;
    if (i) el("line", { x1: x, y1: 372, x2: x, y2: 386, stroke: C.ink, "stroke-width": .2 }, g);
    T_(g, x + W / 6, 377, k, { fs: 1.6, a: "middle", fill: MM_GREY, ls: .2 });
    T_(g, x + W / 6, 383, val, { fs: 2.8, fw: 700, a: "middle" });
  });
  el("rect", { x: X, y: 386, width: W, height: 24, fill: MM_DARK }, g);
  if (OWN) el("image", { href: OWN, x: X + W - 17, y: 388, width: 15, height: 15, preserveAspectRatio: "xMidYMid meet" }, g);
  else if (window.MM_LOGO && !NOLOGO) el("image", { href: window.MM_LOGO, x: X + W - 15, y: 389, width: 13, height: 13 * 433 / 486 }, g);
  T_(g, X + 3, 393, "REV. " + (P.revizija || "00"), { fs: 2.6, fw: 700, fill: MM_ACC, ls: .4 });
  T_(g, X + 3, 398.5, P.datums || "", { fs: 2.2, fill: "#fff" });
  T_(g, X + 3, 405, "MM Homes", { fs: 2.2, fw: 600, fill: MM_BEIGE, ls: .3 });
}


// ================= Automātiska lapas kompozīcija (projekts.kompozicija) =================
// kompozicija = { orient: "p" | "l", elementi: ["plan","loft","fas_south","fas_west","fas_north","fas_east","griez","expl","mat","viz"],
//                 merogs: "auto" | 50 | 100 | 150 ..., viz: { src: dataURL, w, h } }
// projekts.titul = rakstlaukuma slēdži: { brand, phase, model, key, adrese, piezimes, watermark, info, rev, cells, footer } (false = izslēgts)
const MM_MER = [50, 75, 100, 150, 200, 250, 300, 400, 500];
// [MM] automātiskais RAL kalkulators: brīvai krāsai (hex) atrod tuvāko RAL Classic toni (CIE Lab attālums); rezultāts ir tuvinājums, galīgo kodu pārbauda pēc RAL vēdekļa
const MM_RALT = "1000 BEBD7F,1001 C2B078,1002 C6A664,1003 E5BE01,1004 CDA434,1005 A98307,1006 E4A010,1007 DC9D00,1011 8A6642,1012 C7B446,1013 EAE6CA,1014 E1CC4F,1015 E6D690,1016 EDFF21,1017 F5D033,1018 F8F32B,1019 9E9764,1020 999950,1021 F3DA0B,1023 FAD201,1024 AEA04B,1026 FFFF00,1027 9D9101,1028 F4A900,1032 D6AE01,1033 F3A505,1034 EFA94A,1035 6A5D4D,1036 705335,1037 F39F18,2000 ED760E,2001 C93C20,2002 CB2821,2003 FF7514,2004 F44611,2008 F75E25,2009 F54021,2010 D84B20,2011 EC7C26,2012 E55137,3000 AF2B1E,3002 A2231D,3003 9B111E,3005 5E2129,3007 412227,3009 642424,3011 781F19,3012 C1876B,3013 A12312,3014 D36E70,3015 EA899A,3016 B32821,3017 E63244,3018 D53032,3020 CC0605,3022 D95030,3027 C51D34,3031 B32428,4001 6D3F5B,4002 922B3E,4003 DE4C8A,4004 641C34,4005 6C4675,4006 A03472,4007 4A192C,4008 924E7D,4009 A18594,4010 CF3476,5000 354D73,5001 1F3438,5002 20214F,5003 1D1E33,5004 18171C,5005 1E2460,5007 3E5F8A,5008 26252D,5009 025669,5010 0E294B,5011 231A24,5012 3B83BD,5013 1E213D,5014 606E8C,5015 2271B3,5017 063971,5018 3F888F,5019 1B5583,5020 1D334A,5021 256D7B,5022 252850,5023 49678D,5024 5D9B9B,6000 316650,6001 287233,6002 2D572C,6003 424632,6004 1F3A3D,6005 2F4538,6006 3E3B32,6007 343B29,6008 39352A,6009 31372B,6010 35682D,6011 587246,6012 343E40,6013 6C7156,6014 47402E,6015 3B3C36,6016 1E5945,6017 4C9141,6018 57A639,6019 BDECB6,6020 2E3A23,6021 89AC76,6022 25221B,6024 308446,6025 3D642D,6026 015D52,6027 84C3BE,6028 2C5545,6029 20603D,6032 317F43,6033 497E76,6034 7FB5B5,7000 78858B,7001 8A9597,7002 7E7B52,7003 6C7059,7004 969992,7005 646B63,7006 6D6552,7008 6A5F31,7009 4D5645,7010 4C514A,7011 434B4D,7012 4E5754,7013 464531,7015 434750,7016 293133,7021 23282B,7022 332F2C,7023 686C5E,7024 474A51,7026 2F353B,7030 8B8C7A,7031 474B4E,7032 B8B799,7033 7D8471,7034 8F8B66,7035 D7D7D7,7036 7F7679,7037 7D7F7D,7038 B5B8B1,7039 6C6960,7040 9DA1AA,7042 8D948D,7043 4E5452,7044 CAC4B0,7045 909090,7046 82898F,7047 D0D0D0,7048 898176,8000 826C34,8001 955F20,8002 6C3B2A,8003 734222,8004 8E402A,8007 59351F,8008 6F4F28,8011 5B3A29,8012 592321,8014 382C1E,8015 633A34,8016 4C2F27,8017 45322E,8019 403A3A,8022 212121,8023 A65E2E,8024 79553D,8025 755C48,8028 4E3B31,9001 FDF4E3,9002 E7EBDA,9003 F4F4F4,9004 282828,9005 0A0A0A,9006 A5A5A5,9007 8F8F8F,9010 FFFFFF,9011 1C1C1C,9016 F6F6F6,9017 1E1E1E,9018 D7D7D7,9022 9C9C9C,9023 828282".split(",").map(t => { const q = t.split(" "); return ["RAL " + q[0], q[1]]; });
const mmLab = h => { const c = [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16) / 255).map(v => (v > .04045 ? Math.pow((v + .055) / 1.055, 2.4) : v / 12.92)), x = (c[0] * .4124 + c[1] * .3576 + c[2] * .1805) / .95047, y = c[0] * .2126 + c[1] * .7152 + c[2] * .0722, z = (c[0] * .0193 + c[1] * .1192 + c[2] * .9505) / 1.08883, f = t => (t > .008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116); return [116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))]; };
function mmNearRal(hex) {
  if (!/^#[0-9a-f]{6}$/i.test(hex || "")) return null;
  const a = mmLab(hex); let best = null, bd = 1e9;
  MM_RALT.forEach(q => { const b = q[2] || (q[2] = mmLab("#" + q[1])), d = (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2; if (d < bd) { bd = d; best = q[0]; } });
  return best;
}
window.mmNearRal = mmNearRal;
const mmRalTxt = (hex, ral) => ral || (mmNearRal(hex) ? "≈ " + mmNearRal(hex) : hex.toUpperCase());   // RAL kods; brīvai krāsai tikai tuvākais RAL (hex lapā nerāda)
function mmMatTones(L, PR) {   // [MM] redaktora spaiņa toņi: katrai atsevišķi nokrāsotai daļai sava leģendas rinda ar RAL kodu
  const out = [];
  const SN = L === "en" ? { south: "south", north: "north", east: "east", west: "west" } : { south: "dienvidu", north: "ziemeļu", east: "austrumu", west: "rietumu" }, FS = PR.fasade_side || {};
  const en = L === "en", seen = new Set(), addF = q => { if (!q || !q.hex) return; const key = q.hex.toLowerCase() + "|" + (q.ral || ""); if (seen.has(key)) return; seen.add(key); out.push([q.hex, en ? (PR.apdare_orient === "h" ? "Facade: horizontal cladding," : "Facade: vertical cladding,") : (PR.apdare_orient === "h" ? "Fasāde: horizontāls apdares dēlis," : "Fasāde: vertikāls apdares dēlis,"), mmRalTxt(q.hex, q.ral)]); };   // atsevišķi nokrāsotās fasādes daļas: viena rinda katram tonim (bez sienu nosaukumiem un garumiem)
  ["south", "north", "east", "west"].forEach(sd => { addF(FS[sd]); (((PR.fasade_wall || {})[sd]) || []).forEach(addF); });
  if (PR.parkare_hex) out.push([PR.parkare_hex, en ? "Roof overhang" : "Jumta pārkare", mmRalTxt(PR.parkare_hex, PR.parkare_ral)]);
  ["south", "north", "east", "west"].forEach(sd => { const q = (PR.parkare_side || {})[sd]; if (q) out.push([q, en ? `Roof overhang, ${SN[sd]} side` : `Jumta pārkare, ${SN[sd]} puse`, ((PR.parkare_side_ral || {})[sd]) || mmRalTxt(q)]); });
  return out;
}
function mmMatList(L) {   // materiālu leģenda (tā pati kā klasiskajā lapā)
  const tx = MM_TXT[L], PR = (window.ARC && ARC.projekts) || (window.AR && AR.projekts) || {}, plate = PR.pamati === "platne";
  const out = tx.mats.map(m => m[0] === "wood" && PR.tonis_lv ? ["wood", ...(L === "en" ? PR.tonis_en : PR.tonis_lv)]
    : m[0] === "#1d1d1d" && plate ? [PR.cokols_plate_hex || "#9b9c98", ...(L === "en" ? ["Plinth: foundation slab,", PR.cokols_plate ? "tinted concrete, " + PR.cokols_plate : "concrete"] : ["Cokols: pamatu plātne,", PR.cokols_plate ? "tonēts betons, " + PR.cokols_plate : "betons"])]
    : m[0] === "#383E42" && PR.logi ? [PR.logi_hex || m[0], m[1], PR.logi]
    : m[0] === "#1d1d1d" && PR.cokols ? [PR.cokols_hex || m[0], m[1], PR.cokols] : m);
  out.push(...mmMatTones(L, PR));
  return out;
}
// plāna zīmējuma izvirzījumi ārpus mājas taisnstūra (terases, lievenis, kontūra): ap tiem pārvietojas asis un mēru ķēdes, tāpēc bloks par tik lielāks
function mmPlanExt(vv) {
  const W = vv.W, D = vv.D, e = { l: 0, r: 0, t: 0, b: 0 }, add = pl => (pl || []).forEach(q => { e.l = Math.max(e.l, -q[0]); e.r = Math.max(e.r, q[0] - W); e.t = Math.max(e.t, -q[1]); e.b = Math.max(e.b, q[1] - D); });
  add(vv.poly); (vv.terraces || []).forEach(t => { if (!t.up) add(t.poly); }); if (vv.porch) add(vv.porch.poly);
  return e;
}
// bloku izmēri (lapas mm) pie mēroga SC; fiksētie (tabulas, materiāli) no mēroga nav atkarīgi
function mmBlockSizes(v, lf, L, K, SC, aw) {
  const k = 1 / SC, RG = roofGeo(v), ids = (K.elementi || []).filter(id => id !== "viz"), out = [];
  const eave = RG.eEdge + RG.thV;
  ids.forEach(id => {
    if (id === "plan" || (id === "loft" && lf)) { const e = mmPlanExt(v); out.push({ id, w: (v.W + e.l + e.r + 5600) * k, h: (v.D + e.t + e.b + 5600) * k + 8, el: e.l, et: e.t }); }
    else if (/^fas_/.test(id)) { const sd = id.slice(4), gb = sd === "east" || sd === "west", sp = gb ? v.D : v.W; out.push({ id, w: (sp + 5400) * k, h: (RG.ridgeTop + 3300) * k + 3 }); }
    else if (id === "griez") { const hz = true, sp = hz ? v.W : v.D; out.push({ id, w: (sp + 5400) * k, h: (RG.ridgeTop + 2600) * k + 8 }); }
    else if (id === "expl") { const nr = mmRooms(v).length + (lf ? mmRooms(lf).length + 2 : 0); out.push({ id, w: 66, h: 6.5 + (nr + 2) * 5 + 12 }); }
    else if (id === "mat") { const n = mmMatList(L).length, cols = Math.max(1, Math.min(Math.ceil(n / 3), Math.floor((aw || 220) / 78))), R = Math.max(3, Math.ceil(n / cols)); out.push({ id, w: Math.max(80, cols * 78), h: 12 + Math.min(n, R) * 11 + 5, R }); }   // kolonnu skaits ierobežots ar lapas platumu, rindu skaits kolonnā aug (citādi lapa nesaietilpa un palika tukša)
  });
  return out;
}
// plauktu iepakošana: bloki pa rindām pēc dotās kārtības (next-fit); atgriež rindas un lietoto augstumu vai null
function mmShelf(ord, aw, ah, gap) {
  const shelves = []; let cur = null;
  for (const b of ord) {
    if (b.w > aw + .01 || b.h > ah + .01) return null;
    if (!cur || cur.w + gap + b.w > aw + .01) { cur = { items: [], w: 0, h: 0 }; shelves.push(cur); }
    cur.w += (cur.items.length ? gap : 0) + b.w; cur.h = Math.max(cur.h, b.h); cur.items.push(b);
  }
  const used = shelves.reduce((a, s) => a + s.h, 0) + gap * Math.max(0, shelves.length - 1);
  return used > ah + .01 ? null : { shelves, used };
}
function mmLayout(v, lf, L, K, area, gap) {
  const [ax, ay, aw, ah] = area, vizOn = (K.elementi || []).includes("viz") && K.viz && K.viz.src, ratio = vizOn ? (K.viz.w || 4) / (K.viz.h || 3) : 0;
  const cands = K.merogs && K.merogs !== "auto" ? [+K.merogs] : MM_MER;
  let seed = 12345; const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
  const MINW = 50, MINH = 32;
  for (const SC of cands) {
    const all = mmBlockSizes(v, lf, L, K, SC, aw), matB = all.find(b => b.id === "mat"), bl = all.filter(b => b.id !== "mat");
    const PRI = ["plan", "expl", "loft", "fas_south", "fas_west", "fas_north", "fas_east", "griez"], pr = b => { const q = PRI.indexOf(b.id); return q < 0 ? 99 : q; };
    const canon = [...bl].sort((a, b) => pr(a) - pr(b));   // pastāvīga kārtība: plāns, tabula, mansards, fasādes; materiāli vienmēr atsevišķā rindā zem visa (tāpēc neleciena pēc katras krāsu maiņas)
    const orders = [canon, [...bl].sort((a, b) => b.h - a.h), [...bl].sort((a, b) => b.w - a.w)];
    for (let i = 0; i < 500; i++) { const o = [...bl]; for (let j = o.length - 1; j > 0; j--) { const r = Math.floor(rnd() * (j + 1)); [o[j], o[r]] = [o[r], o[j]]; } orders.push(o); }
    const rsv = matB ? matB.h + gap : 0;   // vieta materiāliem zem fasādēm
    let best = null;
    for (const ord of orders) {
      if (best && ord !== canon && best.canon) break;   // kanoniskā kārtība ietilpst: lieto to (stabils izkārtojums)
      const pk = mmShelf(ord, aw, ah - rsv, gap); if (!pk) continue;
      const place = [], free = [], n = pk.shelves.length, gy = gap + (n > 1 ? Math.min(14, Math.max(0, (ah - rsv - pk.used) / (n - 1) * (vizOn ? 0 : 1))) : 0);
      let y = ay;
      pk.shelves.forEach(sh => {
        let x = ax; sh.items.forEach(b => { place.push({ id: b.id, x, y, w: b.w, h: b.h, R: b.R, el: b.el, et: b.et }); x += b.w + gap; });
        if (aw - sh.w - gap > 20) free.push({ x: ax + sh.w + gap, y, w: aw - sh.w - gap, h: sh.h });
        y += sh.h + gy;
      });
      let bot = y - gy;
      if (matB) { place.push({ id: "mat", x: ax, y: bot + gap, w: matB.w, h: matB.h, R: matB.R }); bot += gap + matB.h; }
      if (ay + ah - bot - gap > 20) free.push({ x: ax, y: bot + gap, w: aw, h: ay + ah - bot - gap });
      let viz = null;
      if (vizOn) free.forEach(f => { let w = f.w, h = w / ratio; if (h > f.h) { h = f.h; w = h * ratio; } if (w >= MINW && h >= MINH && (!viz || w * h > viz.w * viz.h)) viz = { x: f.x + (f.w - w) / 2, y: f.y + (f.h - h) / 2, w, h }; });
      if (vizOn && !viz) continue;
      const score = vizOn ? viz.w * viz.h : -pk.used;
      if (!best || score > best.score) best = { SC, place, viz, score, canon: ord === canon };
    }
    if (best) return best;
  }
  return null;
}
// rakstlaukuma pārplūstošā izkārtojuma versija: slēdži (projekts.titul), nekad ārpus lauka
function mmTitleFlow(svg, v, lf, L, R) {
  const tx = MM_TXT[L], P = (window.AR && window.AR.projekts) || {}, TT = P.titul || {}, on = k => TT[k] !== false;
  const [X, Y, W, H] = R, cx = X + W / 2, wide = W >= 55, NEU = TT.stils === "neitrals", DK = NEU ? "#2f3338" : MM_DARK, AC = NEU ? "#8b929b" : MM_ACC, BG = NEU ? "#d5d8dc" : MM_BEIGE, CO = /^individu/i.test((P.uznemums || "").toString().trim()) ? "" : (P.uznemums || "").toString();   // neitrāls stils: bez logo un MM zīmola
  const g = el("g", { "data-block": "title" }, svg), cid = "ttl-" + Math.random().toString(36).slice(2, 7);
  el("rect", { x: X, y: Y, width: W, height: H }, el("clipPath", { id: cid }, g));
  const gg = el("g", { "clip-path": `url(#${cid})` }, g);
  const lab = (y, t) => { T_(gg, X + 3, y, t, { fs: 1.8, fw: 700, ls: .35, fill: AC }); el("line", { x1: X + 3, y1: y + 1.2, x2: X + W - 3, y2: y + 1.2, stroke: "#d6d0c4", "stroke-width": .2 }, gg); };
  const OWN = P.logo && P.logo !== "none" ? P.logo : null, NOLOGO = P.logo === "none", NONAME = P.modela_nosaukums === "";
  const nChar = (fs, w) => Math.max(6, Math.floor(w / (fs * .5)));
  // apakšējā daļa (no apakšas uz augšu): kājene, šūnas, revīzijas, informācija
  let by = Y + H;
  if (on("footer")) { by -= 20; el("rect", { x: X, y: by, width: W, height: 20, fill: DK }, gg);
    if (OWN) el("image", { href: OWN, x: X + W - 15, y: by + 3, width: 12, height: 12, preserveAspectRatio: "xMidYMid meet" }, gg); else if (window.MM_LOGO && !NOLOGO && !NEU) el("image", { href: window.MM_LOGO, x: X + W - 13, y: by + 4, width: 10, height: 10 * 433 / 486 }, gg);
    T_(gg, X + 3, by + 7, "REV. " + (P.revizija || "00"), { fs: 2.4, fw: 700, fill: AC, ls: .4 }); T_(gg, X + 3, by + 12, P.datums || "", { fs: 2, fill: "#fff" }); T_(gg, X + 3, by + 17, NEU ? CO.slice(0, nChar(2, W - 6)) : "MM Homes", { fs: 2, fw: 600, fill: BG, ls: .3 }); }
  if (on("cells")) { by -= 13; el("line", { x1: X, y1: by, x2: X + W, y2: by, stroke: C.ink, "stroke-width": .35 }, gg);
    [[tx.scale, window.MM_SCALE_TXT || ("1:" + (window.MM_SCALE || 100))], [tx.fmt, "A3"], [tx.sheet, P.lapa || "1/1"]].forEach(([k, val], i) => { const x = X + i * W / 3;
      if (i) el("line", { x1: x, y1: by, x2: x, y2: by + 13, stroke: C.ink, "stroke-width": .2 }, gg);
      T_(gg, x + W / 6, by + 4.5, k, { fs: 1.6, a: "middle", fill: MM_GREY, ls: .2 }); T_(gg, x + W / 6, by + 10.5, val, { fs: 2.6, fw: 700, a: "middle" }); }); }
  if (on("rev")) { by -= 14; lab(by + 1, tx.rev); const ry = by + 5.5;
    T_(gg, X + 3, ry, tx.rNr, { fs: 1.7, fill: MM_GREY }); T_(gg, X + 10, ry, tx.rDate, { fs: 1.7, fill: MM_GREY }); if (P.rev_apraksts) T_(gg, X + 23, ry, tx.rDesc, { fs: 1.7, fill: MM_GREY });
    T_(gg, X + 3, ry + 3.6, P.revizija || "00", { fs: 2.1, fw: 700 }); T_(gg, X + 10, ry + 3.6, P.datums || "", { fs: 2 });
    wrap(L === "en" ? (P.rev_apraksts_en || P.rev_apraksts || "") : (P.rev_apraksts || ""), nChar(1.8, W - 26)).slice(0, 2).forEach((l, i) => T_(gg, X + 23, ry + 3.6 + i * 2.6, l, { fs: 1.8 })); }
  let infoLines = [];
  if (on("info")) { infoLines = wrap(tx.info, nChar(1.7, W - 6)); by -= infoLines.length * 2.7 + 3; infoLines.forEach((l, i) => T_(gg, X + 3, by + 3 + i * 2.7, l, { fs: 1.65, fill: MM_GREY })); }
  const bottom = by;   // virs šīs līnijas plūst augšējā daļa
  // augšējā daļa
  let y = Y;
  if (on("brand")) {
    const bh = Math.max(26, Math.min(58, (bottom - Y) * .2));
    el("rect", { x: X, y, width: W, height: bh, fill: DK }, gg);
    if (NEU) {   // bez logo: projekta nosaukums un uzņēmuma nosaukums tekstā
      const nm = P.modela_nosaukums || v.short || "", ls = wrap(nm, nChar(5.2, W - 8)).slice(0, 3);
      ls.forEach((l, i) => T_(gg, X + 4, y + bh / 2 - (ls.length - 1) * 3.2 + i * 6.4 + (CO ? -2 : 0), l, { fs: 5.2, fw: 700, fill: "#fff" }));
      if (CO) T_(gg, X + 4, y + bh - 5, CO.slice(0, nChar(2.4, W - 8)).toUpperCase(), { fs: 2.2, fw: 600, fill: BG, ls: .6 });
      el("line", { x1: X + 4, y1: y + bh - 9.5, x2: X + 14, y2: y + bh - 9.5, stroke: AC, "stroke-width": .5 }, gg);
    } else {
      if (OWN) el("image", { href: OWN, x: X + 4, y: y + 3, width: W - 8, height: bh - 6, preserveAspectRatio: "xMidYMid meet" }, gg);
      else if (window.MM_LOGO && !NOLOGO) { const iw = Math.min(W - 6, (bh - 14) * 486 / 433); el("image", { href: window.MM_LOGO, x: cx - iw / 2, y: y + 1, width: iw, height: iw * 433 / 486, preserveAspectRatio: "xMidYMid slice" }, gg);
        T_(gg, cx, y + bh - 9, "HOMES", { fs: 3.6, fw: 600, a: "middle", fill: BG, ls: 1.8 }); T_(gg, cx, y + bh - 3.5, tx.tag, { fs: 1.6, a: "middle", fill: "#b9ad93", ls: .5 }); }
    }
    y += bh + 4;
  }
  if (on("phase")) { el("rect", { x: X + 3, y, width: W - 6, height: 7, rx: 3.5, fill: "none", stroke: AC, "stroke-width": .45 }, gg); T_(gg, cx, y + 4.8, tx.phase, { fs: 2.2, fw: 700, a: "middle", ls: .45, fill: DK }); y += 12; }
  if (on("model") && !NONAME && !(NEU && on("brand"))) { lab(y + 2, tx.model); const nm = P.modela_nosaukums || (P.modelis ? "" : v.short || "");
    if (P.modela_nosaukums) { T_(gg, X + 3, y + 10, P.modela_nosaukums, { fs: Math.min(6.2, (W - 6) / (P.modela_nosaukums.length * .62)), fw: 700, fill: DK }); T_(gg, X + 3, y + 15.5, P.modelis || "", { fs: 2.5, fw: 600, fill: AC, ls: .4 }); y += 19; }
    else { T_(gg, X + 3, y + 10, nm || P.modelis || v.short || "", { fs: 5.5, fw: 700, fill: DK }); y += 14; } y += 3; }
  if (on("key")) {
    const I = P.ievade || {}, foot = polyArea(v.poly), net = [...mmRooms(v), ...(lf ? mmRooms(lf) : [])].reduce((a, rm) => a + area(rm), 0);
    const kv = [[tx.kFoot, mmNum(foot) + " m²"], [tx.kNet, mmNum(net) + " m²"], [tx.kSize, `${Math.round(v.W)} × ${Math.round(v.D)}`], [tx.kRidge, I.augstums ? mmNum(I.augstums / 1000) + " m" : "–"], [tx.kCeil, mmNum((v.ceiling || 2200) / 1000) + " m"], [tx.kPitch, (P.pitch || 25) + "°"],
      ...(P.raditaji || []).map(r => L === "en" && r.length > 2 ? [r[2], r[3] || r[1]] : r)];
    lab(y + 2, tx.key); y += 7; const cw = wide ? (W - 6) / 2 : W - 6, rows = wide ? Math.ceil(kv.length / 2) : kv.length, need = rows * 8.2;
    if (y + need < bottom - 6) { kv.forEach(([k, val], i) => { const c = wide ? i % 2 : 0, r = wide ? Math.floor(i / 2) : i, xx = X + 3 + c * cw;
      T_(gg, xx, y + 2 + r * 8.2, k.slice(0, nChar(1.9, cw)), { fs: 1.9, fill: MM_GREY }); T_(gg, xx, y + 6 + r * 8.2, String(val).slice(0, nChar(3, cw)), { fs: 3, fw: 600, fill: DK }); }); y += need + 2; }
  }
  if (on("adrese") && (P.adrese || []).length) { const lines = P.adrese.flatMap(l => wrap(l, nChar(2.3, W - 6))), need = 7 + lines.length * 3.6 + 3;
    if (y + need < bottom - 4) { lab(y + 2, tx.obj); lines.forEach((l, i) => T_(gg, X + 3, y + 7.5 + i * 3.6, l, { fs: 2.3, fill: DK })); y += need; } }
  if (on("piezimes")) { const notes = ((L === "en" ? P.piezimes_en : P.piezimes) || P.piezimes || []);
    if (notes.length && y + 12 < bottom) { lab(y + 2, tx.cont); let ny = y + 8;
      for (const t of notes) { const ls = wrap(t, nChar(2.1, W - 9)); if (ny + ls.length * 3.2 > bottom - 3) { T_(gg, X + 3, ny, "…", { fs: 2.1, fill: MM_GREY }); break; }
        T_(gg, X + 3, ny, "—", { fs: 2.1, fill: AC }); ls.forEach((l, j) => T_(gg, X + 6.5, ny + j * 3.2, l, { fs: 2.1, fill: DK })); ny += ls.length * 3.2 + 1.2; }
      y = ny; } }
  if (on("watermark") && !NONAME) { const wm = (P.modela_nosaukums || P.modelis || v.short || "") + "  ·  " + tx.phase, top = y + 4, bot = bottom - 4, fs = Math.min(5.5, (bot - top) / (wm.length * .95));
    if (fs >= 3) T_(gg, 0, 0, wm, { fs, fw: 700, ls: fs * .22, fill: "#e9e5dc", tr: `translate(${cx + fs * .35} ${(top + bot) / 2}) rotate(-90)`, a: "middle" }); }
  el("line", { x1: X, y1: Y, x2: X, y2: Y + H, stroke: C.ink, "stroke-width": .35, "data-block": "title-strip" }, g);
}
function mmCompose(v, lf, L, K) {
  const tx = MM_TXT[L], land = K.orient === "l", W = land ? 420 : 297, H = land ? 297 : 420, P = (window.AR && AR.projekts) || {};
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, class: "a3", role: "img", "aria-label": v.short || "Modelis" });
  el("rect", { width: W, height: H, fill: "#fff" }, svg);
  el("rect", { x: 20, y: 10, width: W - 30, height: H - 20, fill: "none", stroke: C.ink, "stroke-width": .5 }, svg);
  const TW = land ? 62 : 40, TX = W - 10 - TW;
  const area = [24, 14, TX - 24 - 3, H - 28], lay = mmLayout(v, lf, L, K, area, 6);
  if (!lay) { T_(svg, area[0] + 4, area[1] + 20, L === "en" ? "Selected elements do not fit on the sheet. Remove some or switch orientation." : "Izvēlētie elementi nesaietilpst lapā. Noņem kādu vai maini lapas virzienu.", { fs: 3.2, fill: "#b3261e" }); mmTitleFlow(svg, v, lf, L, [TX, 10, TW, H - 20]); return svg; }
  const SC = lay.SC, k = 1 / SC; window.MM_SCALE = SC;
  const heading = (b, t) => sheetHeading(svg, b.x + 2, b.y + b.h - 2.5, b.w - 4, t, `M 1:${SC}`);
  let firstFas = true;
  lay.place.forEach(b => {
    const M5 = 2800;   // asu un mēru josla ap plānu (mm)
    if (b.id === "plan" || b.id === "loft") {
      const vv = b.id === "plan" ? v : lf;
      cadPlan(el("g", { "data-block": b.id === "plan" ? "plan" : "loft", transform: `translate(${b.x + (M5 + (b.el || 0)) * k} ${b.y + (M5 + (b.et || 0)) * k}) scale(${k})` }, svg), vv, { furniture: true, axes: true, levels: true, tag: b.id === "plan" ? "-a3" : "-loft", tags: false, axOff: 1650 });
      heading(b, b.id === "plan" ? tx.plan : tx.loft);
    } else if (/^fas_/.test(b.id)) {
      const sd = b.id.slice(4), RG = roofGeo(v), gb = sd === "east" || sd === "west", top = (RG.ridgeTop + 600) * k;
      elevation(el("g", { "data-block": "elev-" + sd, transform: `translate(${b.x + 3200 * k} ${b.y + top}) scale(${k})` }, svg), v, sd, { levels: firstFas, noScale: !firstFas, ground: 0, title: `${tx.fas} ${sideAxes(v, sd)}` });
      firstFas = false;
    } else if (b.id === "griez") {
      const s = (v.sections && v.sections[0]) || { n: "1", o: "h", at: v.D / 2, look: -1 }, RG = roofGeo(v);
      const gs = el("g", { "data-block": "sec-1", transform: `translate(${b.x + 3200 * k} ${b.y + (RG.ridgeTop + 600) * k}) scale(${k})` }, svg);
      section(gs, v, Object.assign({ o: "h" }, s));
    } else if (b.id === "expl") {
      let yy = b.y + mmTable(svg, b.x, b.y, b.w, tx.expl, tx.f1, mmRooms(v), L, polyArea(v.poly)) + 4;
      if (lf) mmTable(svg, b.x, yy, b.w, tx.expl, tx.f2, mmRooms(lf), L);
    } else if (b.id === "mat") {
      const keep = ARC.materials; ARC.materials = mmMatList(L);
      const n = ARC.materials.length, mg = materials(svg, b.x, b.y + 4, b.R || true); ARC.materials = keep;
      mg.querySelector("text").textContent = tx.matT; el("line", { x1: 0, y1: 2.2, x2: b.w, y2: 2.2, stroke: C.ink, "stroke-width": .3 }, mg); void n;
    }
  });
  if (lay.viz && K.viz && K.viz.src) { const z = lay.viz;
    el("image", { href: K.viz.src, x: z.x, y: z.y, width: z.w, height: z.h, preserveAspectRatio: "xMidYMid meet", "data-block": "viz-sheet" }, svg);
    el("rect", { x: z.x, y: z.y, width: z.w, height: z.h, fill: "none", stroke: C.ink, "stroke-width": .25 }, svg); }
  mmTitleFlow(svg, v, lf, L, [TX, 10, TW, H - 20]);
  return svg;
}

// klasiskais izkārtojums pats izvēlas mērogu: ja visi bloki neietilpst lapā, ņem sīkāku mērogu (1:100 → 1:150 → 1:200 → 1:250 → 1:300), lai nekas neiziet ārpus rāmja
function mmSheetFits(svg) {
  try {
    svg.style.cssText = "position:absolute;left:-9999px;top:0;width:1000px;height:" + Math.round(1000 * svg.viewBox.baseVal.height / svg.viewBox.baseVal.width) + "px"; document.body.appendChild(svg);
    const sr = svg.getBoundingClientRect(), f = svg.viewBox.baseVal.width / sr.width; let ok = true;
    [...svg.children].filter(g => g.getAttribute && g.getAttribute("data-block") && !/^title/.test(g.getAttribute("data-block"))).forEach(g => { const r = g.getBoundingClientRect(); if (r.height && (r.bottom - sr.top) * f > 408.5) ok = false; });
    svg.remove(); svg.style.cssText = ""; return ok;
  } catch (e) { return true; }
}
function modelSheet(v) {
  const K = (window.AR && AR.projekts && AR.projekts.kompozicija);
  if (K && K.on !== false) { MM_TBLN = 0; return modelSheetAt(v, 0); }
  let svg;
  for (const sc of [0, 150, 200, 250, 300]) { MM_TBLN = 0; svg = modelSheetAt(v, sc); if (mmSheetFits(svg)) break; }
  return svg;
}
function modelSheetAt(v, scMin) {
  MM_TBLN = 0;
  const L = window.MM_LANG || "lv", tx = MM_TXT[L];
  const lf = V.find(x => x.id === "A" && x.rev === v.rev + 1);
  { const K = (window.AR && AR.projekts && AR.projekts.kompozicija); if (K && K.on !== false) return mmCompose(v, lf, L, K); }   // automātiskā kompozīcija; bez tās klasiskais izkārtojums
  const svg = el("svg", { viewBox: "0 0 297 420", class: "a3", role: "img", "aria-label": v.short || "Modelis" });
  el("rect", { width: 297, height: 420, fill: "#fff" }, svg);
  el("rect", { x: 20, y: 10, width: 267, height: 400, fill: "none", stroke: C.ink, "stroke-width": .5 }, svg);
  el("line", { x1: 247, y1: 10, x2: 247, y2: 410, stroke: C.ink, "stroke-width": .35, "data-block": "title-strip" }, svg);
  // platām/lielām mājām mērogs 1:150, citādi 1:100
  const SC = Math.max(scMin || 0, (v.D > 4500 || v.W > 12000) ? 150 : 100), k = 1 / SC, w = v.W * k, d = v.D * k;
  window.MM_SCALE = SC;
  const PX = 49, TX = Math.max(168, PX + w + 26), TW = 241 - TX;   // plan origin x, room tables column (moves right for long houses)

  // 1) ground floor: furniture, inner and outer dimensions, axes close to the outer chain; client mode = no element marks
  const PY = 41;
  cadPlan(el("g", { "data-block": "plan", transform: `translate(${PX} ${PY}) scale(${k})` }, svg), v, { furniture: true, axes: true, levels: true, tag: "-a3", tags: false, axOff: 1650 });
  const planBot = (g, y0) => { try { const hid = svg.isConnected; if (!hid) { svg.style.cssText = "position:absolute;visibility:hidden"; document.body.appendChild(svg); } const b = g.getBBox(); if (!hid) svg.remove(); return b && b.height ? y0 + (b.y + b.height) * k : 0; } catch (e) { return 0; } };   // plāna zīmējuma faktiskā apakšmala lapā (mm): virsraksts nedrīkst iet pāri asu burbuļiem un mēru ķēdēm
  let y = Math.max(PY + d + 29, planBot(svg.querySelector('g[data-block="plan"]'), PY) + 8);
  sheetHeading(svg, 26, y, 215, tx.plan);
  mmTable(svg, TX, PY - 12, TW, tx.expl, tx.f1, mmRooms(v), L, polyArea(v.poly), [].concat(v.porch ? [{ name: v.porch.name || (L === "en" ? "Porch" : "Lievenis"), poly: v.porch.poly }] : [], (v.terraces || []).filter(t => !t.up)));

  // 2) loft: tie paši ārējie izmēri kā 1. stāvam (mājas gabarīti, bez dublēšanas); sava telpu tabula blakus
  if (lf) {
    const LY = y + 27;
    cadPlan(el("g", { "data-block": "loft", transform: `translate(${PX} ${LY}) scale(${k})` }, svg), lf, { furniture: true, axes: true, levels: true, tag: "-loft", tags: false, axOff: 1650 });
    mmTable(svg, TX, LY - 8, TW, tx.expl, tx.f2, mmRooms(lf), L);
    y = Math.max(LY + d + 27, planBot(svg.querySelector('g[data-block="loft"]'), LY) + 8);
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
    : m[0] === "#1d1d1d" && plate ? [PR.cokols_plate_hex || "#9b9c98", ...(L === "en" ? ["Plinth: foundation slab,", PR.cokols_plate ? "tinted concrete, " + PR.cokols_plate : "concrete"] : ["Cokols: pamatu plātne,", PR.cokols_plate ? "tonēts betons, " + PR.cokols_plate : "betons"])]
    : m[0] === "#383E42" && PR.logi ? [PR.logi_hex || m[0], m[1], PR.logi]
    : m[0] === "#1d1d1d" && PR.cokols ? [PR.cokols_hex || m[0], m[1], PR.cokols] : m);
  { // logu aplodas un palodzes, ja to tonis atšķiras no rāmjiem ('tonis' = fasādes tonī)
    const lg = PR.logi || "RAL 7016", ca = PR.aplodas || lg, pa = PR.palodzes || ca, hx = c => (c === "tonis" ? (PR.tonis_sw || "#888") : colHex(c)), nm = c => (c === "tonis" ? (L === "en" ? "facade colour" : "fasādes tonī") : c);
    if (ca === pa) { if (ca !== lg) ARC.materials.push([hx(ca), ...(L === "en" ? ["Window casings, sills", nm(ca)] : ["Logu aplodas, palodzes", nm(ca)])]); }
    else {
      if (ca !== lg) ARC.materials.push([hx(ca), ...(L === "en" ? ["Window casings", nm(ca)] : ["Logu aplodas", nm(ca)])]);
      ARC.materials.push([hx(pa), ...(L === "en" ? ["Window sills", nm(pa)] : ["Palodzes", nm(pa)])]);
    }
  }
  if (PR.sturi) { const o = PR.sturi_opc || "balts", t = { balts: ["white", "balti"], melns: ["black", "melni"], tonis: ["facade colour", "fasādes tonī"] }[o] || ["white", "balti"];
    ARC.materials.push([PR.sturi_hex || "#F2F0EA", ...(L === "en" ? [`Corner boards ${PR.sturi} mm,`, t[0]] : [`Stūru dēļi ${PR.sturi} mm,`, t[1]])]); }
  ARC.materials.push(...mmMatTones(L, PR));   // fasādes sienu, pārkares un fascijas toņi (redaktora spainis)
  const matN = ARC.materials.length;
  const mg = materials(svg, 26, row2 + 31, matN > 6 ? Math.ceil(matN / 2) : true);   // vairāk nekā 6 rindas: divas kolonnas (trešā neietilptu rāmī)
  ARC.materials = keep;
  mg.querySelector("text").textContent = tx.matT;
  el("line", { x1: 0, y1: 2.2, x2: 215, y2: 2.2, stroke: C.ink, "stroke-width": .3 }, mg);
  if (matN > 6) T_(mg, 215, 0, tx.tone, { fs: 2.1, fill: MM_GREY, a: "end" }); else T_(mg, 156, 9, tx.tone, { fs: 2.1, fill: MM_GREY });   // trešā leģendas kolonna aizņem piezīmes vietu: piezīme virsraksta rindā

  mmTitleBlock(svg, v, lf, L);
  return svg;
}
