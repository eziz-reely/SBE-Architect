// Sienu zem L formas terases ierobežojošā taisnstūra var atlasīt un izvilkt (terase atlasās tikai savā kontūrā)
const L = require('./lib.js');
(async () => {
  const html = L.build(__dirname + '/modeli/lievenis-stabi.json', m => { m.terraces = [{ name: 'Terase', poly: [[0, 0], [-1000, 0], [-1000, m.D], [m.W, m.D], [m.W, m.D - 2500], [0, m.D - 2500]], th: 300, corners: false, texRot: 0 }]; });
  const { browser, page, errs } = await L.open(html);
  const m0 = await L.model(page);
  await L.click(page, 'plan', 3000, 130);
  L.ok((await L.sel(page) || {}).k === 'wall', 'ziemeļu siena atlasīta, nevis terase');
  for (const k of ['-', '1', '0', '0', '0', 'Enter']) await page.keyboard.press(k);
  await L.ready(page);
  const m = await L.model(page);
  L.ok(Math.abs(m.D - m0.D - 1000) < 1, 'māja dziļāka par 1000', m.D);
  L.done(errs); await browser.close();
})();
