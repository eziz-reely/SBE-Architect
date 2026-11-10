// ---------- MM rasējuma redaktors: darbojas rasējuma lapā (iframe) ----------
// Lapu zīmē tas pats SBE/MM kods. Šis skripts tikai atrod logus, durvis, mēbeles un sienas, ļauj tās pārvilkt
// un nosūta izmainīto model.json vecākajai lapai, kura lapu pārbūvē.
(function () {
  const ED = window.MM_ED, M = ED.model, NS = "http://www.w3.org/2000/svg", ACC = "#d9480f";
  const post = m => parent.postMessage(Object.assign({ mmEd: 1 }, m), "*");
  const clone = o => JSON.parse(JSON.stringify(o));
  const r10 = v => Math.round(v / 10) * 10;
  const T = Math.min(...M.rooms.flatMap(r => r.r.map(q => q[0])));   // ārsienas biezums
  const SNAP = 60, MINR = 600, GWB = ED.gwBase || 0;                                       // mēbele pielīp sienai tuvāk par 150 mm; telpa ne šaurāka par 600 mm
  let sel = ED.sel || null, drag = null, clip = ED.clip || null;
  { const st = document.createElement("style"); st.textContent = "body{-webkit-user-select:none;user-select:none;touch-action:none}"; document.head.appendChild(st); }

  const sheet = () => document.querySelector("svg.a3");
  const lv = (l, X = M) => (l === "loft" ? X.loft : X);
  // automātiskās mērķēdes [ass, novietojums]; mansards tās manto no 1. stāva, līdz to labo
  const idims = (l, X = M) => lv(l, X).innerDims || (l === "loft" ? X.innerDims : null);
  const idimsOwn = (l, N) => { const L = lv(l, N); if (!L.innerDims) L.innerDims = JSON.parse(JSON.stringify(N.innerDims || [])); return L.innerDims; };
  // mēra līnija pielīp citu tās pašas ass mēru līnijai (viena ķēde vienā taisnē)
  function snapAt(l, axis, v, self, rad = 220) {
    const c = []; (idims(l) || []).forEach((d, i) => { if (d[0] === axis && !(self && self.k === "idim" && self.i === i)) c.push(d[1]); });
    (lv(l).userDims || []).forEach((d, i) => { if (d[0] === axis && !(self && self.k === "dim" && self.i === i)) c.push(d[1]); });
    let best = null; c.forEach(t => { if (Math.abs(t - v) < rad && (best == null || Math.abs(t - v) < Math.abs(best - v))) best = t; });
    return best != null ? { v: best, hit: true } : { v: r10(v), hit: false };
  }
  const tr = g => { const m = /translate\(([-\d.e]+)[ ,]+([-\d.e]+)\)\s*scale\(([-\d.e]+)\)/.exec(g.getAttribute("transform") || ""); return m ? { tx: +m[1], ty: +m[2], k: +m[3] } : null; };
  function toLocal(g, cx, cy) {
    const r = sheet().getBoundingClientRect(), b = tr(g);
    return [((cx - r.left) / r.width * 297 - b.tx) / b.k, ((cy - r.top) / r.height * 420 - b.ty) / b.k];
  }
  // rokturu izmērs ekrānā nemainās, lai cik tuvināts: 1 vienība ≈ 4 px
  const ek = bl => tr(bl.g).k * (sheet().getBoundingClientRect().width / 297) / 4;
  const blocks = () => {
    const sv = sheet(), out = [];
    const p = sv.querySelector("g[data-block=plan][transform]"); if (p) out.push({ g: p, type: "plan", lv: "main" });
    const l = sv.querySelector("g[data-block=loft]"); if (l && M.loft) out.push({ g: l, type: "plan", lv: "loft" });
    sv.querySelectorAll("g[data-block^=elev-]").forEach(g => out.push({ g, type: "elev", side: g.getAttribute("data-block").slice(5) }));
    return out;
  };
  const span = side => (side === "east" || side === "west" ? M.D : M.W);
  const mapU = (side, a) => (side === "north" ? M.W - a : side === "east" ? M.D - a : a);
  const sgn = side => (side === "north" || side === "east" ? -1 : 1);
  const rects = (l, X = M) => (lv(l, X).rooms || []).flatMap(rm => rm.r.map(q => [q[0], q[1], q[0] + q[2], q[1] + q[3]]));

  // furniture: rendered bbox per model entry (one model entry can draw several shapes)
  function furnBoxes(bl) {
    const fm = (window.__FM || {})[bl.lv === "loft" ? 101 : 100] || [];
    const inv = bl.g.getCTM().inverse(), boxes = {};
    bl.g.querySelectorAll("[data-furn]").forEach(e => {
      const fi = +e.getAttribute("data-furn"), mi = fm.findIndex(r => fi >= r[0] && fi < r[1]);
      if (mi < 0) return;
      let bb; try { bb = e.getBBox(); } catch (_) { return; }
      const m = inv.multiply(e.getCTM());
      [[bb.x, bb.y], [bb.x + bb.width, bb.y], [bb.x, bb.y + bb.height], [bb.x + bb.width, bb.y + bb.height]].forEach(([x, y]) => {
        const p = new DOMPoint(x, y).matrixTransform(m), b = boxes[mi];
        boxes[mi] = b ? [Math.min(b[0], p.x), Math.min(b[1], p.y), Math.max(b[2], p.x), Math.max(b[3], p.y)] : [p.x, p.y, p.x, p.y];
      });
    });
    return boxes;
  }
  // room names: rendered bbox per room index, so a name can be moved off the furniture
  function stampBoxes(bl) {
    const inv = bl.g.getCTM().inverse(), boxes = {};
    bl.g.querySelectorAll("[data-stamp]").forEach(e => {
      const i = +e.getAttribute("data-stamp"); let bb; try { bb = e.getBBox(); } catch (_) { return; }
      const m = inv.multiply(e.getCTM());
      [[bb.x, bb.y], [bb.x + bb.width, bb.y + bb.height]].forEach(([x, y]) => { const p = new DOMPoint(x, y).matrixTransform(m), b = boxes[i]; boxes[i] = b ? [Math.min(b[0], p.x), Math.min(b[1], p.y), Math.max(b[2], p.x), Math.max(b[3], p.y)] : [p.x, p.y, p.x, p.y]; });
    });
    return boxes;
  }
  const contained = (boxes, i) => { const b = boxes[i]; return b ? Object.keys(boxes).map(Number).filter(j => j !== i && boxes[j][0] >= b[0] - 5 && boxes[j][1] >= b[1] - 5 && boxes[j][2] <= b[2] + 5 && boxes[j][3] <= b[3] + 5) : []; };
  // the walls drawn between rooms: a wall is the gap between two room rectangles (or an outer wall)
  // telpu sienas vidus punkti gar loga / durvju sienu (garuma virzienā), uz kuriem logs pielīp
  function wallCenters(l, o, th) {
    const H = o.o === "h", out = [];
    rects(l).forEach(r => {
      if (H) { if (Math.abs(r[1] - (o.y + th)) < 3 || Math.abs(r[3] - o.y) < 3) out.push((r[0] + r[2]) / 2); }
      else if (Math.abs(r[0] - (o.x + th)) < 3 || Math.abs(r[2] - o.x) < 3) out.push((r[1] + r[3]) / 2);
    });
    return out;
  }
  function wallAt(l, p) {
    const W = M.W, D = M.D, [x, y] = p;
    if (x < -50 || y < -50 || x > W + 50 || y > D + 50) return null;
    const ext = [["x", -1, T, x < T + 20 && y > T && y < D - T], ["x", W - T, W + 1, x > W - T - 20 && y > T && y < D - T],
      ["y", -1, T, y < T + 20 && x > T && x < W - T], ["y", D - T, D + 1, y > D - T - 20 && x > T && x < W - T]].find(e => e[3]);
    if (ext) return { axis: ext[0], lo: Math.max(0, ext[1]), hi: Math.min(ext[0] === "x" ? W : D, ext[2]), ext: true };
    if (l === "loft") return null;
    const R = rects("main");
    for (const a of R) for (const b of R) {
      if (b[0] - a[2] > 0 && b[0] - a[2] <= 300 && x >= a[2] - 20 && x <= b[0] + 20 && y >= Math.max(a[1], b[1]) && y <= Math.min(a[3], b[3])) return { axis: "x", lo: a[2], hi: b[0], v0: Math.max(a[1], b[1]), v1: Math.min(a[3], b[3]) };
      if (b[1] - a[3] > 0 && b[1] - a[3] <= 300 && y >= a[3] - 20 && y <= b[1] + 20 && x >= Math.max(a[0], b[0]) && x <= Math.min(a[2], b[2])) return { axis: "y", lo: a[3], hi: b[1], v0: Math.max(a[0], b[0]), v1: Math.min(a[2], b[2]) };
    }
    return null;
  }

  // every selectable thing in one block, in that block's local coordinates
  function axO(X) {   // asu galu attālums katrā pusē (kā build_model: ārpus mērķēdēm un ārtelpām), X.axOff to pārraksta
    const pts = [].concat(X.porch ? [X.porch.poly] : [], (X.terraces || []).map(t => t.poly)).flat();
    const ex = { n: Math.max(0, ...pts.map(q => -q[1])), s: Math.max(0, ...pts.map(q => q[1] - X.D)), w: Math.max(0, ...pts.map(q => -q[0])), e: Math.max(0, ...pts.map(q => q[0] - X.W)) }, r = {};
    ["n", "s", "w", "e"].forEach(k => { r[k] = X.axOff && X.axOff[k] != null ? X.axOff[k] : 3150 + (ex[k] > 0 ? ex[k] + 400 : 0); });
    return r;
  }
  function items(bl, X = M) {
    const out = [];
    if (bl.type === "plan") {
      const L = lv(bl.lv, X);
      (L.windows || []).forEach((w, i) => out.push({ k: "win", i, lv: bl.lv, b: w.o === "h" ? [w.x, w.y, w.x + w.len, w.y + T] : [w.x, w.y, w.x + T, w.y + w.len], pad: 120 }));
      (L.doors || []).forEach((d, i) => out.push({ k: "door", i, lv: bl.lv, b: d.o === "h" ? [d.x, d.y, d.x + d.w, d.y + d.th] : [d.x, d.y, d.x + d.th, d.y + d.w], pad: 120 }));
      const fb = X === M ? furnBoxes(bl) : {};
      Object.entries(fb).forEach(([i, b]) => out.push({ k: "furn", i: +i, lv: bl.lv, b, pad: 40 }));
      (idims(bl.lv, X) || []).forEach((d, i) => out.push({ k: "idim", i, lv: bl.lv, b: d[0] === "x" ? [0, d[1] - 160, M.W, d[1] + 160] : [d[1] - 160, 0, d[1] + 160, M.D], pad: 60 }));
      (L.userDims || []).forEach((d, i) => out.push({ k: "dim", i, lv: bl.lv, b: d[0] === "x" ? [d[2], d[1] - 160, d[3], d[1] + 160] : [d[1] - 160, d[2], d[1] + 160, d[3]], pad: 60 }));
      if (bl.lv === "main") {
        const m0 = bl.g.getScreenCTM(), ep0 = m0 && m0.a ? Math.max(40, 7 / Math.abs(m0.a)) : 90;   // malas uztveršanas josla ≈ 7 px
        (X.terraces || []).forEach((t, i) => {   // terase: visa platība (zemākā prioritāte) un katra mala atsevišķi (velkama pa asi)
          const xs = t.poly.map(q => q[0]), ys = t.poly.map(q => q[1]);
          const tb = [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)], ep = Math.min(ep0, Math.max(30, 0.22 * Math.min(tb[2] - tb[0], tb[3] - tb[1])));   // josla nedrīkst aprīt visu platību
          out.push({ k: "ter", i, lv: "main", b: tb, pad: 0 });
          t.poly.forEach((q, j) => { const r = t.poly[(j + 1) % t.poly.length], Hh = Math.abs(q[1] - r[1]) < 1;
            out.push({ k: "tedge", i: i * 100 + j, lv: "main", b: Hh ? [Math.min(q[0], r[0]), q[1] - ep, Math.max(q[0], r[0]), q[1] + ep] : [q[0] - ep, Math.min(q[1], r[1]), q[0] + ep, Math.max(q[1], r[1])], pad: 0 }); });
          if (sel && sel.k === "ter" && sel.i === i) t.poly.forEach((q, j) => out.push({ k: "tvert", i: i * 100 + j, lv: "main", b: [q[0] - ep * 1.4, q[1] - ep * 1.4, q[0] + ep * 1.4, q[1] + ep * 1.4], pad: 0 }));
        });
        (X.posts || []).forEach((q, i) => out.push({ k: "post", i, lv: "main", b: [q.x, q.y, q.x + q.w, q.y + q.d], pad: 40 }));
        const AO = axO(X);   // asu galu josla katrā pusē: velc uz āru / iekšā, visas šīs puses asis pārvietojas kopā
        const pb = Math.max(300, ep0 ? 10 * ep0 / 7 : 300);   // josla ap asu galiem un burbuļiem ≈ 10 px katrā pusē
        out.push({ k: "axo", i: "n", lv: "main", b: [0, -AO.n - 300 - pb, X.W, -AO.n + pb * .4], pad: 0 }, { k: "axo", i: "s", lv: "main", b: [0, X.D + AO.s - pb * .4, X.W, X.D + AO.s + 300 + pb], pad: 0 },
          { k: "axo", i: "w", lv: "main", b: [-AO.w - 300 - pb, 0, -AO.w + pb * .4, X.D], pad: 0 }, { k: "axo", i: "e", lv: "main", b: [X.W + AO.e - pb * .4, 0, X.W + AO.e + 300 + pb, X.D], pad: 0 });
      }
      if (X === M) Object.entries(stampBoxes(bl)).forEach(([i, b]) => out.push({ k: "stamp", i: +i, lv: bl.lv, b, pad: 0 }));
    } else {
      const s = bl.side;
      (X.windows || []).forEach((w, i) => {
        if (w.side !== s) return;
        const a = w.o === "h" ? w.x : w.y, u0 = Math.min(mapU(s, a), mapU(s, a + w.len)), u1 = Math.max(mapU(s, a), mapU(s, a + w.len));
        out.push({ k: "win", i, lv: "main", b: [u0, -(w.head ?? 2100), u1, -(w.sill ?? 0)], pad: 60, side: s });
      });
      (X.gableWins || []).forEach((gw, i) => {
        if (gw.side !== s) return;
        const u0 = Math.min(mapU(s, gw.u0), mapU(s, gw.u1)), u1 = Math.max(mapU(s, gw.u0), mapU(s, gw.u1));
        out.push({ k: "gw", i, lv: "main", b: [u0, -(gw.z1 || gw.z0 + 1400), u1, -gw.z0], pad: 60, side: s });
      });
      (X.posts || []).forEach((q, i) => {   // stabi fasādē (tikai krāsas spainim)
        const a = s === "north" || s === "south" ? q.x : q.y, l = s === "north" || s === "south" ? q.w : q.d, ez0 = (X.jumts && X.jumts.eave) || 2400;
        out.push({ k: "post", i, lv: "main", b: [Math.min(mapU(s, a), mapU(s, a + l)), -ez0, Math.max(mapU(s, a), mapU(s, a + l)), 0], pad: 30, side: s });
      });
      const NT = ((X.projekts || {}).notekas || {});
      // notekas un notekcaurules: katra atsevišķi (north/south = noteka, nw/ne/sw/se = caurule stūrī)
      const ez = (X.jumts && X.jumts.eave) || 2600, sp = span(s), on = key => NT[key] !== false, gut = (key, b) => { if (on(key)) out.push({ k: "gut", i: key, lv: "main", b, pad: 30, side: s }); };
      if (s === "north" || s === "south") {
        gut(s, [-120, -(ez + 330), sp + 120, -(ez - 120)]);
        [180, sp - 180].forEach(u => gut(s[0] + (s === "north" ? (u < sp / 2 ? "e" : "w") : (u < sp / 2 ? "w" : "e")), [u - 90, -(ez - 120), u + 90, 250]));
      } else [-1, 1].forEach(sd => {
        const LS = s === "west" ? (sd < 0 ? "north" : "south") : (sd < 0 ? "south" : "north"), ue = sd < 0 ? 0 : sp, uc = ue + sd * 70;
        gut(LS, sd < 0 ? [ue - 170, -(ez + 330), ue + 10, -(ez - 40)] : [ue - 10, -(ez + 330), ue + 170, -(ez - 40)]);
        gut(LS[0] + s[0], [uc - 80, -(ez - 40), uc + 80, 250]);
      });
      if (s === "south") (X.doors || []).forEach((d, i) => { if (d.entry) out.push({ k: "door", i, lv: "main", b: [d.x, -2100, d.x + d.w, 0], pad: 60, side: s }); });
    }
    return out;
  }
  const area = b => (b[2] - b[0]) * (b[3] - b[1]);
  const inB = (p, b, pad) => p[0] >= b[0] - pad && p[0] <= b[2] + pad && p[1] >= b[1] - pad && p[1] <= b[3] + pad;

  function hit(cx, cy) {
    let best = null;
    const bls = blocks();
    // the handles of the selected item come first: × deletes, ↻ turns, edge squares resize
    if (sel && sel.k !== "stamp") for (const bl of bls) {
      const k = ek(bl), p = toLocal(bl.g, cx, cy), near = (q, r) => Math.hypot(p[0] - q[0], p[1] - q[1]) < r / k;
      for (const it of items(bl)) {
        if (!same(it, sel) && !linked(it, sel)) continue;
        if (near(delPos(it.b, k), 3)) return { it, bl, p, del: true };
        if (it.k !== "furn") continue;
        if (near(handlePos(it.b, k), 3)) return { it, bl, p, rot: true };
        if (canSize(lv(it.lv).furniture[it.i])) for (const [z, q] of edgeHandles(it.b)) if (near(q, 2.4)) return { it, bl, p, rz: z };
      }
    }
    bls.forEach(bl => {
      const p = toLocal(bl.g, cx, cy);
      items(bl).forEach(it => {
        if (!inB(p, it.b, it.pad)) return;
        if (it.k === "post" && bl.type === "elev" && !(place && place.t === "bucket")) return;
        const a = area(it.b) + (it.k === "ter" ? 2e9 : 0) - (it.k === "tvert" ? 1e10 : 0) + (it.k === "furn" ? 1e8 : it.k === "stamp" ? 5e7 : it.k === "gut" ? 1e9 : it.k === "idim" ? 2e8 : 0);   // logi un durvis pirms mēbelēm
        if (!best || a < best.a) best = { a, it, bl, p };
      });
    });
    if (best) return best;
    for (const bl of bls) {
      if (bl.type !== "plan") continue;
      const p = toLocal(bl.g, cx, cy), m0 = bl.g.getScreenCTM(), pad = m0 && m0.a ? 9 / Math.abs(m0.a) : 0;   // plānas sienas: 9 px uztveršanas josla
      const w = [[0, 0], [pad, 0], [-pad, 0], [0, pad], [0, -pad]].map(([dx, dy]) => wallAt(bl.lv, [p[0] + dx, p[1] + dy])).find(Boolean);
      if (w) { const e0 = w.v0 != null ? w.v0 : T, e1 = w.v1 != null ? w.v1 : (w.axis === "x" ? M.D : M.W) - T;   // tikai pati sienas posma garums, nevis visa lapa
      return { it: { k: "wall", lv: bl.lv, b: w.axis === "x" ? [w.lo, e0, w.hi, e1] : [e0, w.lo, e1, w.hi], w }, bl, p, wall: true }; }
    }
    return null;
  }
  function zone(h) {   // facade: which edge is grabbed
    if (h.wall) return h.it.w.axis === "x" ? "wx" : "wy";
    if (h.rot) return "rot";
    if (h.del) return "del";
    if (h.rz) return h.rz;
    if (h.it.k === "tvert") return "tc";
    if (h.it.k === "axo") return h.it.i === "n" || h.it.i === "s" ? "t" : "l";
    if (h.it.k === "tedge") { const t = M.terraces[Math.floor(h.it.i / 100)], j = h.it.i % 100, a = t.poly[j], b = t.poly[(j + 1) % t.poly.length]; return Math.abs(a[1] - b[1]) < 1 ? "t" : Math.abs(a[0] - b[0]) < 1 ? "l" : "move"; }
    if (h.it.k === "gut" || h.it.k === "idim") return "move";
    if (h.it.k === "dim") {   // gali maina garumu, vidus pārvieto mēra līniju
      const d = lv(h.it.lv).userDims[h.it.i], [x, y] = h.p, e = 4 / ek(h.bl);
      if (d[0] === "x") return Math.abs(x - d[2]) < e ? "l" : Math.abs(x - d[3]) < e ? "r" : "move";
      return Math.abs(y - d[2]) < e ? "t" : Math.abs(y - d[3]) < e ? "b" : "move";
    }
    if (h.bl.type === "plan" && (h.it.k === "win" || h.it.k === "door")) {   // plānā loga/durvju gali maina platumu
      const o = lv(h.it.lv)[h.it.k === "win" ? "windows" : "doors"][h.it.i], b = h.it.b, H = o.o === "h", L = H ? b[2] - b[0] : b[3] - b[1], e = Math.min(L * .25, 5 / ek(h.bl)), v = H ? h.p[0] : h.p[1];
      return Math.abs(v - (H ? b[0] : b[1])) < e ? (H ? "l" : "t") : Math.abs(v - (H ? b[2] : b[3])) < e ? (H ? "r" : "b") : "move";
    }
    if (h.bl.type !== "elev" || h.it.k === "door") return "move";
    const [x, y] = h.p, b = h.it.b, ex = Math.max(90, (b[2] - b[0]) * .14), ey = Math.max(90, (b[3] - b[1]) * .14);
    if (Math.abs(x - b[0]) < ex) return "l";
    if (Math.abs(x - b[2]) < ex) return "r";
    if (h.it.k === "gw" && !M.gableWins[h.it.i].win) return Math.abs(y - b[3]) < ey ? "b" : "move";
    if (Math.abs(y - b[1]) < ey) return "t";
    if (Math.abs(y - b[3]) < ey) return "b";
    return "move";
  }
  const same = (a, b) => a && b && a.k === b.k && a.i === b.i && a.lv === b.lv;
  const handlePos = (b, k) => [b[2] + 4 / k, b[1] - 4 / k];
  const delPos = (b, k) => [b[0] - 4 / k, b[1] - 4 / k];
  const edgeHandles = b => [["l", [b[0], (b[1] + b[3]) / 2]], ["r", [b[2], (b[1] + b[3]) / 2]], ["t", [(b[0] + b[2]) / 2, b[1]]], ["b", [(b[0] + b[2]) / 2, b[3]]]];

  // ---- overlay drawing ----
  function overlay(g) {
    let o = g.querySelector(":scope > g.mm-ov");
    if (!o) { o = document.createElementNS(NS, "g"); o.setAttribute("class", "mm-ov"); o.setAttribute("pointer-events", "none"); g.appendChild(o); }
    return o;
  }
  const mk = (o, tag, at) => { const e = document.createElementNS(NS, tag); Object.entries(at).forEach(([a, v]) => e.setAttribute(a, v)); o.appendChild(e); return e; };
  function rect(o, b, dash, k, pad = 1.2 / k) {   // ~1.2 mm uz papīra; mēbelēm 0, lai rāmis sakrīt ar mēbeli
    mk(o, "rect", { x: b[0] - pad, y: b[1] - pad, width: b[2] - b[0] + 2 * pad, height: b[3] - b[1] + 2 * pad, fill: dash ? "rgba(217,72,15,.10)" : "none", stroke: ACC, "stroke-width": 0.45 / k, "stroke-dasharray": dash ? `${1.4 / k} ${0.9 / k}` : "none" });
  }
  // elements zem kursora: gaiši zils, lai redz, ko paņems klikšķis
  let hovKey = "";
  function hover(h) {
    const key = h ? [h.it.k, h.it.i, h.it.lv, h.bl.type, h.it.w ? h.it.w.lo : "", h.it.w && h.it.w.v0 != null ? Math.round(h.it.w.axis === "x" ? h.p[1] / 200 : h.p[0] / 200) : ""].join("|") : "";
    if (!h) hovWall = null;
    if (key === hovKey) return; hovKey = key;
    document.querySelectorAll("g.mm-ov .hv").forEach(x => x.remove());
    if (!h || !h.it || !h.it.b || same(h.it, sel)) return;
    const k = ek(h.bl), b = h.it.b.slice();
    if (h.it.k === "wall") { b[0] = Math.max(b[0], 0); b[2] = Math.min(b[2], M.W); b[1] = Math.max(b[1], 0); b[3] = Math.min(b[3], M.D); }
    if (h.it.k === "wall" && !h.it.w.ext && h.it.w.v0 != null) {
      const w = h.it.w, X = w.axis === "x", u = X ? h.p[1] : h.p[0], pairs = linePairs(w.axis, w.lo, w.hi), segs = wallChains(pairs); let best = -1, bd = 1e9;
      segs.forEach((q, i) => { const d = u < q[0] ? q[0] - u : u > q[1] ? u - q[1] : 0; if (d < bd) { bd = d; best = i; } });
      if (best >= 0) { hovWall = { bl: h.bl, w, pairs, seg: segs[best] }; if (X) { b[1] = segs[best][0]; b[3] = segs[best][1]; } else { b[0] = segs[best][0]; b[2] = segs[best][1]; } const c = (w.lo + w.hi) / 2, r = 2.4 / k;
        segs[best].forEach(e => mk(overlay(h.bl.g), "rect", { class: "hv", x: (X ? c : e) - r, y: (X ? e : c) - r, width: 2 * r, height: 2 * r, fill: "#fff", stroke: "#3d8fe0", "stroke-width": 0.4 / k })); }
    }
    const pd = h.it.k === "furn" ? 0 : 0.8 / k;
    mk(overlay(h.bl.g), "rect", { class: "hv", x: b[0] - pd, y: b[1] - pd, width: b[2] - b[0] + 2 * pd, height: b[3] - b[1] + 2 * pd, rx: 0.6 / k, fill: "#5aa9ff", "fill-opacity": 0.2, stroke: "#3d8fe0", "stroke-width": 0.35 / k, "pointer-events": "none" });
  }
  function label(o, x, y, t, k) {
    mk(o, "text", { x, y, "font-size": 3 / k, "font-family": "Barlow, sans-serif", "font-weight": 600, fill: ACC, stroke: "#fff", "stroke-width": 0.7 / k, "paint-order": "stroke" }).textContent = t;
  }
  // durvīm un logiem plānā: pagaidu mēri līdz tuvākajām šķērssienām (telpas malām) abās pusēs
  function openDims(o, l, it, k, X = M) {
    const L = lv(l, X), ob = ((it.k === "door" ? L.doors : L.windows) || [])[it.i]; if (!ob) return;
    const H = ob.o === "h", a0 = H ? ob.x : ob.y, a1 = a0 + (it.k === "door" ? ob.w : ob.len), c = (a0 + a1) / 2, w0 = H ? ob.y : ob.x, w1 = w0 + (it.k === "door" ? ob.th : T);
    const R = rects(l, X).filter(q => (H ? q[0] <= c && q[2] >= c : q[1] <= c && q[3] >= c));
    const pre = it.k === "door" && ob.side > 0 ? 1 : -1;   // durvis: telpa, uz kuru veras; logs: iekštelpa
    const side = [pre, -pre].map(sd => { const face = sd > 0 ? w1 : w0, q = R.find(r => Math.abs((H ? (sd > 0 ? r[1] : r[3]) : (sd > 0 ? r[0] : r[2])) - face) < 40); return q && { sd, face, q }; }).find(Boolean);
    if (!side) return;
    o = mk(o, "g", { class: "od" });
    const { sd, face, q } = side, lo = H ? q[0] : q[1], hi = H ? q[2] : q[3], at = face + sd * 420, P = (u, v) => (H ? [u, v] : [v, u]);
    const ln = { stroke: ACC, "stroke-width": 0.35 / k };
    [[lo, a0], [a1, hi]].forEach(([u0, u1]) => {
      if (u1 - u0 < 1) return;
      const s0 = P(u0, at), s1 = P(u1, at); mk(o, "line", Object.assign({ x1: s0[0], y1: s0[1], x2: s1[0], y2: s1[1] }, ln));
      [u0, u1].forEach(u => { const e0 = P(u, face), e1 = P(u, at + sd * 120), t0 = P(u - 90, at + 90), t1 = P(u + 90, at - 90);
        mk(o, "line", Object.assign({ x1: e0[0], y1: e0[1], x2: e1[0], y2: e1[1] }, ln, { "stroke-width": 0.2 / k, "stroke-dasharray": `${0.8 / k} ${0.6 / k}` }));
        mk(o, "line", Object.assign({ x1: t0[0], y1: t0[1], x2: t1[0], y2: t1[1] }, ln)); });
      const m = P((u0 + u1) / 2, at - (H ? 1.2 / k : 0)); label(o, m[0] - (H ? 3 / k : -1.2 / k), m[1], `${Math.round(u1 - u0)}`, k);
    });
  }
  // logiem fasādē: pagaidu mēri līdz fasādes malām un no loga apakšas līdz grīdas līmenim (±0,000); tikai kamēr izvēlēts vai velk
  function elevDims(o, bl, it, k, X = M) {
    const b = it.b, sp = span(bl.side), u0 = b[0], u1 = b[2], zb = -b[3]; if (!(u1 > u0)) return;
    o = mk(o, "g", { class: "od" });
    const ln = { stroke: ACC, "stroke-width": 0.35 / k }, ext = { stroke: ACC, "stroke-width": 0.2 / k, "stroke-dasharray": `${0.8 / k} ${0.6 / k}` };
    const tick = (x, y) => mk(o, "line", Object.assign({ x1: x - 90, y1: y + 90, x2: x + 90, y2: y - 90 }, ln));
    const yh = (b[1] + b[3]) / 2;
    [[0, u0], [u1, sp]].forEach(([a, c]) => {
      if (c - a < 1) return;
      mk(o, "line", Object.assign({ x1: a, y1: yh, x2: c, y2: yh }, ln)); tick(a, yh); tick(c, yh);
      label(o, (a + c) / 2 - 3 / k, yh - 1.2 / k, `${Math.round(c - a)}`, k);
    });
    if (zb > 1) {
      const x = u0 + (u1 - u0) * .78;
      mk(o, "line", Object.assign({ x1: x, y1: b[3], x2: x, y2: 0 }, ln)); tick(x, b[3]); tick(x, 0);
      mk(o, "line", Object.assign({ x1: x - 400, y1: 0, x2: x + 400, y2: 0 }, ext));
      label(o, x + 1.2 / k, b[3] / 2, `${Math.round(zb)}`, k);
    }
  }
  function rotHandle(o, b, k) {   // ↻ aplis pie mēbeles augšējā labā stūra: viens klikšķis = 90°
    const [x, y] = handlePos(b, k), r = 2.3 / k;
    mk(o, "circle", { cx: x, cy: y, r, fill: ACC, stroke: "#fff", "stroke-width": 0.35 / k });
    // pulksteņrādītāja virzienā: no kreisās puses pāri augšai uz leju, bultas gals apakšā rāda pa kreisi
    const a = r * .52;
    mk(o, "path", { d: `M ${x - a} ${y} A ${a} ${a} 0 1 1 ${x + r * .08} ${y + a}`, fill: "none", stroke: "#fff", "stroke-width": 0.35 / k, "stroke-linecap": "round" });
    mk(o, "path", { d: `M ${x + r * .38} ${y + a - r * .3} L ${x + r * .02} ${y + a} L ${x + r * .38} ${y + a + r * .3}`, fill: "none", stroke: "#fff", "stroke-width": 0.32 / k, "stroke-linejoin": "round", "stroke-linecap": "round" });
  }
  function delHandle(o, b, k) {   // × aplis kreisajā augšējā stūrī: viens klikšķis = dzēst
    const [x, y] = delPos(b, k), r = 2.3 / k, a = r * .36;
    mk(o, "circle", { cx: x, cy: y, r, fill: "#c92a2a", stroke: "#fff", "stroke-width": 0.35 / k });
    mk(o, "path", { d: `M ${x - a} ${y - a} L ${x + a} ${y + a} M ${x + a} ${y - a} L ${x - a} ${y + a}`, stroke: "#fff", "stroke-width": 0.4 / k, "stroke-linecap": "round" });
  }
  function sizeHandles(o, b, k) {
    const s = 2 / k;
    edgeHandles(b).forEach(([, q]) => mk(o, "rect", { x: q[0] - s / 2, y: q[1] - s / 2, width: s, height: s, fill: "#fff", stroke: ACC, "stroke-width": 0.35 / k }));
  }
  // ---- palīglīnijas: lapas koordinātās (mm uz papīra), tikai redaktorā; pielīp elementu malām un stūriem ----
  const GC = "#1a9bd7", GUIDES = () => ((M.projekts || {}).guides || []);
  const vbS = () => { const v = sheet().viewBox.baseVal; return [v.width || 297, v.height || 420]; };
  const toSheet = (cx, cy) => { const q = new DOMPoint(cx, cy).matrixTransform(sheet().getScreenCTM().inverse()); return [q.x, q.y]; };
  const pxU = () => sheet().getBoundingClientRect().width / vbS()[0];   // ekrāna pikseļi uz vienu lapas mm
  function guideEnds(gd) {
    const [W, H] = vbS();
    if (gd.o === "v") return [[gd.at, 0], [gd.at, H]];
    if (gd.o === "h") return [[0, gd.at], [W, gd.at]];
    const r = gd.a * Math.PI / 180, L = W + H; return [[gd.x - Math.cos(r) * L, gd.y - Math.sin(r) * L], [gd.x + Math.cos(r) * L, gd.y + Math.sin(r) * L]];
  }
  function drawGuides(extra) {
    const sv = sheet(); if (!sv) return;
    sv.querySelectorAll(":scope > g.mm-gd").forEach(e => e.remove());
    const g = mk(sv, "g", { class: "mm-gd", "pointer-events": "none" });
    const [W, H] = vbS(); mk(g, "clipPath", { id: "mmGdClip" }).appendChild(Object.assign(document.createElementNS(NS, "rect"), {})).setAttribute("width", W);
    g.querySelector("#mmGdClip rect").setAttribute("height", H);
    // tālummaiņa ir CSS transform uz body, tāpēc vector-effect="non-scaling-stroke" Chrome nestrādā: biezumu pikseļos pārrēķina lapas mm
    const u = 1 / pxU();
    const line = (gd, col, w, dash, op) => { const [a, b] = guideEnds(gd); mk(g, "line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1], stroke: col, "stroke-width": w * u, "stroke-opacity": op || 1, "clip-path": "url(#mmGdClip)", ...(dash ? { "stroke-dasharray": dash.map(v => v * u).join(" ") } : {}) }); };
    GUIDES().forEach((gd, i) => { const on = sel && sel.k === "guide" && sel.i === i; if (drag && drag.gi === i) return; line(gd, on ? ACC : GC, on ? 1.5 : 1, null, on ? 1 : .75); });
    if (extra) { line(extra, GC, 1, [5, 4]); if (extra.hit) mk(g, "circle", { cx: extra.hp[0], cy: extra.hp[1], r: 3.5 * u, fill: "#fff", stroke: GC, "stroke-width": 1.5 * u }); }
  }
  // pielipšanas punkti lapas koordinātās: visu elementu malas plānos un fasādēs, sienu un telpu malas, stūri
  function guidePts() {
    const sv = sheet(), RI = sv.getScreenCTM().inverse(), xs = [], ys = [], pts = [];
    blocks().forEach(bl => {
      const m = RI.multiply(bl.g.getScreenCTM()), T2 = (x, y) => { const q = new DOMPoint(x, y).matrixTransform(m); return [q.x, q.y]; };
      const box = b => { if (b.some(v => !isFinite(v) || Math.abs(v) > 1e7)) return; const a = T2(b[0], b[1]), c = T2(b[2], b[3]), y0 = Math.min(a[1], c[1]), y1 = Math.max(a[1], c[1]), x0 = Math.min(a[0], c[0]), x1 = Math.max(a[0], c[0]); xs.push([a[0], y0, y1], [c[0], y0, y1]); ys.push([a[1], x0, x1], [c[1], x0, x1]); pts.push(a, c, [a[0], c[1]], [c[0], a[1]]); };
      try { items(bl).forEach(it => it.b && box(it.b)); } catch (e) {}
      if (bl.type === "plan") { rects(bl.lv).forEach(box); box([0, 0, M.W, M.D]); (M.poly || []).forEach(q => { const a = T2(q[0], q[1]); xs.push([a[0], a[1], a[1]]); ys.push([a[1], a[0], a[0]]); pts.push(a); }); }
      else { const sp = span(bl.side), e = (M.jumts && M.jumts.eave) || 2600; box([0, -e, sp, 0]); const r = T2(sp / 2, -e - sp / 2 * Math.tan(((M.jumts && M.jumts.pitch) || 30) * Math.PI / 180)); pts.push(r); xs.push([r[0], r[1], r[1]]); ys.push([r[1], r[0], r[0]]); }
    });
    return { xs, ys, pts };
  }
  function guideAt(o, cx, cy, P) {   // jaunā/pārvietotā palīglīnija pie kursora, ar pielipšanu
    // pielipšana: vispirms malas, kas sniedzas līdz kursoram (±40 px), rādiuss 8 px; tālākas malas tikai pavisam tuvu (3 px)
    const [x, y] = toSheet(cx, cy), u = 1 / pxU(), reach = 40 * u, rad = 7 * u;
    const near = (arr, v, w) => { let b = null, bd = 8 * u; arr.forEach(([t, a, c]) => { if (w < a - reach || w > c + reach) return; const d = Math.abs(t - v); if (d < bd) { bd = d; b = t; } });
      if (b == null) { bd = 3 * u; arr.forEach(([t]) => { const d = Math.abs(t - v); if (d < bd) { bd = d; b = t; } }); } return b; };
    if (o === "v") { const b = near(P.xs, x, y); return { o, at: +(b ?? x).toFixed(2), hit: b != null, hp: [b ?? x, y] }; }
    if (o === "h") { const b = near(P.ys, y, x); return { o, at: +(b ?? y).toFixed(2), hit: b != null, hp: [x, b ?? y] }; }
    let bp = null, bd = rad * 1.5; P.pts.forEach(q => { const d = Math.hypot(q[0] - x, q[1] - y); if (d < bd) { bd = d; bp = q; } });
    const pt = bp || [x, y], pitch = (M.jumts && M.jumts.pitch) || 30, [W] = vbS();
    let side = -1; blocks().filter(b => b.type === "elev").forEach(bl => { const r = bl.g.getBoundingClientRect(); if (cx >= r.left && cx <= r.right) side = cx < r.left + r.width / 2 ? -1 : 1; }); void W;
    return { o, x: +pt[0].toFixed(2), y: +pt[1].toFixed(2), a: side < 0 ? -pitch : pitch, hit: !!bp, hp: pt };
  }
  function guideAuto(cx, cy, P, shift) {   // pati izvēlas vertikālu vai horizontālu: kurai tuvāks pielipšanas punkts, citādi vertikāla (Shift = horizontāla)
    const v = guideAt("v", cx, cy, P), h = guideAt("h", cx, cy, P), [x, y] = toSheet(cx, cy);
    if (v.hit && h.hit) return Math.abs(v.at - x) <= Math.abs(h.at - y) ? v : h;
    if (v.hit) return v; if (h.hit) return h;
    return shift ? h : v;
  }
  const guideNow = (pl, cx, cy, shift) => pl.o === "a" ? guideAuto(cx, cy, pl.P || (pl.P = guidePts()), shift) : guideAt(pl.o, cx, cy, pl.P || (pl.P = guidePts()));
  function guideHit(cx, cy) {   // palīglīnija tuvāk par 5 px
    const [x, y] = toSheet(cx, cy), rad = 5 / pxU(); let best = -1, bd = rad;
    GUIDES().forEach((gd, i) => {
      let d; if (gd.o === "v") d = Math.abs(x - gd.at); else if (gd.o === "h") d = Math.abs(y - gd.at);
      else { const r = gd.a * Math.PI / 180; d = Math.abs(-(x - gd.x) * Math.sin(r) + (y - gd.y) * Math.cos(r)); }
      if (d < bd) { bd = d; best = i; }
    });
    return best;
  }
  function drawSel() {
    drawGuides();
    document.querySelectorAll("g.mm-ov").forEach(o => o.remove());
    if (!sel) return;
    blocks().forEach(bl => items(bl).forEach(it => {
      if (!same(it, sel) && !linked(it, sel)) return;
      const k = ek(bl), o = overlay(bl.g);
      rect(o, it.b, false, k, it.k === "furn" ? 0 : undefined);
      if (it.k === "ter") { const t = M.terraces[it.i]; mk(o, "polygon", { points: t.poly.map(q => q.join(",")).join(" "), fill: "rgba(34,102,216,.10)", stroke: ACC, "stroke-width": 1.2 / k, "stroke-dasharray": `${2.4 / k} ${1.6 / k}` }); t.poly.forEach(q => snapMark(o, q, true, k)); }
      if (it.k === "post") gpts(it.b).forEach((q, j) => mk(o, "circle", { cx: q[0], cy: q[1], r: 1.3 / k, fill: j === 4 ? ACC : "#fff", stroke: ACC, "stroke-width": 0.4 / k }));
      if (it.k !== "stamp" && it.k !== "axo") delHandle(o, it.b, k);
      if (bl.type === "plan" && (it.k === "door" || it.k === "win")) openDims(o, bl.lv, it, k);
      if (bl.type === "elev" && (it.k === "win" || it.k === "gw")) elevDims(o, bl, it, k);
      if (it.k === "furn") { rotHandle(o, it.b, k); if (canSize(lv(it.lv).furniture[it.i])) sizeHandles(o, it.b, k); }
      const t = sizeText(it);
      if (t) { const at = selPt && selPt.g === bl.g ? [selPt.p[0] + 4 / k, selPt.p[1] - 4 / k] : [it.b[0] + 7 / k, it.b[1] - 2.5 / k]; label(o, at[0], at[1], t, k); }
    }));
    // grupa (Shift+klikšķis): pārējie atlasītie elementi
    (sel.more || []).forEach(m => blocks().forEach(bl => { if (bl.type !== "plan") return; items(bl).forEach(it => { if (same(it, m)) rect(overlay(bl.g), it.b, false, ek(bl), it.k === "furn" ? 0 : undefined); }); }));
  }
  // izvēlētā loga / durvju izmēri pie kursora, kontrolei
  let selPt = null;
  function sizeText(it) {
    const L = lv(it.lv);
    if (it.k === "win") { const w = L.windows[it.i]; return `${Math.round(w.len)} × ${Math.round((w.head ?? 2100) - (w.sill ?? 0))} mm`; }
    if (it.k === "door") { const d = L.doors[it.i]; return `${Math.round(d.w)} × 2100 mm`; }
    if (it.k === "gw") { const g = M.gableWins[it.i]; return `${Math.round(g.u1 - g.u0)}${g.z1 ? " × " + Math.round(g.z1 - g.z0) : ""} mm`; }
    return "";
  }
  // a loft gable window and its facade drawing are the same window
  function linked(it, s) {
    if (!s) return false;
    if (s.k === "gw" && it.k === "win" && it.lv === "loft") return loftFor(M.gableWins[s.i]) === M.loft.windows[it.i];
    if (it.k === "gw" && s.k === "win" && s.lv === "loft") return loftFor(M.gableWins[it.i]) === M.loft.windows[s.i];
    return false;
  }
  // a gable window and its loft plan opening are linked by wall side and position
  const gwMatch = (gw, w) => w.side === gw.side && Math.abs(w.y - Math.min(gw.u0, gw.u1)) < 2 && Math.abs(w.len - Math.abs(gw.u1 - gw.u0)) < 2;
  function loftFor(gw, X = M) { return X.loft && (X.loft.windows || []).find(w => gwMatch(gw, w)); }

  // ---- furniture geometry ----
  // a rotated piece is stored as ["_rot", grādi, cx, cy, [mēbele]]; build_model.py zīmē to tāpat
  function shiftF(f, dx, dy) {
    if (f[0] === "_rot") { f[2] = +(f[2] + dx).toFixed(1); f[3] = +(f[3] + dy).toFixed(1); shiftF(f[4], dx, dy); return; }
    f[1] = +(f[1] + dx).toFixed(1); f[2] = +(f[2] + dy).toFixed(1);
    if (f[0] === "Ln") { f[3] = +(f[3] + dx).toFixed(1); f[4] = +(f[4] + dy).toFixed(1); }
  }
  // which arguments set the drawn width (x) and depth (y) of a piece; null = fixed size
  const baseF = f => (f && f[0] === "_rot" ? baseF(f[4]) : f);
  const totDeg = f => (f && f[0] === "_rot" ? f[1] + totDeg(f[4]) : 0);
  const canSize = f => !!sizeSpec(baseF(f)) && (((totDeg(f) % 90) + 90) % 90) === 0;
  function sizeSpec(f) {
    if (!f) return null;
    const t = f[0].replace(/[13]$/, "");
    if (t === "bed") return f[5] === "n" || f[5] === "s" ? { x: 4, y: 3 } : { x: 3, y: 4 };
    if (t === "sofaL") return { x: 3, y: 5 };
    if (t === "kapnes" || t === "kapnesL") return { x: 3, y: 4 };
    if (t === "shower" || t === "armchair") return { x: 3, y: 3 };
    if (t === "Ci") return { x: 3, y: 3, ci: true };
    if (["R", "wardrobe", "desk", "basin", "sofa", "galds"].includes(t)) return { x: 3, y: 4 };
    return null;
  }
  // grow one end of a piece along its own x or y by g mm (negative shrinks)
  function grow(f, sp, ax, end, g) {
    const i = sp[ax], pi = ax === "x" ? 1 : 2, min = sp.ci ? 100 : f[0].startsWith("sofaL") && ax === "y" ? 300 : 200;
    if (sp.ci) { const r = Math.max(min, f[3] + g / 2); g = (r - f[3]) * 2; f[3] = +r.toFixed(1); f[pi] = +(f[pi] + (end === "hi" ? g / 2 : -g / 2)).toFixed(1); return; }
    const v = Math.max(min, f[i] + g); g = v - f[i]; f[i] = +v.toFixed(1);
    if (end === "lo") f[pi] = +(f[pi] - g).toFixed(1);
  }
  // a drawn edge of a turned piece is another edge of the piece itself (rotate about cx cy is rigid)
  const EDGE = { 0: { r: ["x", "hi"], l: ["x", "lo"], b: ["y", "hi"], t: ["y", "lo"] }, 90: { b: ["x", "hi"], t: ["x", "lo"], l: ["y", "hi"], r: ["y", "lo"] },
    180: { l: ["x", "hi"], r: ["x", "lo"], t: ["y", "hi"], b: ["y", "lo"] }, 270: { t: ["x", "hi"], b: ["x", "lo"], r: ["y", "hi"], l: ["y", "lo"] } };
  function roomOf(l, b) {
    const c = [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2], R = rects(l);
    return R.find(q => c[0] >= q[0] && c[0] <= q[2] && c[1] >= q[1] && c[1] <= q[3]);
  }
  // resize by dragging an edge: the opposite edge stays, the piece stays in its room
  function resizeFurn(N, l, i, b, z, dq) {
    const L = lv(l, N), f = L.furniture[i], inner = baseF(f), sp = sizeSpec(inner); if (!sp) return null;
    let q = r10(dq); const r = roomOf(l, b);
    if (r) { if (z === "r") q = Math.min(q, r[2] - b[2]); if (z === "l") q = Math.max(q, r[0] - b[0]); if (z === "b") q = Math.min(q, r[3] - b[3]); if (z === "t") q = Math.max(q, r[1] - b[1]); }
    const g = z === "r" || z === "b" ? q : -q, deg = ((totDeg(f) % 360) + 360) % 360, [ax, end] = (EDGE[deg] || EDGE[0])[z];
    grow(inner, sp, ax, end, g);
    const nb = b.slice(); if (z === "r") nb[2] += q; if (z === "l") nb[0] += q; if (z === "b") nb[3] += q; if (z === "t") nb[1] += q;
    return { N, nb };
  }
  // mēbeles aizmugure (galvgalis, atzveltne, poda tvertne): kurā pusē tā ir pašlaik
  const DIRS = ["n", "e", "s", "w"], OPP = { n: "s", s: "n", e: "w", w: "e" };
  function backOf(f) {
    const q = baseF(f); if (!q) return null;
    const t = q[0].replace(/[13]$/, ""); let s = null;
    if (t === "bed") s = q[5] || "w";
    else if (t === "sofa") s = q[5] || "n";
    else if (t === "toilet") s = q[4] || (q[3] < 0 ? "s" : "n");
    else if (t === "basin") s = q[5] || "n";
    else if (t === "wardrobe") s = OPP[q[5] || "s"];
    else if (t === "desk") s = OPP[q[5] || "e"];
    else if (t === "washer") s = "n";
    else if (t === "armchair") s = "e";
    if (!DIRS.includes(s)) return null;
    const deg = ((Math.round(totDeg(f) / 90) % 4) + 4) % 4;
    return DIRS[(DIRS.indexOf(s) + deg) % 4];
  }
  // bīdot mēbeli ar aizmuguri: kursors pie telpas sienas -> mēbele pagriežas ar aizmuguri pret to un pielīp
  const WALLR = 300;   // pagriešana pie sienas tikai tuvu sienai; Alt vilkšanas laikā to izslēdz, bultiņas pārvieto bez pielipšanas
  function wallSnap(N, l, it, d, dx, dy, grp) {
    if (!d.h.p || d.alt) return null;
    const L = lv(l, N), f = L.furniture[it.i], cur = backOf(f); if (!cur) return null;
    const p = [d.h.p[0] + dx, d.h.p[1] + dy], R = rects(l), r = R.find(q => p[0] >= q[0] && p[0] <= q[2] && p[1] >= q[1] && p[1] <= q[3]); if (!r) return null;
    const ds = { n: p[1] - r[1], s: r[3] - p[1], w: p[0] - r[0], e: r[2] - p[0] };
    const side = DIRS.slice().sort((a, b2) => ds[a] - ds[b2])[0]; if (ds[side] > WALLR) return null;
    const b = it.b, c = [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2], turn = ((DIRS.indexOf(side) - DIRS.indexOf(cur)) % 4 + 4) % 4 * 90;
    const rb = turn ? rotBox(b, c, turn) : b.slice(), bw = rb[2] - rb[0], bh = rb[3] - rb[1];
    if ((side === "n" || side === "s") ? bw > r[2] - r[0] + 1 : bh > r[3] - r[1] + 1) return null;
    if (turn) grp.forEach(j => {
      const F = L.furniture[j];
      if (F[0] === "_rot" && Math.abs(F[2] - c[0]) < 1 && Math.abs(F[3] - c[1]) < 1) { F[1] = (((F[1] + turn) % 360) + 360) % 360; if (!F[1]) L.furniture[j] = F[4]; }
      else L.furniture[j] = ["_rot", turn, +c[0].toFixed(1), +c[1].toFixed(1), F];
    });
    const cl = (v, a, z) => Math.max(a, Math.min(z, v));
    let x0, y0;
    if (side === "n" || side === "s") { x0 = cl(p[0] - bw / 2, r[0], r[2] - bw); y0 = side === "n" ? r[1] : r[3] - bh; if (x0 - r[0] < SNAP) x0 = r[0]; else if (r[2] - x0 - bw < SNAP) x0 = r[2] - bw; }
    else { y0 = cl(p[1] - bh / 2, r[1], r[3] - bh); x0 = side === "w" ? r[0] : r[2] - bw; if (y0 - r[1] < SNAP) y0 = r[1]; else if (r[3] - y0 - bh < SNAP) y0 = r[3] - bh; }
    {   // pie sienas var slīdēt tikai pa sienu un neiebraukt citā mēbelē
      const hz = side === "n" || side === "s", others = Object.entries(d.boxes || {}).filter(([j]) => !grp.includes(+j) && !NOCOL.includes((baseF(L.furniture[+j]) || [""])[0])).map(e => e[1]);
      for (let pass = 0; pass < 4; pass++) {
        const nb = [x0, y0, x0 + bw, y0 + bh], o = others.find(q => ovl(nb, q)); if (!o) break;
        if (hz) { const c = [o[0] - bw, o[2]].filter(v => v >= r[0] - 1 && v + bw <= r[2] + 1).sort((m, n) => Math.abs(m - x0) - Math.abs(n - x0))[0]; if (c == null) return null; x0 = c; }
        else { const c = [o[1] - bh, o[3]].filter(v => v >= r[1] - 1 && v + bh <= r[3] + 1).sort((m, n) => Math.abs(m - y0) - Math.abs(n - y0))[0]; if (c == null) return null; y0 = c; }
        if (pass === 3) return null;
      }
    }
    let sx = r10(x0 - rb[0]), sy = r10(y0 - rb[1]);
    if (Math.abs(x0 - r[0]) < 1 || Math.abs(x0 + bw - r[2]) < 1) sx = +(x0 - rb[0]).toFixed(1);
    if (Math.abs(y0 - r[1]) < 1 || Math.abs(y0 + bh - r[3]) < 1) sy = +(y0 - rb[1]).toFixed(1);
    if (side === "n" || side === "s") sy = +(y0 - rb[1]).toFixed(1); else sx = +(x0 - rb[0]).toFixed(1);
    grp.forEach(j => shiftF(L.furniture[j], sx, sy));
    return { nb: [rb[0] + sx, rb[1] + sy, rb[2] + sx, rb[3] + sy], side };
  }
  // ---- WC / vannas istaba: pēc sienas pārbīdes santehnika pārkārtojas tā, lai priekšā paliek brīva vieta ----
  // pods: 700 platumā (350 no ass līdz sienai), 600 brīvi priekšā; duša, izlietne, veļasmašīna: 600 brīvi priekšā; durvju vēriens brīvs
  const BATH = ["toilet", "shower", "basin", "washer"];
  function bathSpec(f) {
    let rot = 0, q = f;
    if (f[0] === "_rot") { if (!f[4] || String(f[4][0]).replace(/[13]$/, "") !== "washer") return null; rot = f[1]; q = f[4]; }
    const t = String(q[0]).replace(/[13]$/, ""); if (!BATH.includes(t)) return null;
    if (t === "toilet") { const w = q[4] || (q[3] < 0 ? "s" : "n"), dp = q[5] === "k" ? 660 : 540; return { t, q, al: 700, dp, wall: w, c: w === "e" ? [q[1] - dp / 2, q[2]] : w === "w" ? [q[1] + dp / 2, q[2]] : w === "n" ? [q[1], q[2] + dp / 2] : [q[1], q[2] - dp / 2] }; }
    if (t === "basin") { const w = q[5] || "n", H = w === "n" || w === "s"; return { t, q, al: H ? q[3] : q[4], dp: H ? q[4] : q[3], wall: w, c: [q[1] + q[3] / 2, q[2] + q[4] / 2] }; }
    if (t === "shower") { const g = q[4] || []; return { t, q, al: q[3], dp: q[3], wall: DIRS.find(d => !g.includes(d)) || "n", c: [q[1] + q[3] / 2, q[2] + q[3] / 2] }; }
    return { t, q, al: 600, dp: 600, wall: DIRS[((Math.round(rot / 90) % 4) + 4) % 4], c: [q[1] + 300, q[2] + 300] };
  }
  const BATHMSG = "Tik šaurā telpā santehnika ar 600 mm brīvu vietu priekšā vairs nesaiet. Siena palika vietā: izdzēs kādu priekšmetu vai pabīdi mazāk.";
  const CLR = 600, ovl = (a, b) => Math.min(a[2], b[2]) - Math.max(a[0], b[0]) > 1 && Math.min(a[3], b[3]) - Math.max(a[1], b[1]) > 1;
  function bathBox(sp, r, w, u) {
    const { al, dp } = sp;
    if (w === "n") return [[r[0] + u, r[1], r[0] + u + al, r[1] + dp], [r[0] + u, r[1] + dp, r[0] + u + al, r[1] + dp + CLR]];
    if (w === "s") return [[r[0] + u, r[3] - dp, r[0] + u + al, r[3]], [r[0] + u, r[3] - dp - CLR, r[0] + u + al, r[3] - dp]];
    if (w === "w") return [[r[0], r[1] + u, r[0] + dp, r[1] + u + al], [r[0] + dp, r[1] + u, r[0] + dp + CLR, r[1] + u + al]];
    return [[r[2] - dp, r[1] + u, r[2], r[1] + u + al], [r[2] - dp - CLR, r[1] + u, r[2] - dp, r[1] + u + al]];
  }
  function doorZones(L, r) {
    const z = [];
    (L.doors || []).forEach(d => {
      const th = d.th || T;
      if (d.o === "h") { if (d.x + d.w <= r[0] || d.x >= r[2]) return;
        if (Math.abs(d.y + th - r[1]) < 6) z.push([d.x, r[1], d.x + d.w, r[1] + d.w]); else if (Math.abs(d.y - r[3]) < 6) z.push([d.x, r[3] - d.w, d.x + d.w, r[3]]); }
      else { if (d.y + d.w <= r[1] || d.y >= r[3]) return;
        if (Math.abs(d.x + th - r[0]) < 6) z.push([r[0], d.y, r[0] + d.w, d.y + d.w]); else if (Math.abs(d.x - r[2]) < 6) z.push([r[2] - d.w, d.y, r[2], d.y + d.w]); }
    });
    return z;
  }
  function bathLayout(L, r, list) {   // list: [{j, sp}] -> best [{j, sp, w, box}] or null
    const inR = b => b[0] >= r[0] - 0.5 && b[1] >= r[1] - 0.5 && b[2] <= r[2] + 0.5 && b[3] <= r[3] + 0.5;
    const dz = doorZones(L, r), ord = list.slice().sort((a, b) => b.sp.al * b.sp.dp - a.sp.al * a.sp.dp);
    let best = null, bestC = 1e12;
    const go = (k, placed, cost) => {
      if (cost >= bestC) return;
      if (k === ord.length) { best = placed.slice(); bestC = cost; return; }
      const { sp } = ord[k];
      for (const w of DIRS) {
        const H = w === "n" || w === "s", len = H ? r[2] - r[0] : r[3] - r[1], o0 = H ? r[0] : r[1], max = len - sp.al; if (max < -0.5) continue;
        const us = new Set([0, max, (H ? sp.c[0] : sp.c[1]) - o0 - sp.al / 2]);
        placed.forEach(P => [P.box, P.clr].forEach(b => { const a0 = H ? b[0] : b[1], a1 = H ? b[2] : b[3]; us.add(a1 - o0); us.add(a0 - o0 - sp.al); }));
        dz.forEach(b => { const a0 = H ? b[0] : b[1], a1 = H ? b[2] : b[3]; us.add(a1 - o0); us.add(a0 - o0 - sp.al); });
        for (let u of us) {
          u = Math.max(0, Math.min(max, u)); u = Math.round(u * 2) / 2;
          const [box, clr] = bathBox(sp, r, w, u);
          if (!inR(box) || !inR(clr)) continue;
          if (dz.some(z => ovl(z, box)) || dz.some(z => ovl(z, clr) && false)) continue;
          if (placed.some(P => ovl(P.box, box) || ovl(P.clr, box) || ovl(P.box, clr))) continue;
          const c = [(box[0] + box[2]) / 2, (box[1] + box[3]) / 2], cc = cost + Math.hypot(c[0] - sp.c[0], c[1] - sp.c[1]) + (w === sp.wall ? 0 : 800);
          placed.push({ j: ord[k].j, sp, w, box, clr }); go(k + 1, placed, cc); placed.pop();
        }
      }
    };
    go(0, [], 0);
    return best;
  }
  function bathEntry(P, r) {
    const { sp, w, box } = P, q = sp.q, cx = (box[0] + box[2]) / 2, cy = (box[1] + box[3]) / 2, n = q[0], f1 = v => +v.toFixed(1);
    if (sp.t === "toilet") { const e = w === "e" ? [n, f1(r[2]), f1(cy), 1, "e"] : w === "w" ? [n, f1(r[0]), f1(cy), 1, "w"] : w === "n" ? [n, f1(cx), f1(r[1]), 1] : [n, f1(cx), f1(r[3]), -1]; if (q[5] === "k") { while (e.length < 5) e.push(null); e.push("k"); } return e; }
    if (sp.t === "basin") return [n, f1(box[0]), f1(box[1]), f1(box[2] - box[0]), f1(box[3] - box[1]), w, ...q.slice(6)];
    if (sp.t === "shower") { const g = []; if (box[1] > r[1] + 1) g.push("n"); if (box[3] < r[3] - 1) g.push("s"); if (box[0] > r[0] + 1) g.push("w"); if (box[2] < r[2] - 1) g.push("e"); return [n, f1(box[0]), f1(box[1]), q[3], g, ...q.slice(5)]; }
    const inner = [n, f1(cx - 300), f1(cy - 300), ...q.slice(3)], deg = { n: 0, e: 90, s: 180, w: 270 }[w];
    return deg ? ["_rot", deg, f1(cx), f1(cy), inner] : inner;
  }
  // N: jaunais modelis pēc sienas pārbīdes; telpām, kas mainījās, santehniku izkārto no jauna (ja esošā vieta der, paliek)
  function bathFix(N) {
    let bad = false;
    ["main", "loft"].forEach(l => {
      const L = lv(l, N), L0 = lv(l, M); if (!L || !L0 || !L.rooms || !L0.rooms) return;
      L.rooms.forEach((rm, i) => {
        const rm0 = L0.rooms[i]; if (!rm0 || rm.r.length !== 1 || rm0.r.length !== 1) return;
        const a = rm.r[0], b0 = rm0.r[0]; if (a.every((v, k) => Math.abs(v - b0[k]) < 0.5)) return;
        const r = [a[0], a[1], a[0] + a[2], a[1] + a[3]], r0 = [b0[0], b0[1], b0[0] + b0[2], b0[1] + b0[3]];
        const list = [];
        (L0.furniture || []).forEach((f, j) => { const s0 = bathSpec(f); if (!s0) return; if (s0.c[0] < r0[0] || s0.c[0] > r0[2] || s0.c[1] < r0[1] || s0.c[1] > r0[3]) return; const sp = bathSpec(L.furniture[j]); if (sp) list.push({ j, sp }); });
        if (!list.length) return;
        const res = bathLayout(L, r, list);
        if (!res) { bad = true; return; }
        res.forEach(P => { L.furniture[P.j] = bathEntry(P, r); });
      });
    });
    return bad;
  }
  // furniture does not go into other furniture: push out of the nearest overlap, and close a small gap
  const NOCOL = ["Ln", "chair", "stool", "Pth", "Tx"];
  function collide(l, b, dx, dy, boxes, group, rm, fresh) {
    const L = lv(l), F2 = 120, inR = q => !rm || (q[0] >= rm[0] - 1 && q[1] >= rm[1] - 1 && q[2] <= rm[2] + 1 && q[3] <= rm[3] + 1);
    let nb = [b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy];
    const others = Object.entries(boxes || {}).filter(([j, o]) => !group.includes(+j) && !NOCOL.includes((baseF(L.furniture[+j]) || [""])[0])
      && !(!fresh && o[0] <= b[0] + 1 && o[1] <= b[1] + 1 && o[2] >= b[2] - 1 && o[3] >= b[3] - 1)).map(e => e[1]);   // ja jau stāv uz tās (paklājs), neatgrūž
    for (let pass = 0; pass < 3; pass++) {
      let moved = false;
      for (const o of others) {
        const ox = Math.min(nb[2], o[2]) - Math.max(nb[0], o[0]), oy = Math.min(nb[3], o[3]) - Math.max(nb[1], o[1]);
        if (ox <= 1 || oy <= 1) continue;
        const cs = [[o[0] - nb[2], 0], [o[2] - nb[0], 0], [0, o[1] - nb[3]], [0, o[3] - nb[1]]].sort((a, b2) => Math.abs(a[0] + a[1]) - Math.abs(b2[0] + b2[1]));
        const c = cs.find(q => inR([nb[0] + q[0], nb[1] + q[1], nb[2] + q[0], nb[3] + q[1]])) || cs[0];   // tikai tā, lai paliek telpā
        nb = [nb[0] + c[0], nb[1] + c[1], nb[2] + c[0], nb[3] + c[1]]; moved = true;
      }
      if (!moved) break;
    }
    for (const o of others) {   // pielīp pie blakus mēbeles, ja sprauga mazāka par 120 mm
      const ovY = Math.min(nb[3], o[3]) - Math.max(nb[1], o[1]) > 0, ovX = Math.min(nb[2], o[2]) - Math.max(nb[0], o[0]) > 0;
      if (ovY) { const g1 = o[0] - nb[2], g2 = nb[0] - o[2]; if (g1 > 0 && g1 < F2 && !(rm && nb[0] - rm[0] < 1)) { nb[0] += g1; nb[2] += g1; } else if (g2 > 0 && g2 < F2 && !(rm && rm[2] - nb[2] < 1)) { nb[0] -= g2; nb[2] -= g2; } }
      if (ovX) { const g1 = o[1] - nb[3], g2 = nb[1] - o[3]; if (g1 > 0 && g1 < F2 && !(rm && nb[1] - rm[1] < 1)) { nb[1] += g1; nb[3] += g1; } else if (g2 > 0 && g2 < F2 && !(rm && rm[3] - nb[3] < 1)) { nb[1] -= g2; nb[3] -= g2; } }
    }
    return [+(nb[0] - b[0]).toFixed(1), +(nb[1] - b[1]).toFixed(1)];
  }
  // mēra gals pielīp sienas virsmai (telpas malai) tuvāk par 120 mm
  // mēra gals pielīp: sienu virsmām, ārsienu ārmalai, logu un durvju malām, asīm; citur solis 10 mm
  function snapPts(l, axis) {
    const X = axis === "x", L = lv(l), c = rects(l).flatMap(q => (X ? [q[0], q[2]] : [q[1], q[3]]));
    c.push(0, X ? M.W : M.D);
    (M.posts || []).forEach(q => c.push(X ? q.x : q.y, X ? q.x + q.w : q.y + q.d));   // stabu malas
    (M.terraces || []).forEach(t => t.poly.forEach(q => c.push(X ? q[0] : q[1])));   // terases stūri
    (L.windows || []).forEach(w => { if ((w.o === "h") === X) c.push(X ? w.x : w.y, (X ? w.x : w.y) + w.len); });
    (L.doors || []).forEach(d => { if ((d.o === "h") === X) c.push(X ? d.x : d.y, (X ? d.x : d.y) + d.w); });
    ((M.axes || {})[axis] || []).forEach(a => c.push(a[0]));
    GUIDES().forEach(g => { if ((g.o === "v" && X) || (g.o === "h" && !X)) c.push(g.at); });   // palīglīnijas: viegli pielīp
    return c;
  }
  function furnEdges(l, axis) {   // mēbeļu malas (mēram un sienu galiem)
    const bl = blocks().find(b => b.type === "plan" && b.lv === l); if (!bl) return [];
    let bx; try { bx = furnBoxes(bl); } catch (_) { return []; }
    return Object.values(bx).flatMap(q => axis === "x" ? [q[0], q[2]] : [q[1], q[3]]);
  }
  function snapI(l, axis, v, rad = 150) {
    let best = null; snapPts(l, axis).concat(furnEdges(l, axis)).forEach(t => { if (Math.abs(t - v) < rad && (best == null || Math.abs(t - v) < Math.abs(best - v))) best = t; });
    return best != null ? { v: best, hit: true } : { v: r10(v), hit: false };
  }
  function snapAx(l, axis, v, rad = 150) {
    let best = null; snapPts(l, axis).concat(furnEdges(l, axis)).forEach(t => { if (Math.abs(t - v) < rad && (best == null || Math.abs(t - v) < Math.abs(best - v))) best = t; });
    return best != null ? best : r10(v);
  }
  // keep a box inside the room it stands in, and pull it flush to a wall that is closer than SNAP
  function fit(l, b, dx, dy, free) {
    const nb = [b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy], c = [(nb[0] + nb[2]) / 2, (nb[1] + nb[3]) / 2];
    const R = rects(l);
    let r = R.find(q => c[0] >= q[0] && c[0] <= q[2] && c[1] >= q[1] && c[1] <= q[3]);
    if (!r) { let bd = 1e12; R.forEach(q => { const d = Math.hypot(Math.max(q[0] - c[0], 0, c[0] - q[2]), Math.max(q[1] - c[1], 0, c[1] - q[3])); if (d < bd) { bd = d; r = q; } }); }
    if (!r) return [dx, dy, null];
    const w = nb[2] - nb[0], h = nb[3] - nb[1];
    // a room made of several rectangles (L shape): allow the piece to reach into the neighbour rectangle
    const ext = R.filter(q => q !== r && ((Math.abs(q[0] - r[0]) < 2 && Math.abs(q[2] - r[2]) < 2) || (Math.abs(q[1] - r[1]) < 2 && Math.abs(q[3] - r[3]) < 2)));
    void ext;
    let x0 = nb[0], y0 = nb[1];
    if (w <= r[2] - r[0]) { x0 = Math.max(r[0], Math.min(r[2] - w, x0)); if (!free) { if (x0 - r[0] < SNAP) x0 = r[0]; else if (r[2] - (x0 + w) < SNAP) x0 = r[2] - w; } }
    if (h <= r[3] - r[1]) { y0 = Math.max(r[1], Math.min(r[3] - h, y0)); if (!free) { if (y0 - r[1] < SNAP) y0 = r[1]; else if (r[3] - (y0 + h) < SNAP) y0 = r[3] - h; } }
    return [x0 - b[0], y0 - b[1], r];
  }
  // pagriež mēbeli (un to, kas uz tās) ap tās centru par deg grādiem; pēc tam atpakaļ telpā
  const rotPt = (p, c, deg) => { const r = deg * Math.PI / 180, x = p[0] - c[0], y = p[1] - c[1]; return [c[0] + x * Math.cos(r) - y * Math.sin(r), c[1] + x * Math.sin(r) + y * Math.cos(r)]; };
  const rotBox = (b, c, deg) => { const q = [[b[0], b[1]], [b[2], b[1]], [b[0], b[3]], [b[2], b[3]]].map(p => rotPt(p, c, deg)); return [Math.min(...q.map(p => p[0])), Math.min(...q.map(p => p[1])), Math.max(...q.map(p => p[0])), Math.max(...q.map(p => p[1]))]; };
  function rotate(N, l, i, boxes, deg = 90) {
    const L = lv(l, N), b = boxes[i]; if (!b || !deg) return N;
    const c = [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2];
    const turn = j => {
      const f = L.furniture[j];
      if (f[0] === "_rot" && Math.abs(f[2] - c[0]) < 1 && Math.abs(f[3] - c[1]) < 1) { f[1] = (((f[1] + deg) % 360) + 360) % 360; if (!f[1]) L.furniture[j] = f[4]; }
      else L.furniture[j] = ["_rot", (deg + 360) % 360, +c[0].toFixed(1), +c[1].toFixed(1), f];
    };
    const grp = [i, ...contained(boxes, i)];
    grp.forEach(turn);
    const [dx, dy] = fit(l, rotBox(b, c, deg), 0, 0);
    if (dx || dy) grp.forEach(j => shiftF(L.furniture[j], dx, dy));
    return N;
  }

  // ---- walls: move every coordinate that lies in the wall, and the rooms on both sides stretch with it ----
  function mapModel(N, axis, f) {
    const X = axis === "x", one = (o, k) => { if (o && typeof o[k] === "number") o[k] = +f(o[k]).toFixed(1); };
    const rr = q => { const a = X ? 0 : 1, s = X ? 2 : 3, v0 = f(q[a]), v1 = f(q[a] + q[s]); q[a] = +v0.toFixed(1); q[s] = +(v1 - v0).toFixed(1); };
    const furn = fl => (fl || []).forEach(F => {
      if (F[0] === "_rot") { F[X ? 2 : 3] = +f(F[X ? 2 : 3]).toFixed(1); furn([F[4]]); return; }
      F[X ? 1 : 2] = +f(F[X ? 1 : 2]).toFixed(1);
      if (F[0] === "Ln") F[X ? 3 : 4] = +f(F[X ? 3 : 4]).toFixed(1);
    });
    const level = L => {
      if (!L) return;
      (L.rooms || []).forEach(rm => rm.r.forEach(rr));
      (L.doors || []).forEach(d => one(d, X ? "x" : "y"));
      (L.windows || []).forEach(w => one(w, X ? "x" : "y"));
      furn(L.furniture);
      if (L.levelAt) L.levelAt[X ? 0 : 1] = +f(L.levelAt[X ? 0 : 1]).toFixed(1);
    };
    level(N); level(N.loft);
    if (N.axes && N.axes[axis]) N.axes[axis].forEach(a => { a[0] = +f(a[0]).toFixed(1); });
    (N.innerDims || []).forEach(d => { if (d[0] !== axis) d[1] = +f(d[1]).toFixed(1); });
    if (!X) (N.gableWins || []).forEach(g => { g.u0 = +f(g.u0).toFixed(1); g.u1 = +f(g.u1).toFixed(1); });
  }
  function stamps(N0, N) {   // room names follow their room's centre
    [[N0, N], [N0.loft, N.loft]].forEach(([A, B]) => {
      if (!A || !B || !B.stampAt) return;
      (B.rooms || []).forEach((rm, i) => {
        const bx = r => { const q = r.r; return [Math.min(...q.map(t => t[0])), Math.min(...q.map(t => t[1])), Math.max(...q.map(t => t[0] + t[2])), Math.max(...q.map(t => t[1] + t[3]))]; };
        const a = bx(A.rooms[i]), b = bx(rm), s = B.stampAt[i];
        if (s) { s[0] = +(s[0] + ((b[0] + b[2]) - (a[0] + a[2])) / 2).toFixed(1); s[1] = +(s[1] + ((b[1] + b[3]) - (a[1] + a[3])) / 2).toFixed(1); }
      });
    });
  }
  function bandList(X) {   // visas iekšējās sienas josla: [ass, biezums, no, līdz]
    const R = roomRects(X), out = [];
    for (const a of R) for (const b of R) for (const ax of ["x", "y"]) {
      const A = a.b, B = b.b, g0 = ax === "x" ? A[2] : A[3], g1 = ax === "x" ? B[0] : B[1];
      if (g1 - g0 < 100 || g1 - g0 > 300) continue;
      const v0 = ax === "x" ? Math.max(A[1], B[1]) : Math.max(A[0], B[0]), v1 = ax === "x" ? Math.min(A[3], B[3]) : Math.min(A[2], B[2]); if (v1 - v0 < 50) continue;
      out.push(Math.round(g1 - g0) + ax);
    }
    return out.sort();
  }
  function sameBands(A, B) { const a = bandList(A).join(), b = bandList(B).join(); return a === b; }
  function moveWall(w, d) {
    d = +(+d).toFixed(1); if (!d) return null;   // izsaucēji jau noapaļo; pielipinot citai sienai jāpaliek precīzi
    const N = clone(M), X = w.axis === "x", inW = v => v >= w.lo - 1 && v <= w.hi + 1, origin = w.lo <= 0;
    const f = origin ? (v => (inW(v) ? v : v - d)) : (v => (inW(v) ? v + d : v));
    mapModel(N, w.axis, f);
    const key = X ? "W" : "D", old = N[key];
    N[key] = +(origin ? old - d : (w.hi >= old - 1 ? old + d : old)).toFixed(1);
    if (N.poly) N.poly = null;
    if (!X && N[key] !== old) {   // jumta kore paliek tajā pašā augstumā; piecstūra logs paliek kores asī
      const t = Math.tan(((N.jumts && N.jumts.pitch) || 25) * Math.PI / 180);
      if (N.jumts && N.jumts.eave) N.jumts.eave = Math.round(N.jumts.eave - (N[key] - old) / 2 * t);
      (N.gableWins || []).forEach(g => { if (!g.win && g.u0 < old / 2 && g.u1 > old / 2) { const h = (g.u1 - g.u0) / 2; g.u0 = +(N.D / 2 - h).toFixed(1); g.u1 = +(N.D / 2 + h).toFixed(1); const lw = (N.loft && N.loft.windows || []).find(q => q.side === g.side && q.shape === "gable" && q.y < old / 2 && q.y + q.len > old / 2); if (lw) { lw.y = g.u0; } } });
    }
    if (N.ievade) { if (X) N.ievade.garums = N.W; else N.ievade.platums = N.D; }
    // par šauru kļūst tikai tas, kas pirms pārbīdes nebija šaurs (izgrieztas atveres ir 195 mm joslas, tās neskaita)
    const bad = [[N, M], [N.loft, M.loft]].some(([A, B]) => A && B && (A.rooms || []).some((rm, ri) => rm.r.some((q, qi) => { const o = (((B.rooms || [])[ri] || {}).r || [])[qi] || q; return (q[2] < MINR && o[2] >= MINR) || (q[3] < MINR && o[3] >= MINR); })));
    if (bad) return null;
    if (!w.ext && !sameBands(M, N)) return null;   // citu sienu biezums nedrīkst mainīties
    stamps(M, N);
    return N;
  }

  // ---- edits (on a copy of the model) ----
  function syncGw(N, gi) {
    const gw = N.gableWins[gi], lw = loftFor(M.gableWins[gi], N);
    if (!lw) return;
    lw.y = gw.u0; lw.len = gw.u1 - gw.u0; lw.sill = gw.z0; if (gw.z1) lw.head = gw.z1;
  }
  function syncLoftWin(N, wi) {
    const lw = N.loft.windows[wi], gw = (N.gableWins || []).find(g => gwMatch(g, M.loft.windows[wi]));
    if (!gw) return;
    gw.u0 = lw.y; gw.u1 = lw.y + lw.len;
  }
  // Ctrl (vai Cmd) + vilkšana: kopija; oriģināls paliek vietā
  // atlasīta grupa (Shift+klikšķis): pārvieto vai (ar Ctrl) nokopē visus kopā; logi un durvis pa savu sienu, mēbeles brīvi
  const GRP = ["furn", "win", "door"];
  function applyGrp(d, dx, dy) {
    const N = clone(M), q = { x: r10(dx), y: r10(dy) }, out = [];
    d.grp.forEach(s => {
      const L = lv(s.lv, N), arr = L[s.k === "furn" ? "furniture" : s.k === "win" ? "windows" : "doors"];
      let o = arr[s.i], idx = s.i;
      if (d.copy) { o = clone(o); arr.push(o); idx = arr.length - 1; }
      if (s.k === "furn") shiftF(o, q.x, q.y);
      else { const ax = o.o === "h" ? "x" : "y", len = s.k === "win" ? o.len : o.w, lim = o.o === "h" ? M.W : M.D; o[ax] = +Math.max(T, Math.min(lim - T - len, o[ax] + (o.o === "h" ? q.x : q.y))).toFixed(1); }
      out.push({ k: s.k, i: idx, lv: s.lv });
    });
    d.ghost = out; d.fdx = q.x; d.fdy = q.y; return N;
  }
  function pasteGrp(list) {   // Ctrl+V: iekopē nokopētos elementus ar nobīdi
    const N = clone(M), out = [];
    list.forEach(c => {
      const L = lv(c.lv, N), arr = L[c.k === "furn" ? "furniture" : c.k === "win" ? "windows" : "doors"], o = clone(c.o);
      if (c.k === "furn") shiftF(o, 200, 200);
      else { const ax = o.o === "h" ? "x" : "y", len = c.k === "win" ? o.len : o.w, lim = o.o === "h" ? M.W : M.D; o[ax] = +Math.max(T, Math.min(lim - T - len, o[ax] + 300)).toFixed(1); }
      arr.push(o); out.push({ k: c.k, i: arr.length - 1, lv: c.lv });
    });
    return { N, sel: Object.assign({}, out[0], { more: out.slice(1) }) };
  }
  function delGrp() {
    const N = clone(M), all = [sel, ...(sel.more || [])];
    ["furn", "win", "door"].forEach(k => {
      const idx = all.filter(s => s.k === k).map(s => s.i).sort((a, b) => b - a), L = lv(sel.lv, N), arr = L[k === "furn" ? "furniture" : k === "win" ? "windows" : "doors"];
      idx.forEach(i => arr.splice(i, 1));
    });
    sel = null; post({ t: "edit", model: N, sel: null });
  }
  // stabu satveršanas punkti kā SketchUp: 4 stūri, 4 malu vidi, centrs
  const gpts = b => { const x = [b[0], (b[0] + b[2]) / 2, b[2]], y = [b[1], (b[1] + b[3]) / 2, b[3]]; return y.flatMap(v => x.map(u => [u, v])); };
  const nearestGrab = (b, p) => gpts(b).reduce((r, q) => (Math.hypot(q[0] - p[0], q[1] - p[1]) < r.d ? { d: Math.hypot(q[0] - p[0], q[1] - p[1]), q } : r), { d: 1e12, q: null }).q;
  // punkti, pie kuriem var pielipt un ko var izmantot par atsauci: mājas un telpu stūri, asu krustpunkti, terases / lievena stūri, citu stabu punkti
  function refPoints(skip) {
    const out = [[0, 0], [M.W, 0], [M.W, M.D], [0, M.D]];
    (M.poly || []).forEach(q => out.push([q[0], q[1]]));
    rects("main").forEach(q => out.push([q[0], q[1]], [q[2], q[1]], [q[2], q[3]], [q[0], q[3]]));
    const ax = (M.axes || {}); (ax.x || []).forEach(a => (ax.y || []).forEach(c => out.push([a[0], c[0]])));
    (M.terraces || []).forEach(t => t.poly.forEach(q => out.push([q[0], q[1]])));
    ((M.porch && M.porch.poly) || []).forEach(q => out.push([q[0], q[1]]));
    (M.posts || []).forEach((q, i) => { if (i !== skip) gpts([q.x, q.y, q.x + q.w, q.y + q.d]).forEach(g => out.push(g)); });
    return out;
  }
  // mērķa punkta pielipšana: vispirms punkti (abas ass reizē), tad atsevišķi x un y (palīglīnijas, malas, atsauces)
  function snapTarget(d, tx, ty, lock, skip) {
    const m = d.h.bl.g.getScreenCTM(), thr = m && m.a ? 12 / Math.abs(m.a) : 120, refs = d.refs || [], res = { x: null, y: null, pt: null };
    const P = refPoints(skip).concat(refs);
    if (!lock) { let bd = thr; P.forEach(q => { const e = Math.hypot(q[0] - tx, q[1] - ty); if (e < bd) { bd = e; res.pt = q; } }); if (res.pt) { res.x = res.pt[0]; res.y = res.pt[1]; return res; } }
    const best = (axis, v) => { let b = null, bd = thr; snapPts("main", axis).concat(refs.map(q => q[axis === "x" ? 0 : 1]), P.map(q => q[axis === "x" ? 0 : 1])).forEach(c => { if (Math.abs(c - v) < bd) { bd = Math.abs(c - v); b = c; } }); return b; };
    if (lock !== "y") res.x = best("x", tx); if (lock !== "x") res.y = best("y", ty);
    if (lock === "x") res.y = null; if (lock === "y") res.x = null;
    return res;
  }
  function applyC(d, dx, dy) {
    if (d.grp && d.zone === "move") return applyGrp(d, dx, dy);
    if (!d.copy || d.zone !== "move") return apply(d, dx, dy);
    if (!d.it0) { d.it0 = d.h.it; d.b0 = d.boxes; }
    const it = d.it0, key = it.k === "furn" ? "furniture" : it.k === "win" ? "windows" : it.k === "post" ? "posts" : "doors", L = it.k === "post" ? M : lv(it.lv), arr = L[key];
    const ni = arr.length; arr.push(clone(arr[it.i]));
    d.h = Object.assign({}, d.h, { it: Object.assign({}, it, { i: ni }) });
    if (d.b0) { d.boxes = Object.assign({}, d.b0, { [ni]: d.b0[it.i] }); delete d.boxes[it.i]; }
    let N; try { N = apply(d, dx, dy); } finally { arr.pop(); }
    d.cpI = ni; return N;
  }
  // palīglīnijas pievilkšana vilkšanas laikā: vals = elementa malas/centrs attiecīgajā ass virzienā; atgriež labojumu mm vai null
  function gSnap(d, axis, vals) {
    const m = d.h.bl.g.getScreenCTM(), thr = m && m.a ? 9 / Math.abs(m.a) : 60;
    let best = null;
    GUIDES().forEach(g => { if (!((g.o === "v" && axis === "x") || (g.o === "h" && axis === "y"))) return; vals.forEach(v => { const df = g.at - v; if (Math.abs(df) <= thr && (best == null || Math.abs(df) < Math.abs(best.df))) best = { df, at: g.at }; }); });
    return best;
  }
  // visas pārējās iekšējās sienas vienā virzienā: [lo, hi] (lai pārbīdot siena nostātos vienā taisnē ar citu)
  function wallBands(axis, skip) {
    const R = roomRects(M), out = [], seen = new Set();
    for (const a of R) for (const b of R) {
      const A = a.b, B = b.b, X = axis === "x", g0 = X ? A[2] : A[3], g1 = X ? B[0] : B[1];
      if (g1 - g0 < 100 || g1 - g0 > 300) continue;
      const ov = X ? Math.min(A[3], B[3]) - Math.max(A[1], B[1]) : Math.min(A[2], B[2]) - Math.max(A[0], B[0]); if (ov < 50) continue;
      if (Math.abs(g0 - skip.lo) < 1) continue;
      const k = Math.round(g0) + "|" + Math.round(g1); if (seen.has(k)) continue; seen.add(k); out.push([g0, g1]);
    }
    return out;
  }
  function apply(d, dx, dy) {
    const it = d.h.it, z = d.zone;
    if (z === "wx" || z === "wy") {
      let q = r10(z === "wx" ? dx : dy); const w = it.w, ax = z === "wx" ? "x" : "y", sn = gSnap(d, ax, [w.lo + q, w.hi + q, (w.lo + w.hi) / 2 + q]);
      let al = null;   // pievilkšana citai sienai: abas vienā taisnē
      if (!w.ext && d.shift) wallBands(w.axis, w).forEach(([l2, h2]) => [[l2 - w.lo], [h2 - w.hi], [(l2 + h2) / 2 - (w.lo + w.hi) / 2]].forEach(([df]) => { const t = (() => { const m = d.h.bl.g.getScreenCTM(); return m && m.a ? 12 / Math.abs(m.a) : 80; })(); const e = df - q; if (Math.abs(e) <= t && (!al || Math.abs(e) < Math.abs(al.e))) al = { e, at: (l2 + h2) / 2 }; }));
      if (al && (!sn || Math.abs(al.e) <= Math.abs(sn.df))) { q = +(q + al.e).toFixed(1); d.wd = q; d.snapLine = [ax === "x" ? "y" : "x", al.at]; return moveWall(w, q); }
      if (sn) q = +(q + sn.df).toFixed(1);
      d.wd = q; d.snapLine = sn ? [ax === "x" ? "y" : "x", sn.at] : null;
      return moveWall(w, q);
    }
    const N = clone(M);
    if (d.h.bl.type === "plan") {
      const L = lv(it.lv, N);
      if (it.k === "post") {
        const q = N.posts[it.i], b0 = [q.x, q.y, q.x + q.w, q.y + q.d], gp = d.gp0 || [q.x + q.w / 2, q.y + q.d / 2];
        let ddx = dx, ddy = dy, lock = null;
        if (d.shift) { if (Math.abs(dx) >= Math.abs(dy)) { ddy = 0; lock = "x"; } else { ddx = 0; lock = "y"; } }
        let tx = gp[0] + r10(ddx), ty = gp[1] + r10(ddy), si = null;
        if (!d.nudge) { si = snapTarget(d, gp[0] + ddx, gp[1] + ddy, lock, it.i); if (si.x != null) tx = si.x; if (si.y != null) ty = si.y; }
        d.snapInfo = si;
        const mx = r10(tx - gp[0]) === tx - gp[0] ? tx - gp[0] : +(tx - gp[0]).toFixed(1), my = +(ty - gp[1]).toFixed(1);
        q.x = +(q.x + mx).toFixed(1); q.y = +(q.y + my).toFixed(1); d.fdx = mx; d.fdy = my; return N;
      }
      if (it.k === "ter") {
        const t = N.terraces[it.i], sx = r10(dx), sy = r10(dy);
        t.poly = t.poly.map(q => [q[0] + sx, q[1] + sy]); if (t.posts) t.posts = t.posts.map(q => [q[0] + sx, q[1] + sy, q[2]]);
        d.fdx = sx; d.fdy = sy; return N;
      }
      if (it.k === "tvert") {   // stūris: kaimiņu malas paliek paralēlas asīm
        const t = N.terraces[Math.floor(it.i / 100)], n = t.poly.length, j = it.i % 100, v = t.poly[j], pv = t.poly[(j + n - 1) % n], nx = t.poly[(j + 1) % n];
        const hp = Math.abs(pv[1] - v[1]) < 1, vp = Math.abs(pv[0] - v[0]) < 1, hn = Math.abs(nx[1] - v[1]) < 1, vn = Math.abs(nx[0] - v[0]) < 1;
        let tx = v[0] + dx, ty = v[1] + dy; if (d.shift) { if (Math.abs(dx) > Math.abs(dy)) ty = v[1]; else tx = v[0]; }
        const ix = snapAx("main", "x", tx, 150), iy = snapAx("main", "y", ty, 150);
        if (hp) pv[1] = iy; if (vp) pv[0] = ix; if (hn) nx[1] = iy; if (vn) nx[0] = ix;
        v[0] = ix; v[1] = iy; d.fdx = ix - it.b[0] - (it.b[2] - it.b[0]) / 2; d.fdy = 0; return N;
      }
      if (it.k === "tedge") {   // mala pa x vai y asi (pielīp mājas elementiem); slīpu malu bīda brīvi
        const t = N.terraces[Math.floor(it.i / 100)], n = t.poly.length, a = t.poly[it.i % 100], b = t.poly[(it.i % 100 + 1) % n];
        if (Math.abs(a[1] - b[1]) < 1) { const ny = snapAx("main", "y", a[1] + dy, 150); d.fdx = 0; d.fdy = ny - a[1]; a[1] = b[1] = ny; }
        else if (Math.abs(a[0] - b[0]) < 1) { const nx = snapAx("main", "x", a[0] + dx, 150); d.fdx = nx - a[0]; d.fdy = 0; a[0] = b[0] = nx; }
        else { a[0] += r10(dx); a[1] += r10(dy); b[0] += r10(dx); b[1] += r10(dy); d.fdx = r10(dx); d.fdy = r10(dy); }
        return N;
      }
      if (it.k === "axo") {
        const o = N.axOff = Object.assign({}, axO(M)), sg = it.i === "n" || it.i === "w" ? -1 : 1, dv = it.i === "n" || it.i === "s" ? dy : dx;
        o[it.i] = Math.max(1200, r10(o[it.i] + sg * dv)); d.fdx = r10(dx); d.fdy = r10(dy); return N;
      }
      if (it.k === "stamp") {
        const L2 = lv(it.lv, N), s0 = (L2.stampAt = L2.stampAt || {})[it.i];
        const c = s0 || [(it.b[0] + it.b[2]) / 2, (it.b[1] + it.b[3]) / 2];
        L2.stampAt[it.i] = [+(c[0] + r10(dx)).toFixed(1), +(c[1] + r10(dy)).toFixed(1)];
        d.fdx = r10(dx); d.fdy = r10(dy);
        return N;
      }
      if (it.k === "idim") {
        const arr = idimsOwn(it.lv, N), dm = arr[it.i], sn = snapAt(it.lv, dm[0], dm[1] + (dm[0] === "x" ? dy : dx), it);
        dm[1] = +sn.v.toFixed(1); d.snapLine = sn.hit ? [dm[0], dm[1]] : null; return N;
      }
      if (it.k === "dim") {
        const dm = L.userDims[it.i], X = dm[0] === "x", par = X ? dx : dy, per = X ? dy : dx;
        if (z === "move") { const sn = snapAt(it.lv, dm[0], dm[1] + per, it); dm[1] = +sn.v.toFixed(1); d.snapLine = sn.hit ? [dm[0], dm[1]] : null; }
        else if (z === "l" || z === "t") dm[2] = Math.min(snapAx(it.lv, dm[0], dm[2] + par), dm[3] - 100);
        else dm[3] = Math.max(snapAx(it.lv, dm[0], dm[3] + par), dm[2] + 100);
        return N;
      }
      if (it.k === "furn") {
        const grp = [it.i, ...contained(d.boxes, it.i)];
        if (z !== "move") {
          const r = resizeFurn(N, it.lv, it.i, it.b, z, z === "l" || z === "r" ? dx : dy);
          if (!r) return null; d.nb = r.nb; return r.N;
        }
        if (d.nudge) {   // bultiņas: tieši pa 10 / 100 mm, bez pielipšanas un atgrūšanas, tikai paliek telpā
          const [nx, ny] = fit(it.lv, it.b, dx, dy, true);
          grp.forEach(j => shiftF(L.furniture[j], nx, ny)); d.fdx = nx; d.fdy = ny; return N;
        }
        const ws = wallSnap(N, it.lv, it, d, dx, dy, grp);
        if (ws) { d.nb = ws.nb; d.back = ws.side; return N; }
        d.nb = null; d.back = null;
        let [fx, fy, rm] = fit(it.lv, it.b, r10(dx), r10(dy));
        [fx, fy] = collide(it.lv, it.b, fx, fy, d.boxes, grp, rm);
        {   // pielīp palīglīnijām (malas vai centrs)
          const b0 = it.b, sx = gSnap(d, "x", [b0[0] + fx, b0[2] + fx, (b0[0] + b0[2]) / 2 + fx]), sy = gSnap(d, "y", [b0[1] + fy, b0[3] + fy, (b0[1] + b0[3]) / 2 + fy]);
          if (sx || sy) { let [gx, gy] = fit(it.lv, it.b, fx + (sx ? sx.df : 0), fy + (sy ? sy.df : 0)); [gx, gy] = collide(it.lv, it.b, gx, gy, d.boxes, grp, rm); fx = gx; fy = gy; }
        }
        grp.forEach(j => shiftF(L.furniture[j], fx, fy));
        d.fdx = fx; d.fdy = fy;
        return N;
      }
      const o = it.k === "win" ? L.windows[it.i] : L.doors[it.i], lk = it.k === "win" ? "len" : "w", len = o[lk];
      const key = o.o === "h" ? "x" : "y", lim = o.o === "h" ? M.W : M.D, dd = o.o === "h" ? dx : dy, q = r10(dd), mn = it.k === "win" ? 300 : 600;
      if (z === "l" || z === "t") { const a = Math.max(T, Math.min(o[key] + len - mn, o[key] + q)); o[lk] = +(o[key] + len - a).toFixed(1); o[key] = a; }
      else if (z === "r" || z === "b") o[lk] = Math.max(mn, Math.min(lim - T - o[key], len + q));
      else {
        let v = o[key] + q; v = Math.max(T, Math.min(lim - T - len, v));
        d.snapLine = null;
        if (!d.alt && !d.nudge) {   // logs / durvis pielīp telpas sienas vidum (ar Alt neliek)
          const c = v + len / 2, cs = wallCenters(it.lv, o, it.k === "win" ? T : o.th), best = cs.sort((a, b2) => Math.abs(a - c) - Math.abs(b2 - c))[0];
          if (best != null && Math.abs(best - c) < 220) { v = Math.max(T, Math.min(lim - T - len, +(best - len / 2).toFixed(1))); d.snapLine = [o.o === "h" ? "y" : "x", best]; }
        }
        const gs = gSnap(d, key, [v, v + len, v + len / 2]);
        if (gs) v = Math.max(T, Math.min(lim - T - len, +(v + gs.df).toFixed(1)));
        o[key] = v;
      }
      if (o.parts && o.parts.length === 2) o.parts[1].len = Math.max(200, o.len - o.parts[0].len);
      if (it.k === "win" && it.lv === "loft") syncLoftWin(N, it.i);
      return N;
    }
    if (it.k === "gut") return null;
    const s = d.h.bl.side, du = dx, dz = -dy;
    if (it.k === "door") { const o = N.doors[it.i]; o.x = Math.max(T, Math.min(M.W - T - o.w, o.x + sgn(s) * r10(du))); return N; }
    const isG = it.k === "gw", o = isG ? N.gableWins[it.i] : N.windows[it.i];
    let [u0, u1] = [it.b[0], it.b[2]];
    const q = r10(du);   // solis 10 mm; nekustinātā mala paliek, kur bija
    if (z === "move") { u0 += q; u1 += q; } else if (z === "l") u0 = Math.min(u0 + q, u1 - 300); else if (z === "r") u1 = Math.max(u1 + q, u0 + 300);
    const sp = span(s);
    if (u0 < T) { u1 += T - u0; u0 = T; } if (u1 > sp - T) { u0 -= u1 - (sp - T); u1 = sp - T; }
    d.gwMid = false;
    if (isG) {
      if (z === "b" || (z === "move" && o.win)) o.z0 = o.z0 + r10(dz);
      if (o.z0 < GWB) { if (o.z1) o.z1 += GWB - o.z0; o.z0 = GWB; }   // 2. stāva logs nav zemāk par mansarda paneļa augšu
      if (o.z1 && (z === "t" || z === "move")) o.z1 = o.z1 + r10(dz);
      if (o.z1 && o.z1 < o.z0 + 300) o.z1 = o.z0 + 300;
      if (!o.win) {
        // slīpais logs paliek gala trijstūrī (stūros var kļūt trijstūrains, ārā neiziet) un pielīp kores vidus līnijai
        const ev = (M.jumts && M.jumts.eave) || 2600, tn = Math.tan(((M.jumts && M.jumts.pitch) || 30) * Math.PI / 180), um = Math.max(T, (o.z0 + 200 - ev) / tn);
        if (um >= sp / 2 - 150) { o.z0 = Math.round(ev - 200 + (sp / 2 - 150) * tn); }
        const lo = Math.max(T, (o.z0 + 200 - ev) / tn), hi = sp - lo, mid = sp / 2, SN = 150;
        if (z === "move") { const w = Math.min(u1 - u0, hi - lo); let c = (u0 + u1) / 2; if (Math.abs(c - mid) < SN) c = mid; c = Math.max(lo + w / 2, Math.min(hi - w / 2, c)); u0 = c - w / 2; u1 = c + w / 2; }
        else if (z === "l") { if (Math.abs(u0 + u1 - sp) < 2 * SN) u0 = sp - u1; u0 = Math.max(lo, u0); }
        else if (z === "r") { if (Math.abs(u0 + u1 - sp) < 2 * SN) u1 = sp - u0; u1 = Math.min(hi, u1); }
        else { u0 = Math.max(lo, u0); u1 = Math.min(hi, u1); }
        u0 = +u0.toFixed(1); u1 = +u1.toFixed(1);
        d.gwMid = Math.abs(u0 + u1 - sp) < 1;
      }
      const a0 = Math.min(mapU(s, u0), mapU(s, u1)), a1 = Math.max(mapU(s, u0), mapU(s, u1));
      o.u0 = a0; o.u1 = a1;
      syncGw(N, it.i);
    } else {
      const a0 = Math.min(mapU(s, u0), mapU(s, u1)), a1 = Math.max(mapU(s, u0), mapU(s, u1));
      if (o.o === "h") o.x = a0; else o.y = a0; o.len = a1 - a0;
      if (o.parts && o.parts.length === 2) o.parts[1].len = Math.max(200, o.len - o.parts[0].len);
      const sill = o.sill ?? 0, head = o.head ?? 2100;
      if (z === "move" && sill > 0) { o.sill = Math.max(0, sill + r10(dz)); o.head = o.sill + (head - sill); }
      if (z === "t") o.head = Math.max(sill + 300, head + r10(dz));
      if (z === "b") o.sill = Math.max(0, Math.min(head - 300, sill + r10(dz)));
    }
    return N;
  }

  function rotGhost(d) {
    const bl = d.h.bl, k = ek(bl), o = overlay(bl.g), b = d.h.it.b;
    o.querySelectorAll(".gh").forEach(e => e.remove());
    const g = mk(o, "g", { class: "gh" });
    const q = [[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]]].map(p => rotPt(p, d.c, d.ang));
    mk(g, "polygon", { points: q.map(p => p.join(",")).join(" "), fill: "rgba(217,72,15,.10)", stroke: ACC, "stroke-width": 0.45 / k, "stroke-dasharray": `${1.4 / k} ${0.9 / k}` });
    label(g, d.c[0] + 3 / k, d.c[1] - 3 / k, (d.ang > 0 ? "+" : "") + d.ang + "°", k);
  }
  // ghost while dragging: the new outline and its numbers
  function showGhost(d, N) {
    const bl = d.h.bl, it = d.h.it, k = ek(bl), o = overlay(bl.g);
    o.querySelectorAll(".gh").forEach(e => e.remove());
    const g = mk(o, "g", { class: "gh" });
    if (it.k === "wall") {
      const w = it.w, dd = d.wd != null ? d.wd : r10(d.zone === "wx" ? d.dx : d.dy), X = w.axis === "x";
      const b = X ? [w.lo + dd, 0, w.hi + dd, M.D] : [0, w.lo + dd, M.W, w.hi + dd];
      rect(g, b, true, k);
      label(g, X ? b[2] + 1.5 / k : b[0] + 1.5 / k, X ? M.D / 2 : b[1] - 1.5 / k, (dd > 0 ? "+" : "") + dd + " mm" + (N ? "" : "  · par šauru"), k);
      return;
    }
    if (!N) return;
    if (d.grp && d.ghost) {
      d.ghost.forEach((m, j) => { const so = d.grp[j]; let gb;
        if (m.k === "furn") { const fb = d.boxes[so.i]; gb = fb && [fb[0] + d.fdx, fb[1] + d.fdy, fb[2] + d.fdx, fb[3] + d.fdy]; }
        else { const f = items(bl, N).find(x => same(x, m)); gb = f && f.b; }
        if (gb) rect(g, gb, true, k, m.k === "furn" ? 0 : undefined); });
      label(g, d.h.it.b[0], d.h.it.b[1] - 2.2 / k, (d.copy ? "Kopija " : "") + d.ghost.length + " gab.  ·  Δx " + d.fdx + "  Δy " + d.fdy, k);
      return;
    }
    let b;
    if (d.snapLine) { const [ax, at] = d.snapLine; mk(g, "line", Object.assign(ax === "x" ? { x1: -1500, y1: at, x2: M.W + 1500, y2: at } : { x1: at, y1: -1500, x2: at, y2: M.D + 1500 }, { stroke: ACC, "stroke-width": 0.3 / k, "stroke-dasharray": `${1.2 / k} ${0.8 / k}` })); }
    if (d.snapInfo || (d.refs && d.refs.length)) {   // atsauces: punktētas x / y līnijas caur atsauces punktiem un pielipšanas vietu
      const dash = { stroke: ACC, "stroke-width": 0.3 / k, "stroke-dasharray": `${1.2 / k} ${0.8 / k}` }, si = d.snapInfo || {};
      (d.refs || []).forEach(q => { mk(g, "line", Object.assign({ x1: q[0], y1: -1500, x2: q[0], y2: M.D + 1500 }, dash, { opacity: 0.6 })); mk(g, "line", Object.assign({ x1: -1500, y1: q[1], x2: M.W + 1500, y2: q[1] }, dash, { opacity: 0.6 })); mk(g, "circle", { cx: q[0], cy: q[1], r: 1.6 / k, fill: ACC, stroke: "#fff", "stroke-width": 0.3 / k }); });
      if (si.x != null) mk(g, "line", Object.assign({ x1: si.x, y1: -1500, x2: si.x, y2: M.D + 1500 }, dash));
      if (si.y != null) mk(g, "line", Object.assign({ x1: -1500, y1: si.y, x2: M.W + 1500, y2: si.y }, dash));
      if (si.pt) mk(g, "circle", { cx: si.pt[0], cy: si.pt[1], r: 1.8 / k, fill: "none", stroke: ACC, "stroke-width": 0.5 / k });
    }
    if (it.k === "tedge" || it.k === "tvert") { const tt = N.terraces[Math.floor(it.i / 100)]; mk(g, "polygon", { points: tt.poly.map(q => q.join(",")).join(" "), fill: "rgba(34,102,216,.10)", stroke: ACC, "stroke-width": 0.8 / k, "stroke-dasharray": `${1.4 / k} ${0.9 / k}` }); label(g, it.b[0], it.b[1] - 2.2 / k, `${(Math.abs(tt.poly.reduce((s, q, j) => s + q[0] * tt.poly[(j + 1) % tt.poly.length][1] - tt.poly[(j + 1) % tt.poly.length][0] * q[1], 0)) / 2e6).toFixed(2)} m²`, k); return; }
    if (it.k === "dim" || it.k === "idim") b = (items(bl, N).find(x => same(x, it)) || it).b;
    else if (it.k === "furn" && d.nb) b = d.nb;
    else if (it.k === "furn" || it.k === "stamp") b = [it.b[0] + d.fdx, it.b[1] + d.fdy, it.b[2] + d.fdx, it.b[3] + d.fdy];
    else b = (items(bl, N).find(x => same(x, it)) || it).b;
    rect(g, b, true, k, it.k === "furn" ? 0 : undefined);
    if (it.k === "furn" && d.back) { const q = { n: [b[0], b[1], b[2], b[1]], s: [b[0], b[3], b[2], b[3]], w: [b[0], b[1], b[0], b[3]], e: [b[2], b[1], b[2], b[3]] }[d.back];
      mk(g, "line", { x1: q[0], y1: q[1], x2: q[2], y2: q[3], stroke: ACC, "stroke-width": 2.2 / k, "stroke-linecap": "round" }); }
    const L2 = lv(it.lv, N);
    let t;
    if (it.k === "win") { const w = L2.windows[it.i]; t = bl.type === "elev" ? `${w.len} mm  ·  ${w.sill ?? 0}–${w.head ?? 2100}` : `${w.len} mm  ·  ${w.o === "h" ? w.x : w.y}`; }
    else if (it.k === "gw") { const w = N.gableWins[it.i]; t = `${w.u1 - w.u0} mm  ·  ${w.z0}${w.z1 ? "–" + w.z1 : ""}`; }
    else if (it.k === "door") { const w = L2.doors[it.i]; t = `${w.o === "h" ? w.x : w.y}`; }
    else if (it.k === "stamp") t = "Telpas nosaukums";
    else if (it.k === "dim") { const dm = L2.userDims[it.i]; t = `${Math.round(dm[3] - dm[2])} mm` + (d.snapLine ? "  · vienā ķēdē" : ""); }
    else if (it.k === "idim") t = "Mērķēde" + (d.snapLine ? "  · vienā ķēdē" : "");
    else if (d.nb) t = `${Math.round(b[2] - b[0])} × ${Math.round(b[3] - b[1])} mm`;
    else t = `Δx ${d.fdx}  Δy ${d.fdy}`;
    label(g, b[0], b[1] - 2.2 / k, t, k);
    if (bl.type === "plan" && (it.k === "door" || it.k === "win")) { o.querySelectorAll(".od").forEach(e => e.remove()); openDims(g, it.lv, it, k, N); }
    if (bl.type === "elev" && (it.k === "win" || it.k === "gw")) {
      o.querySelectorAll(".od").forEach(e => e.remove());
      const nb = (items(bl, N).find(x => same(x, it)) || it); elevDims(g, bl, nb, k, N);
      if (d.gwMid) { const sp = span(bl.side), ev = (M.jumts && M.jumts.eave) || 2600, top = ev + sp / 2 * Math.tan(((M.jumts && M.jumts.pitch) || 30) * Math.PI / 180);
        mk(g, "line", { x1: sp / 2, y1: -top - 300, x2: sp / 2, y2: 300, stroke: ACC, "stroke-width": 0.3 / k, "stroke-dasharray": `${1.2 / k} ${0.8 / k}` });
        label(g, sp / 2 + 1.2 / k, -top - 150, "kores vidus", k); }
    }
  }

  const cur = z => (z === "l" || z === "r" || z === "wx" ? "ew-resize" : z === "t" || z === "b" || z === "wy" ? "ns-resize" : z === "rot" ? "grab" : z === "del" ? "pointer" : z === "tc" ? "crosshair" : "move");

  // lineāli kā ArchiCAD: izvelc palīglīniju no kreisās vai augšējās malas, atpakaļ uz lineālu to dzēš
  const RUL = 16;
  (function () {
    const css = document.createElement("style"); css.textContent = ".mm-rul{position:fixed;z-index:5;background-color:#eceef1;border:0 solid #b4bac2}.mm-rul.v{background-image:repeating-linear-gradient(to bottom,#9aa1a9 0 1px,transparent 1px 10px);background-size:5px 100%;background-repeat:no-repeat;background-position:right 0 top 0}.mm-rul.h{background-image:repeating-linear-gradient(to right,#9aa1a9 0 1px,transparent 1px 10px);background-size:100% 5px;background-repeat:no-repeat;background-position:left 0 bottom 0}.mm-rul.v{left:0;top:0;bottom:0;width:" + RUL + "px;border-right-width:1px;cursor:col-resize}.mm-rul.h{left:0;top:0;right:0;height:" + RUL + "px;border-bottom-width:1px;cursor:row-resize}.mm-rul:hover{background-color:#dde6f6}@media (prefers-color-scheme:dark){.mm-rul{background-color:#2a2e33;border-color:#454b52}.mm-rul:hover{background-color:#1f3354}}";
    document.head.appendChild(css);
    [["v", "v"], ["h", "h"]].forEach(([o]) => {
      const el = document.createElement("div"); el.className = "mm-rul " + o; el.title = o === "v" ? "Velc, lai ievilktu vertikālu palīglīniju" : "Velc, lai ievilktu horizontālu palīglīniju"; document.documentElement.appendChild(el);
      el.addEventListener("pointerdown", e => {
        if (e.button !== 0 || place) return; e.preventDefault(); e.stopPropagation(); try { el.setPointerCapture(e.pointerId); } catch (_) {}
        drag = { gi: -1, isNew: true, gd: { o }, x0: e.clientX, y0: e.clientY, moved: false, P: guidePts(), h: null };
      });
    });
  })();
  // ---- pamatu plāns: stabu izvēle ar klikšķi, bultiņas pārbīda (to dara vecākā lapa, šeit tikai izcelšana un pārsūtīšana) ----
  let pst = ED.pst || null;
  const pstOn = k => { if (!pst) return false; const m = /^(\d+\/)?([rc]):(\d+)$/.exec(pst); if (!m) return k === pst;   // [n/]r:j visa rinda, [n/]c:i visa kolona
    const pre = (m[1] || "").replace("/", "\\/"); return (m[2] === "r" ? new RegExp("^" + pre + "a?\\d+," + m[3] + "$") : new RegExp("^" + pre + "b?" + m[3] + ",\\d+$")).test(k); };
  const pstMark = () => {
    document.querySelectorAll("[data-pst]").forEach(c => { const on = pstOn(c.dataset.pst); c.setAttribute("fill", on ? ACC : "#8a8d90"); c.setAttribute("stroke", on ? ACC : C_INK); });
    document.querySelectorAll("[data-pkom] > [data-hit]").forEach(c => { const on = pst === "k:" + c.parentNode.dataset.pkom; c.setAttribute("stroke", on ? ACC : "none"); c.setAttribute("stroke-width", on ? 40 : 0); });
    document.querySelectorAll("[data-pax] > circle").forEach(c => { const on = pst === c.parentNode.dataset.pax; c.setAttribute("stroke", on ? ACC : C_INK); c.setAttribute("fill", on ? "#dfe9fb" : "#fff"); });
    document.querySelectorAll("rect[data-ppart]").forEach(r => { const on = pst === "p:" + r.dataset.ppart; r.setAttribute("fill", on ? "rgba(34,102,216,.08)" : "transparent"); r.style.outline = ""; r.setAttribute("stroke", on ? ACC : C_INK); });
    document.querySelectorAll("[data-pdim]").forEach(g => { const on = pst && pst[0] === "m" && g.dataset.pdim.endsWith(":u" + pst.slice(2)); g.style.filter = on ? "drop-shadow(0 0 1.5px " + ACC + ")" : ""; });
  };
  // ---- pamatu lapa: mēru ķēžu vilkšana, pievadu vilkšana, D mēri un pievadu likšana ar klikšķi ----
  const PPM = () => (M.projekts || {}).pamatu_plans || {};
  const pView = el => el && el.closest && el.closest("g[data-pview]");
  const pLocal = (g, cx, cy) => { const sv = g.ownerSVGElement, r = sv.getBoundingClientRect(), vb = sv.viewBox.baseVal, b = tr(g);
    return [((cx - r.left) / r.width * vb.width - b.tx) / b.k, ((cy - r.top) / r.height * vb.height - b.ty) / b.k]; };
  const pK = g => tr(g).k;
  function pSnap(g, p, lines) {   // stabu centri un malas, kontūras stūri, asu krustpunkti; lines: arī atsevišķi pa X un Y (stabu līnijas, kontūru malas)
    const c = [], tol = 1.6 / pK(g);
    g.querySelectorAll("circle[data-pst]").forEach(e => { const x = +e.getAttribute("cx"), y = +e.getAttribute("cy"), r = +e.getAttribute("r"); c.push([x, y], [x - r, y], [x + r, y], [x, y - r], [x, y + r]); });
    g.querySelectorAll("rect[data-snap]").forEach(e => { const x = +e.getAttribute("x"), y = +e.getAttribute("y"), w = +e.getAttribute("width"), h = +e.getAttribute("height"); c.push([x, y], [x + w, y], [x, y + h], [x + w, y + h]); });
    (M.axes.x || []).forEach(([x]) => (M.axes.y || []).forEach(([y]) => c.push([x, y])));
    let best = null, bd = tol; c.forEach(q => { const d = Math.hypot(q[0] - p[0], q[1] - p[1]); if (d < bd) { bd = d; best = q; } });
    if (best) return { p: best, hit: true };
    const r = [Math.round(p[0] / 10) * 10, Math.round(p[1] / 10) * 10], hx = [], hy = [];
    if (lines) {
      const X = [], Y = []; g.querySelectorAll("circle[data-pst]").forEach(e => { X.push(+e.getAttribute("cx")); Y.push(+e.getAttribute("cy")); });
      g.querySelectorAll("rect[data-snap]").forEach(e => { const x = +e.getAttribute("x"), y = +e.getAttribute("y"); X.push(x, x + +e.getAttribute("width")); Y.push(y, y + +e.getAttribute("height")); });
      const nb = (A, v) => A.reduce((b, a) => Math.abs(a - v) < tol && (b == null || Math.abs(a - v) < Math.abs(b - v)) ? a : b, null);
      const sx = nb(X, p[0]), sy = nb(Y, p[1]); if (sx != null) { r[0] = sx; hx.push(sx); } if (sy != null) { r[1] = sy; hy.push(sy); }
    }
    return { p: r, hit: false, hx, hy };
  }
  let pPlace = ED.pamMode || null, pDim = null, pDrag = null;   // pPlace: "dim" | "kom" | "rect" | "rect0" | "post"; pDim: { g, pts }
  // paliekošs režīms (kontūras, stabi) pēc pārzīmēšanas turpinās: vecākā lapa to atdod ED.pamMode
  const pEnd = () => { pPlace = null; document.body.style.cursor = ""; pHov(null); };
  let pHv = null;   // priekšskatījums pie kursora: pielipšanas punkts un palīglīnijas
  function pHov(g, sn) {
    if (pHv) { pHv.remove(); pHv = null; } if (!g || !sn) return;
    const k = pK(g), G = document.createElementNS(NS, "g"); G.setAttribute("pointer-events", "none");
    const ln = (x1, y1, x2, y2) => { const l = document.createElementNS(NS, "line"); Object.entries({ x1, y1, x2, y2, stroke: ACC, "stroke-width": .25 / k, "stroke-dasharray": `${1.2 / k} ${.8 / k}` }).forEach(([a, v]) => l.setAttribute(a, v)); G.appendChild(l); };
    (sn.hx || []).forEach(x => ln(x, -1e5, x, 1e5)); (sn.hy || []).forEach(y => ln(-1e5, y, 1e5, y));
    const c = document.createElementNS(NS, "circle"); Object.entries({ cx: sn.p[0], cy: sn.p[1], r: (pPlace === "post" ? (+PPM().d || 120) / 2 : 1 / k), fill: sn.hit ? ACC : "none", stroke: ACC, "stroke-width": .3 / k, "fill-opacity": .35 }).forEach(([a, v]) => c.setAttribute(a, v)); G.appendChild(c);
    g.appendChild(G); pHv = G;
  }
  const pMarks = [];
  const pMark = (g, p) => { const k = pK(g), c = document.createElementNS(NS, "circle"); c.setAttribute("cx", p[0]); c.setAttribute("cy", p[1]); c.setAttribute("r", 1.2 / k); c.setAttribute("fill", ACC); g.appendChild(c); pMarks.push(c); };
  const pClear = () => { pMarks.splice(0).forEach(c => c.remove()); pDim = null; };
  const pEdit = (f, extra) => { const N = clone(M); N.projekts = N.projekts || {}; N.projekts.pamatu_plans = N.projekts.pamatu_plans || {}; f(N.projekts.pamatu_plans, N); post(Object.assign({ t: "edit", model: N, sel: null, pst }, extra || {})); };
  const pKomList = Q => { if (!Q.kom) { const L = []; document.querySelectorAll("[data-pkom]").forEach(e => { L[+e.dataset.pkom] = JSON.parse(e.dataset.kom); }); Q.kom = L.filter(Boolean); } return Q.kom; };
  function pamHook(e) {   // true = notikums apstrādāts
    const dimMode = pPlace === "dim" || (place && place.t === "dim"), sv = e.target && e.target.closest && e.target.closest("svg.a3");
    // ārpus zīmējuma (tukšā lapas vietā) ņem tuvāko skatu: stabu plānu vai vienīgo skatu lapā
    const g = pView(e.target) || ((pPlace || dimMode) && sv ? (sv.querySelector("g[data-pview=stabi]") || sv.querySelector("g[data-pview]")) : null);
    if (g && dimMode) {
      const sn = pSnap(g, pLocal(g, e.clientX, e.clientY));
      if (!pDim || pDim.g !== g) { pClear(); pDim = { g, pts: [] }; }
      if (pDim.pts.length < 2) { pDim.pts.push(sn.p); pMark(g, sn.p); post({ t: "hint", text: pDim.pts.length === 1 ? "Mērs: otrais punkts (pielīp stabu centriem un malām)" : "Mērs: klikšķis, kur novietot mēra līniju" }); return true; }
      const [a, b] = pDim.pts, q = pLocal(g, e.clientX, e.clientY), H = Math.abs(b[0] - a[0]) >= Math.abs(b[1] - a[1]), view = g.dataset.pview;
      pClear(); pEnd();
      pEdit(Q => { Q.udims = (Q.udims || []).concat([{ v: view, a, b, h: H, at: Math.round(H ? q[1] : q[0]) }]); }, { placed: true });
      return true;
    }
    if (g && (pPlace === "rect" || pPlace === "rect0")) {   // kontūra: velk taisnstūri, pielīp stūriem
      pHov(null); const a = pSnap(g, pLocal(g, e.clientX, e.clientY), true).p, r = document.createElementNS(NS, "rect"), k = pK(g);
      r.setAttribute("fill", "rgba(34,102,216,.10)"); r.setAttribute("stroke", ACC); r.setAttribute("stroke-width", .4 / k); r.setAttribute("stroke-dasharray", `${1.5 / k} ${1 / k}`); g.appendChild(r);
      const t = document.createElementNS(NS, "text"); t.setAttribute("font-size", 3 / k); t.setAttribute("fill", ACC); t.setAttribute("font-weight", 600); g.appendChild(t);
      pDrag = { kind: "rect", g, a, b: a, p0: a, el: r, tx: t, mode: pPlace, moved: true }; return true;
    }
    if (g && (pPlace === "axx" || pPlace === "axy")) {   // būvass: vertikāla (axx, pa X) vai horizontāla (axy, pa Y); pielīp kontūru malām un stabu līnijām
      const p = pSnap(g, pLocal(g, e.clientX, e.clientY), true).p.map(Math.round), X = pPlace === "axx"; pEnd();
      pEdit((Q, N) => { const A = N.axes = N.axes || {}, L = A[X ? "x" : "y"] = (A[X ? "x" : "y"] || []).slice(), pos = X ? p[0] : p[1];
        const LET = "ABCDEFGHIJKLMNOPRSTUVZ", nm = X ? String(Math.max(0, ...L.map(a => parseInt(a[1], 10) || 0)) + 1) : (LET.split("").find(c => !L.some(a => a[1] === c)) || "Y");
        L.push([pos, nm]); L.sort((a, b) => a[0] - b[0]); Q.asisMan = true; pst = (X ? "x:" : "y:") + L.findIndex(a => a[0] === pos && a[1] === nm); }, { placed: true });
      return true;
    }
    if (g && pPlace === "post" && g.dataset.pview === "stabi") {   // stabs ar klikšķi: pielīp stabu līnijām un centriem; režīms paliek līdz Esc
      const p = pSnap(g, pLocal(g, e.clientX, e.clientY), true).p.map(Math.round);
      pEdit(Q => { Q.ext = (Q.ext || []).concat([[p[0], p[1]]]); }, { pamMode: "post" });
      return true;
    }
    if (g && pPlace === "kom") {
      const p = pLocal(g, e.clientX, e.clientY).map(v => Math.round(v / 10) * 10), d = { n: p[1], s: M.D - p[1], w: p[0], e: M.W - p[0] };
      const side = Object.keys(d).sort((a, b) => d[a] - d[b])[0];
      pEnd();
      pEdit(Q => { const L = pKomList(Q); L.push({ n: "Jauns pievads", c: "#0b8a6a", side, x: p[0], y: p[1], sym: "ievads" }); pst = "k:" + (L.length - 1); }, { placed: true });
      post({ t: "pst", key: pst });
      return true;
    }
    if (place) return false;
    const dEl = e.target.closest && e.target.closest("[data-pdim]");
    if (dEl && g) { pDrag = { kind: "dim", el: dEl, g, id: dEl.dataset.pdim, h: dEl.dataset.h === "1", p0: pLocal(g, e.clientX, e.clientY), d: 0, moved: false }; return true; }
    const kEl = e.target.closest && e.target.closest("[data-pkom]");
    if (kEl && g) { pDrag = { kind: "kom", el: kEl, g, i: +kEl.dataset.pkom, p0: pLocal(g, e.clientX, e.clientY), d: [0, 0], moved: false }; return true; }
    return false;
  }
  addEventListener("pointermove", e => {
    if (!pDrag && /^(post|rect0?|ax[xy])$/.test(pPlace || "")) { const sv = e.target && e.target.closest && e.target.closest("svg.a3"), g = sv && sv.querySelector("g[data-pview=stabi]"); pHov(g, g && pSnap(g, pLocal(g, e.clientX, e.clientY), true)); }
    if (!pDrag) return;
    const p = pLocal(pDrag.g, e.clientX, e.clientY), dx = p[0] - pDrag.p0[0], dy = p[1] - pDrag.p0[1];
    if (!pDrag.moved && Math.hypot(dx, dy) * pK(pDrag.g) < .6) return;
    pDrag.moved = true;
    if (pDrag.kind === "rect") { const sn = pSnap(pDrag.g, p, true), b = sn.p; pHov(pDrag.g, sn); a = pDrag.a, x = Math.min(a[0], b[0]), y = Math.min(a[1], b[1]), w = Math.abs(b[0] - a[0]), h = Math.abs(b[1] - a[1]); pDrag.b = b;
      Object.entries({ x, y, width: w, height: h }).forEach(([n, v]) => pDrag.el.setAttribute(n, v)); pDrag.tx.setAttribute("x", x + 2 / pK(pDrag.g)); pDrag.tx.setAttribute("y", y - 1.5 / pK(pDrag.g)); pDrag.tx.textContent = `${Math.round(w)} × ${Math.round(h)}`; return; }
    if (pDrag.kind === "dim") { pDrag.d = Math.round((pDrag.h ? dy : dx) / 10) * 10; pDrag.el.setAttribute("transform", pDrag.h ? `translate(0 ${pDrag.d})` : `translate(${pDrag.d} 0)`); }
    else { pDrag.d = [Math.round(dx / 10) * 10, Math.round(dy / 10) * 10]; pDrag.el.setAttribute("transform", `translate(${pDrag.d[0]} ${pDrag.d[1]})`); }
  });
  addEventListener("pointerup", () => {
    const D = pDrag; pDrag = null; if (!D) return;
    if (D.kind === "rect") {
      D.el.remove(); D.tx.remove(); pHov(null);
      const a = D.a, b = D.b, R = [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.abs(b[0] - a[0]), Math.abs(b[1] - a[1])].map(Math.round);
      if (R[2] < 500 || R[3] < 500) { pPlace = "rect"; post({ t: "hint", text: "Kontūra par mazu (vismaz 500 × 500 mm). Velc lielāku." }); return; }
      pPlace = null;
      pEdit((Q, N) => {
        delete Q.zimet;
        if (D.mode === "rect0") { ["nx", "ny", "mov", "rmov", "cmov", "del", "doff"].forEach(f => delete Q[f]); Q.ext = (Q.ext || []).filter(q => Array.isArray(q)); Q.parts = [{ r: R }]; pst = "p:0"; }
        else { if (!(Q.parts || []).length) Q.parts = [{ r: [0, 0, N.W, N.D] }]; Q.parts.push({ r: R }); pst = "p:" + (Q.parts.length - 1); }
      }, { pamMode: "rect" });
      post({ t: "hint", text: "Kontūra pievienota. Velc nākamo paneli vai spied Esc." }); return;
    }
    if (D.kind === "dim") {
      const u = /:u(\d+)$/.exec(D.id);
      if (!D.moved) { if (u) { pst = "m:" + u[1]; pstMark(); post({ t: "pst", key: pst }); } return; }
      pEdit(Q => { if (u) { const q = (Q.udims || [])[+u[1]]; if (q) q.at += D.d; } else { Q.doff = Q.doff || {}; Q.doff[D.id] = (Q.doff[D.id] || 0) + D.d; if (!Q.doff[D.id]) delete Q.doff[D.id]; } });
    } else {
      if (!D.moved) { pst = "k:" + D.i; pstMark(); post({ t: "pst", key: pst }); return; }
      pEdit(Q => { const q = pKomList(Q)[D.i]; if (q) { q.x = (+q.x || 0) + D.d[0]; q.y = (+q.y || 0) + D.d[1]; } });
    }
  });
  const C_INK = "#111";
  addEventListener("keydown", e => {
    if (e.key === "Escape" && (pPlace || pDim)) { pClear(); pEnd(); post({ t: "placed", pamMode: null }); }
    if (!pst || e.ctrlKey || e.metaKey || e.altKey) return;
    if (/^Arrow(Left|Right|Up|Down)$/.test(e.key) || e.key === "Delete" || e.key === "Escape") {
      e.preventDefault(); e.stopImmediatePropagation();
      if (e.key === "Escape") { pst = null; pstMark(); post({ t: "pst", key: null }); }
      else post({ t: "pstKey", key: e.key, shiftKey: e.shiftKey });
    }
  }, true);
  addEventListener("message", e => { const m = e.data; if (m && "mmPst" in m) { pst = m.mmPst; pstMark(); }
    if (m && "mmPamPlace" in m) { pClear(); pHov(null); pPlace = m.mmPamPlace; document.body.style.cursor = pPlace ? "crosshair" : ""; }
    if (m && "mmPlace" in m && !m.mmPlace) { pClear(); pEnd(); } });
  addEventListener("load", () => { pstMark(); if (pPlace) document.body.style.cursor = "crosshair"; if (window.MM_PAM) post({ t: "pam", info: window.MM_PAM }); });
  window.MMZ_HOOK = e => {
    if (e.button !== 0) return false;
    if (pamHook(e)) return true;
    { const ax = !place && e.target && e.target.closest && e.target.closest("[data-pax]");
      if (ax) { pst = ax.dataset.pax; pstMark(); if (sel) { sel = null; drawSel(); post({ t: "sel", sel: null }); } post({ t: "pst", key: pst }); return true; } }
    { const pe = e.target && e.target.closest && e.target.closest("[data-pst]");
      if (pe && !place) { pst = pe.dataset.pst; pstMark(); if (sel) { sel = null; drawSel(); post({ t: "sel", sel: null }); } post({ t: "pst", key: pst }); return true; }
      // kontūras izvēle: klikšķis tās laukumā (arī uz režģa līnijām), ja nav trāpīts stabs, mērs vai pievads
      const gv = !place && pView(e.target), lp = gv && gv.dataset.pview === "stabi" ? pLocal(gv, e.clientX, e.clientY) : null;
      const pp = lp && [...gv.querySelectorAll("rect[data-ppart]")].reverse().find(r => { const x = +r.getAttribute("x"), y = +r.getAttribute("y"); return lp[0] >= x && lp[1] >= y && lp[0] <= x + +r.getAttribute("width") && lp[1] <= y + +r.getAttribute("height"); });
      if (pp) { pst = "p:" + pp.dataset.ppart; pstMark(); if (sel) { sel = null; drawSel(); post({ t: "sel", sel: null }); } post({ t: "pst", key: pst }); return true; }
      if (pst && e.target && e.target.closest && e.target.closest("svg[data-part=pamati]")) { pst = null; pstMark(); post({ t: "pst", key: null }); return false; } }
    if (drag && drag.wend && drag.sticky) { commitWend(); return true; }
    if (place && place.t === "erase") {
      const gi = guideHit(e.clientX, e.clientY);
      if (gi >= 0) { const N = clone(M); N.projekts.guides.splice(gi, 1); post({ t: "edit", model: N, sel: null }); return true; }
      const h = hit(e.clientX, e.clientY); if (!h) return true;
      if (h.wall) {
        if (!hovWall || h.it.w.ext) { post({ t: "hint", text: "Ārsienu dzēst nevar. Starpsienu dzēs ar klikšķi uz tās." }); return true; }
        const hw = hovWall, N = clone(M); let did = 0;
        linePairs(hw.w.axis, hw.w.lo, hw.w.hi).forEach(q => { const a0 = Math.max(q.v0, hw.seg[0]), b0 = Math.min(q.v1, hw.seg[1]); if (b0 - a0 >= 100 && !cutWall(N, q, a0, b0).err) did++; });
        if (did) post({ t: "edit", model: N, sel: null }); return true;
      }
      if (h.it.k === "stamp") return true;
      sel = { k: h.it.k, i: h.it.i, lv: h.it.lv }; post({ t: "sel", sel }); post({ t: "delete" }); return true;
    }
    if (place && place.t === "guide") {
      const gd = guideNow(place, e.clientX, e.clientY, e.shiftKey); delete gd.hit; delete gd.hp;
      const N = clone(M); N.projekts = N.projekts || {}; N.projekts.guides = (N.projekts.guides || []).concat([gd]);
      post({ t: "edit", model: N, sel }); return true;
    }
    if (!place) { const gi = guideHit(e.clientX, e.clientY);
      if (gi >= 0) { sel = { k: "guide", i: gi }; drawSel(); post({ t: "sel", sel }); drag = { gi, gd: GUIDES()[gi], x0: e.clientX, y0: e.clientY, moved: false, P: guidePts(), h: null }; return true; } }
    if (place && place.t === "bucket") return bucketClick(e);
    if (place && place.t === "post") return postClick(e);
    if (place && place.t === "terrace") return terClick(e);
    if (place) {
      const r = placeAt(e.clientX, e.clientY);
      if (r.miss) { post({ t: "hint", text: r.miss }); return true; }
      if (r.pending) { post({ t: "hint", text: r.pending }); return true; }
      place = null; document.body.style.cursor = ""; sel = r.sel;
      post({ t: "edit", model: r.N, sel: r.sel, place: !!r.fit, placed: true });
      return true;
    }
    if (hovWall) {   // sienas posma gala rokturis
      const hw = hovWall, X = hw.w.axis === "x", ix = nearHandle(e);
      if (ix >= 0) { drag = { wend: true, hw, ix, e0: hw.seg[ix], fixed: hw.seg[1 - ix], u: hw.seg[ix], x0: e.clientX, y0: e.clientY, moved: false }; document.body.style.cursor = X ? "ns-resize" : "ew-resize"; return true; }
    }
    const h = hit(e.clientX, e.clientY); hover(null);
    if (!h) { if (sel) { sel = null; drawSel(); post({ t: "sel", sel: null }); } return false; }
    if (h.del) { post({ t: "delete" }); return true; }
    if (h.rot) {   // klikšķis = 90°, vilkšana = brīvi (solis 15°, ar Shift 1°)
      const b = h.it.b, c = [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2];
      drag = { h, x0: e.clientX, y0: e.clientY, dx: 0, dy: 0, zone: "rot", c, a0: Math.atan2(h.p[1] - c[1], h.p[0] - c[0]), ang: 0, boxes: furnBoxes(h.bl), moved: false };
      document.body.style.cursor = "grabbing"; return true;
    }
    const grpOk = h.bl.type === "plan" && !h.wall && GRP.includes(h.it.k) && h.it.lv !== "loft";
    if (e.shiftKey && grpOk && sel && GRP.includes(sel.k) && sel.lv === h.it.lv && !same(h.it, sel)) {   // Shift+klikšķis: pievieno / noņem no atlasītās grupas
      const more = (sel.more || []).slice(), ix = more.findIndex(m => same(m, h.it));
      if (ix >= 0) more.splice(ix, 1); else more.push({ k: h.it.k, i: h.it.i, lv: h.it.lv });
      sel = Object.assign({}, sel, { more }); drawSel(); post({ t: "sel", sel }); return true;
    }
    const inGrp = grpOk && sel && sel.more && sel.more.length && (same(h.it, sel) || sel.more.some(m => same(m, h.it)));
    if (!h.wall && !inGrp) { sel = h.it.k === "tedge" || h.it.k === "tvert" ? { k: "ter", i: Math.floor(h.it.i / 100), lv: "main" } : { k: h.it.k, i: h.it.i, lv: h.it.lv }; selPt = { g: h.bl.g, p: h.p }; drawSel(); post({ t: "sel", sel }); }
    drag = { h, x0: e.clientX, y0: e.clientY, dx: 0, dy: 0, zone: inGrp ? "move" : zone(h), boxes: h.bl.type === "plan" ? furnBoxes(h.bl) : null, moved: false, copy: (e.ctrlKey || e.metaKey) && ["furn", "win", "door", "post"].includes(h.it.k), grp: inGrp ? [sel, ...sel.more] : null };
    if (h.it.k === "post" && drag.zone === "move") { const pq = M.posts[h.it.i]; drag.gp0 = nearestGrab([pq.x, pq.y, pq.x + pq.w, pq.y + pq.d], h.p); drag.refs = []; }
    document.body.style.cursor = h.wall ? MVC : cur(drag.zone);
    return true;
  };
  let moveMode = false;
  const MVC = "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 32 32'><g fill='%23e0201b' stroke='%23fff' stroke-width='1.2' stroke-linejoin='round'><path d='M16 2l5 6h-3.4v6.6H24V11l6 5-6 5v-3.6h-6.4V24H21l-5 6-5-6h3.4v-6.6H8V21l-6-5 6-5v3.6h6.4V8H11z'/></g></svg>\") 16 16, move";
  const ERC = "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='26' height='26' viewBox='0 0 40 40'><path d='M26 6l10 10-14 14H12l-6-6z' fill='%23fff' stroke='%23d9480f' stroke-width='3'/><path d='M14 14l10 10' stroke='%23d9480f' stroke-width='3'/></svg>\") 6 24, crosshair";
  addEventListener("pointermove", e => {
    if (place && place.t === "erase") { document.body.style.cursor = ERC; const h = guideHit(e.clientX, e.clientY) >= 0 ? null : hit(e.clientX, e.clientY); hover(h); return; }
    if (place && place.t === "dim" && fdimMove(e)) return;
    if (place && place.t === "dim") { if (place.p0) dimPreview(e.clientX, e.clientY); else dimHover(e.clientX, e.clientY); return; }
    if (place && (place.t === "wall" || place.t === "cut")) { wallPreview(e.clientX, e.clientY); return; }
    if (place && place.t === "post") { postPreview(e.clientX, e.clientY); return; }
    if (place && place.t === "terrace") { terPreview(e.clientX, e.clientY, e.shiftKey); return; }
    if (place && place.t === "guide") { drawGuides(guideNow(place, e.clientX, e.clientY, e.shiftKey)); return; }
    if (drag && drag.wend) {
      const hw = drag.hw, X = hw.w.axis === "x", p = toLocal(hw.bl.g, e.clientX, e.clientY), o = overlay(hw.bl.g), k = ek(hw.bl);
      if (Math.hypot(e.clientX - drag.x0, e.clientY - drag.y0) > 3) drag.moved = true;
      drag.u = Math.max(0, Math.min(X ? M.D : M.W, snapAx("main", X ? "y" : "x", X ? p[1] : p[0], 150)));
      o.querySelectorAll(".gh").forEach(q => q.remove()); const g = mk(o, "g", { class: "gh" }), a = Math.min(drag.fixed, drag.u), b = Math.max(drag.fixed, drag.u);
      rect(g, X ? [hw.w.lo, a, hw.w.hi, b] : [a, hw.w.lo, b, hw.w.hi], true, k, 0); let msg = `${Math.round(b - a)} mm`;
      if (Math.abs(drag.u - drag.e0) >= 10) { const rr = moveWallEnd(clone(M), endPair(hw, drag.ix), drag.e0, drag.u, (drag.e0 + drag.fixed) / 2); if (rr.err) msg += "  ✕ " + rr.err; }
      label(g, X ? hw.w.hi : a, X ? a : hw.w.lo - 2.2 / k, msg, k); return;
    }
    if (drag && drag.gi != null) {
      if (Math.hypot(e.clientX - drag.x0, e.clientY - drag.y0) > 3) drag.moved = true;
      if (drag.moved) { drag.ng = guideAt(drag.gd.o, e.clientX, e.clientY, drag.P); if (drag.gd.o === "s") drag.ng.a = drag.gd.a; drag.over = drag.gd.o === "v" ? e.clientX < RUL : drag.gd.o === "h" ? e.clientY < RUL : false; drawGuides(drag.over ? null : drag.ng); }
      return;
    }
    if (!drag && !place && hovWall && nearHandle(e) >= 0) { document.body.style.cursor = hovWall.w.axis === "x" ? "ns-resize" : "ew-resize"; return; }
    if (!drag && !place) { const gi = guideHit(e.clientX, e.clientY); if (gi >= 0) { document.body.style.cursor = GUIDES()[gi].o === "h" ? "ns-resize" : "ew-resize"; hover(null); return; } }
    if (place && place.t === "bucket") { document.body.style.cursor = e.altKey ? PIC : BKC; const t = bucketTarget(e.clientX, e.clientY); hover(t && t.k !== "fas" ? hit(e.clientX, e.clientY) : null); return; }
    if (place) { hover(null); return; }
    if (!drag) {
      const h = hit(e.clientX, e.clientY);
      document.body.style.cursor = h ? (h.wall ? MVC : cur(zone(h))) : (moveMode ? MVC : ""); hover(h);
      document.querySelectorAll("g.mm-ov .gph").forEach(x => x.remove());
      if (h && h.it.k === "post" && sel && sel.k === "post") { const pq = M.posts[h.it.i], q = nearestGrab([pq.x, pq.y, pq.x + pq.w, pq.y + pq.d], h.p); mk(overlay(h.bl.g), "circle", { class: "gph", cx: q[0], cy: q[1], r: 1.9 / ek(h.bl), fill: ACC, "fill-opacity": 0.35, stroke: ACC, "stroke-width": 0.5 / ek(h.bl) }); }
      return;
    }
    const a = toLocal(drag.h.bl.g, e.clientX, e.clientY), b = toLocal(drag.h.bl.g, drag.x0, drag.y0);
    drag.dx = a[0] - b[0]; drag.dy = a[1] - b[1]; drag.alt = e.altKey; drag.shift = e.shiftKey;
    if (Math.hypot(e.clientX - drag.x0, e.clientY - drag.y0) > 3) drag.moved = true;
    if (drag.zone === "rot") {
      let g = (Math.atan2(a[1] - drag.c[1], a[0] - drag.c[0]) - drag.a0) * 180 / Math.PI;
      const st = e.shiftKey ? 1 : 15; g = Math.round(g / st) * st; g = ((g % 360) + 540) % 360 - 180; drag.ang = g;
      if (drag.moved) rotGhost(drag); return;
    }
    if (drag.moved) showGhost(drag, applyC(drag, drag.dx, drag.dy));
    if (drag.moved && drag.gp0 && !drag.nudge) {   // kursors uz punkta ~0,6 s: tas kļūst par atsauci (SketchUp secinājums)
      clearTimeout(drag.dwT); const cp = a.slice();
      drag.dwT = setTimeout(() => {
        if (!drag || !drag.gp0) return;
        const m = drag.h.bl.g.getScreenCTM(), thr = m && m.a ? 14 / Math.abs(m.a) : 140; let bq = null, bd = thr;
        refPoints(drag.h.it.i).forEach(q => { const e = Math.hypot(q[0] - cp[0], q[1] - cp[1]); if (e < bd) { bd = e; bq = q; } });
        if (!bq) return;
        drag.refs = (drag.refs || []).filter(r => r[0] !== bq[0] || r[1] !== bq[1]); drag.refs.push(bq.slice()); if (drag.refs.length > 3) drag.refs.shift();
        post({ t: "hint", text: "Atsauce ņemta (" + Math.round(bq[0]) + ", " + Math.round(bq[1]) + "). Velc tālāk, stabs pielips pie tās x / y līnijām." });
        showGhost(drag, applyC(drag, drag.dx, drag.dy));
      }, 600);
    }
  });
  addEventListener("pointerup", () => {
    if (!drag) return;
    if (drag.wend) {
      if (!drag.moved && !drag.sticky) { drag.sticky = true; post({ t: "hint", text: "Tagad uzklikšķini, kur siena beidzas. Esc atceļ." }); return; }   // klikšķis uz gala, tad klikšķis, cik gara
      if (drag.sticky) return;
      commitWend();
      return;
    }
    if (drag.gi != null) {
      const d = drag; drag = null; document.body.style.cursor = "";
      if (d.isNew) {   // jauna palīglīnija, izvilkta no lineāla: tukšums = atcelts
        if (d.moved && d.ng && d.over !== true) { const gd = Object.assign({}, d.ng); delete gd.hit; delete gd.hp; const N = clone(M); N.projekts = N.projekts || {}; N.projekts.guides = (N.projekts.guides || []).concat([gd]); post({ t: "edit", model: N, sel }); } else drawGuides();
        return;
      }
      if (d.moved && d.over === true) { const N = clone(M); N.projekts.guides.splice(d.gi, 1); sel = null; post({ t: "edit", model: N, sel: null }); return; }   // vilkta atpakaļ uz lineālu: dzēš
      if (d.moved && d.ng) { const N = clone(M), g = N.projekts.guides[d.gi]; if (g.o === "s") { g.x = d.ng.x; g.y = d.ng.y; } else g.at = d.ng.at; post({ t: "edit", model: N, sel }); }
      else drawGuides();
      return;
    }
    const d = drag; drag = null; document.body.style.cursor = ""; clearTimeout(d.dwT);
    if (d.zone === "rot") { const deg = d.moved ? d.ang : 90; if (deg) post({ t: "edit", model: rotate(clone(M), d.h.it.lv, d.h.it.i, d.boxes, deg), sel }); else drawSel(); return; }
    if (!d.moved) return;
    const N = applyC(d, d.dx, d.dy);
    if (N && d.grp && d.ghost) { if (d.copy) sel = Object.assign({}, d.ghost[0], { more: d.ghost.slice(1) }); post({ t: "edit", model: N, sel }); return; }
    if (N && d.cpI != null) { sel = { k: d.h.it.k, i: d.cpI, lv: d.h.it.lv }; if (d.h.it.k === "post") sel.from = d.it0.i; post({ t: "edit", model: N, sel }); return; }
    if (N && (d.zone === "wx" || d.zone === "wy") && bathFix(N)) { post({ t: "hint", text: BATHMSG }); document.querySelectorAll("g.mm-ov .gh").forEach(x => x.remove()); return; }
    if (N) post({ t: "edit", model: N, sel });
    else document.querySelectorAll("g.mm-ov .gh").forEach(x => x.remove());
  });

  // keyboard: arrows move, R turns, Delete removes, Ctrl+Z / Ctrl+Y, Esc
  // stabu kopēšana kā SketchUp: Ctrl+vilkt kopē; /n sadala attālumu starp oriģinālu un kopiju ar n stabiem, *n atkārto to pašu soli n reizes
  let divBuf = null;
  function postDiv(n, op) {
    const src = M.posts[sel.from], cp = M.posts[sel.i]; if (!src || !cp) return;
    const N = clone(M), dx = cp.x - src.x, dy = cp.y - src.y, arr = [];
    if (op === "/") for (let k = 1; k < n; k++) arr.push([src.x + dx * k / n, src.y + dy * k / n]);
    else for (let k = 2; k <= n; k++) arr.push([src.x + dx * k, src.y + dy * k]);
    arr.forEach(([x, y]) => N.posts.push(Object.assign(clone(src), { x: +x.toFixed(1), y: +y.toFixed(1) })));
    post({ t: "edit", model: N, sel: { k: "post", i: sel.i, lv: "main" } });
  }
  addEventListener("keydown", e => {
    if (sel && sel.k === "post" && sel.from != null && !divBuf && (e.key === "/" || e.key === "*") && !e.ctrlKey) { e.preventDefault(); divBuf = { op: e.key, s: "" }; post({ t: "hint", text: (e.key === "/" ? "Dalīt ar: " : "Atkārtot reizes: ") + "ieraksti skaitli un Enter" }); return; }
    if (divBuf) {
      if (/^[0-9]$/.test(e.key)) { e.preventDefault(); divBuf.s += e.key; post({ t: "hint", text: (divBuf.op === "/" ? "Dalīt ar: " : "Atkārtot reizes: ") + divBuf.s + "  (Enter apstiprina)" }); return; }
      if (e.key === "Backspace") { e.preventDefault(); divBuf.s = divBuf.s.slice(0, -1); return; }
      if (e.key === "Enter") { e.preventDefault(); const n = +divBuf.s, op = divBuf.op; divBuf = null; if (n >= (op === "/" ? 2 : 1)) postDiv(n, op); return; }
      if (e.key === "Escape") { divBuf = null; post({ t: "hint", text: "" }); return; }
    }
    if (place && place.t === "terrace" && e.key === "Enter") { e.preventDefault(); terFinish(); return; }
    if (place && place.t === "terrace" && e.key === "Backspace") { e.preventDefault(); (place.pts || []).pop(); return; }
    if ((e.ctrlKey || e.metaKey) && (e.key === "z" || e.key === "Z")) { e.preventDefault(); post({ t: e.shiftKey ? "redo" : "undo" }); return; }
    if ((e.ctrlKey || e.metaKey) && (e.key === "y" || e.key === "Y")) { e.preventDefault(); post({ t: "redo" }); return; }
    if (e.key === "Escape" && drag) { drag = null; document.body.style.cursor = ""; document.querySelectorAll("g.mm-ov .gh").forEach(x => x.remove()); drawSel(); return; }
    if (e.key === "Escape" && moveMode && !drag) { moveMode = false; document.body.style.cursor = ""; post({ t: "mvoff" }); }
    if (e.key === "Escape" && place) { place = null; document.body.style.cursor = ""; document.querySelectorAll("g.mm-ov .gh").forEach(x => x.remove()); drawGuides(); post({ t: "placed" }); return; }
    if (!e.ctrlKey && !e.metaKey && !e.altKey && e.key.length === 1) post({ t: "key", k: "combo", c: (e.shiftKey ? "shift+" : "") + e.key.toLowerCase() });   // taustiņus apstrādā ārējā lapa (pielāgojami)
    if ((e.ctrlKey || e.metaKey) && /^[cC]$/.test(e.key) && sel && GRP.includes(sel.k)) {   // Ctrl+C: nokopē atlasītos logus, durvis, mēbeles
      e.preventDefault(); const L = lv(sel.lv), list = [sel, ...(sel.more || [])].map(s => ({ k: s.k, lv: s.lv, o: clone(L[s.k === "furn" ? "furniture" : s.k === "win" ? "windows" : "doors"][s.i]) }));
      clip = list; post({ t: "clip", clip: list, n: list.length }); return;
    }
    if ((e.ctrlKey || e.metaKey) && /^[vV]$/.test(e.key) && clip && clip.length) { e.preventDefault(); const r = pasteGrp(clip); sel = r.sel; post({ t: "edit", model: r.N, sel }); return; }
    if (!sel && (e.key === "Delete" || e.key === "Backspace") && hovWall) {   // starpsienas posms zem kursora: Delete to izgriež
      e.preventDefault(); const hw = hovWall, N = clone(M); let did = 0;
      linePairs(hw.w.axis, hw.w.lo, hw.w.hi).forEach(q => { const a0 = Math.max(q.v0, hw.seg[0]), b0 = Math.min(q.v1, hw.seg[1]); if (b0 - a0 >= 100 && !cutWall(N, q, a0, b0).err) did++; });
      if (!did) post({ t: "hint", text: "Siena nav atrasta." }); else post({ t: "edit", model: N, sel: null }); return;
    }
    if (!sel) return;
    if (e.key === "Escape") { sel = null; drawSel(); post({ t: "sel", sel: null }); return; }
    if ((e.key === "Delete" || e.key === "Backspace") && sel.more && sel.more.length) { e.preventDefault(); delGrp(); return; }
    if (e.key === "Delete" || e.key === "Backspace") { e.preventDefault(); post({ t: "delete" }); return; }
    const bl = blocks().find(x => (sel.k === "gw" ? x.type === "elev" && x.side === M.gableWins[sel.i].side : x.type === "plan" && x.lv === sel.lv));
    const it = bl && items(bl).find(x => same(x, sel));
    if (!it) return;
    if (sel.k === "door" && /^[fFhH]$/.test(e.key)) { e.preventDefault(); post({ t: "edit", model: flipDoor(clone(M), sel, /[fF]/.test(e.key) ? "side" : "hinge"), sel }); return; }
    if ((e.key === "r" || e.key === "R") && sel.k === "furn") { e.preventDefault(); post({ t: "edit", model: rotate(clone(M), sel.lv, sel.i, furnBoxes(bl)), sel }); return; }
    const st = e.shiftKey ? 100 : 10, dir = { ArrowLeft: [-st, 0], ArrowRight: [st, 0], ArrowUp: [0, -st], ArrowDown: [0, st] }[e.key];
    if (!dir) return;
    e.preventDefault();
    const d = { h: { it, bl }, dx: dir[0], dy: dir[1], zone: "move", nudge: true, boxes: bl.type === "plan" ? furnBoxes(bl) : null };
    post({ t: "edit", model: apply(d, d.dx, d.dy), sel });
  });

  // durvis: vēršanās virziens (F, dubultklikšķis) un eņģu puse (H)
  function flipDoor(N, s, what) {
    const d = lv(s.lv, N).doors[s.i];
    if (what === "side") d.side = -(d.side || 1); else d.hinge = d.hinge === "e" ? "s" : "e";
    return N;
  }
  addEventListener("dblclick", e => {
    if (place && place.t === "terrace") { terFinish(); return; }
    const h = hit(e.clientX, e.clientY);
    if (h && h.it.k === "door" && !h.del) { sel = { k: "door", i: h.it.i, lv: h.it.lv }; post({ t: "edit", model: flipDoor(clone(M), sel, e.shiftKey ? "hinge" : "side"), sel }); }
  });

  // ---- placing a new item from the library: the next click on the drawing says where ----
  let place = null;
  addEventListener("message", e => {
    const m = e.data;
    if (m && m.mmFlip && sel && sel.k === "door") { post({ t: "edit", model: flipDoor(clone(M), sel, m.mmFlip), sel }); return; }
    if (m && m.mmRotate && sel && sel.k === "furn") { const bl = blocks().find(x => x.type === "plan" && x.lv === sel.lv); if (bl) post({ t: "edit", model: rotate(clone(M), sel.lv, sel.i, furnBoxes(bl)), sel }); return; }
    if (m && m.mmKey) { dispatchEvent(new KeyboardEvent("keydown", { key: m.mmKey.key, shiftKey: !!m.mmKey.shiftKey })); return; }
    if (m && m.mmDesel) { sel = null; drawSel(); return; }
    if (m && m.mmSize) {   // ievadīts garums / platums: pārvieto austrumu un dienvidu ārsienu, telpas stiepjas līdzi
      let N = M; const { W, D } = m.mmSize;
      if (W && Math.abs(W - M.W) >= 10) N = moveWall({ axis: "x", lo: M.W - T, hi: M.W, ext: true }, W - M.W) || null;
      if (N === M && D && Math.abs(D - M.D) >= 10) N = moveWall({ axis: "y", lo: M.D - T, hi: M.D, ext: true }, D - M.D) || null;
      else if (N && D && Math.abs(D - N.D) >= 10) { const keep = Object.assign({}, M); Object.keys(M).forEach(k => delete M[k]); Object.assign(M, N);
        const N2 = moveWall({ axis: "y", lo: M.D - T, hi: M.D, ext: true }, D - M.D); Object.keys(M).forEach(k => delete M[k]); Object.assign(M, keep); N = N2; }
      if (!N || N === M) { post({ t: "hint", text: "Tik mazu māju nevar: kāda telpa kļūtu šaurāka par minimumu." }); post({ t: "edit", model: clone(M), sel }); return; }
      if (bathFix(N)) { post({ t: "hint", text: BATHMSG }); post({ t: "edit", model: clone(M), sel }); return; }
      post({ t: "edit", model: N, sel, resized: 1 }); return;
    }
    if (m && "mmMove" in m) { moveMode = !!m.mmMove; document.body.style.cursor = moveMode ? MVC : ""; return; }
    if (!m || !("mmPlace" in m)) return;
    document.querySelectorAll(".fdc").forEach(x => x.remove());
    place = m.mmPlace; document.body.style.cursor = place ? "crosshair" : ""; drawGuides();
  });
  const sideOfWall = w => (w.axis === "x" ? (w.lo <= 0 ? "west" : "east") : (w.lo <= 0 ? "north" : "south"));
  function newWin(N, side, a, z) {   // ordinary window in an outer wall, centred on a
    const len = 1000, sp = side === "east" || side === "west" ? N.D : N.W, at = Math.max(T, Math.min(sp - T - len, r10(a - len / 2)));
    const GH = +((N.projekts || {}).logu_augsa) || 2100, w = { len, sill: 900, head: GH, kind: "tilt", o: side === "north" || side === "south" ? "h" : "v", side };
    if (w.o === "h") { w.x = at; w.y = side === "north" ? 0 : N.D - T; } else { w.y = at; w.x = side === "west" ? 0 : N.W - T; w.out = side === "west" ? -1 : 1; }
    if (z != null && z > 0 && z < 2000) { w.sill = r10(z - 600); w.head = w.sill + 1200; if (w.sill < 0) { w.sill = 0; w.head = GH; } }
    N.windows.push(w); return { k: "win", i: N.windows.length - 1, lv: "main" };
  }
  function newGableWin(N, side, a, z, slope) {   // window in the gable above the eave; a sloped one follows the roof
    const len = 1000, u0 = r10(a - len / 2), z0 = slope && GWB ? GWB : Math.max(GWB, r10(z == null ? 2500 : z));
    const gw = slope ? { side, u0, u1: u0 + len, z0 } : { side, u0, u1: u0 + len, z0, win: 1, z1: z0 + 550, kind: "hopper" };
    N.gableWins = N.gableWins || []; N.gableWins.push(gw);
    if (N.loft) { N.loft.windows = N.loft.windows || []; N.loft.windows.push(Object.assign({ len, sill: z0, head: slope ? z0 + 800 : z0 + 550, kind: slope ? "fixed" : "hopper", x: side === "west" ? 0 : N.W - T, y: u0, o: "v", out: side === "west" ? -1 : 1, side }, slope ? { shape: "gable" } : {})); }
    return { k: "gw", i: N.gableWins.length - 1, lv: "main" };
  }
  // mēra likšana: redzams, kur gals pielīp (pildīts kvadrāts = pielipis, aplis = brīvs), un kad līnija iet vienā ķēdē ar citu mēru
  function snapMark(g, q, hit, k) {
    if (hit) mk(g, "rect", { x: q[0] - 1.3 / k, y: q[1] - 1.3 / k, width: 2.6 / k, height: 2.6 / k, fill: ACC, stroke: "#fff", "stroke-width": 0.3 / k });
    else mk(g, "circle", { cx: q[0], cy: q[1], r: 1.2 / k, fill: "#fff", stroke: ACC, "stroke-width": 0.4 / k });
  }
  // plāna darba laukums: māja + terases, lievenis un stabi, kas var iziet ārpus mājas (mērīšanai, novietošanai)
  function outPlan(p) {
    let x0 = 0, y0 = 0, x1 = M.W, y1 = M.D;
    const add = q => { x0 = Math.min(x0, q[0]); y0 = Math.min(y0, q[1]); x1 = Math.max(x1, q[0]); y1 = Math.max(y1, q[1]); };
    (M.terraces || []).forEach(t => t.poly.forEach(add)); ((M.porch && M.porch.poly) || []).forEach(add); (M.posts || []).forEach(q => { add([q.x, q.y]); add([q.x + q.w, q.y + q.d]); });
    return p[0] < x0 - 300 || p[1] < y0 - 300 || p[0] > x1 + 300 || p[1] > y1 + 300;
  }
  function dimHover(cx, cy) {
    for (const bl of blocks()) {
      if (bl.type !== "plan") continue;
      const p = toLocal(bl.g, cx, cy), o = overlay(bl.g); o.querySelectorAll(".gh").forEach(e => e.remove());
      if (outPlan(p)) continue;
      const k = ek(bl), g = mk(o, "g", { class: "gh" }), sx = snapI(bl.lv, "x", p[0]), sy = snapI(bl.lv, "y", p[1]), q = [sx.hit ? sx.v : p[0], sy.hit ? sy.v : p[1]];
      const gl = { stroke: ACC, "stroke-width": 0.25 / k, "stroke-dasharray": `${1 / k} ${0.7 / k}` };
      if (sx.hit) mk(g, "line", Object.assign({ x1: q[0], y1: q[1] - 6 / k, x2: q[0], y2: q[1] + 6 / k }, gl));
      if (sy.hit) mk(g, "line", Object.assign({ x1: q[0] - 6 / k, y1: q[1], x2: q[0] + 6 / k, y2: q[1] }, gl));
      snapMark(g, q, sx.hit || sy.hit, k);
    }
  }
  function dimPreview(cx, cy) {
    const bl = blocks().find(b => b.type === "plan" && b.lv === place.lv); if (!bl) return;
    const k = ek(bl), o = overlay(bl.g), p = toLocal(bl.g, cx, cy), a = place.p0, X = Math.abs(p[0] - a[0]) >= Math.abs(p[1] - a[1]), ax = X ? "x" : "y";
    o.querySelectorAll(".gh").forEach(e => e.remove());
    const g = mk(o, "g", { class: "gh" }), s0i = snapI(place.lv, ax, X ? a[0] : a[1]), s1i = snapI(place.lv, ax, X ? p[0] : p[1]), u0 = s0i.v, u1 = s1i.v, ai = snapAt(place.lv, ax, X ? a[1] : a[0]), at = ai.v;
    const P2 = (u, w) => (X ? [u, w] : [w, u]), s0 = P2(u0, at), s1 = P2(u1, at);
    if (ai.hit) mk(g, "line", Object.assign(X ? { x1: -1500, y1: at, x2: M.W + 1500, y2: at } : { x1: at, y1: -1500, x2: at, y2: M.D + 1500 }, { stroke: ACC, "stroke-width": 0.25 / k, "stroke-dasharray": `${1.2 / k} ${0.8 / k}` }));
    mk(g, "line", { x1: s0[0], y1: s0[1], x2: s1[0], y2: s1[1], stroke: ACC, "stroke-width": 0.5 / k });
    snapMark(g, s0, s0i.hit, k); snapMark(g, s1, s1i.hit, k);
    label(g, (s0[0] + s1[0]) / 2, (s0[1] + s1[1]) / 2 - 2 / k, `${Math.round(Math.abs(u1 - u0))} mm` + (ai.hit ? "  · vienā ķēdē" : ""), k);
  }

  // ---- starpsienas: telpas taisnstūris tiek sadalīts ar 195 mm sienu; sienas posmu var izgriezt (atvere bez durvīm) ----
  const PT = 195; let PMIN = 600;
  function partC(l, axis, v) {   // sienas ass pielīp tā, lai viena virsma sakristu ar citas sienas virsmu
    const h = PT / 2; let best = null;
    snapPts(l, axis).forEach(t => [t + h, t - h].forEach(cc => { if (Math.abs(cc - v) < 150 && (best == null || Math.abs(cc - v) < Math.abs(best - v))) best = cc; }));
    return best != null ? { v: best, hit: true } : { v: r10(v), hit: false };
  }
  function roomRects(X) { return (X.rooms || []).flatMap((rm, ri) => rm.r.map((q, qi) => ({ ri, qi, b: [q[0], q[1], q[0] + q[2], q[1] + q[3]] }))); }
  // kādā taisnstūrī ies starpsiena (centrs c, no a līdz b) un kā to sadalīt
  function partitionSpec(X, vertical, c, a, b) {
    if (b < a) [a, b] = [b, a];
    const h = PT / 2, mid = (a + b) / 2;
    for (const e of roomRects(X)) {
      const [x0, y0, x1, y1] = e.b, U0 = vertical ? x0 : y0, U1 = vertical ? x1 : y1, V0 = vertical ? y0 : x0, V1 = vertical ? y1 : x1;
      if (c < U0 || c > U1 || mid < V0 || mid > V1) continue;
      const fLo = Math.abs(c - h - U0) < 1, fHi = Math.abs(c + h - U1) < 1;   // siena precīzi pie telpas malas: tur paliekošas joslas nav
      if ((!fLo && c - h < U0 + MINR) || (!fHi && c + h > U1 - MINR)) return { err: "Starpsiena par tuvu sienai: telpa kļūtu šaurāka par 600 mm." };
      const a2 = a <= V0 + 300 ? V0 : a, b2 = b >= V1 - 300 ? V1 : b, tA = a2 <= V0 + 1, tB = b2 >= V1 - 1;
      if (b2 - a2 < PMIN) return { err: "Siena par īsu." };
      if (!tA && !tB) return { err: "Siena jāsāk pie telpas malas (ārsienas vai citas sienas)." };
      const P = (u0, v0, u1, v1) => (vertical ? [u0, v0, u1 - u0, v1 - v0] : [v0, u0, v1 - v0, u1 - u0]);
      let parts;
      if (tA && tB) parts = [P(U0, V0, c - h, V1), P(c + h, V0, U1, V1)];
      else if (tA) parts = [P(U0, V0, c - h, b2), P(c + h, V0, U1, b2), P(U0, b2, U1, V1)];
      else parts = [P(U0, V0, U1, a2), P(U0, a2, c - h, V1), P(c + h, a2, U1, V1)];
      parts = parts.filter(q => q[2] > 1 && q[3] > 1);
      return { e, parts, full: tA && tB, a: a2, b: b2 };
    }
    return { err: "Uzklikšķini telpas iekšpusē." };
  }
  function addPartition(N, vertical, c, a, b) {
    const sp = partitionSpec(N, vertical, c, a, b); if (sp.err) return sp;
    const rm = N.rooms[sp.e.ri], q = rm.r[sp.e.qi], cen = r => [r[0] + r[2] / 2, r[1] + r[3] / 2];
    rm.r[sp.e.qi] = sp.parts[0];
    if (sp.full && rm.r.length === 1 && sp.parts.length === 2) {   // pilna siena vienā taisnstūrī: otra puse kļūst par jaunu telpu
      N.rooms.push({ n: "Telpa", en: "Room", r: [sp.parts[1]] });
      N.stampAt = N.stampAt || {}; N.stampScale = N.stampScale || {};
      const ni = N.rooms.length - 1, cn = cen(sp.parts[1]); N.stampAt[ni] = [+cn[0].toFixed(1), +cn[1].toFixed(1)]; N.stampScale[ni] = 0.4;
      const s0 = N.stampAt[sp.e.ri], f = sp.parts[0];
      if (s0 && !(s0[0] >= f[0] && s0[0] <= f[0] + f[2] && s0[1] >= f[1] && s0[1] <= f[1] + f[3])) { const cf = cen(f); N.stampAt[sp.e.ri] = [+cf[0].toFixed(1), +cf[1].toFixed(1)]; }
    } else sp.parts.slice(1).forEach(r => rm.r.push(r));
    void q; return { N };
  }

  // starpsiena drīkst šķērsot esošas sienas un telpas: tā tiek automātiski sadalīta pa telpām un savienota ar sienām
  function acrossPlan(X, vertical, c, a, b) {
    if (b < a) [a, b] = [b, a];
    const segs = [];
    roomRects(X).forEach(e => {
      const [x0, y0, x1, y1] = e.b, U0 = vertical ? x0 : y0, U1 = vertical ? x1 : y1, V0 = vertical ? y0 : x0, V1 = vertical ? y1 : x1;
      if (c < U0 || c > U1) return;
      const sa = Math.max(a, V0), sb = Math.min(b, V1); if (sb - sa < 1) return;
      segs.push([a <= V0 + 300 ? V0 : sa, b >= V1 - 300 ? V1 : sb]);
    });
    segs.sort((p, q) => p[0] - q[0]);
    const ok = segs.filter(sg => !partitionSpec(X, vertical, c, sg[0], sg[1]).err);
    if (!ok.length) { const e = partitionSpec(X, vertical, c, a, b); return { err: e.err || "Šeit starpsienu likt nevar." }; }
    return { segs: ok, a: ok[0][0], b: ok[ok.length - 1][1] };
  }
  function addPartitionAcross(N, vertical, c, a, b) {
    const pl = acrossPlan(N, vertical, c, a, b); if (pl.err) return pl;
    for (const sg of pl.segs) { const r = addPartition(N, vertical, c, sg[0], sg[1]); if (r.err) return r; }
    return { N };
  }
  // sienas posms starp divām telpām: [ass, lo, hi, v0, v1, istaba]
  function wallPair(p) {
    const R = roomRects(M), [x, y] = p;
    for (const a of R) for (const b of R) {
      const A = a.b, B = b.b;
      if (B[0] - A[2] > 0 && B[0] - A[2] <= 300 && x >= A[2] - 20 && x <= B[0] + 20) { const v0 = Math.max(A[1], B[1]), v1 = Math.min(A[3], B[3]); if (y >= v0 && y <= v1) return { axis: "x", lo: A[2], hi: B[0], v0, v1, ri: a.ri }; }
      if (B[1] - A[3] > 0 && B[1] - A[3] <= 300 && y >= A[3] - 20 && y <= B[1] + 20) { const v0 = Math.max(A[0], B[0]), v1 = Math.min(A[2], B[2]); if (x >= v0 && x <= v1) return { axis: "y", lo: A[3], hi: B[1], v0, v1, ri: a.ri }; }
    }
    return null;
  }
  function cutWall(N, w, u0, u1) {
    if (u1 < u0) [u0, u1] = [u1, u0];
    u0 = Math.max(w.v0, u0); u1 = Math.min(w.v1, u1);
    if (u1 - u0 < 100) return { err: "Posms par īsu." };
    const X = w.axis === "x";
    N.rooms[w.ri].r.push(X ? [w.lo, u0, +(w.hi - w.lo).toFixed(1), +(u1 - u0).toFixed(1)] : [u0, w.lo, +(u1 - u0).toFixed(1), +(w.hi - w.lo).toFixed(1)]);
    N.doors = (N.doors || []).filter(d => { const dx = X ? d.o === "v" && Math.abs(d.x - w.lo) < 2 : d.o === "h" && Math.abs(d.y - w.lo) < 2, a = X ? d.y : d.x; return !(dx && a < u1 && a + d.w > u0); });
    return { N };
  }
  function toolPoint(l, axis, v) { const t = snapI(l, axis, v, 250); return t; }

  // ---- sienas posmu gali: velc rokturi, lai posmu pagarinātu (aizpilda izgriezto atveri) vai saīsinātu ----
  function wallSegs(w) {   // redzamie sienas posmi: v0..v1 mīnus izgrieztie laukumi (taisnstūri, kas pilnībā aizpilda sienas joslu)
    const X = w.axis === "x", cov = roomRects(M).map(r => r.b).filter(b => X ? b[0] <= w.lo + 1 && b[2] >= w.hi - 1 : b[1] <= w.lo + 1 && b[3] >= w.hi - 1).map(b => X ? [b[1], b[3]] : [b[0], b[2]]).sort((a, c) => a[0] - c[0]);
    const out = []; let cur = w.v0;
    cov.forEach(([a, b]) => { if (a > cur + 1) out.push([cur, Math.min(a, w.v1)]); cur = Math.max(cur, b); });
    if (cur < w.v1 - 1) out.push([cur, w.v1]);
    return out.filter(q => q[1] - q[0] > 1);
  }
  // visa siena = visi vienas līnijas posmi, savienoti pāri krustojošām sienām (ne gabali starp krustojumiem)
  function linePairs(axis, lo, hi) {
    const R = roomRects(M), out = [], seen = new Set();
    for (const a of R) for (const b of R) {
      const A = a.b, B = b.b, X = axis === "x";
      const g0 = X ? A[2] : A[3], g1 = X ? B[0] : B[1];
      if (Math.abs(g0 - lo) > 1 || Math.abs(g1 - hi) > 1) continue;
      const v0 = X ? Math.max(A[1], B[1]) : Math.max(A[0], B[0]), v1 = X ? Math.min(A[3], B[3]) : Math.min(A[2], B[2]);
      if (v1 - v0 < 1) continue; const key = v0 + "|" + v1 + "|" + a.ri; if (seen.has(key)) continue; seen.add(key);
      out.push({ axis, lo, hi, v0, v1, ri: a.ri });
    }
    return out;
  }
  function wallChains(pairs) {
    const all = pairs.flatMap(p => wallSegs(p)).sort((p, q) => p[0] - q[0]), out = [];
    all.forEach(q => { const l = out[out.length - 1]; if (l && q[0] - l[1] <= 300) l[1] = Math.max(l[1], q[1]); else out.push([q[0], q[1]]); });
    return out;
  }
  function endPair(hw, ix) {   // posms, kurā beidzas sienas gals (no tā ņem robežu tālākai pagarināšanai)
    let best = null, bd = 1e9; const e = hw.seg[ix];
    hw.pairs.forEach(p => { const d = Math.abs((ix ? p.v1 : p.v0) - e); if (d < bd) { bd = d; best = p; } });
    return Object.assign({}, best || hw.w, { endIdx: ix });
  }
  function moveWallEnd(N, w, e0, uRaw, mid) {
    const X = w.axis === "x", cc = (w.lo + w.hi) / 2;
    uRaw = r10(uRaw); let u = Math.max(w.v0, Math.min(w.v1, uRaw)); if (Math.abs(uRaw - e0) < 10) return { err: "Nav ko mainīt." };
    const beyond = w.endIdx === 1 ? uRaw > w.v1 + 10 : uRaw < w.v0 - 10;   // aiz sienas robežas: turpina pa telpām un sienām
    if (beyond) {
      const lim = w.endIdx === 1 ? w.v1 : w.v0;
      if (Math.abs(lim - e0) >= 10) { const r1 = moveWallEnd(N, Object.assign({}, w), e0, lim, mid); if (r1.err && r1.err !== "Šeit nav ko aizpildīt ar sienu.") return r1; }
      PMIN = 150; try { return addPartitionAcross(N, X, cc, lim, uRaw); } finally { PMIN = 600; }   // pagarinot siena var būt īsa
    }
    if (Math.abs(u - e0) < 10) return { err: "Nav ko mainīt." };
    const shrink = (w.endIdx === 1 && u < e0) || (w.endIdx === 0 && u > e0);
    const a = Math.min(e0, u), b = Math.max(e0, u);
    if (shrink) {
      const ps = linePairs(w.axis, w.lo, w.hi).filter(q => q.v1 > a + 1 && q.v0 < b - 1); if (!ps.length) return { err: "Siena nav atrasta." };
      let did = 0, last = null;
      for (const q of ps) { if (Math.min(q.v1, b) - Math.max(q.v0, a) < 100) continue; const r1 = cutWall(N, q, a, b); if (r1.err) last = r1; else did++; }
      return did ? { N } : (last || { err: "Posms par īsu." });
    }
    let ch = 0;
    for (const rm of N.rooms || []) {
      const out = [];
      rm.r.forEach(q => {
        const y0 = X ? q[1] : q[0], y1 = y0 + (X ? q[3] : q[2]), x0 = X ? q[0] : q[1], x1 = x0 + (X ? q[2] : q[3]);
        if (Math.abs(x0 - w.lo) > 1 || Math.abs(x1 - w.hi) > 1 || y1 <= a + 1 || y0 >= b - 1) { out.push(q); return; }
        ch++;
        const mkq = (ya, yb) => X ? [q[0], ya, q[2], +(yb - ya).toFixed(1)] : [ya, q[1], +(yb - ya).toFixed(1), q[3]];
        if (a - y0 > 1) out.push(mkq(y0, a)); if (y1 - b > 1) out.push(mkq(b, y1));
      });
      if (!out.length && rm.r.length) return { err: "Telpa pazustu." };
      rm.r = out;
    }
    return ch ? { N } : { err: "Šeit nav ko aizpildīt ar sienu." };
  }
  let hovWall = null;
  function nearHandle(e) {   // tuvākais sienas gala rokturis ekrāna pikseļos (liels uztveršanas laukums)
    if (!hovWall) return -1;
    const hw = hovWall, X = hw.w.axis === "x", c = (hw.w.lo + hw.w.hi) / 2, m = hw.bl.g.getScreenCTM(); if (!m) return -1;
    let best = -1, bd = 18;
    hw.seg.forEach((v, i) => { const q = new DOMPoint(X ? c : v, X ? v : c).matrixTransform(m), d = Math.hypot(q.x - e.clientX, q.y - e.clientY); if (d < bd) { bd = d; best = i; } });
    return best;
  }
  function commitWend() {
    const d = drag; drag = null; document.body.style.cursor = ""; document.querySelectorAll("g.mm-ov .gh").forEach(x => x.remove());
    post({ t: "hint", text: "" });
    if (!d || Math.abs(d.u - d.e0) < 10) return;
    const N = clone(M), w = endPair(d.hw, d.ix), r = moveWallEnd(N, w, d.e0, d.u, (d.e0 + d.fixed) / 2);
    if (r.err) { post({ t: "hint", text: r.err }); return; }
    post({ t: "edit", model: r.N || N, sel: null });
  }
  // ---- terases rīks: polilīnija plānā (klikšķi punktos; pēc noklusējuma taisni leņķi, Shift = brīvi) ----
  function terBlock() { return blocks().find(b => b.type === "plan" && b.lv === "main"); }
  function terPt(p, shift) {
    let x = snapAx("main", "x", p[0], 150), y = snapAx("main", "y", p[1], 150);
    const pts = place.pts || [];
    if (pts.length && !shift && !place.rect) { const a = pts[pts.length - 1]; if (Math.abs(x - a[0]) >= Math.abs(y - a[1])) y = a[1]; else x = a[0]; }
    return [x, y];
  }
  function terPreview(cx, cy, shift) {
    const bl = terBlock(); if (!bl) return;
    const p = toLocal(bl.g, cx, cy), o = overlay(bl.g); o.querySelectorAll(".gh").forEach(e => e.remove());
    const k = ek(bl), g = mk(o, "g", { class: "gh" }), pts = place.pts || [], q = terPt(p, shift), all = place.rect && pts.length ? [pts[0], [q[0], pts[0][1]], q, [pts[0][0], q[1]], pts[0]] : pts.concat([q]);
    if (all.length > 1) mk(g, "polyline", { points: all.map(a => a.join(",")).join(" "), fill: pts.length > 1 ? "rgba(34,102,216,.12)" : "none", stroke: ACC, "stroke-width": 1.2 / k, "stroke-dasharray": `${2.4 / k} ${1.6 / k}` });
    pts.forEach(a => snapMark(g, a, true, k)); snapMark(g, q, false, k);
    const last = pts[pts.length - 1];
    label(g, q[0] + 3 / k, q[1] - 3 / k, !last ? "Terase: uzklikšķini pirmo stūri" : `${Math.round(Math.hypot(q[0] - last[0], q[1] - last[1]))} mm` + (pts.length > 2 ? "  · dubultklikšķis vai Enter noslēdz" : ""), k);
  }
  function terCommit(pts, up, name) {
    const N = clone(M); N.terraces = (N.terraces || []).concat([{ name: name || "Terase", poly: pts, th: 120, preset: "deck", tex: null, texRot: 0, texW: 1000, corners: false, up }]);
    place = null; document.body.style.cursor = ""; document.querySelectorAll("g.mm-ov .gh").forEach(x => x.remove());
    post({ t: "edit", model: N, sel: { k: "ter", i: N.terraces.length - 1, lv: "main" }, placed: true });
  }
  // jauna terase, kad jau ir cita: jautā, vai likt virs esošās (pakāpiens) vai vienā līmenī
  function terFinish() {
    if (place.asking) return;
    const pts = (place.pts || []).filter((a, i, A) => !i || Math.hypot(a[0] - A[i - 1][0], a[1] - A[i - 1][1]) > 50);
    if (pts.length < 3) { post({ t: "hint", text: "Terasei vajag vismaz 3 punktus." }); return; }
    const T = M.terraces || [];
    if (!T.length) { terCommit(pts, 0); return; }
    const cx = pts.reduce((s, q) => s + q[0], 0) / pts.length, cy = pts.reduce((s, q) => s + q[1], 0) / pts.length;
    let par = T.length - 1;   // esošā terase, kurā ietilpst jaunā centrs (citādi pēdējā)
    T.forEach((t, i) => { const xs = t.poly.map(q => q[0]), ys = t.poly.map(q => q[1]); if (cx >= Math.min(...xs) && cx <= Math.max(...xs) && cy >= Math.min(...ys) && cy <= Math.max(...ys)) par = i; });
    const up0 = T[par].up || 0, RISE = 150;
    place.asking = true;
    const box = document.createElement("div");
    box.style.cssText = "position:fixed;z-index:99;left:50%;top:40%;transform:translateX(-50%);background:#fff;color:#1c2024;border:1px solid #2266d8;border-radius:10px;box-shadow:0 8px 30px rgba(0,0,0,.25);padding:14px;font:14px system-ui,sans-serif;display:grid;gap:8px;min-width:300px;height:auto!important;max-height:none!important;overflow:visible!important";
    const q = document.createElement("div"); q.textContent = "Kur novietot jauno terasi?"; q.style.cssText = "font-weight:600"; box.appendChild(q);
    const done = (up, name) => { box.remove(); place && (place.asking = false); terCommit(pts, up, name); };
    [["Virs esošās (pakāpiens, +" + RISE + " mm)", () => done(up0 + RISE, "Pakāpiens")], ["Vienā līmenī ar esošo", () => done(up0)], ["Atcelt", () => { box.remove(); place && (place.asking = false); place.pts = []; }]].forEach(([t, f], i) => {
      const b = document.createElement("button"); b.type = "button"; b.textContent = t; b.style.cssText = "padding:8px 10px;border-radius:8px;border:1px solid #c9ced4;background:" + (i === 0 ? "#2266d8;color:#fff;border-color:#2266d8" : "#f4f5f7") + ";cursor:pointer;font:inherit";
      b.addEventListener("pointerdown", e => e.stopPropagation()); b.onclick = f; box.appendChild(b);
    });
    document.documentElement.appendChild(box);
  }
  function postPreview(cx, cy) {
    const bl = terBlock(); if (!bl) return;
    const p = toLocal(bl.g, cx, cy), o = overlay(bl.g); o.querySelectorAll(".gh").forEach(e => e.remove());
    const k = ek(bl), g = mk(o, "g", { class: "gh" }), x = snapAx("main", "x", p[0], 150), y = snapAx("main", "y", p[1], 150);
    rect(g, [x - 150, y - 150, x + 150, y + 150], true, k, 0); label(g, x + 200, y - 200, "Stabs 300 × 300", k);
  }
  function postClick(e) {
    const bl = terBlock(); if (!bl) return true;
    const p = toLocal(bl.g, e.clientX, e.clientY), x = snapAx("main", "x", p[0], 150), y = snapAx("main", "y", p[1], 150), N = clone(M);
    N.posts = (N.posts || []).concat([{ name: "Stabs", x: x - 150, y: y - 150, w: 300, d: 300 }]);
    place = null; document.body.style.cursor = ""; document.querySelectorAll("g.mm-ov .gh").forEach(q => q.remove());
    post({ t: "edit", model: N, sel: { k: "post", i: N.posts.length - 1, lv: "main" }, placed: true }); return true;
  }
  function terClick(e) {
    const bl = terBlock(); if (!bl) return true;
    if (place.asking) return true;
    place.pts = place.pts || [];
    const p = terPt(toLocal(bl.g, e.clientX, e.clientY), e.shiftKey), pts = place.pts;
    if (place.rect) {   // taisnstūris: pirmais klikšķis un pretējais stūris
      if (!pts.length) { pts.push(p); terPreview(e.clientX, e.clientY, e.shiftKey); return true; }
      const a = pts[0]; if (Math.abs(p[0] - a[0]) < 100 || Math.abs(p[1] - a[1]) < 100) { post({ t: "hint", text: "Terase par šauru. Uzklikšķini tālāk." }); return true; }
      place.pts = [a, [p[0], a[1]], p, [a[0], p[1]]]; terFinish(); return true;
    }
    if (pts.length > 2 && Math.hypot(p[0] - pts[0][0], p[1] - pts[0][1]) < 250) { terFinish(); return true; }
    if (!pts.length || Math.hypot(p[0] - pts[pts.length - 1][0], p[1] - pts[pts.length - 1][1]) > 50) pts.push(p);
    terPreview(e.clientX, e.clientY, e.shiftKey); return true;
  }
  function wallPreview(cx, cy) {
    for (const bl of blocks()) {
      if (bl.type !== "plan" || bl.lv !== "main") continue;
      const p = toLocal(bl.g, cx, cy), o = overlay(bl.g); o.querySelectorAll(".gh").forEach(e => e.remove());
      if (p[0] < -300 || p[1] < -300 || p[0] > M.W + 300 || p[1] > M.D + 300) continue;
      const k = ek(bl), g = mk(o, "g", { class: "gh" });
      if (place.t === "cut") {
        const w = place.w || wallPair(p); if (!w) { label(g, p[0], p[1] - 2 / k, "Uzvelc uz iekšējās sienas", k); return; }
        const X = w.axis === "x"; let a = w.v0, b = w.v1;
        if (place.w) { const u1 = snapAx("main", X ? "y" : "x", X ? p[1] : p[0], 150); if (Math.abs(u1 - place.u0) >= 150) { a = Math.max(w.v0, Math.min(place.u0, u1)); b = Math.min(w.v1, Math.max(place.u0, u1)); } }
        const bb = X ? [w.lo, a, w.hi, b] : [a, w.lo, b, w.hi];
        rect(g, bb, true, k, 0); label(g, bb[0], bb[1] - 2.2 / k, place.w ? `${Math.round(b - a)} mm` : "klikšķis: sākums · otrs klikšķis tajā pašā vietā: visa siena", k); return;
      }
      const sx = place.p0 ? null : partC(bl.lv, "x", p[0]), sy = place.p0 ? null : partC(bl.lv, "y", p[1]);
      if (!place.p0) { snapMark(g, [sx.hit ? sx.v : p[0], sy.hit ? sy.v : p[1]], sx.hit || sy.hit, k); label(g, p[0], p[1] - 2.2 / k, "Starpsiena: uzklikšķini sākumu (pie sienas)", k); return; }
      const a = place.p0, vertical = Math.abs(p[1] - a[1]) >= Math.abs(p[0] - a[0]), h = PT / 2;
      const c = partC(bl.lv, vertical ? "x" : "y", vertical ? a[0] : a[1]).v, v0 = snapAx(bl.lv, vertical ? "y" : "x", vertical ? a[1] : a[0], 300), v1 = snapAx(bl.lv, vertical ? "y" : "x", vertical ? p[1] : p[0], 300);
      const sp = acrossPlan(M, vertical, c, v0, v1), A = sp.err ? Math.min(v0, v1) : sp.a, B = sp.err ? Math.max(v0, v1) : sp.b;
      const bb = vertical ? [c - h, A, c + h, B] : [A, c - h, B, c + h];
      rect(g, bb, true, k, 0); label(g, bb[0], bb[1] - 2.2 / k, sp.err ? sp.err : `${Math.round(B - A)} mm`, k); return;
    }
  }

  // ---- fasādes mēri: viens klikšķis, tad izvēle starp augstuma atzīmi un lineāru mēru ----
  const fdCache = {};
  function fCand(bl) {
    if (fdCache[bl.side]) return fdCache[bl.side];
    const U = [0], Z = [0], lim = span(bl.side) * 1.5;
    bl.g.querySelectorAll("rect,polygon,line,path,polyline").forEach(n => {
      if (n.closest("g.mm-ov") || n.closest("defs") || n.closest("clipPath") || n.hasAttribute("transform")) return;
      let b; try { b = n.getBBox(); } catch (_) { return; }
      if (!isFinite(b.x) || b.width > lim) return;
      U.push(b.x, b.x + b.width); Z.push(-b.y, -(b.y + b.height));
    });
    return (fdCache[bl.side] = { U, Z });
  }
  function fSnap(bl, p) {
    const c = fCand(bl), near = (arr, v) => { let r = null; arr.forEach(x => { if (Math.abs(x - v) < 150 && (r == null || Math.abs(x - v) < Math.abs(r - v))) r = x; }); return r; };
    const u = near(c.U, p[0]), z = near(c.Z, -p[1]);
    return { u: Math.round(u != null ? u : p[0]), z: Math.round(z != null ? z : -p[1]), hu: u != null, hz: z != null };
  }
  const zTxt = z => (z > 0 ? "+" : z < 0 ? "−" : "±") + (Math.abs(z) / 1000).toFixed(3).replace(".", ",");
  function fChooser(cx, cy, bl, q) {
    document.querySelectorAll(".fdc").forEach(x => x.remove());
    const d = document.createElement("div"); d.className = "fdc";
    d.style.cssText = `position:fixed;left:${Math.max(4, Math.min(cx + 12, innerWidth - 200))}px;top:${Math.max(4, Math.min(cy + 12, innerHeight - 110))}px;z-index:99;background:#fff;border:1px solid #bbb;border-radius:9px;box-shadow:0 8px 24px rgba(0,0,0,.28);padding:6px;display:grid;gap:5px;font:600 13px system-ui,sans-serif;width:188px;color:#222`;
    const mkb = (t, fn) => { const b = document.createElement("button"); b.type = "button"; b.textContent = t; b.style.cssText = "padding:9px 11px;border:1px solid #cfcac0;border-radius:6px;background:#f6f4ef;cursor:pointer;text-align:left;font:inherit;color:#222"; b.onclick = ev => { ev.stopPropagation(); fn(); }; return b; };
    d.append(mkb("Augstuma atzīme  " + zTxt(q.z), () => {
      const N = clone(M); N.projekts = N.projekts || {}; (N.projekts.fdims = N.projekts.fdims || []).push({ s: bl.side, k: "lvl", z: q.z });
      d.remove(); place = null; document.body.style.cursor = ""; post({ t: "edit", model: N, sel: null, placed: true });
    }), mkb("Lineārs mērs", () => { place.fm = true; d.remove(); post({ t: "hint", text: "Uzklikšķini mēra otro punktu. Līnija tiek novietota automātiski." }); }));
    ["pointerdown", "pointerup", "wheel"].forEach(t => d.addEventListener(t, ev => ev.stopPropagation()));
    document.documentElement.appendChild(d);
  }
  const fdAt = (H, p) => (H ? Math.round(-p[1] / 50) * 50 : Math.round(p[0] / 50) * 50);   // mēra līnijas vieta: z (horiz.) vai u (vert.)
  function fdimClick(bl, p, cx, cy) {
    const q = fSnap(bl, p), a = place.fp;
    if (a && place.fm && place.f2) {   // trešais klikšķis: kur novietot mēra līniju
      const f = place.f2; if (f.side !== bl.side) return { miss: "Mēra līnija jāliek tajā pašā fasādē." };
      const N = clone(M); N.projekts = N.projekts || {};
      (N.projekts.fdims = N.projekts.fdims || []).push({ s: f.side, k: "lin", o: f.H ? "h" : "v", a: f.a, b: f.b, p: f.p, at: fdAt(f.H, p) });
      return { N, sel: null };
    }
    if (a && place.fm) {
      if (a.side !== bl.side) return { miss: "Otrajam punktam jābūt tajā pašā fasādē." };
      const H = Math.abs(q.u - a.u) >= Math.abs(q.z - a.z), A = H ? a.u : a.z, B = H ? q.u : q.z;
      if (Math.abs(B - A) < 100) return { miss: "Mērs par īsu. Uzklikšķini tālāk." };
      const pa = H ? a.z : a.u, pb = H ? q.z : q.u, lo = A <= B;
      place.f2 = { side: bl.side, H, a: Math.min(A, B), b: Math.max(A, B), p: lo ? [pa, pb] : [pb, pa] };
      return { pending: "Uzklikšķini, kur novietot mēra līniju." };
    }
    place.fp = { side: bl.side, u: q.u, z: q.z }; place.fm = false; place.f2 = null;
    fChooser(cx, cy, bl, q);
    return { pending: "Izvēlies: augstuma atzīme vai lineārs mērs." };
  }
  function fdimMove(e) {
    document.querySelectorAll("g.mm-ov .gh").forEach(x => x.remove());
    const eave = (M.jumts && M.jumts.eave) || 2600, ov = (M.jumts && M.jumts.ov) || 0;
    for (const bl of blocks()) {
      if (bl.type !== "elev") continue;
      const p = toLocal(bl.g, e.clientX, e.clientY), sp = span(bl.side), rl = place.f2 ? 3500 : 200;
      if (p[0] < -rl || p[0] > sp + rl || p[1] > (place.f2 ? 3500 : 300) || p[1] < -(eave + sp)) continue;
      const o = overlay(bl.g), k = ek(bl), g = mk(o, "g", { class: "gh" }), q = fSnap(bl, p), a = place.fp, st = { stroke: ACC, "stroke-width": 0.4 / k };
      if (a && place.fm && place.f2 && place.f2.side === bl.side) {   // mēra līnijas novietojums
        const f = place.f2, at = fdAt(f.H, p), X = f.H;
        const P2 = (c, d) => (X ? [c, d] : [d, c]);
        const s0 = P2(f.a, -at), s1 = P2(f.b, -at), e0 = P2(f.a, -f.p[0]), e1 = P2(f.b, -f.p[1]);
        if (!X) { s0[0] = at; s1[0] = at; s0[1] = -f.a; s1[1] = -f.b; e0[0] = f.p[0]; e0[1] = -f.a; e1[0] = f.p[1]; e1[1] = -f.b; }
        mk(g, "line", Object.assign({ x1: e0[0], y1: e0[1], x2: s0[0], y2: s0[1] }, st, { "stroke-dasharray": `${1 / k} ${0.7 / k}` }));
        mk(g, "line", Object.assign({ x1: e1[0], y1: e1[1], x2: s1[0], y2: s1[1] }, st, { "stroke-dasharray": `${1 / k} ${0.7 / k}` }));
        mk(g, "line", Object.assign({ x1: s0[0], y1: s0[1], x2: s1[0], y2: s1[1] }, st));
        label(g, (s0[0] + s1[0]) / 2, (s0[1] + s1[1]) / 2 - 2 / k, `${Math.round(f.b - f.a)} mm`, k);
        return true;
      }
      snapMark(g, [q.u, -q.z], q.hu || q.hz, k);
      if (a && place.fm && a.side === bl.side) {
        const H = Math.abs(q.u - a.u) >= Math.abs(q.z - a.z), x2 = H ? q.u : a.u, y2 = H ? -a.z : -q.z;
        mk(g, "line", { x1: a.u, y1: -a.z, x2, y2, stroke: ACC, "stroke-width": 0.5 / k });
        label(g, (a.u + x2) / 2, (-a.z + y2) / 2 - 2 / k, `${Math.round(H ? Math.abs(q.u - a.u) : Math.abs(q.z - a.z))} mm`, k);
        label(g, q.u + 6 / k, -q.z - 3 / k, "±0 → " + zTxt(q.z), k);
      } else if (!a || !place.fm) {   // augstuma atzīme no ±0,000 redzama jau pie kursora
        const lx = sp + ov + 1300;
        mk(g, "line", Object.assign({ x1: -300, y1: -q.z, x2: lx, y2: -q.z }, st, { "stroke-dasharray": `${1.2 / k} ${0.9 / k}`, opacity: 0.55 }));
        label(g, q.u + 6 / k, -q.z - 3 / k, "±0 → " + zTxt(q.z), k);
      }
      return true;
    }
    return false;
  }

  // krāsas spainis (SketchUp "Paint Bucket"): klikšķis uzliek materiālu, Alt+klikšķis paņem to no elementa
  const svgCur = (svg, x, y, fb) => `url("data:image/svg+xml;utf8,${encodeURIComponent(svg)}") ${x} ${y}, ${fb}`;
  const BKC = svgCur("<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 32 32'><g stroke='#fff' stroke-width='3' stroke-linejoin='round' fill='#fff'><path d='M5 14 14 5l10 10-9 9z'/></g><g stroke='#1d2733' stroke-width='1.6' stroke-linejoin='round' fill='#e9f1fb'><path d='M5 14 14 5l10 10-9 9z'/><path d='M7 14h16' fill='none'/></g><path d='M25 20c1.6 2.2 2.4 3.6 2.4 4.6a2.4 2.4 0 0 1-4.8 0c0-1 .8-2.4 2.4-4.6z' fill='#2266d8' stroke='#fff' stroke-width='1'/></svg>", 5, 27, "cell");
  const PIC = svgCur("<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 32 32'><g stroke='#fff' stroke-width='3.4' stroke-linecap='round' fill='none'><path d='M6 26l3-1 12-12-3-3L6 22z'/><path d='M19 8l5-5 5 5-5 5'/></g><g stroke='#1d2733' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round' fill='none'><path d='M6 26l3-1 12-12-3-3L6 22z' fill='#e9f1fb'/><path d='M19 8l5-5 5 5-5 5z' fill='#2266d8'/></g></svg>", 5, 27, "copy");
  function bucketTarget(cx, cy) {
    const h = hit(cx, cy);
    if (h && !h.wall && h.bl.type === "elev" && (h.it.k === "win" || h.it.k === "gw" || h.it.k === "door")) return { k: "frame" };
    if (h && !h.wall && h.it.k === "post") return { k: "post", i: h.it.i };
    if (h && (h.it.k === "ter" || h.it.k === "tedge" || h.it.k === "tvert")) return { k: "ter", i: h.it.k === "ter" ? h.it.i : Math.floor(h.it.i / 100) };
    if (!h || (h.bl.type === "elev" && h.it && !["gut", "win", "gw", "door"].includes(h.it.k))) { const bl = blocks().find(b => { if (b.type !== "elev") return false; const r = b.g.getBoundingClientRect(); return cx >= r.left && cx <= r.right && cy >= r.top && cy <= r.bottom; }); if (bl) return { k: "fas" }; }
    return null;
  }
  function bucketClick(e) {
    const t = bucketTarget(e.clientX, e.clientY), P = M.projekts || {};
    if (!t) { post({ t: "hint", text: "Spainis darbojas uz stabu, terasi, logiem un fasādes laukumu (fasādes rasējumā)." + (window.__dbg ? " [" + (hit(e.clientX, e.clientY) || {}).it + "]" : "") }); return true; }
    if (e.altKey) {   // paņem materiālu
      const o = t.k === "post" ? M.posts[t.i] : t.k === "ter" ? M.terraces[t.i] : t.k === "frame" ? { col: P.logu_hex, ral: /^RAL/.test(P.logu_tonis || "") ? P.logu_tonis : null } : { col: P.fasade_hex, ral: P.fasade_ral };
      if (t.k === "fas" && !o.col) { post({ t: "hint", text: "Fasādei nav izvēlēta RAL krāsa, nav ko paņemt." }); return true; }
      place.mat = { col: o.col || null, ral: o.ral || null, tex: o.tex || null, texW: o.texW || 1000, texRot: o.texRot || 0 };
      post({ t: "bmat", mat: place.mat }); post({ t: "hint", text: "Materiāls paņemts." }); return true;
    }
    const m = place.mat || {}, N = clone(M);
    if (t.k === "frame") {
      if (!m.col) { post({ t: "hint", text: "Logu un durvju rāmjiem der tikai krāsa (RAL vai brīva)." }); return true; }
      N.projekts = N.projekts || {}; N.projekts.logu_hex = m.col; N.projekts.logu_tonis = m.ral || "Cita krāsa";
    } else if (t.k === "fas") {
      if (!m.col) { post({ t: "hint", text: "Fasādei der tikai krāsa (RAL vai brīva), ne tekstūra." }); return true; }
      N.projekts = N.projekts || {}; N.projekts.fasade_hex = m.col; if (m.ral) N.projekts.fasade_ral = m.ral; else delete N.projekts.fasade_ral;
    } else {
      const o = t.k === "post" ? N.posts[t.i] : N.terraces[t.i];
      ["col", "ral", "tex"].forEach(k => { if (m[k]) o[k] = m[k]; else delete o[k]; });
      if (m.tex) { o.texW = m.texW || 1000; o.texRot = m.texRot || 0; }
      if (t.k === "ter" && !m.tex) delete o.tex;
    }
    post({ t: "edit", model: N, sel }); return true;
  }
  function placeAt(cx, cy) {
    const P = place, N = clone(M), eave = (M.jumts && M.jumts.eave) || 2600;
    for (const bl of blocks()) {
      const p = toLocal(bl.g, cx, cy), bb = bl.g.getBBox(); void bb;
      if (bl.type === "plan") {
        if (outPlan(p)) continue;
        if (P.t === "dim") {   // divi klikšķi: sākums un beigas; ass pēc garākā virziena
          if (!P.p0) { P.p0 = [p[0], p[1]]; P.lv = bl.lv; return { pending: "Tagad uzklikšķini mēra otro galu." }; }
          const a = P.p0, X = Math.abs(p[0] - a[0]) >= Math.abs(p[1] - a[1]), ax = X ? "x" : "y";
          const u0 = snapAx(P.lv, ax, X ? a[0] : a[1]), u1 = snapAx(P.lv, ax, X ? p[0] : p[1]);
          if (Math.abs(u1 - u0) < 100) return { miss: "Mērs par īsu. Uzklikšķini tālāk." };
          const L = lv(P.lv, N); L.userDims = L.userDims || []; L.userDims.push([ax, snapAt(P.lv, ax, X ? a[1] : a[0]).v, Math.min(u0, u1), Math.max(u0, u1)]);
          return { N, sel: { k: "dim", i: L.userDims.length - 1, lv: P.lv } };
        }
        if (P.t === "wall" || P.t === "cut") {
          if (bl.lv !== "main") return { miss: "Sienas var likt 1. stāva plānā." };
          if (P.t === "cut") {
            if (!P.w) { const w = wallPair(p); if (!w) return { miss: "Uzklikšķini uz iekšējās sienas (starp divām telpām)." }; P.w = w; P.u0 = snapAx("main", w.axis === "x" ? "y" : "x", w.axis === "x" ? p[1] : p[0], 150); return { pending: "Tagad uzklikšķini posma otru galu. Klikšķis tajā pašā vietā izgriež visu sienas posmu." }; }
            const X = P.w.axis === "x", u1 = snapAx("main", X ? "y" : "x", X ? p[1] : p[0], 150);
            const r = Math.abs(u1 - P.u0) < 150 ? cutWall(N, P.w, P.w.v0, P.w.v1) : cutWall(N, P.w, P.u0, u1);
            if (r.err) { P.w = null; return { miss: r.err }; }
            return { N, sel: null };
          }
          if (!P.p0) { P.p0 = [p[0], p[1]]; P.lv = bl.lv; return { pending: "Tagad uzklikšķini sienas otru galu (pie ārsienas vai citas sienas)." }; }
          const a = P.p0, vertical = Math.abs(p[1] - a[1]) >= Math.abs(p[0] - a[0]);
          const c = partC("main", vertical ? "x" : "y", vertical ? a[0] : a[1]).v, v0 = snapAx("main", vertical ? "y" : "x", vertical ? a[1] : a[0], 300), v1 = snapAx("main", vertical ? "y" : "x", vertical ? p[1] : p[0], 300);
          const r = addPartitionAcross(N, vertical, c, v0, v1);
          if (r.err) { P.p0 = null; return { miss: r.err }; }
          return { N, sel: null };
        }
        if (P.t === "furn") {
          const e = clone(P.entry);
          if (P.center) { e[1] = r10(p[0]); e[2] = r10(p[1]); } else { e[1] = r10(p[0] - P.w / 2); e[2] = r10(p[1] - P.h / 2); }
          const L = lv(bl.lv, N); L.furniture = L.furniture || []; L.furniture.push(e);
          return { N, sel: { k: "furn", i: L.furniture.length - 1, lv: bl.lv }, fit: true };
        }
        const w = wallAt(bl.lv, p); if (!w) return { miss: "Uzklikšķini uz sienas." };
        if (P.t === "door") {
          const ext = !!w.ext, wd = ext ? 1000 : 800, X = w.axis === "x", L = lv(bl.lv, N);
          const along = r10((X ? p[1] : p[0]) - wd / 2), d = { o: X ? "v" : "h", hinge: "s", side: ext ? (sideOfWall(w) === "south" || sideOfWall(w) === "east" ? 1 : -1) : -1, w: wd, th: +(w.hi - w.lo).toFixed(1) };
          if (X) { d.x = w.lo; d.y = along; } else { d.y = w.lo; d.x = along; }
          if (ext && sideOfWall(w) === "south") d.entry = true;
          L.doors = L.doors || []; L.doors.push(d);
          return { N, sel: { k: "door", i: L.doors.length - 1, lv: bl.lv } };
        }
        if (!w.ext) return { miss: "Logu var ielikt tikai ārsienā." };
        const side = sideOfWall(w), a = w.axis === "x" ? p[1] : p[0];
        if (bl.lv === "loft") { if (side === "east" || side === "west") return { N, sel: newGableWin(N, side, a, null, P.t === "gwin") }; return { miss: "Mansardā logu var ielikt gala sienā." }; }
        if (P.t === "gwin") return { miss: "Slīpo logu ieliec gala fasādē virs dzegas." };
        return { N, sel: newWin(N, side, a, null) };
      } else {
        const s = bl.side, sp = span(s);
        const rl = P.t === "dim" && P.f2 ? 3500 : 200;
        if (p[0] < -rl || p[0] > sp + rl || p[1] > (P.f2 && P.t === "dim" ? 3500 : 300) || p[1] < -(eave + sp)) continue;
        if (P.t === "dim") return fdimClick(bl, p, cx, cy);
        if (P.t !== "win" && P.t !== "gwin") return { miss: "Mēbeles un durvis ieliec plānā." };
        const a = mapU(s, p[0]), z = -p[1], gable = s === "east" || s === "west";
        if (gable && (z > eave - 150 || P.t === "gwin")) return { N, sel: newGableWin(N, s, a, Math.max(z, eave - 400), P.t === "gwin") };
        return { N, sel: newWin(N, s, a, z) };
      }
    }
    return { miss: "Uzklikšķini plānā vai fasādē." };
  }

  // view (zoom) is kept between rebuilds
  let vt = 0;
  window.MMZ_CANCEL = () => { drag = null; document.body.style.cursor = ""; document.querySelectorAll("g.mm-ov .gh").forEach(x => x.remove()); drawSel(); };   // otrs pirksts: atceļ vilkšanu, sāk tuvināšanu
  window.MMZ_ON = () => { if (!drag) drawSel(); clearTimeout(vt); vt = setTimeout(() => window.MMZ && post({ t: "view", view: window.MMZ.get() }), 120); };

  addEventListener("load", () => setTimeout(() => {
    drawSel();
    let out = [];
    try { out = window.MM_RUN_CHECK ? window.MM_RUN_CHECK().out : []; } catch (err) { out = ["Pārbaudi neizdevās palaist: " + err.message]; }
    // a newly inserted piece of furniture is pushed into its room once it has been drawn
    if (ED.place && sel && sel.k === "furn") {
      const bl = blocks().find(x => x.type === "plan" && x.lv === sel.lv), boxes = bl && furnBoxes(bl), b = boxes && boxes[sel.i];
      if (b) { let [dx, dy, rm] = fit(sel.lv, b, 0, 0); [dx, dy] = collide(sel.lv, b, dx, dy, boxes, [sel.i], rm, true); if (dx || dy) { const N = clone(M); shiftF(lv(sel.lv, N).furniture[sel.i], dx, dy); post({ t: "replace", model: N, sel }); return; } }
    }
    post({ t: "ready", check: out });
  }, 120));
})();
