// Eksplikācijas tabulu var pabīdīt pa lapu (projekts.tblOff), plāna virsraksts neietiek plāna asīs, brīvai krāsai tiek rēķināts tuvākais RAL
const T = require('./lib'); const path = require('path');
(async () => {
  const html = T.build(path.join(__dirname, 'modeli', 'lievenis-stabi.json'));
  const { browser, page, errs } = await T.open(html, { width: 1600, height: 1150 });
  const fr = await T.live(page);
  const near = await fr.evaluate(() => mmNearRal('#C88F5F'));
  T.ok(/^RAL \d{4}$/.test(near), 'RAL kalkulators atrod tuvāko RAL brīvam tonim', near);
  // virsraksts zem plāna: tā y lielāks par plāna zīmējuma apakšmalu
  const gap = await fr.evaluate(() => { const s = document.querySelector('svg.a3'), g = s.querySelector('g[data-block=plan]'), b = g.getBoundingClientRect(), h = [...s.querySelectorAll('text')].find(t => /STĀVA PLĀNS/.test(t.textContent)); return h ? h.getBoundingClientRect().top - b.bottom : null; });
  T.ok(gap != null && gap >= -1, 'virsraksts nepārklājas ar plāna asīm', gap);
  { const h2 = T.build(path.join(__dirname, 'modeli', 'lievenis-stabi.json'), m => { m.terraces = (m.terraces || []).concat([{ name: 'Terase', poly: [[1000, m.D], [9000, m.D], [9000, m.D + 3000], [1000, m.D + 3000]], th: 300, corners: false, texRot: 0 }]); });   // terase uz dienvidiem: plāns sniedzas zemāk
    const o2 = await T.open(h2, { width: 1600, height: 1150 }), f2 = await T.live(o2.page);
    const g2 = await f2.evaluate(() => { const s = document.querySelector('svg.a3'), g = s.querySelector('g[data-block=plan]'), b = g.getBoundingClientRect(), h = [...s.querySelectorAll('text')].find(t => /STĀVA PLĀNS/.test(t.textContent)); return h ? h.getBoundingClientRect().top - b.bottom : null; });
    T.ok(g2 != null && g2 >= -1, 'ar terasi dienvidu pusē virsraksts joprojām zem plāna', g2); await o2.browser.close(); }
  const box = await fr.evaluate(() => { const t = document.querySelector('svg.a3 g[data-tbl="0"]'), r = t.getBoundingClientRect(); return [r.x + r.width / 2, r.y + 6]; });
  const fb = await (await page.evaluateHandle(() => window.MMAPI.frame())).asElement().boundingBox();
  const x = fb.x + box[0], y = fb.y + box[1];
  await page.mouse.move(x, y); await page.mouse.down(); for (let i = 1; i <= 6; i++) await page.mouse.move(x - 20 * i, y + 10 * i); await page.mouse.up(); await T.ready(page);
  const m = await T.model(page), o = ((m.projekts || {}).tblOff || {})['0'];
  T.ok(o && o[0] < -5 && o[1] > 2, 'tabula pabīdīta, nobīde saglabāta modelī', o);
  await browser.close(); T.done(errs);
})().catch(e => { console.error(e); process.exit(1); });
