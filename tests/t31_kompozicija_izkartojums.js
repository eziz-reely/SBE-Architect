// Automātiskā kompozīcija: plāns ar terasi nelien pāri rāmim, materiāli vienmēr zem fasādēm, izkārtojums nemainās no fascijas krāsas maiņas
const L = require('./lib');
const mk = (P, or) => m => { m.projekts = m.projekts || {}; Object.assign(m.projekts, { kompozicija: { orient: or || 'p', elementi: ['plan', 'loft', 'fas_south', 'fas_west', 'fas_north', 'fas_east', 'expl', 'mat'], merogs: 'auto' } }, P || {}); };
const geo = async page => { const fr = await L.live(page); return await fr.evaluate(() => { const s = document.querySelector('svg.a3'), sr = s.getBoundingClientRect(), f = s.viewBox.baseVal.width / sr.width, bx = e => { const r = e.getBoundingClientRect(); return { l: (r.left - sr.left) * f, r: (r.right - sr.left) * f, t: (r.top - sr.top) * f, b: (r.bottom - sr.top) * f }; };
  const ax = [...s.querySelectorAll('g[data-block=plan] circle')].map(bx), fas = [...s.querySelectorAll('g[data-block^=elev-]')].map(bx), mat = bx(s.querySelector('g[data-block=materials]'));
  return { axL: Math.min(...ax.map(a => a.l)), axR: Math.max(...ax.map(a => a.r)), fasB: Math.max(...fas.map(a => a.b)), matT: mat.t, planT: Math.min(...ax.map(a => a.t)) }; }); };
(async () => {
  const html = L.build(__dirname + '/modeli/lievenis-stabi.json', mk());
  const o = await L.open(html, { width: 1600, height: 1150 }); const g0 = await geo(o.page);
  L.ok(g0.axL >= 20.5 && g0.axR <= 246, 'plāna asis (arī ar terasi) paliek lapas rāmī', g0);
  L.ok(g0.matT >= g0.fasB - 0.5, 'materiāli ir zem fasādēm', g0);
  const m0 = await L.model(o.page); await o.browser.close();
  const html2 = L.build(__dirname + '/modeli/lievenis-stabi.json', mk({ fascia_side: { west: '#C88F5F' }, fascia_side_ral: {} }));
  const o2 = await L.open(html2, { width: 1600, height: 1150 }); const g1 = await geo(o2.page);
  L.ok(Math.abs(g1.planT - g0.planT) < 1 && Math.abs(g1.axL - g0.axL) < 1, 'fascijas toņa maiņa nepārkārto lapu', { g0, g1 });
  await o2.browser.close();
  // horizontālā lapa: tie paši noteikumi (apakšā materiāli, plāns rāmī, neveidojas "nesaietilpst")
  const o3 = await L.open(L.build(__dirname + '/modeli/lievenis-stabi.json', mk({ fascia_side: { west: '#C88F5F' } }, 'l')), { width: 1600, height: 1150 }); const g3 = await geo(o3.page);
  const t3 = await (await L.live(o3.page)).evaluate(() => document.body.innerText.includes('nesaietilpst'));
  L.ok(!t3 && g3.axL >= 20.5 && g3.axR <= 346 && g3.matT >= g3.fasB - 0.5, 'horizontālā lapa: plāns rāmī, materiāli zem fasādēm', g3);
  await o3.browser.close(); L.done([...o.errs, ...o2.errs, ...o3.errs]);
})().catch(e => { console.error(e); process.exit(1); });
