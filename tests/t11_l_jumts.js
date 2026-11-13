// L formas jumts: stūra ieliekums + jumts.L dod četras slīpnes ar ieleju; 3D skats uzbūvējas bez kļūdām
const T = require('./lib'); const path = require('path');
(async () => {
  const html = T.build(path.join(T.ROOT, 'MĀJAS', '100m2', 'MM-100-01', 'model.json'));
  const { browser, page, errs } = await T.open(html);
  await page.evaluate(() => window.MMAPI.addRecess({ side: 'north', len: 5000, dep: 3000, off: 0 })); await T.ready(page);
  let m = await T.model(page); T.ok(m.poly && m.poly.length === 6, 'kontūra ir L (6 stūri)', m.poly);
  let rb = await page.evaluate(() => window.MM_RB());
  T.ok(/Jumts ziemeļi/.test(rb) && !/spārna slīpne/.test(rb), 'bez izvēles jumts paliek pār visu gabarītu');
  await page.evaluate(() => { const n = JSON.parse(JSON.stringify(window.MMAPI.model())); n.jumts.L = true; window.MMAPI.commit(n); }); await T.ready(page);
  rb = await page.evaluate(() => window.MM_RB());
  T.ok(/spārna slīpne 1/.test(rb) && /spārna slīpne 2/.test(rb) && /slīpne ar ieleju/.test(rb) && !/Jumts ziemeļi/.test(rb), 'L jumtam četras slīpnes ar ieleju');
  T.ok(!/NaN/.test(rb), 'ģeometrijā nav NaN');
  await page.click('#b3d'); await page.waitForTimeout(1200);
  const n = await page.evaluate(() => { const V = window.MM_VIZ3D.state; let c = 0; V.grp.traverse(o => { if (o.userData && o.userData.bk && o.userData.bk.k === 'ov') c++; }); return c; });
  T.ok(n >= 4, '3D skatā ir jumta slīpnes', n);
  await browser.close(); T.done(errs);
})();
