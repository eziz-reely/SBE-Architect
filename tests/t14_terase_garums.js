const L = require('./lib.js');
// polilīnija: ierakstīts garums (mm) + Enter dod punktu pa virzienu uz peli
(async () => {
  const html = L.build(__dirname + '/modeli/lievenis-stabi.json');
  const { browser, page, errs } = await L.open(html);
  const fr = await L.live(page);
  await fr.evaluate(() => postMessage({ mmPlace: { t: 'terrace' } }, '*'));
  await L.click(page, 'plan', -3000, 6000);
  const [a, b] = await L.pt(page, 'plan', -1500, 6000); await page.mouse.move(a, b); await page.waitForTimeout(100);
  for (const ch of '1000') await page.keyboard.press(ch);
  await page.keyboard.press('Enter');
  const [c, d] = await L.pt(page, 'plan', -2000, 7500); await page.mouse.move(c, d); await page.waitForTimeout(100);
  for (const ch of '1500') await page.keyboard.press(ch);
  await page.keyboard.press('Enter');
  const [e2, f] = await L.pt(page, 'plan', -4000, 7500); await page.mouse.move(e2, f); await page.mouse.click(e2, f); await page.waitForTimeout(100);
  await page.keyboard.press('Enter'); await page.waitForTimeout(200);
  await fr.getByText('Vienā līmenī ar esošo').click(); await L.ready(page);
  const m = await L.model(page), t = (m.terraces || []).slice(-1)[0];
  L.ok(t && Math.abs(t.poly[1][0] - t.poly[0][0] - 1000) < 1 && Math.abs(t.poly[2][1] - t.poly[1][1] - 1500) < 1, 'garums 1000 un 1500 mm', t && t.poly);
  L.done(errs); await browser.close();
})();
