// Saskarne: augšā tikai lapas pogas, visi rīki kreisajā joslā, labajā sakļaujamas sadaļas, mērījumu lauks statusa joslā
const T = require('./lib'); const path = require('path');
(async () => {
  const html = T.build(path.join(__dirname, 'modeli', 'lievenis-stabi.json'));
  const { browser, page, errs } = await T.open(html);
  const top = await page.evaluate(() => [...document.querySelectorAll('header button')].filter(b => b.offsetParent && !b.closest('.pop')).map(b => b.id));
  T.ok(top.join() === 'bUndo,bRedo,bFit,bRib,bTb,bSave', 'augšā: atsaukt, atkārtot, visa lapa, Noformējums, Rakstlaukums, Saglabāt', top);
  const rail = await page.evaluate(() => [...document.querySelectorAll('#rail button[data-id]')].map(b => b.dataset.id));
  T.ok(['sel', 'er', 't0', 't1', 't2', 't3', 't4', 'zone', 'zonep', 't5', 't6', 'gv', 'gh', 'gs', 'ter', 'terp', 'dec', 'decp', 'post', 'bk'].every(i => rail.includes(i)), 'kreisajā joslā visi rīki', rail.length);
  T.ok(await page.isVisible('#rail #b3d'), '3D poga kreisās joslas apakšā');
  // katrs rīks ieslēdzas un statusa josla rāda nosaukumu
  for (const id of ['t0', 'post', 'zone', 'dec', 'terp', 'gs']) {
    await page.click(`#rail button[data-id=${id}]`);
    const on = await page.evaluate(() => [...document.querySelectorAll('#rail button.on')].map(b => b.dataset.id).join());
    T.ok(on === id, 'rīks ' + id + ' ieslēdzas', [on, (await page.textContent('#sbTool')).slice(0, 40)]);
  }
  await page.click('#rail button[data-id=bk]');
  T.ok(await page.isVisible('details.tr[data-pane=tool] #bktGrid'), 'spainim parādās sadaļa "Rīka opcijas"');
  await page.click('#rail button[data-id=sel]');
  T.ok(!(await page.isVisible('details.tr[data-pane=tool]')), 'atlasei rīka opciju nav');
  // sadaļas
  T.ok(!(await page.isVisible('#topMode')), '"Lapa un eksports" sākumā sakļauta');
  await page.click('details.tr[data-pane=sheet] > summary');
  T.ok(await page.isVisible('#topMode') && await page.isVisible('#topLang') && await page.isVisible('#bRazos') && await page.isVisible('#bReset'), 'sadaļā ir režīms, valoda, ražošana, atiestatīšana');
  await page.click('#bKeys'); T.ok(await page.isVisible('#keysPane'), 'taustiņu poga atver sadaļu "Taustiņi"');
  // mērījumu lauks: logs → platums
  const m0 = await T.model(page), w = m0.windows[0];
  await page.evaluate(() => window.MMAPI.select({ k: 'win', i: 0, lv: 'main' })); await page.waitForTimeout(200);
  T.ok(!(await page.isDisabled('#sbVal')), 'mērījumu lauks aktīvs izvēlētam logam', [await page.textContent('#sbLab'), await page.inputValue('#sbVal')]);
  await page.fill('#sbVal', '1500'); await page.press('#sbVal', 'Enter'); await T.ready(page);
  const m1 = await T.model(page); T.ok(JSON.stringify(m1.windows[0]) !== JSON.stringify(w), 'skaitlis un Enter maina loga izmēru', [w, m1.windows[0]]);
  // telefons
  await page.setViewportSize({ width: 390, height: 800 }); await page.waitForTimeout(300);
  T.ok(await page.isVisible('#rail button[data-id=post]') || await page.isVisible('#rail button[data-id=sel]'), 'telefonā rīku josla redzama');
  T.ok(await page.isVisible('#sbTool'), 'telefonā statusa rinda redzama');
  await browser.close(); T.done(errs);
})();
