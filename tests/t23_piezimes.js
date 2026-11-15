// Piezīmes lapā: katru var nodzēst un atjaunot
const L = require('./lib.js'); const path = require('path');
(async () => {
  const html = L.build(path.join(__dirname, 'modeli', 'lievenis-stabi.json'));
  const { browser, page, errs } = await L.open(html);
  await page.evaluate(() => { document.querySelector('details[data-pane=notes]').open = true; });
  await page.waitForTimeout(400);
  const rows = page.locator('#notesPane .nrow'); const n = await rows.count();
  L.ok(n >= 2, 'piezīmju saraksts ir', n);
  const t = await rows.first().locator('span').innerText();
  const fr = await L.live(page);
  const c0 = await fr.evaluate(t => [...document.querySelectorAll('[data-note]')].filter(e => e.getAttribute('data-note') === t).length, t);
  L.ok(c0 >= 1, 'piezīme ir lapā', c0);
  await rows.first().getByText('Dzēst').click(); await L.ready(page);
  const m = await L.model(page);
  L.ok((m.projekts.notes_off || []).includes(t), 'piezīme ierakstīta notes_off', m.projekts.notes_off);
  const fr2 = await L.live(page);
  const c1 = await fr2.evaluate(t => [...document.querySelectorAll('[data-note]')].filter(e => e.getAttribute('data-note') === t).length, t);
  L.ok(c1 === 0, 'piezīme vairs nav lapā', c1);
  await page.locator('#notesPane .nrow.off').getByText('Atjaunot').click(); await L.ready(page);
  const m2 = await L.model(page);
  L.ok(!(m2.projekts.notes_off || []).length, 'piezīme atjaunota', m2.projekts.notes_off);
  L.done(errs); await browser.close();
})();
