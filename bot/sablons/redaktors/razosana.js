// ---- Ražošanas pakete: izvēlas lapas un izveido visu komplektu (logu plāns, logu un ārdurvju specifikācija, skices un pamatu lapa) ----
(function () {
  const ITEMS = [
    ["skice", "Skices lapa (A3 .html)", true],
    ["pamati", "Pamatu un vainaga plāns (ietverts lapā, ja ieslēgts)", true],
    ["logplans", "Logu plāns (SVG)", true],
    ["logspec", "Logu specifikācija", true],
    ["durspec", "Ārdurvju specifikācija", true],
    ["elektr", "Elektrības plāns (automātisks priekšlikums)", false],
  ];
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const SIDE = { north: "Ziemeļi", south: "Dienvidi", east: "Austrumi", west: "Rietumi" };
  const isExt = d => d.entry || (+d.th || 0) >= 250;
  const winKey = w => [w.len, (w.head || 2100) - (w.sill || 0), w.sill || 0, w.kind || ""].join("|");
  const KIND = { tilt: "Kipējs", fix: "Fiksēts", casement: "Vērtnes", sliding: "Bīdāms", hopper: "Augšā atverams", parts: "Stiklota siena" };
  function winRows() {
    const m = window.MM_VIZ3D && MM_VIZ3D.model ? MM_VIZ3D.model() : null; return (m && m.windows) || [];
  }
  function tableHtml(title, head, rows, mdl) {
    return `<section><h2>${esc(title)}</h2><table><thead><tr>${head.map(h => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows.map(r => `<tr>${r.map(c => `<td>${esc(c)}</td>`).join("")}</tr>`).join("")}</tbody></table></section>`;
  }
  function page(mdl, title, body) {
    return `<!doctype html><html lang="lv"><meta charset="utf-8"><title>${esc(title)}</title><style>@page{size:A3 landscape;margin:12mm}body{font:13px/1.4 Arial,sans-serif;color:#1d1d1d;margin:0;padding:16mm}h1{font-size:20px;margin:0 0 4px}h2{font-size:15px;margin:22px 0 8px}p.s{color:#666;margin:0 0 16px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #888;padding:6px 9px;text-align:left}th{background:#2a2e32;color:#fff;font-weight:600}tr:nth-child(even) td{background:#f4f5f6}svg{width:100%;height:auto;border:1px solid #bbb}</style><h1>${esc(title)}</h1><p class="s">${esc((mdl.projekts && mdl.projekts.modela_nosaukums) || mdl.nosaukums || "")} · ${esc(mdl.id)} · ${new Date().toLocaleDateString("lv-LV")}</p>${body}</html>`;
  }
  function winSchedule(mdl) {
    const W = mdl.windows || [], G = mdl.gableWins || [], rows = [];
    W.forEach((w, i) => rows.push(["L" + (i + 1), w.len, (w.head || 2100) - (w.sill || 0), w.sill || 0, SIDE[w.side] || w.side || "", KIND[w.kind] || w.kind || "", ""]));
    G.forEach((g, i) => rows.push(["G" + (i + 1), Math.round(g.u1 - g.u0), g.z1 != null ? Math.round(g.z1 - g.z0) : "slīps", Math.round(g.z0), SIDE[g.side] || g.side || "", "Gala logs (seko jumtam)", ""]));
    const cnt = {}; W.forEach(w => { cnt[winKey(w)] = (cnt[winKey(w)] || 0) + 1; });
    const sum = Object.entries(cnt).map(([k, n]) => { const [l, h, s, kd] = k.split("|"); return [l + " × " + h, "parapets " + s, KIND[kd] || kd, n + " gab."]; });
    return tableHtml("Logu specifikācija", ["Poz.", "Platums, mm", "Augstums, mm", "Parapets, mm", "Fasāde", "Tips", "Piezīmes"], rows) + tableHtml("Kopsavilkums pēc izmēra", ["Izmērs", "Parapets", "Tips", "Skaits"], sum);
  }
  function durSchedule(mdl) {
    const D = (mdl.doors || []).filter(isExt);
    const rows = D.map((d, i) => ["D" + (i + 1), d.w, 2100, d.hinge === "w" || d.hinge === "e" || d.hinge === "n" || d.hinge === "s" ? ({ w: "rietumu", e: "austrumu", n: "ziemeļu", s: "dienvidu" })[d.hinge] + " puse" : "", d.entry ? "Galvenā ieeja" : "Ārdurvis", d.side === 1 ? "uz iekšu" : "uz āru"]);
    return tableHtml("Ārdurvju specifikācija", ["Poz.", "Platums, mm", "Augstums, mm", "Eņģes", "Lietojums", "Vēršanās"], rows.length ? rows : [["", "", "", "", "Ārdurvju nav", ""]]);
  }
  function winPlan(mdl) {
    const poly = (mdl.poly && mdl.poly.length > 2 ? mdl.poly : [[0, 0], [mdl.W, 0], [mdl.W, mdl.D], [0, mdl.D]]), pad = 1200, T = 283.5;
    let svg = `<svg viewBox="${-pad} ${-pad} ${mdl.W + 2 * pad} ${mdl.D + 2 * pad}" xmlns="http://www.w3.org/2000/svg"><polygon points="${poly.map(p => p.join(",")).join(" ")}" fill="#f6f6f4" stroke="#222" stroke-width="40"/>`;
    (mdl.windows || []).forEach((w, i) => { const h = w.o === "h", x = w.x, y = w.y, a = h ? [x, y - 60, w.len, 120] : [x - 60, y, 120, w.len];
      svg += `<rect x="${a[0]}" y="${a[1]}" width="${a[2]}" height="${a[3]}" fill="#9fd0e6" stroke="#145" stroke-width="20"/><text x="${h ? x + w.len / 2 : x + (x < mdl.W / 2 ? -240 : 240)}" y="${h ? y + (y < mdl.D / 2 ? -190 : 330) : y + w.len / 2}" font-size="190" text-anchor="middle" fill="#145">L${i + 1}</text>`; });
    (mdl.doors || []).filter(isExt).forEach((d, i) => { const h = d.o === "h", a = h ? [d.x, d.y - 80, d.w, 160] : [d.x - 80, d.y, 160, d.w];
      svg += `<rect x="${a[0]}" y="${a[1]}" width="${a[2]}" height="${a[3]}" fill="#d6a36a" stroke="#531" stroke-width="20"/><text x="${h ? d.x + d.w / 2 : d.x + 330}" y="${h ? d.y + 400 : d.y + d.w / 2}" font-size="190" text-anchor="middle" fill="#531">D${i + 1}</text>`; });
    return svg + "</svg>";
  }

  // ---- elektrības plāns: automātisks priekšlikums pēc telpām un durvīm (ligzdas, slēdži, gaismekļi, sadales skapis) ----
  const WET = /vann|wc|duš|dus|santeh|sanit|mezgl|bath|toilet/i, KITCH = /virtuv|kitchen/i, BED = /guļ|gul|bed/i, HALL = /priekšn|priekšnams|gaitenis|hall|entr/i, TECH = /tehn|katl|boiler|utility|noliktav/i;
  function roomSpec(n, area) {
    const lights = Math.max(1, Math.round(area / 12e6));
    if (WET.test(n)) return { lights, sockets: 1, wet: true };
    if (KITCH.test(n)) return { lights, sockets: 6 };
    if (BED.test(n)) return { lights, sockets: 4 };
    if (HALL.test(n)) return { lights, sockets: 1 };
    if (TECH.test(n)) return { lights, sockets: 2 };
    return { lights, sockets: Math.max(3, Math.round(area / 5e6)) };
  }
  // ---- grupu aprēķins: slodze, strāva, automāts, kabeļa garums, sprieguma kritums, skapja izmērs ----
  // Aprēķina loģika pārņemta no egmalt/house-planner (MIT licence, sk. docs/TRESO_PUSU_LICENCES.md), pielāgota MM modelim.
  const EL = { P: { light: 50, socket: 300, wet: 500, power: 3500 }, U: 230, RHO: 0.0175, BELOW: 150, PANEL_H: 1700, TAIL: 1500, RES: 0.15,
    DEF: { light: ["MCB", "C10", 1.5, 10], socket: ["RCBO", "C16", 2.5, 16], wet: ["RCBO", "C16", 2.5, 16], power: ["MCB", "C32", 6, 32] },
    DROP: { light: 0, switch: 1500, socket: 2400, wet: 2400, power: 2400 }, SIZES: [12, 18, 24, 36, 48, 54, 72, 96] };
  // īsākais koks (Manhetenas attālumi) no skapja caur visiem grupas punktiem
  function mstLen(panel, ps) {
    const N = [panel, ...ps], inT = [true], best = N.map(p => Math.abs(p.x - panel.x) + Math.abs(p.y - panel.y)); let L = 0;
    for (let k = 1; k < N.length; k++) { let j = -1; for (let i = 0; i < N.length; i++) if (!inT[i] && (j < 0 || best[i] < best[j])) j = i;
      inT[j] = true; L += best[j]; for (let i = 0; i < N.length; i++) if (!inT[i]) best[i] = Math.min(best[i], Math.abs(N[i].x - N[j].x) + Math.abs(N[i].y - N[j].y)); }
    return L;
  }
  function circuits(m, pts, panel) {
    const H = (m.sienas_augstums || m.wallH || 2500), out = [], by = k => pts.filter(p => p.k === k);
    const split = (arr, max) => { const g = []; let cur = []; let room = null;
      arr.forEach(p => { if (cur.length >= max || (cur.length && p.room !== room && cur.length + arr.filter(q => q.room === p.room).length > max)) { g.push(cur); cur = []; } cur.push(p); room = p.room; });
      if (cur.length) g.push(cur); return g; };
    split(by("light"), 12).forEach((g, i) => out.push({ t: "light", n: "Apgaismojums " + (i + 1), ps: g, sw: by("switch").filter(q => g.some(p => p.room === q.room)) }));
    const kit = by("socket").filter(p => KITCH.test(p.room || "")), rest = by("socket").filter(p => !KITCH.test(p.room || ""));
    if (kit.length) out.push({ t: "socket", n: "Virtuves ligzdas", ps: kit });
    split(rest, 8).forEach((g, i) => out.push({ t: "socket", n: "Ligzdas " + (i + 1), ps: g }));
    if (by("wet").length) out.push({ t: "wet", n: "Slapjo telpu ligzdas (IP44)", ps: by("wet") });
    by("power").forEach(p => out.push({ t: "power", n: "Plīts / cepeškrāsns", ps: [p] }));
    out.forEach((c, i) => {
      const d = EL.DEF[c.t], all = c.ps.concat(c.sw || []);
      c.id = "G" + (i + 1); c.dev = d[0]; c.br = d[1]; c.sec = d[2]; c.In = d[3];
      c.load = c.ps.reduce((s2, p) => s2 + EL.P[p.k], 0); c.I = c.load / EL.U;
      const drops = all.reduce((s2, p) => s2 + (H - EL.BELOW - EL.DROP[p.k] > 0 ? H - EL.BELOW - EL.DROP[p.k] : 0), 0);
      c.len = (mstLen(panel, all) + drops + (H - EL.BELOW - EL.PANEL_H) + EL.TAIL) * (1 + EL.RES) / 1000;
      c.drop = 2 * c.len * c.I * EL.RHO / c.sec / EL.U * 100;
      c.warn = (c.I > c.In ? "pārslodze, dali grupu" : "") + (c.drop > 5 ? (c.I > c.In ? "; " : "") + "sprieguma kritums virs 5 %" : "");
    });
    return out;
  }
  function circuitTables(cs) {
    const f1 = v => v.toFixed(1).replace(".", ","), mods = cs.reduce((s2, c) => s2 + (c.dev === "RCBO" ? 2 : 1), 0) + 4, need = Math.ceil(mods * 1.2), size = EL.SIZES.find(z => z >= need) || need;
    const rows = cs.map(c => [c.id, c.n, c.ps.length, c.load, f1(c.I), (c.dev === "RCBO" ? "Dif. automāts " : "Automāts ") + c.br, "3×" + String(c.sec).replace(".", ","), f1(c.len), f1(c.drop), c.warn]);
    const cab = {}; cs.forEach(c => { cab[c.sec] = (cab[c.sec] || 0) + c.len; });
    const tot = cs.reduce((s2, c) => s2 + c.load, 0);
    const sum = Object.keys(cab).sort((a, b) => a - b).map(k => ["Kabelis 3×" + k.replace(".", ",") + " mm²", Math.ceil(cab[k]) + " m"]).concat([
      ["Uzstādītā jauda kopā", (tot / 1000).toFixed(1).replace(".", ",") + " kW"], ["Moduļi skapī (ar ievada slēdzi)", mods], ["Ieteicamais skapis (20 % rezerve)", size + " moduļi"]]);
    return tableHtml("Grupu saraksts", ["Grupa", "Nosaukums", "Punkti", "Slodze, W", "Strāva, A", "Aizsardzība", "Kabelis, mm²", "Garums, m", "Kritums, %", "Piezīme"], rows) + tableHtml("Kabeļi un sadales skapis", ["Pozīcija", "Daudzums"], sum);
  }
  function elecPlan(m) {
    const T = 195, rooms = (m.rooms || []).filter(r => !r.void && r.r && r.r[0]), pts = [], doors = m.doors || [];
    const poly = (m.poly && m.poly.length > 2 ? m.poly : [[0, 0], [m.W, 0], [m.W, m.D], [0, m.D]]);
    rooms.forEach(rm => {
      const q = rm.r[0], [x, y, w, h] = q, area = rm.r.reduce((s2, a) => s2 + a[2] * a[3], 0), sp = roomSpec(rm.n || "", area);
      // gaismekļi: telpas centrs vai režģis
      const nl = sp.lights, cols = Math.ceil(Math.sqrt(nl * w / h)), rows = Math.ceil(nl / cols);
      for (let i = 0; i < nl; i++) { const cx = i % cols, cy = Math.floor(i / cols); pts.push({ k: "light", x: x + w * (cx + .5) / cols, y: y + h * (cy + .5) / rows, room: rm.n }); }
      // ligzdas gar sienām, vienmērīgi pa perimetru (no 400 mm no stūriem)
      const per = [[x + 400, y + 120, 1, 0, w - 800], [x + w - 120, y + 400, 0, 1, h - 800], [x + w - 400, y + h - 120, -1, 0, w - 800], [x + 120, y + h - 400, 0, -1, h - 800]];
      const tot = per.reduce((s2, e) => s2 + Math.max(0, e[4]), 0); let d = tot / (sp.sockets * 2), placed = 0;
      for (let i = 0; i < sp.sockets; i++) {
        let t = d * (2 * i + 1); for (const e of per) { const L = Math.max(0, e[4]); if (t <= L) { pts.push({ k: sp.wet ? "wet" : "socket", x: e[0] + e[2] * t, y: e[1] + e[3] * t, room: rm.n }); placed++; break; } t -= L; }
      }
      if (KITCH.test(rm.n || "")) pts.push({ k: "power", x: x + w / 2, y: y + 120, room: rm.n });   // plīts pieslēgums
      // slēdzis pie telpas durvīm (iekšpusē, 150 mm no ailas)
      const dr = doors.find(dd => { const c = dd.o === "h" ? [dd.x + dd.w / 2, dd.y] : [dd.x, dd.y + dd.w / 2]; return c[0] >= x - 350 && c[0] <= x + w + 350 && c[1] >= y - 350 && c[1] <= y + h + 350; });
      if (dr) { const H = dr.o === "h"; const cx = H ? dr.x + dr.w + 200 : (dr.x < x + w / 2 ? x + 120 : x + w - 120), cy = H ? (dr.y < y + h / 2 ? y + 120 : y + h - 120) : dr.y + dr.w + 200; pts.push({ k: "switch", x: Math.min(x + w - 120, Math.max(x + 120, cx)), y: Math.min(y + h - 120, Math.max(y + 120, cy)), room: rm.n }); }
    });
    const ent = doors.find(d => d.entry) || doors[0], panel = ent ? { k: "panel", x: ent.x + (ent.o === "h" ? ent.w + 500 : 400), y: ent.y + (ent.o === "h" ? -300 : ent.w + 500) } : null;
    if (panel) pts.push(panel);
    const pad = 1200, cnt = k => pts.filter(p => p.k === k).length;
    let svg = `<svg viewBox="${-pad} ${-pad} ${m.W + 2 * pad} ${m.D + 2 * pad}" xmlns="http://www.w3.org/2000/svg"><polygon points="${poly.map(p => p.join(",")).join(" ")}" fill="#fafafa" stroke="#222" stroke-width="40"/>`;
    rooms.forEach(rm => rm.r.forEach(([x, y, w, h]) => { svg += `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="none" stroke="#bbb" stroke-width="15"/>`; }));
    rooms.forEach(rm => { const [x, y, w, h] = rm.r[0]; svg += `<text x="${x + w / 2}" y="${y + h / 2 + 330}" font-size="170" text-anchor="middle" fill="#999">${esc(rm.n || "")}</text>`; });
    pts.forEach(p => {
      const c = { x: Math.round(p.x), y: Math.round(p.y) };
      if (p.k === "light") svg += `<g stroke="#b8860b" stroke-width="22" fill="#fff8dc"><circle cx="${c.x}" cy="${c.y}" r="150"/><path d="M${c.x - 106} ${c.y - 106}L${c.x + 106} ${c.y + 106}M${c.x + 106} ${c.y - 106}L${c.x - 106} ${c.y + 106}"/></g>`;
      else if (p.k === "switch") svg += `<g stroke="#145" stroke-width="22" fill="#fff"><circle cx="${c.x}" cy="${c.y}" r="80"/><path d="M${c.x} ${c.y}L${c.x + 170} ${c.y - 170}"/></g>`;
      else if (p.k === "socket" || p.k === "wet") svg += `<g stroke="${p.k === "wet" ? "#0a6" : "#b00"}" stroke-width="22" fill="#fff"><circle cx="${c.x}" cy="${c.y}" r="95"/><path d="M${c.x - 95} ${c.y}L${c.x + 95} ${c.y}"/>${p.k === "wet" ? `<text x="${c.x + 140}" y="${c.y - 100}" font-size="110" fill="#0a6" stroke="none">IP44</text>` : ""}</g>`;
      else if (p.k === "power") svg += `<g stroke="#b00" stroke-width="22" fill="#fff"><rect x="${c.x - 110}" y="${c.y - 110}" width="220" height="220"/><path d="M${c.x - 110} ${c.y}L${c.x + 110} ${c.y}M${c.x} ${c.y - 110}L${c.x} ${c.y + 110}"/></g>`;
      else if (p.k === "panel") svg += `<g><rect x="${c.x - 160}" y="${c.y - 100}" width="320" height="200" fill="#d6a36a" stroke="#531" stroke-width="22"/><text x="${c.x}" y="${c.y + 45}" font-size="120" text-anchor="middle" fill="#531">SP</text></g>`;
    });
    let svg2 = "";
    const cs = panel ? circuits(m, pts.filter(p => p.k !== "panel"), panel) : [];
    pts.forEach(p => { const c = cs.find(q => q.ps.includes(p)); if (c && (p.k === "socket" || p.k === "wet" || p.k === "power")) svg2 += `<text x="${Math.round(p.x) - 130}" y="${Math.round(p.y) + 250}" font-size="100" fill="#555">${c.id}</text>`; });
    const rows = [["Sadales skapis (SP)", cnt("panel")], ["Gaismekļi griestos", cnt("light")], ["Kontaktligzdas", cnt("socket")], ["Kontaktligzdas IP44 (slapjās telpas)", cnt("wet")], ["Plīts pieslēgums (3,5 kW)", cnt("power")], ["Slēdži", cnt("switch")]];
    svg += svg2 + "</svg>";
    return `<section><h2>Elektrības plāns (automātisks priekšlikums)</h2>${svg}<p class="s">Izvietojums ir aptuvens priekšlikums pēc telpu platības un durvīm; precizē pēc elektriķa projekta un spēkā esošajām normām.</p></section>` + tableHtml("Elektroiekārtu saraksts", ["Elements", "Skaits"], rows) + (cs.length ? circuitTables(cs) : "");
  }
  function build(sel) {
    const m = MM_VIZ3D.model(), out = [];
    if (sel.skice || sel.pamati) out.push([m.id + "_skice_pamati.html", sheetHtml(m, false)]);
    const body = (sel.logplans ? `<section><h2>Logu plāns</h2>${winPlan(m)}</section>` : "") + (sel.logspec ? winSchedule(m) : "") + (sel.durspec ? durSchedule(m) : "") + (sel.elektr ? elecPlan(m) : "");
    if (body) out.push([m.id + "_logi_durvis.html", page(m, "Ražošanas dokumentācija", body)]);
    return out;
  }
  const dlg = document.createElement("div"); dlg.id = "prod"; dlg.hidden = true; dlg.setAttribute("role", "dialog"); dlg.setAttribute("aria-label", "Ražošanas pakete");
  dlg.style.cssText = "position:fixed;inset:0;z-index:70;display:grid;place-items:center;background:rgba(20,24,28,.55)";
  dlg.innerHTML = `<div style="background:#fff;color:#1d1d1d;border-radius:10px;padding:20px 22px;width:min(440px,92vw);box-shadow:0 10px 40px rgba(0,0,0,.3)"><b style="font-size:16px">Ražošanas pakete</b><p style="color:#666;margin:6px 0 12px">Izvēlies lapas, kuras iekļaut komplektā.</p><div id="prodList" style="display:grid;gap:8px"></div><div style="display:flex;gap:8px;margin-top:16px;justify-content:flex-end"><button type="button" id="prodX">Atcelt</button><button type="button" id="prodGo" class="pri">Izveidot komplektu</button></div></div>`;
  document.body.appendChild(dlg);
  const list = dlg.querySelector("#prodList");
  ITEMS.forEach(([k, t, on]) => { const l = document.createElement("label"), c = document.createElement("input"); c.type = "checkbox"; c.checked = on; c.dataset.k = k; l.style.cssText = "display:flex;flex-direction:row;gap:10px;align-items:center;justify-content:flex-start;text-align:left;margin:0"; c.style.cssText = "width:auto;margin:0;flex:0 0 auto"; l.append(c, document.createTextNode(t)); list.appendChild(l); });
  const close = () => { dlg.hidden = true; };
  dlg.querySelector("#prodX").onclick = close; dlg.addEventListener("click", e => { if (e.target === dlg) close(); });
  dlg.querySelector("#prodGo").onclick = async () => {
    const sel = {}; list.querySelectorAll("input").forEach(c => { sel[c.dataset.k] = c.checked; });
    const files = build(sel); close();
    if (!files.length) { status("Nekas nav izvēlēts."); return; }
    const put = async (n, d) => {
      if (typeof dl !== "undefined" && dl) return save(n, d);
      const u = URL.createObjectURL(new Blob([d], { type: "text/html" })), a = document.createElement("a"); a.href = u; a.download = n; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(u), 4000);   // atvērtā failā bez programmas
    };
    for (const [n, d] of files) { await put(n, d); await new Promise(r => setTimeout(r, 300)); }
    status("Ražošanas pakete: " + files.map(f => f[0]).join(", "));
  };
  if ($("bRazos")) $("bRazos").onclick = () => { dlg.hidden = false; };
  window.MM_PROD = { build, open: () => { dlg.hidden = false; } };
  const b = document.createElement("button"); b.type = "button"; b.className = "it"; b.id = "bProd"; b.innerHTML = "<b>Ražošanas pakete</b><small>Izvēlies lapas: skice, pamati, logu plāns un specifikācijas</small>";
  b.onclick = () => { dlg.hidden = false; };
  $("bJson").parentNode.insertBefore(b, $("bJson"));
  addEventListener("keydown", e => { if (!dlg.hidden && e.key === "Escape") close(); });
})();
