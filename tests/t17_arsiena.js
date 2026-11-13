// Ārsiena: klikšķis + -1000 + Enter izvelk sienu uz terases pusi; terase un pārējā zonēšana paliek vietā
const L = require('./lib.js');
(async () => {
  const html = L.build(__dirname + '/modeli/lievenis-stabi.json', m => { m.terraces = [{ name: 'Terase', poly: [[-1000, 0], [0, 0], [0, 5078], [-1000, 5078]], th: 300, corners: false, texRot: 0 }]; });
  const { browser, page, errs } = await L.open(html);
  const m0 = await L.model(page);
  const kor0 = m0.rooms.find(r => r.n === 'Koridors').r[0].slice();
  await L.click(page, 'plan', 230, 600);
  L.ok((await L.sel(page) || {}).k === 'wall', 'siena atlasīta');
  for (const k of ['-', '1', '0', '0', '0', 'Enter']) await page.keyboard.press(k);
  await L.ready(page);
  const m = await L.model(page);
  const kor = m.rooms.find(r => r.n === 'Koridors').r[0];
  L.ok(Math.abs(m.W - m0.W - 1000) < 1, 'māja platāka par 1000', m.W);
  // pasaulē paliek: koridora absolūtā pozīcija (+1000 modeļa koordinātēs)
  L.ok(Math.abs(kor[0] - kor0[0] - 1000) < 1 && Math.abs(kor[2] - kor0[2]) < 1, 'koridors nemainās', kor);
  const t = m.terraces[0].poly.map(p => p[0]);
  L.ok(Math.min(...t) >= -1 && Math.max(...t) <= 1001, 'terase paliek pasaulē', t);
  // vilkšana un vilkšanas laikā ierakstīts attālums
  await page.keyboard.press('Control+z'); await L.ready(page);
  const [a, b] = await L.pt(page, 'plan', 230, 600), [c] = await L.pt(page, 'plan', -300, 600);
  await page.mouse.move(a, b); await page.mouse.down(); for (let i = 1; i <= 6; i++) await page.mouse.move(a + (c - a) * i / 6, b);
  for (const k of ['-', '5', '0', '0', 'Enter']) await page.keyboard.press(k);
  await page.mouse.up(); await L.ready(page);
  const m2 = await L.model(page);
  L.ok(Math.abs(m2.W - m0.W - 500) < 1, 'vilkšanas laikā ierakstīts -500', m2.W);
  L.done(errs); await browser.close();
})();
