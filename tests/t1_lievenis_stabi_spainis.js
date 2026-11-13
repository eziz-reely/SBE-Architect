// Lievenis (atlase, dzēšana), fasādes stabi (dzēšana, platums, augstums, nogriešana pie pārkares), spainis (viena siena, pārkare)
const T = require('./lib'); const path = require('path');
(async () => {
  const html = T.build(process.argv[2] || path.join(__dirname, 'modeli', 'lievenis-stabi.json'));
  const { browser, page, errs } = await T.open(html);
  let m = await T.model(page);
  T.ok(!!m.porch, 'modelī ir lievenis');
  // --- lievenis: klikšķis tā laukumā (prom no pakāpiena un stabiem), tad Delete
  await T.click(page, 'plan', 2000, 6000);
  T.ok((await T.sel(page) || {}).k === 'porch', 'klikšķis atlasa lieveni', await T.sel(page));
  T.ok(/Lievenis/.test(await page.textContent('#panel')), 'panelī "Lievenis"');
  await page.keyboard.press('Delete'); await T.ready(page);
  m = await T.model(page); T.ok(!m.porch, 'Delete izdzēš lieveni');
  await page.keyboard.press('Control+z'); await T.ready(page);
  m = await T.model(page); T.ok(!!m.porch, 'Ctrl+Z atjauno lieveni');
  // --- stabs fasādē: 0. stabs (x 0..300, y 6736) dienvidu fasādē
  const p0 = m.posts[0];
  await T.click(page, 'elev-south', p0.x + p0.w / 2, -1200);
  T.ok((await T.sel(page) || {}).k === 'post' && (await T.sel(page)).i === 0, 'klikšķis fasādē atlasa stabu', await T.sel(page));
  // labā mala +200 → platums 500
  await T.drag(page, 'elev-south', p0.x + p0.w - 10, -1200, p0.x + p0.w + 590, -1200);
  m = await T.model(page); T.ok(Math.abs(m.posts[0].w - (p0.w + 600)) <= 60, 'labās malas vilkšana maina platumu', m.posts[0].w);
  // augšmala uz leju par 800 → h ≈ dzega − 800
  const fr = await T.live(page), eE = await fr.evaluate(() => window.__FDF.south.eEdge);
  await T.drag(page, 'elev-south', p0.x + 150, -eE + 20, p0.x + 150, -eE + 820);
  m = await T.model(page); T.ok(m.posts[0].h > 0 && Math.abs(m.posts[0].h - (eE - 800)) < 60, 'augšmalas vilkšana maina augstumu', [m.posts[0].h, eE]);
  // augšmala uz augšu pāri pārkarei → nogriežas pie pārkares
  const h1 = m.posts[0].h;
  await T.drag(page, 'elev-south', p0.x + 150, -h1 + 20, p0.x + 150, -eE - 900);
  m = await T.model(page); T.ok(m.posts[0].h >= 90000, 'virs pārkares: stabs nogriežas pie pārkares', m.posts[0].h);
  const fr2 = await T.live(page);
  const top = await fr2.evaluate(() => { const g = document.querySelector('g[data-block=elev-south]'); const ps = [...g.querySelectorAll('polygon')].filter(p => (p.getAttribute('fill') || '').toLowerCase() === ((window.AR && AR.projekts && AR.projekts.tonis_sw) || '#c68a58').toLowerCase() && !p.closest('[data-block=elev-south] [clip-path]') && p.getAttribute('points').split(' ').length === 4); return ps.map(p => Math.min(...p.getAttribute('points').split(' ').map(q => +q.split(',')[1]))); });
  T.ok(top.length > 0 && top.every(y => y >= -eE - 1), 'fasādē stabs nav augstāks par pārkari', top);
  // dzēšana fasādē
  const n0 = m.posts.length; await T.click(page, 'elev-south', m.posts[0].x + 100, -1200); await page.keyboard.press('Delete'); await T.ready(page);
  m = await T.model(page); T.ok(m.posts.length === n0 - 1, 'Delete fasādē izdzēš stabu', m.posts.length);
  // --- spainis: tikai viena siena
  await page.evaluate(() => { const m = JSON.parse(JSON.stringify(MMAPI.model())); MMAPI.commit(m); });
  await T.ready(page);
  await page.keyboard.press('b'); await page.waitForTimeout(200);
  const hasB = await page.evaluate(() => !document.getElementById('bktBox').hidden);
  T.ok(hasB, 'B ieslēdz spaini');
  // izvēlas RAL krāsu spainim
  await page.evaluate(() => { const s = [...document.querySelectorAll('#bktGrid select')][0]; s.value = 'RAL 9016'; s.dispatchEvent(new Event('change', { bubbles: true })); });
  await page.waitForTimeout(150);
  await T.click(page, 'elev-north', 6000, -1900); await T.ready(page);
  m = await T.model(page);
  T.ok(m.projekts.fasade_side && m.projekts.fasade_side.north && !m.projekts.fasade_side.south, 'spainis krāso tikai ziemeļu fasādi', m.projekts.fasade_side);
  T.ok(!m.projekts.fasade_hex, 'visas mājas tonis nemainās', m.projekts.fasade_hex);
  const fr3 = await T.live(page);
  const filt = await fr3.evaluate(() => ['north', 'south'].map(s => !!document.querySelector(`g[data-block=elev-${s}] g[filter]`)));
  T.ok(filt[0] && !filt[1], 'rasējumā pārkrāsota tikai ziemeļu fasāde', filt);
  // pārkare: klikšķis uz spāres gala joslas garajā fasādē
  const F = await fr3.evaluate(() => window.__FDF.north);
  await T.click(page, 'elev-north', 6000, -(F.eEdge + (F.eT - F.eEdge) / 2)); await T.ready(page);
  m = await T.model(page); T.ok(!!m.projekts.parkare_hex, 'spainis krāso jumta pārkari', m.projekts.parkare_hex);
  await page.screenshot({ path: path.join(require('os').tmpdir(), 't1.png') });
  await browser.close(); T.done(errs);
})().catch(e => { console.error(e); process.exit(1); });
