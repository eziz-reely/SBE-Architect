// Piebūve visās četrās pusēs: rietumos un ziemeļos māja aug sākuma pusē, viss pabīdās, malas ārpus spārna nogrieztas
const T = require('./lib'); const path = require('path');
(async () => {
  const src = path.join(T.ROOT, 'MĀJAS', '100m2', 'MM-100-01', 'model.json');
  for (const [side, key] of [['west', 'W'], ['north', 'D'], ['east', 'W'], ['south', 'D']]) {
    const { browser, page, errs } = await T.open(T.build(src));
    const m0 = await T.model(page);
    await page.evaluate(s => window.MMAPI.addExtension({ side: s, len: 3500, dep: 3000, off: 1000 }), side); await T.ready(page); await page.waitForTimeout(400);
    const m = await T.model(page), xs = m.poly.map(q => q[0]), ys = m.poly.map(q => q[1]);
    T.ok(Math.abs(m[key] - (m0[key] + 3000)) < 1, side + ': gabarīts aug par 3000', [m0.W, m0.D, m.W, m.D]);
    T.ok(m.poly.length === 8 && Math.min(...xs) === 0 && Math.min(...ys) === 0 && Math.max(...xs) === m.W && Math.max(...ys) === m.D, side + ': kontūra ar spārnu (8 stūri) sākas no 0', m.poly);
    const out = m.rooms.flatMap(q => q.r).filter(([x, y, w, h]) => { const cx = x + w / 2, cy = y + h / 2; let c = false; for (let i = 0, j = m.poly.length - 1; i < m.poly.length; j = i++) { const [xi, yi] = m.poly[i], [xj, yj] = m.poly[j]; if ((yi > cy) !== (yj > cy) && cx < (xj - xi) * (cy - yi) / (yj - yi) + xi) c = !c; } return !c; });
    T.ok(!out.length, side + ': visas telpas ir kontūras iekšpusē', out);
    T.ok(m.recess && Object.keys(m.recess).length >= 1, side + ': fasāžu ieliekumu profils pārrēķināts', m.recess);
    const n = await (await T.live(page)).evaluate(() => document.querySelectorAll('svg.a3 g[data-block^=elev]').length); T.ok(n === 4, side + ': lapa pārzīmējas', n);
    await browser.close(); if (errs.length) { T.ok(false, side + ': lapas kļūdas', errs); }
  }
  T.done([]);
})();
