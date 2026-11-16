// Fasādes dēļu virziens: horizontāls pagriež tekstūru visās fasādēs, materiālu sarakstā "horizontāls apdares dēlis"
const T = require('./lib'); const path = require('path');
(async () => {
  const html = T.build(path.join(__dirname, 'modeli', 'lievenis-stabi.json'), m => { m.projekts = m.projekts || {}; m.projekts.apdare_orient = 'h'; m.projekts.fasade_side = { south: { hex: '#C88F5F' } }; });
  const { browser, page, errs } = await T.open(html, { width: 1600, height: 1150 });
  const fr = await T.live(page);
  const r = await fr.evaluate(() => ({ rot: document.querySelectorAll('svg.a3 g[data-block^=elev-] use[transform^="rotate(90"]').length, txt: [...document.querySelectorAll('svg text')].map(t => t.textContent).join(' ') }));
  T.ok(r.rot > 0, 'fasādēs dēļu tekstūra pagriezta (horizontāli)', r.rot);
  T.ok(/horizontāls apdares dēlis/.test(r.txt) && !/Fascijas dēlis/.test(r.txt), 'materiālu sarakstā "horizontāls apdares dēlis"', (r.txt.match(/MATERI.{0,200}/) || [''])[0]);
  T.ok(!/vertikāl/.test(r.txt.replace(/.*MATERI/, 'MATERI')), 'materiālu sarakstā nekur nav "vertikāls"');
  await page.evaluate(() => { document.querySelector('details[data-pane=house]').open = true; });
  const sel = await page.evaluate(() => [...document.querySelectorAll('select')].some(s => [...s.options].some(o => o.textContent === 'Horizontāls')));
  T.ok(sel, 'panelī ir fasādes dēļu virziena izvēle');
  await browser.close(); T.done(errs);
})().catch(e => { console.error(e); process.exit(1); });
