  // ---------- MM mēbeļu bibliotēka: 3 detalizācijas līmeņi (…1 vienkāršs, standarta SBE simbols, …3 detalizēts) un L dīvāns ----------
  // Izmanto tos pašus SBE zīmēšanas palīgus (R, Ci, Ln, Pth, soft), tāpēc līnijas un biezumi paliek tādi paši kā pārējām mēbelēm.
  const mmTurnNS = (fn, x, y, w, h, head) => {   // zīmē kā "w" un pagriež, ja galvgalis ir ziemeļos vai dienvidos
    const i0 = F.length; fn(0, 0, w, h, "w");
    const tr = head === "n" ? `translate(${x + h} ${y}) rotate(90)` : `translate(${x} ${y + w}) rotate(-90)`;
    for (let i = i0; i < F.length; i++) F[i].tr = tr + (F[i].tr ? " " + F[i].tr : "");
  };
  const bed1 = (x, y, w, h, head) => {
    if (head === "n" || head === "s") return mmTurnNS(bed1, x, y, w, h, head);
    const dir = head === "e" ? -1 : 1, h0 = head === "e" ? x + w : x, X = d => h0 + dir * d;
    R(x, y, w, h, { rx: 20 });
    Ln(X(80), y, X(80), y + h, { sw: 4 });
    const n = h > 1400 ? 2 : 1, ph = (h - 120 - (n - 1) * 50) / n;
    for (let k = 0; k < n; k++) R(Math.min(X(130), X(560)), y + 60 + k * (ph + 50), 430, ph, { rx: 40, sw: 3 });
    Ln(X(640), y, X(640), y + h, { sw: 3 });
  };
  const bed3 = (x, y, w, h, head) => {
    if (head === "n" || head === "s") return mmTurnNS(bed3, x, y, w, h, head);
    bed(x, y, w, h, head);
    const dir = head === "e" ? -1 : 1, h0 = head === "e" ? x + w : x, X = d => h0 + dir * d;
    // pārklājs kājgalī un dūnu segas stepējums
    const b0 = X(w - 520), b1 = X(w - 120);
    R(Math.min(b0, b1), y - 30, 400, h + 60, { rx: 25, sw: 4 });
    for (let k = 1; k < 4; k++) Ln(Math.min(b0, b1) + k * 100, y - 30, Math.min(b0, b1) + k * 100, y + h + 30, { sw: 2 });
    for (let d = 760; d < w - 560; d += 260) Ln(X(d), y + 60, X(d), y + h - 60, { sw: 1.6, dash: 1 });
  };
  const nightstand1 = (x, y) => { R(x, y, 450, 420, { rx: 10 }); };
  const nightstand3 = (x, y) => { nightstand(x, y); Ci(x + 225, y + 210, 110, { sw: 3 }); Ci(x + 225, y + 210, 40, s); Ln(x + 60, y + 330, x + 390, y + 330, { sw: 2 }); };
  const sofa1 = (x, y, w, h, back = "n") => {
    R(x, y, w, h, { rx: 40 });
    const bs = back === "s";
    Ln(x, bs ? y + h - 200 : y + 200, x + w, bs ? y + h - 200 : y + 200, { sw: 3 });
    Ln(x + 180, y, x + 180, y + h, { sw: 3 }); Ln(x + w - 180, y, x + w - 180, y + h, { sw: 3 });
  };
  const sofa3 = (x, y, w, h, back = "n") => {
    sofa(x, y, w, h, back);
    const bs = back === "s", py = bs ? y + h - 430 : y + 230;
    [x + 250, x + w - 470].forEach(px => Pth(`M ${px} ${py + 110} L ${px + 110} ${py} L ${px + 220} ${py + 110} L ${px + 110} ${py + 220} Z`, { sw: 4 }));
    soft(x + w * .42, bs ? y + 40 : y + h - 300, w * .22, 260, 50, 10, { sw: 3 });
  };
  // L dīvāns: pamatdaļa w × h (atzveltne ziemeļos), atpūtas daļa L garumā uz leju kreisajā ("l") vai labajā ("r") pusē
  const sofaL = (x, y, w, h, L = 900, side = "r", v = 2) => {
    const cx = side === "l" ? x : x + w - h, H = h + L;
    Pth(`M ${x + 60} ${y} H ${x + w - 60} Q ${x + w} ${y} ${x + w} ${y + 60} V ${side === "r" ? y + H - 60 : y + h - 60} ${side === "r" ? `Q ${x + w} ${y + H} ${x + w - 60} ${y + H} H ${cx + 60} Q ${cx} ${y + H} ${cx} ${y + H - 60} V ${y + h} H ${x + 60} Q ${x} ${y + h} ${x} ${y + h - 60}` : `Q ${x + w} ${y + h} ${x + w - 60} ${y + h} H ${x + h} V ${y + H - 60} Q ${x + h} ${y + H} ${x + h - 60} ${y + H} H ${x + 60} Q ${x} ${y + H} ${x} ${y + H - 60}`} V ${y + 60} Q ${x} ${y} ${x + 60} ${y} Z`, {});
    if (v === 1) { Ln(x, y + 200, x + w, y + 200, { sw: 3 }); Ln(side === "l" ? x + h : x + w - h, y + h, side === "l" ? x + h : x + w - h, y + 200, { sw: 3 }); return; }
    // atzveltne un roku balsti
    R(x + 20, y + 20, w - 40, 190, { rx: 60, sw: 4 });
    const armX = side === "l" ? x + w - 190 : x + 20;
    R(armX, y + 20, 170, h - 40, { rx: 70, sw: 4 });
    // sēdekļi pamatdaļā
    const s0 = side === "l" ? x + h : x + 210, s1 = side === "l" ? x + w - 210 : x + w - h, n = Math.max(1, Math.round((s1 - s0) / 700)), cw = (s1 - s0) / n;
    for (let k = 0; k < n; k++) soft(s0 + k * cw + 5, y + 230, cw - 10, h - 255, 60, 12, { sw: 4 });
    // atpūtas daļa
    soft(cx + 25, y + 230, h - 50, H - 255, 60, 12, { sw: 4 });
    if (v === 3) {
      [s0 + 60, cx + h * .3].forEach(px => Pth(`M ${px} ${y + 330} L ${px + 110} ${y + 220} L ${px + 220} ${y + 330} L ${px + 110} ${y + 440} Z`, { sw: 4 }));
      soft(cx + 60, y + H - 520, h - 120, 360, 50, 10, { sw: 3 });
    }
  };
  const sofaL1 = (x, y, w, h, L, side) => sofaL(x, y, w, h, L, side, 1);
  const sofaL3 = (x, y, w, h, L, side) => sofaL(x, y, w, h, L, side, 3);
  const wardrobe1 = (x, y, w, h, front) => {
    R(x, y, w, h);
    if (front === "e") Ln(x + w - 22, y, x + w - 22, y + h); if (front === "w") Ln(x + 22, y, x + 22, y + h);
    if (front === "n") Ln(x, y + 22, x + w, y + 22); if (front === "s") Ln(x, y + h - 22, x + w, y + h - 22);
    Ln(x, y, x + w, y + h, { sw: 2.5 }); Ln(x + w, y, x, y + h, { sw: 2.5 });
  };
  const wardrobe3 = (x, y, w, h, front) => {
    wardrobe(x, y, w, h, front);
    const horiz = front === "n" || front === "s", L = horiz ? w : h, n = Math.max(2, Math.round(L / 600));
    for (let k = 1; k < n; k++) { const t = L * k / n; horiz ? Ln(x + t, front === "s" ? y + h - 22 : y, x + t, front === "s" ? y + h : y + 22, { sw: 4 }) : Ln(front === "e" ? x + w - 22 : x, y + t, front === "e" ? x + w : x + 22, y + t, { sw: 4 }); }
    for (let k = 0; k < n; k++) { const t = L * (k + .5) / n; horiz ? Ci(x + t, front === "s" ? y + h + 25 : y - 25, 14, s) : Ci(front === "e" ? x + w + 25 : x - 25, y + t, 14, s); }
  };
  const armchair1 = (x, y, sz) => { R(x, y, sz, sz, { rx: 50 }); Ln(x + sz - 180, y, x + sz - 180, y + sz, { sw: 3 }); };
  const armchair3 = (x, y, sz) => { armchair(x, y, sz); Pth(`M ${x + sz * .28} ${y + sz * .5} L ${x + sz * .42} ${y + sz * .36} L ${x + sz * .56} ${y + sz * .5} L ${x + sz * .42} ${y + sz * .64} Z`, { sw: 3 }); };
  // galds ar krēsliem gar garajām malām
  const galds = (x, y, w, h, v = 2) => {
    R(x, y, w, h, { rx: 20 });
    if (v >= 2) R(x + 40, y + 40, w - 80, h - 80, { rx: 10, sw: 2.5 });
    if (v === 1) return;
    const horiz = w >= h, L = horiz ? w : h, n = Math.max(1, Math.floor(L / 600)), st = L / n;
    for (let k = 0; k < n; k++) {
      const t = st * (k + .5);
      if (horiz) { chair(x + t, y - 260, "n"); chair(x + t, y + h + 260, "s"); if (v === 3) { R(x + t - 170, y + 50, 340, 240, { rx: 20, sw: 2 }); R(x + t - 170, y + h - 290, 340, 240, { rx: 20, sw: 2 }); } }
      else { chair(x - 260, y + t, "w"); chair(x + w + 260, y + t, "e"); if (v === 3) { R(x + 50, y + t - 170, 240, 340, { rx: 20, sw: 2 }); R(x + w - 290, y + t - 170, 240, 340, { rx: 20, sw: 2 }); } }
    }
    if (v === 3) { Ci(x + w / 2, y + h / 2, 90, { sw: 3 }); Ci(x + w / 2, y + h / 2, 45, s); }
  };
  const galds1 = (x, y, w, h) => galds(x, y, w, h, 1);
  const galds3 = (x, y, w, h) => galds(x, y, w, h, 3);
  const desk1 = (x, y, w, h) => { R(x, y, w, h, { rx: 10 }); };
  const desk3 = (x, y, w, h, side) => { desk(x, y, w, h, side); R(x + w * .3, side === "w" ? y + 40 : y + 40, w * .4, 60, { rx: 10, sw: 3 }); Ci(side === "w" ? x + w - 120 : x + 120, y + 120, 70, { sw: 3 }); };
  // ---------- kāpnes: taisnas un L veida (v: 1 vienkāršas, 2 standarta ar kāpšanas bultu, 3 ar griezuma līniju un margu) ----------
  const GO = 250;   // pakāpiena dziļums plānā, mm
  const stArrow = (pts, v) => {   // kāpšanas virziens: aplītis sākumā, bulta augšējā galā
    if (v < 2) return;
    Ci(pts[0][0], pts[0][1], 45, { sw: 3 });
    Pth("M " + pts.map(p => p.join(" ")).join(" L "), { sw: 3, fill: "none" });
    const [a, b] = pts.slice(-2), L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1, ux = (b[0] - a[0]) / L, uy = (b[1] - a[1]) / L;
    Pth(`M ${b[0]} ${b[1]} L ${b[0] - ux * 170 - uy * 70} ${b[1] - uy * 170 + ux * 70} L ${b[0] - ux * 170 + uy * 70} ${b[1] - uy * 170 - ux * 70} Z`, { sw: 2, fill: "#5c5c5c" });
  };
  // taisnas: garums w (pa x), platums h; up "e" kāpj uz x + w, "w" uz x
  const kapnes = (x, y, w, h, up = "e", v = 2) => {
    R(x, y, w, h);
    const n = Math.max(2, Math.round(w / GO)), st = w / n, cut = v === 3 ? Math.floor(n * .55) : n;
    for (let k = 1; k < n; k++) {
      const xx = up === "w" ? x + w - k * st : x + k * st;
      Ln(xx, y, xx, y + h, { sw: 3, ...(k > cut ? { dash: 1 } : {}) });
    }
    if (v === 3) {   // griezuma līnija ar lūzumu, marga gar vienu malu
      const c = up === "w" ? x + w - (cut + .5) * st : x + (cut + .5) * st, d = up === "w" ? -1 : 1;
      Pth(`M ${c - d * 120} ${y + h + 60} L ${c} ${y + h * .58} L ${c + d * 60} ${y + h * .42} L ${c + d * 120} ${y - 60}`, { sw: 4, fill: "none" });
      Ln(x, y + 60, x + w, y + 60, { sw: 2 });
    }
    const a = up === "w" ? x + w - st / 2 : x + st / 2, b = up === "w" ? x + 80 : x + w - 80;
    stArrow([[a, y + h / 2], [b, y + h / 2]], v);
  };
  const kapnes1 = (x, y, w, h, up) => kapnes(x, y, w, h, up, 1);
  const kapnes3 = (x, y, w, h, up) => kapnes(x, y, w, h, up, 3);
  // L veida: kopējais izmērs w × h, marša platums b; pagrieziens labajā ("r") vai kreisajā ("l") apakšējā stūrī;
  // turn "lauk" = starplaukums, "vij" = vītņu pakāpieni pagriezienā; rev = kāpj pretējā virzienā
  const kapnesL = (x, y, w, h, b = 900, side = "r", turn = "lauk", rev = 0, v = 2) => {
    b = Math.min(b, w - 300, h - 300);
    const X = u => (side === "l" ? 2 * x + w - u : u), P = pts => "M " + pts.map(([u, z]) => `${X(u)} ${z}`).join(" L ");
    const x1 = x + w - b, y1 = y + h - b;   // pagrieziena laukuma iekšējais stūris
    Pth(P([[x, y1], [x1, y1], [x1, y], [x + w, y], [x + w, y + h], [x, y + h]]) + " Z", {});
    // 1. maršs gar apakšu (pa x), 2. maršs augšup (pa y)
    const n1 = Math.max(2, Math.round((x1 - x) / GO)), s1 = (x1 - x) / n1, n2 = Math.max(2, Math.round((y1 - y) / GO)), s2 = (y1 - y) / n2;
    for (let k = 1; k <= n1; k++) Pth(P([[x + k * s1, y1], [x + k * s1, y + h]]), { sw: 3, fill: "none" });
    for (let k = 0; k < n2; k++) Pth(P([[x1, y + k * s2], [x + w, y + k * s2]]), { sw: 3, fill: "none" });
    if (turn === "vij") [[x1 + b * .5, y + h], [x + w, y + h], [x + w, y1 + b * .5]].forEach(p => Pth(P([[x1, y1], p]), { sw: 3, fill: "none" }));
    if (v === 3) {
      Pth(P([[x + 60, y1 + 60], [x1 + 60, y1 + 60], [x1 + 60, y + 0]]), { sw: 2, fill: "none" });   // marga iekšējā malā
      const c = x + (x1 - x) * .55;
      Pth(P([[c - 120, y + h + 60], [c, y1 + b * .58], [c + 60, y1 + b * .42], [c + 120, y1 - 60]]), { sw: 4, fill: "none" });
    }
    const pts = [[x + s1 / 2, y1 + b / 2], [x1 + b / 2, y1 + b / 2], [x1 + b / 2, y + 80]].map(([u, z]) => [X(u), z]);
    stArrow(rev ? [[pts[2][0], pts[2][1] + s2 / 2 - 80], pts[1], [X(x + 80), pts[0][1]]] : pts, v);
  };
  const kapnesL1 = (x, y, w, h, b, side, turn, rev) => kapnesL(x, y, w, h, b, side, turn, rev, 1);
  const kapnesL3 = (x, y, w, h, b, side, turn, rev) => kapnesL(x, y, w, h, b, side, turn, rev, 3);
  // ---------- televizors: sienas stiprinājums, izmērs pēc diagonāles collās (16:9); aizmugure pret sienu ("n") ----------
  const tvW = d => Math.round(d * 25.4 * 0.8716);
  const tv = (x, y, d = 55) => {
    const w = tvW(d);
    R(x, y, w, 45, { rx: 8 });
    R(x + 18, y + 9, w - 36, 27, { rx: 4, sw: 2.5 });
    R(x + w / 2 - 110, y + 45, 220, 25, { rx: 6, sw: 3 });
  };
  // ---------- virtuves virsma ar tehniku: moduļi pa kreisi uz labi (ledusskapis, izlietne, trauku mašīna, plīts virsma 2/4 riņķi), pārējais ir skapīši; aizmugure pret sienu ("n") ----------
  const KMOD = { fridge: 600, sink: 800, dish: 600, hob2: 450, hob4: 600 };
  const kitchen = (x, y, w, h, mods = ["sink", "dish", "hob4", "fridge"]) => {
    const has = k => mods.find(m => m === k || (k === "hob" && /^hob/.test(m))), hb = mods.find(m => /^hob/.test(m));
    // ja sarakstā ir "cab", tas ir paša lietotāja secība (pa kreisi uz labi); citādi vecā noklusētā secība
    const order = mods.includes("cab") ? mods.filter(k => k === "cab" || KMOD[k]) : ["fridge", "cab", "sink", "dish", "cab", "hob", "cab"].map(k => k === "hob" ? hb : k).filter(k => k === "cab" || (k && has(k)));
    const tot = order.reduce((a, k) => a + (k === "cab" ? 0 : KMOD[k]), 0), k = tot > w ? w / tot : 1, left = Math.max(0, w - tot * k);
    const ncab = order.filter(q => q === "cab").length;
    let cx = x;
    order.forEach(m => {
      const mw = m === "cab" ? left / ncab : KMOD[m] * k;
      if (mw < 1) return;
      if (m === "cab") { R(cx, y, mw, h, { sw: 3 }); Ln(cx, y + h - 30, cx + mw, y + h - 30, { dash: 1, sw: 2 }); }
      else if (m === "fridge") { R(cx, y, mw, h, { sw: 3 }); Ln(cx, y, cx + mw, y + h, { sw: 2 }); Ln(cx + mw, y, cx, y + h, { sw: 2 }); }
      else if (m === "dish") { R(cx, y, mw, h, { sw: 3 }); R(cx + 40, y + 40, mw - 80, h - 80, { rx: 10, sw: 2.5 }); Ln(cx + 80, y + h - 90, cx + mw - 80, y + h - 90, { sw: 3 }); Ci(cx + mw / 2, y + h / 2 - 20, 90, { sw: 2 }); }
      else if (m === "sink") {
        R(cx, y, mw, h, { sw: 3 });
        R(cx + 50, y + 70, mw * .5, h - 140, { rx: 50, sw: 3.5 }); Ci(cx + 50 + mw * .25, y + h / 2, 24, { sw: 2.5 });
        for (let q = 0; q < 4; q++) Ln(cx + mw * .62 + q * 45, y + 100, cx + mw * .62 + q * 45, y + h - 100, { sw: 2.5 });
        Ci(cx + 50 + mw * .25, y + 40, 20, { sw: 2.5 });
      } else {
        R(cx, y, mw, h, { sw: 3 });
        const two = m === "hob2", hw = two ? 300 : 560, hd = two ? 520 : 520, hx = cx + (mw - hw) / 2, hy = y + (h - hd) / 2;
        R(hx, hy, hw, hd, { rx: 20, sw: 4 });
        const pts = two ? [[hx + hw / 2, hy + hd * .27, 80], [hx + hw / 2, hy + hd * .73, 100]] : [[hx + hw * .27, hy + hd * .27, 100], [hx + hw * .73, hy + hd * .27, 80], [hx + hw * .27, hy + hd * .73, 80], [hx + hw * .73, hy + hd * .73, 100]];
        pts.forEach(([a, b, r]) => { Ci(a, b, r, s); Ci(a, b, r * .5, { sw: 2.5 }); });
      }
      cx += mw;
    });
    Ln(x, y + h - 30, x + w, y + h - 30, { dash: 1, sw: 1.6 });
  };

  // ---------- Papildu mēbeles un tehnika: viens simbols mmF(x, y, w, h, veids) ----------
  // Veidu saraksts un noklusētie izmēri ņemti no egmalt/house-planner mēbeļu kataloga (MIT licence, skat. docs/TRESO_PUSU_LICENCES.md);
  // plāna simboli zīmēti šeit ar SBE palīgiem. Priekšpuse ir apakšējā (dienvidu) mala; pagriež redaktors.
  const mmF = (x, y, w, h, k) => {
    const cx = x + w / 2, cy = y + h / 2, m = Math.min(w, h);
    if (k === "augs") { Ci(cx, cy, m / 2); Ci(cx, cy, m * .18, { sw: 3 }); for (let a = 0; a < 6; a++) { const t = a * Math.PI / 3; Ln(cx + Math.cos(t) * m * .2, cy + Math.sin(t) * m * .2, cx + Math.cos(t) * m * .46, cy + Math.sin(t) * m * .46, { sw: 2.5 }); } return; }
    if (k === "boilers") { Ci(cx, cy, m / 2); Ci(cx, cy, m * .34, { sw: 2.5 }); Ln(cx - m * .12, cy, cx + m * .12, cy, { sw: 3 }); Ln(cx, cy - m * .12, cx, cy + m * .12, { sw: 3 }); return; }
    if (k === "bkresls") { Ci(cx, cy, m * .42); Pth(`M ${cx - m * .36} ${cy - m * .3} Q ${cx} ${cy - m * .62} ${cx + m * .36} ${cy - m * .3}`, { sw: 6 }); for (let a = 0; a < 5; a++) { const t = a * 2 * Math.PI / 5 + .3; Ln(cx, cy, cx + Math.cos(t) * m * .5, cy + Math.sin(t) * m * .5, { sw: 2 }); } return; }
    R(x, y, w, h, { rx: k === "vanna" ? 60 : 12 });
    if (k === "kumode") { const n = Math.max(2, Math.round(w / 500)); for (let i = 1; i < n; i++) Ln(x + w * i / n, y, x + w * i / n, y + h, { sw: 2.5 }); Ln(x, y + h - 30, x + w, y + h - 30, { sw: 2, dash: 1 }); for (let i = 0; i < n; i++) Ci(x + w * (i + .5) / n, y + h + 22, 12, { sw: 2.5 }); }
    else if (k === "plaukts") { const n = Math.max(2, Math.round(w / 400)); for (let i = 1; i < n; i++) Ln(x + w * i / n, y, x + w * i / n, y + h, { sw: 2.5 }); Ln(x, y + 30, x + w, y + 30, { sw: 2.5 }); }
    else if (k === "zgalds") { R(x + 50, y + 50, w - 100, h - 100, { rx: 8, sw: 2.5 }); }
    else if (k === "tvgalds") { Ln(x, y + h - 40, x + w, y + h - 40, { sw: 2.5 }); const n = Math.max(2, Math.round(w / 550)); for (let i = 1; i < n; i++) Ln(x + w * i / n, y + h - 40, x + w * i / n, y + h, { sw: 2.5 }); }
    else if (k === "ledus") { Ln(x, y, x + w, y + h, { sw: 2 }); Ln(x + w, y, x, y + h, { sw: 2 }); Ln(x + 40, y + h + 22, x + w * .45, y + h + 22, { sw: 5 }); }
    else if (k === "tmasina") { R(x + 40, y + 40, w - 80, h - 80, { rx: 10, sw: 2.5 }); Ci(cx, cy - 20, Math.min(90, m * .16), { sw: 2 }); Ln(x + 80, y + h - 90, x + w - 80, y + h - 90, { sw: 3 }); }
    else if (k === "plits") { const r = m * .15; [[.28, .28, 1.1], [.72, .28, .85], [.28, .72, .85], [.72, .72, 1.1]].forEach(([a, b, q]) => { Ci(x + w * a, y + h * b, r * q, { sw: 3 }); Ci(x + w * a, y + h * b, r * q * .5, { sw: 2 }); }); }
    else if (k === "vanna") { R(x + 70, y + 70, w - 140, h - 140, { rx: Math.min(260, (h - 140) / 2), sw: 3 }); Ci(x + 230, cy, 28, { sw: 2.5 }); Ci(x + 110, cy, 22, { sw: 2.5 }); }
    else if (k === "vskapis") { R(cx - Math.min(w * .35, 260), y + 60, Math.min(w * .7, 520), h - 150, { rx: 70, sw: 3 }); Ci(cx, y + 45, 18, { sw: 2.5 }); Ci(cx, cy, 16, { sw: 2.5 }); }
    else if (k === "pakaramais") { Ln(x + 40, cy, x + w - 40, cy, { sw: 5 }); const n = Math.max(3, Math.round(w / 160)); for (let i = 0; i < n; i++) { const px = x + 80 + (w - 160) * i / (n - 1); Ln(px - 30, y + 40, px + 30, y + h - 40, { sw: 2.5 }); } }
    else if (k === "apavi") { Ln(x, cy, x + w, cy, { sw: 2.5 }); const n = Math.max(2, Math.round(w / 400)); for (let i = 1; i < n; i++) Ln(x + w * i / n, y, x + w * i / n, y + h, { sw: 2.5 }); }
    else if (k === "kamins") { R(x + w * .18, y + h * .3, w * .64, h * .7, { sw: 3 }); Pth(`M ${cx - w * .12} ${y + h * .9} Q ${cx - w * .16} ${y + h * .62} ${cx} ${y + h * .45} Q ${cx + w * .16} ${y + h * .62} ${cx + w * .12} ${y + h * .9}`, { sw: 2.5 }); Ci(cx, y + h * .14, Math.min(90, m * .12), { sw: 2.5 }); }
    else if (k === "krasns") { R(x + 60, y + 60, w - 120, h - 120, { sw: 3 }); Ci(x + w * .3, y + h * .32, Math.min(110, m * .14), { sw: 2.5 }); R(x + w * .25, y + h - 60, w * .5, 60, { sw: 4 }); Ln(x, y, x + 60, y + 60, { sw: 2 }); Ln(x + w, y, x + w - 60, y + 60, { sw: 2 }); }
    else if (k === "gkatls") { R(x + 40, y + 40, w - 80, h - 80, { rx: 8, sw: 2.5 }); Ci(cx - w * .2, y + h + 26, 14, { sw: 2.5 }); Ci(cx + w * .2, y + h + 26, 14, { sw: 2.5 }); Ln(cx - 50, cy, cx + 50, cy, { sw: 3 }); }
  };
