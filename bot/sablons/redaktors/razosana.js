// ---- Ražošanas pakete: izvēlas lapas un izveido visu komplektu (logu plāns, logu un ārdurvju specifikācija, skices un pamatu lapa) ----
(function () {
  const ITEMS = [
    ["skice", "Skices lapa (A3 .html)", true],
    ["pamati", "Pamatu un vainaga plāns (ietverts lapā, ja ieslēgts)", true],
    ["logplans", "Logu plāns (SVG)", true],
    ["logspec", "Logu specifikācija", true],
    ["durspec", "Ārdurvju specifikācija", true],
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
  function build(sel) {
    const m = MM_VIZ3D.model(), out = [];
    if (sel.skice || sel.pamati) out.push([m.id + "_skice_pamati.html", sheetHtml(m, false)]);
    const body = (sel.logplans ? `<section><h2>Logu plāns</h2>${winPlan(m)}</section>` : "") + (sel.logspec ? winSchedule(m) : "") + (sel.durspec ? durSchedule(m) : "");
    if (body) out.push([m.id + "_logi_durvis.html", page(m, "Logu un durvju dokumentācija", body)]);
    return out;
  }
  const dlg = document.createElement("div"); dlg.id = "prod"; dlg.hidden = true; dlg.setAttribute("role", "dialog"); dlg.setAttribute("aria-label", "Ražošanas pakete");
  dlg.style.cssText = "position:fixed;inset:0;z-index:70;display:grid;place-items:center;background:rgba(20,24,28,.55)";
  dlg.innerHTML = `<div style="background:#fff;color:#1d1d1d;border-radius:10px;padding:20px 22px;width:min(440px,92vw);box-shadow:0 10px 40px rgba(0,0,0,.3)"><b style="font-size:16px">Ražošanas pakete</b><p style="color:#666;margin:6px 0 12px">Izvēlies lapas, kuras iekļaut komplektā.</p><div id="prodList" style="display:grid;gap:8px"></div><div style="display:flex;gap:8px;margin-top:16px;justify-content:flex-end"><button type="button" id="prodX">Atcelt</button><button type="button" id="prodGo" class="pri">Izveidot komplektu</button></div></div>`;
  document.body.appendChild(dlg);
  const list = dlg.querySelector("#prodList");
  ITEMS.forEach(([k, t, on]) => { const l = document.createElement("label"), c = document.createElement("input"); c.type = "checkbox"; c.checked = on; c.dataset.k = k; l.style.cssText = "display:flex;gap:8px;align-items:center"; l.append(c, document.createTextNode(t)); list.appendChild(l); });
  const close = () => { dlg.hidden = true; };
  dlg.querySelector("#prodX").onclick = close; dlg.addEventListener("click", e => { if (e.target === dlg) close(); });
  dlg.querySelector("#prodGo").onclick = async () => {
    const sel = {}; list.querySelectorAll("input").forEach(c => { sel[c.dataset.k] = c.checked; });
    const files = build(sel); close();
    if (!files.length) { status("Nekas nav izvēlēts."); return; }
    for (const [n, d] of files) await save(n, d);
    status("Ražošanas pakete: " + files.map(f => f[0]).join(", "));
  };
  window.MM_PROD = { build, open: () => { dlg.hidden = false; } };
  const b = document.createElement("button"); b.type = "button"; b.className = "it"; b.id = "bProd"; b.innerHTML = "<b>Ražošanas pakete</b><small>Izvēlies lapas: skice, pamati, logu plāns un specifikācijas</small>";
  b.onclick = () => { $("exp").hidden = true; dlg.hidden = false; };
  $("bJson").parentNode.insertBefore(b, $("bJson"));
  addEventListener("keydown", e => { if (!dlg.hidden && e.key === "Escape") close(); });
})();
