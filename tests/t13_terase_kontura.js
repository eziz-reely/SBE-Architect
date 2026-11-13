// Terase: dubultklikšķis uz malas pievieno stūri; pakāpiens no paneļa (up +150) un eksplikācija
const L = require('./lib.js');
(async () => {
  const html = L.build(__dirname + '/modeli/lievenis-stabi.json', m => { m.terraces = [{ name: 'Terase', poly: [[-1000, 0], [0, 0], [0, 5078], [-1000, 5078]], th: 300, corners: false, texRot: 0 }]; });
  const { browser, page, errs } = await L.open(html);
  await L.click(page, 'plan', -500, 2500);
  L.ok((await L.sel(page) || {}).k === 'ter', 'terase atlasīta');
  const [a, b] = await L.pt(page, 'plan', -500, 0);
  await page.mouse.dblclick(a, b); await L.ready(page);
  let m = await L.model(page);
  L.ok(m.terraces[0].poly.length === 5, 'dubultklikšķis pievieno stūri', m.terraces[0].poly.length);
  const fr = await L.live(page);
  await fr.evaluate(() => postMessage({ mmPlace: { t: 'terrace', step: 0 } }, '*'));
  for (const q of [[-900, 500], [-100, 500], [-100, 1500]]) await L.click(page, 'plan', q[0], q[1]);
  const [c, d] = await L.pt(page, 'plan', -900, 1500); await page.mouse.move(c, d); await page.mouse.dblclick(c, d); await L.ready(page);
  m = await L.model(page);
  L.ok(m.terraces.length === 2 && m.terraces[1].up === 150 && m.terraces[1].name === 'Pakāpiens', 'pakāpiens +150', m.terraces.map(t => [t.name, t.up]));
  L.done(errs); await browser.close();
})();
