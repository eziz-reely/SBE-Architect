// 3D skats: ailas redzamas arī mājai ar kontūru, fasādes detaļas (aplodas, palodzes, notekas, stabi, terases), krāsa pa pusēm, staba augstums
const T = require('./lib'); const path = require('path');
(async () => {
  const html = T.build(path.join(__dirname, 'modeli', 'lievenis-stabi.json'), m => { m.projekts.fasade_side = { south: { hex: '#7a3b2e' } }; m.projekts.parkare_hex = '#d8d2c4'; m.posts[0].h = 1500; });
  const { browser, page, errs } = await T.open(html);
  await page.click('#b3d'); await page.waitForTimeout(900);
  const r = await page.evaluate(() => { const V = window.MM_VIZ3D.state, m = window.MMAPI.model(); let meshes = 0, boxes = 0, cyls = 0, cols = new Set(), postH = [];
    V.grp.traverse(o => { if (!o.isMesh) return; meshes++; const g = o.geometry.type; if (g === 'BoxGeometry') { boxes++; if (o.geometry.parameters.width === 300 && o.geometry.parameters.depth === 300) postH.push(Math.round(o.geometry.parameters.height)); } if (g === 'CylinderGeometry') cyls++; [].concat(o.material).forEach(x => cols.add('#' + x.color.getHexString())); });
    return { ok: !!V.renderer, picks: V.picks.length, wins: m.windows.length, meshes, boxes, cyls, cols: [...cols], postH }; });
  T.ok(r.ok, '3D skats atveras');
  T.ok(r.picks >= r.wins + 1, 'visi logi un ārdurvis ir 3D skatā (arī mājai ar kontūru)', [r.picks, r.wins]);
  T.ok(r.boxes > 40, 'aplodas, palodzes, statņi un stabi uzbūvēti', r.boxes);
  T.ok(r.cyls >= 2, 'notekas uzbūvētas', r.cyls);
  T.ok(r.cols.includes('#7a3b2e'), 'dienvidu fasāde savā krāsā (projekts.fasade_side)');
  T.ok(r.cols.includes('#d8d2c4'), 'jumta pārkare savā tonī (projekts.parkare_hex)');
  T.ok(r.postH.includes(1800), 'stabs ar h = 1500 ir īsāks (1500 + 300 zem nulles)', r.postH);
  await browser.close(); T.done(errs);
})();
