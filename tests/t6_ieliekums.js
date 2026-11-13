// Ieliekums: izgriezums no mājas malas; kontūra, telpas, ailas un fasāžu ieliekumu profils
const T = require('./lib'); const path = require('path');
(async () => {
  // 1) recessOf atbilst esošam modelim ar sarežģītu kontūru
  let html = T.build(path.join(__dirname, 'modeli', 'lievenis-stabi.json'));
  let { browser, page, errs } = await T.open(html);
  let r = await page.evaluate(() => { const m = window.MMAPI.model(); return [m.recess, window.MMAPI.recessOf(m)]; });
  T.ok(['south', 'north', 'east', 'west'].every(k => JSON.stringify(r[0][k]) === JSON.stringify(r[1][k])), 'ieliekumu profils no kontūras sakrīt ar modeļa datiem', r[1]);
  await browser.close(); const e1 = errs;
  // 2) taisnstūra māja: ieliekums dienvidu malas vidū
  html = T.build(path.join(T.ROOT, 'MĀJAS', '100m2', 'MM-100-01', 'model.json'));
  ({ browser, page, errs } = await T.open(html));
  const m0 = await T.model(page);
  await page.evaluate(() => window.MMAPI.addRecess({ side: 'south', len: 3000, dep: 1500, off: 4000, ter: '1' })); await T.ready(page);
  const m = await T.model(page);
  T.ok(m.poly && m.poly.length === 8, 'kontūrai 8 stūri (U izgriezums)', m.poly);
  T.ok(m.W === m0.W && m.D === m0.D, 'gabarīts nemainās');
  T.ok(m.recess.south && m.recess.south[0][0] === 4000 && m.recess.south[0][1] === 7000 && m.recess.south[0][2] === 1500, 'dienvidu fasādei ieliekums 4000..7000, dziļums 1500', m.recess);
  const bad = m.rooms.flatMap(q => q.r).filter(([x, y, w, h]) => x < 7000 && x + w > 4000 && y + h > m.D - 1500);
  T.ok(!bad.length, 'neviena telpa neiesniedzas ieliekumā', bad);
  T.ok((m.terraces || []).length === (m0.terraces || []).length + 1, 'ieliekumā pievienota terase');
  T.ok(m.windows.length <= m0.windows.length, 'ailas izgriezumā noņemtas', [m0.windows.length, m.windows.length]);
  const svgOk = await (await T.live(page)).evaluate(() => !!document.querySelector('svg.a3 g[data-block=plan]') && document.querySelectorAll('svg.a3 g[data-block^=elev]').length);
  T.ok(svgOk === 4, 'lapa pārzīmējas ar plānu un 4 fasādēm', svgOk);
  await page.keyboard.press('Control+z'); await T.ready(page);
  T.ok(!((await T.model(page)).poly || []).length || (await T.model(page)).poly.length === 4, 'Ctrl+Z atsauc');
  // 3) stūra ieliekums austrumos un mēģinājums sadalīt māju
  await page.evaluate(() => window.MMAPI.addRecess({ side: 'east', len: 2000, dep: 2000, off: 0, ter: '0' })); await T.ready(page);
  const m3 = await T.model(page); T.ok(m3.poly.length === 6, 'stūra ieliekums dod L formu', m3.poly);
  await browser.close(); T.done(e1.concat(errs));
})();
