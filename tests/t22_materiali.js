// Materiāli: saraksts sānjoslā, katras fasādes tonis atsevišķi, paņemšana spainim
const L = require('./lib.js'); const path = require('path');
(async () => {
  const html = L.build(path.join(__dirname, 'modeli', 'lievenis-stabi.json'));
  const { browser, page, errs } = await L.open(html);
  await page.evaluate(() => { document.querySelector('details[data-pane=mats]').open = true; });
  const n = await page.locator('#matsPane .mrow').count();
  L.ok(n >= 7, 'materiālu saraksts ir (fasādes, pārkare, rāmji, stabi, terases)', n);
  const row = page.locator('#matsPane .mrow', { hasText: 'Austrumu fasāde' });
  await row.locator('select').selectOption('RAL 9016'); await L.ready(page);
  let m = await L.model(page);
  L.ok(m.projekts.fasade_side && m.projekts.fasade_side.east && !m.projekts.fasade_side.north, 'austrumu fasāde nokrāsota atsevišķi', m.projekts.fasade_side);
  await page.locator('#matsPane .mrow', { hasText: 'Austrumu fasāde' }).getByText('Paņemt spainim').click(); await page.waitForTimeout(250);
  const txt = await page.evaluate(() => document.getElementById('bktGrid').textContent);
  L.ok(/Paņemts: RAL 9016/.test(txt), 'spainī parādās paņemtais materiāls', txt.slice(0, 80));
  L.done(errs); await browser.close();
})();
