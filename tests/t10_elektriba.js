// Elektrības plāns ražošanas paketē: punkti, grupu saraksts ar slodzi, strāvu, kabeli un skapja izmēru
const T = require('./lib'); const path = require('path'); const fs = require('fs');
(async () => {
  const html = T.build(path.join(T.ROOT, 'MĀJAS', '100m2', 'MM-100-01', 'model.json'));
  const { browser, page, errs } = await T.open(html);
  const files = await page.evaluate(() => window.MM_PROD.build({ elektr: true }));
  T.ok(files.length === 1, 'izveidots viens fails', files.map(f => f[0]).join());
  const h = files[0][1];
  T.ok(/Grupu saraksts/.test(h) && /Kabeļi un sadales skapis/.test(h), 'ir grupu un kabeļu tabulas');
  const g = (h.match(/<td>G\d+<\/td>/g) || []).length; T.ok(g >= 4, 'vismaz 4 grupas', g);
  T.ok(/Dif\. automāts C16/.test(h) && /Automāts C10/.test(h), 'ligzdām dif. automāts C16, gaismai C10');
  const sk = h.match(/Ieteicamais skapis[^<]*<\/td><td>(\d+) moduļi/); T.ok(sk && +sk[1] >= 12, 'skapja izmērs', sk && sk[1]);
  T.ok(!/NaN|undefined/.test(h), 'nav NaN vai undefined');
  fs.writeFileSync(path.join(path.dirname(html), 'elektriba_test.html'), h);
  await browser.close(); T.done(errs);
})();
