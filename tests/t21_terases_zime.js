// Terases zīme (nosaukums, Nr., m²) atlasāma un pārvietojama (stampAt)
const L = require('./lib.js');
(async () => {
  const html = L.build('tests/modeli/lievenis-stabi.json'.replace(/^/, __dirname + '/../'), m => { m.terraces = [{ name: 'Terase', poly: [[-3000, 0], [-1000, 0], [-1000, 5000], [-3000, 5000]], th: 300, corners: false, texRot: 0 }]; });
  const { browser, page, errs } = await L.open(html);
  const fr = await L.live(page);
  const c = await fr.evaluate(() => { const e = document.querySelector('g[data-block=plan] [data-tstamp]'); const g = document.querySelector('g[data-block=plan][transform]'); const bb = e.getBBox(), m = g.getCTM().inverse().multiply(e.getCTM()); const p = new DOMPoint(bb.x + bb.width / 2, bb.y + bb.height / 2).matrixTransform(m); return [p.x, p.y, +e.getAttribute('data-tstamp')]; });
  await L.drag(page, 'plan', c[0] + 400, c[1] - 150, c[0] + 400, c[1] - 150 + 1000);
  const m = await L.model(page);
  L.ok(m.stampAt && m.stampAt[c[2]] && Math.abs(m.stampAt[c[2]][1] - (c[1] + 1000)) < 60, 'terases zīme pārvietota par 1000', m.stampAt && m.stampAt[c[2]]);
  L.done(errs); await browser.close();
})();
