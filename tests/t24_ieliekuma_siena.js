// Ieliekuma siena fasādē: zem karnīzes tā ir atsevišķa siena, virs tās (frontonā) tā pati ārējās plaknes siena
const L = require('./lib.js');
(async () => {
  const html = L.build(path_(), m => {
    m.W = 13073; m.D = 7036; m.windows = []; m.doors = []; delete m.porch; m.terraces = []; m.posts = [];
    m.poly = [[0, 0], [11561, 0], [11561, 1569], [13073, 1569], [13073, 7036], [8561, 7036], [8561, 4576], [4399, 4576], [4399, 5078], [0, 5078]];
  });
  const { browser, page, errs } = await L.open(html);
  await L.ready(page);
  const f = await L.live(page);
  const eE = await f.evaluate(() => (window.__FDF.west || {}).eEdge);
  const sg = await f.evaluate(M => mmFacSegs(M, 'west'), await L.model(page));
  const out = sg.find(q => !q.rec), rec = sg.find(q => q.rec);
  L.ok(out && rec && out.ext && out.ext.length, 'rietumu fasādē ir ārējā siena (ar paplašinājumu virs ieliekuma) un ieliekuma siena', sg);
  const pick = async (u, z) => { await page.keyboard.press('a'); await L.click(page, 'elev-west', u, -z); return await L.sel(page); };
  const mid = (rec.u0 + rec.u1) / 2 + 400;
  let s = null; for (const du of [400, -900, 900, -1300, 1300]) { s = await pick((rec.u0 + rec.u1) / 2 + du, 150); if (s && s.k === 'fsien') break; } L.ok(s && s.k === 'fsien' && Math.abs(s.u0 - rec.u0) < 2, 'zem karnīzes klikšķis atlasa ieliekuma sienu', s);
  s = await pick(mid, eE + 400); L.ok(s && s.k === 'fsien' && Math.abs(s.u0 - out.u0) < 2 && Math.abs(s.u1 - out.u1) < 2, 'virs karnīzes klikšķis atlasa ārējo sienu', s);
  // tonis ieliekuma sienai neskar frontonu virs tās
  await page.evaluate(([a, b]) => { const n = JSON.parse(JSON.stringify(MMAPI.model())); n.projekts = n.projekts || {}; n.projekts.fasade_wall = { west: [{ u0: a, u1: b, hex: '#1d1d1d' }] }; MMAPI.commit(n); }, [rec.u0, rec.u1]);
  await L.ready(page);
  const r = await (await L.live(page)).evaluate(() => [...document.querySelectorAll('clipPath[id^=wr-west] rect')].map(e => [+e.getAttribute('y'), +e.getAttribute('height')]));
  L.ok(r.length === 1 && Math.abs(r[0][0] + eE) < 2, 'ieliekuma sienas tonis sākas tikai no karnīzes uz leju', r);
  await page.evaluate(([a, b]) => { const n = JSON.parse(JSON.stringify(MMAPI.model())); n.projekts.fasade_wall = { west: [{ u0: a, u1: b, hex: '#dd9955' }] }; MMAPI.commit(n); }, [out.u0, out.u1]);
  await L.ready(page);
  const r2 = await (await L.live(page)).evaluate(() => [...document.querySelectorAll('clipPath[id^=wr-west] rect')].length);
  L.ok(r2 === 1 + out.ext.length, 'ārējās sienas tonis aptver arī frontonu virs ieliekuma', r2);
  // klikšķis uz kontūras sienas plānā atlasa to pašu sienu (rietumu fasādes ieliekuma siena: mala x=8561, y 4576..7036)
  await page.keyboard.press('a'); await L.click(page, 'plan', 8561 - 20, 6000); s = await L.sel(page);
  L.ok(s && s.k === 'fsien' && s.side === 'west' && Math.abs(s.u0 - rec.u0) < 2, 'klikšķis uz sienas plānā atlasa fasādes sienu', s);
  await browser.close(); L.done(errs);
})();
function path_() { return require('path').join(__dirname, 'modeli', 'lievenis-stabi.json'); }
