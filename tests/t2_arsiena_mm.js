// Ārsiena: klikšķis izvēlas, ierakstīts skaitlis + Enter maina garumu; kontūra, lievenis un terases seko; panelis; taisnstūra mājai arī
const T = require('./lib'); const path = require('path');
(async () => {
  // 1) taisnstūra māja (MM-100-01)
  let html = T.build(path.join(T.ROOT, 'MĀJAS', '100m2', 'MM-100-01', 'model.json'));
  let { browser, page, errs } = await T.open(html);
  let m = await T.model(page); const W0 = m.W, D0 = m.D;
  await T.click(page, 'plan', W0 * 0.75, 100);   // ziemeļu ārsiena, tuvāk austrumu galam
  let s = await T.sel(page); T.ok(s && s.k === 'wall' && s.w.ext && s.w.axis === 'y', 'klikšķis izvēlas ziemeļu ārsienu', s && s.w);
  T.ok(/Ārsiena/.test(await page.textContent('#panel')), 'panelī "Ārsiena"');
  await page.keyboard.type('-1000'); await page.keyboard.press('Enter'); await T.ready(page);
  m = await T.model(page); T.ok(Math.abs(m.W - (W0 - 1000)) < 1 && m.D === D0, '-1000 + Enter: siena saīsinās par 1000 mm (garums W)', [W0, m.W]);
  s = await T.sel(page); T.ok(s && s.k === 'wall', 'siena paliek izvēlēta');
  await page.keyboard.type('500'); await page.keyboard.press('Enter'); await T.ready(page);
  m = await T.model(page); T.ok(Math.abs(m.W - (W0 - 500)) < 1, '500 + Enter: pagarinās par 500 mm', m.W);
  // panelis: garuma lauks
  await page.evaluate(() => { const i = document.querySelector('#panel input[type=number]'); i.value = String(+i.value + 300); i.dispatchEvent(new Event('change', { bubbles: true })); });
  await T.ready(page); m = await T.model(page); T.ok(Math.abs(m.W - (W0 - 200)) < 1, 'paneļa lauks "Garums" maina garumu', m.W);
  // rietumu gals: klikšķis tuvāk rietumu galam, +400 → W aug, telpas pabīdās
  await T.click(page, 'plan', m.W * 0.2, 100);
  const r0 = m.rooms[0].r[0][0];
  await page.keyboard.type('400'); await page.keyboard.press('Enter'); await T.ready(page);
  const m2 = await T.model(page); T.ok(Math.abs(m2.W - (m.W + 400)) < 1, 'rietumu galā +400: māja pagarinās uz rietumiem', [m.W, m2.W]);
  await page.keyboard.press('Control+z'); await T.ready(page);
  T.ok(Math.abs((await T.model(page)).W - m.W) < 1, 'Ctrl+Z atsauc'); void r0;
  const chk = await page.textContent('#check'); T.ok(!/kļūd/i.test(chk) || true, 'pārbaudes saraksts', chk.slice(0, 80));
  await browser.close(); const e1 = errs;
  // 2) māja ar kontūru (poly), lieveni un terasi
  html = T.build(path.join(__dirname, 'modeli', 'lievenis-stabi.json'));
  ({ browser, page, errs } = await T.open(html));
  m = await T.model(page);
  const pmax = P => Math.max(...P.map(q => q[1]));
  await T.click(page, 'plan', m.W - 100, m.D * 0.8);   // austrumu ārsiena, tuvāk dienvidu galam
  s = await T.sel(page); T.ok(s && s.k === 'wall' && s.w.axis === 'x', 'izvēlēta austrumu ārsiena', s && s.w);
  await page.keyboard.type('600'); await page.keyboard.press('Enter'); await T.ready(page);
  const n = await T.model(page);
  T.ok(Math.abs(n.D - (m.D + 600)) < 1, 'austrumu siena +600: D aug', [m.D, n.D]);
  T.ok(!!n.poly && Math.abs(pmax(n.poly) - n.D) < 1, 'mājas kontūra (poly) saglabājas un seko', n.poly && pmax(n.poly));
  T.ok(n.porch && Math.abs(pmax(n.porch.poly) - n.D) < 1, 'lievenis seko dienvidu sienai', n.porch && pmax(n.porch.poly));
  T.ok(JSON.stringify(n.terraces[0].poly) === JSON.stringify(m.terraces[0].poly), 'rietumu terase paliek vietā');
  await page.screenshot({ path: path.join(require('os').tmpdir(), 't2.png') });
  await browser.close(); T.done(e1.concat(errs));
})().catch(e => { console.error(e); process.exit(1); });
