// Lapā nekas nedrīkst pārklāties: katra bloka (plāns, fasādes, eksplikācija, materiāli, virsraksti, rakstlaukums) redzamais saturs ir atsevišķs
const T = require('./lib'); const path = require('path'), fs = require('fs');
const EXTRA = [['mansards', m => {}], ['posti', m => {}]];
(async () => {
  const modeli = [path.join(__dirname, 'modeli', 'lievenis-stabi.json')];
  const mj = path.join(T.ROOT, 'MĀJAS', '100m2', 'MM-100-01', 'model.json'); if (fs.existsSync(mj)) modeli.push(mj);
  for (const mp of modeli) {
    const html = T.build(mp), { browser, page, errs } = await T.open(html, { width: 1600, height: 1150 });
    const fr = await T.live(page);
    const r = await fr.evaluate(() => {
      const s = document.querySelector('svg.a3'), items = [];
      const leafBox = g => { let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
        g.querySelectorAll('text,line,path,polygon,polyline,circle,ellipse,rect').forEach(e => {
          if (e.closest('clipPath,defs,pattern,mask') || e.closest('[clip-path]') || e.getAttribute('clip-path') || e.closest('.mm-ov')) return;
          const r = e.getBoundingClientRect(); if (r.width < 0.3 && r.height < 0.3) return;
          if (e.tagName === 'text' && !(e.textContent || '').trim()) return;
          x0 = Math.min(x0, r.left); y0 = Math.min(y0, r.top); x1 = Math.max(x1, r.right); y1 = Math.max(y1, r.bottom); });
        return x1 > x0 ? { x0, y0, x1, y1 } : null; };
      [...s.children].forEach((g, i) => { if (g.tagName === 'rect' || g.tagName === 'defs' || g.tagName === 'style') return; const b = leafBox(g); if (!b) return;
        items.push(Object.assign(b, { id: g.getAttribute('data-block') || g.tagName + i, txt: (g.textContent || '').trim().slice(0, 18) })); });
      const ov = []; for (let a = 0; a < items.length; a++) for (let c = a + 1; c < items.length; c++) { const A = items[a], B = items[c], w = Math.min(A.x1, B.x1) - Math.max(A.x0, B.x0), h = Math.min(A.y1, B.y1) - Math.max(A.y0, B.y0); if (w > 1.5 && h > 1.5) ov.push(`${A.id}[${A.txt}] × ${B.id}[${B.txt}] ${w.toFixed(0)}×${h.toFixed(0)}px`); }
      return { n: items.length, ov }; });
    T.ok(r.n >= 6 && !r.ov.length, 'lapā nekas nepārklājas: ' + path.basename(path.dirname(mp)) + '/' + path.basename(mp), r.ov);
    await browser.close(); T.done && 0;
  }
  T.done([]);
})().catch(e => { console.error(e); process.exit(1); });
