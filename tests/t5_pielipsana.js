// Pielipšana: visa terase velkot pielīp mājas sienai; stabs plānā pielīp terases stūrim
const T = require('./lib'); const path = require('path');
(async () => {
  const html = T.build(path.join(__dirname, 'modeli', 'lievenis-stabi.json'), m => { m.terraces.push({ name: 'Terase 2', poly: [[14000, 2000], [16000, 2000], [16000, 4000], [14000, 4000]], th: 300 }); });
  const { browser, page, errs } = await T.open(html);
  // terase 2 ir 927 mm pa labi no austrumu sienas (13073); velk par -860: jāpielīp tieši pie sienas
  await T.click(page, 'plan', 15000, 3000); await T.drag(page, 'plan', 15000, 3000, 15000 - 860, 3000);
  let m = await T.model(page); const x0 = Math.min(...m.terraces[1].poly.map(q => q[0]));
  T.ok(Math.abs(x0 - 13073) < 1, 'terases mala pielīp austrumu sienai', x0);
  await browser.close(); T.done(errs);
})();
