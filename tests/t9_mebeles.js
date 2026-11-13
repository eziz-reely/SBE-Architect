// Papildu mēbeles (mmF): bibliotēkā ir pogas, simbols uzzīmējas plānā, izmēru var mainīt panelī, statiskā lapa uzbūvējas
const T = require('./lib'); const path = require('path'); const fs = require('fs');
(async () => {
  const kinds = ['kumode', 'plaukts', 'apavi', 'pakaramais', 'zgalds', 'tvgalds', 'bkresls', 'augs', 'ledus', 'tmasina', 'plits', 'vanna', 'vskapis', 'boilers', 'gkatls', 'kamins', 'krasns'];
  const html = T.build(path.join(T.ROOT, 'MĀJAS', '100m2', 'MM-100-01', 'model.json'), m => { m.furniture = (m.furniture || []).concat(kinds.map((k, i) => ['mmF', 600 + (i % 6) * 1900, 600 + Math.floor(i / 6) * 1500, 800, 500, k])); });
  const { browser, page, errs } = await T.open(html);
  const n = await page.locator('#libFurn button').count(); T.ok(n >= 21 + 17, 'bibliotēkā ir jaunās mēbeles', n);
  const m = await T.model(page), i0 = m.furniture.length - kinds.length;
  const boxes = await (await T.live(page)).evaluate(() => document.querySelectorAll('svg.a3 g[data-block=plan] [data-furn]').length);
  T.ok(boxes > kinds.length * 2, 'simboli uzzīmēti plānā', boxes);
  await page.evaluate(i => window.MMAPI.select({ k: 'furn', i, lv: 'main' }), i0); await page.waitForTimeout(250);
  const txt = await page.textContent('#panel'); T.ok(/800|Platums|Garums/.test(txt), 'izvēlētai mēbelei ir izmēru lauki', txt.slice(0, 90));
  await browser.close(); T.done(errs);
})();
