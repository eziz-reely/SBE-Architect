// Terases/pakāpiena zīmēšana: kursors uz ārsienas līnijas rāda attālumu līdz tuvākās krustojošās sienas galam un pielīp ārsienas malai
const L = require('./lib.js');
(async () => {
  const html = L.build(__dirname + '/modeli/lievenis-stabi.json', m => { m.terraces = [{ name: 'Terase', poly: [[-1000, 0], [0, 0], [0, 5078], [-1000, 5078]], th: 300, corners: false, texRot: 0 }]; });
  const { browser, page, errs } = await L.open(html);
  const fr = await L.live(page);
  await fr.evaluate(() => postMessage({ mmPlace: { t: 'terrace', step: 0 } }, '*'));
  const [a, b] = await L.pt(page, 'plan', 35, 1000);   // 35 mm no ārsienas ārmalas (x = 0)
  await page.mouse.move(a, b); await page.mouse.move(a + 1, b + 1); await page.waitForTimeout(250);
  const txt = await (await L.live(page)).evaluate(() => [...document.querySelectorAll('g.gh text')].map(t => t.textContent).join(' | '));
  L.ok(/mm no sienas gala/.test(txt), 'uz ārsienas līnijas redzams attālums līdz sienas galam', txt);
  await page.mouse.click(a + 1, b + 1); await page.waitForTimeout(150);
  await page.keyboard.press('Escape');
  L.done(errs); await browser.close();
})();
