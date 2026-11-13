// Izolēts skats: poga un dubultklikšķis izolē bloku, tas paliek pēc labojuma, Esc atgriež
const T = require('./lib'); const path = require('path');
(async () => {
  const { browser, page, errs } = await T.open(T.build(path.join(__dirname, 'modeli', 'lievenis-stabi.json')));
  const st = async () => (await T.live(page)).evaluate(() => { const s = document.getElementById('mmIso'), g = document.querySelector('svg.a3 g[data-block=plan][transform]') || document.querySelector('svg.a3 g[data-block=plan]'), r = g.getBoundingClientRect(), o = document.querySelector('svg.a3 g[data-block=elev-south]'); return { on: !!(s && s.textContent), w: r.width, vw: innerWidth, dim: getComputedStyle(o).opacity }; });
  const a = await st();
  await page.click('#bIso'); await page.waitForTimeout(400);
  const b = await st(); T.ok(b.on && b.dim === '0.08', 'poga izolē plānu, fasādes pieklusinātas', b);
  T.ok(b.w > a.w * 1.5, 'plāns palielināts', [Math.round(a.w), Math.round(b.w)]);
  await page.evaluate(() => { const m = JSON.parse(JSON.stringify(window.MMAPI.model())); m.windows[0].len += 100; window.MMAPI.commit(m); }); await T.ready(page); await page.waitForTimeout(300);
  const c = await st(); T.ok(c.on && Math.abs(c.w - b.w) < b.w * .05, 'pēc labojuma skats paliek izolēts un tajā pašā tuvinājumā', [Math.round(b.w), Math.round(c.w)]);
  await page.click('#bIso'); await page.waitForTimeout(400);
  const d = await st(); T.ok(!d.on && d.dim === '1', 'otrs klikšķis atgriež visu lapu', d);
  await browser.close(); T.done(errs);
})();
