// Logu toņi atsevišķi: spainis krāso tikai vienu logu (rāmis vai aplodas), Shift visus; logu var atlasīt fasādē
const L = require('./lib.js');
(async () => {
  const html = L.build(__dirname + '/modeli/lievenis-stabi.json');
  const { browser, page, errs } = await L.open(html, { width: 1600, height: 1150 });
  let m = await L.model(page);
  const wi = m.windows.findIndex(w => w.o === 'v' && w.out < 0);   // rietumu logs bez side
  const w = m.windows[wi];
  await page.keyboard.press('a'); await L.click(page, 'elev-west', m.D - (w.y + w.len / 2), -1000);
  const s = await L.sel(page); L.ok(s && s.k === 'win' && s.i === wi, 'logu fasādē var atlasīt (arī vecajam logam bez side)', s);
  await page.keyboard.press('Escape');
  await page.keyboard.press('b'); await page.waitForTimeout(200);
  await page.evaluate(() => { const s = [...document.querySelectorAll('#bktGrid select')][0]; s.value = 'RAL 9016'; s.dispatchEvent(new Event('change', { bubbles: true })); });
  await page.waitForTimeout(150);
  await L.click(page, 'elev-west', m.D - (w.y + w.len / 2), -1000); await L.ready(page);
  m = await L.model(page);
  L.ok(m.windows[wi].col && m.windows[wi].colral === 'RAL 9016' && m.windows.every((q, i) => i === wi || !q.col), 'spainis krāso tikai šī loga rāmi', m.windows.map(q => q.col || null));
  L.ok(!m.projekts.logu_hex, 'visu logu tonis nemainās', m.projekts.logu_hex);
  const n = await (await L.live(page)).evaluate(() => [...document.querySelectorAll('[data-block=elev-west] polygon, [data-block=elev-west] rect')].filter(e => /f1f0ea/i.test(e.getAttribute('fill') || '')).length);
  L.ok(n >= 1, 'fasādes rasējumā šī loga rāmis zīmēts izvēlētajā tonī', n);
  L.done(errs); await browser.close();
})();
