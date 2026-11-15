// Fascijas dēlis krāsojams atsevišķi (pēc noklusējuma kā pārkare), un atsevišķi nokrāsotās daļas parādās lapas materiālu sarakstā ar RAL kodu
const T = require('./lib'); const path = require('path');
(async () => {
  const html = T.build(path.join(__dirname, 'modeli', 'lievenis-stabi.json'));
  const { browser, page, errs } = await T.open(html, { width: 1600, height: 1150 });
  await page.evaluate(() => { const m = JSON.parse(JSON.stringify(MMAPI.model())); MMAPI.commit(m); }); await T.ready(page);
  await page.keyboard.press('b'); await page.waitForTimeout(200);
  await page.evaluate(() => { const s = [...document.querySelectorAll('#bktGrid select')][0]; s.value = 'RAL 9016'; s.dispatchEvent(new Event('change', { bubbles: true })); });
  await page.waitForTimeout(150);
  const fr = await T.live(page);
  const F = await fr.evaluate(() => window.__FDF.west), sp = await fr.evaluate(M => M.D, await T.model(page)), u = sp / 2 - 1000;
  await T.click(page, 'elev-west', u, -(F.ridge - 1000 * Math.tan(30 * Math.PI / 180) - 50)); await T.ready(page);   // gala fasādes jumta malas josla (fascijas dēlis)
  let m = await T.model(page), P = m.projekts;
  T.ok(P.fascia_side && P.fascia_side.west && !P.fascia_side.east && !P.parkare_side, 'spainis krāso tikai rietumu fascijas dēli, nevis pārkari', { f: P.fascia_side, p: P.parkare_side });
  T.ok((P.fascia_side_ral || {}).west === 'RAL 9016', 'fascijas RAL kods saglabāts', P.fascia_side_ral);
  const txt = await (await T.live(page)).evaluate(() => [...document.querySelectorAll('svg text')].map(t => t.textContent).join(' ').replace(/\s+/g, ' '));
  T.ok(/Fascijas dēlis, rietumu puse/.test(txt) && /RAL 9016/.test(txt), 'lapas materiālu sarakstā ir fascijas dēlis ar RAL kodu', (txt.match(/MATERI.{0,300}/) || [txt.slice(0, 200)])[0]);
  // parasts klikšķis (bez spaiņa) uz fascijas dēļa atlasa tā kontūru un panelī ļauj mainīt toni tikai šajā fasādē
  await page.keyboard.press('Escape'); await page.keyboard.press('a');
  await T.click(page, 'elev-west', u, -(F.ridge - 1000 * Math.tan(30 * Math.PI / 180) - 50)); await T.ready(page);
  const sl = await T.sel(page); T.ok(sl && sl.k === 'fboard' && sl.side === 'west', 'klikšķis uz fascijas dēļa to atlasa', sl);
  T.ok(/Fascijas dēlis/.test(await page.textContent('#panel')), 'panelī "Fascijas dēlis"');
  await page.evaluate(() => { const s = document.querySelector('#panel select'); s.value = 'RAL 7016'; s.dispatchEvent(new Event('change', { bubbles: true })); }); await T.ready(page);
  m = await T.model(page); T.ok((m.projekts.fascia_side_ral || {}).west === 'RAL 7016' && m.projekts.fascia_side.west === '#383E42', 'panelī nomainīts tikai rietumu fascijas tonis', m.projekts.fascia_side_ral);
  await page.screenshot({ path: path.join(require('os').tmpdir(), 't25.png') });
  await browser.close(); T.done(errs);
})().catch(e => { console.error(e); process.exit(1); });
