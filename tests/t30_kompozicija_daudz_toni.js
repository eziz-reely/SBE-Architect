// Ar daudz papildu toņiem (fascija, pārkare, sienas) materiālu leģenda neizraisa "elementi nesaietilpst lapā": kolonnu skaits ierobežots, lapa nepaliek tukša
const L = require('./lib');
(async () => {
  const html = L.build(__dirname + '/modeli/lievenis-stabi.json', m => {
    m.projekts = m.projekts || {}; const P = m.projekts;
    P.kompozicija = { orient: 'p', elementi: ['plan', 'loft', 'fas_south', 'fas_west', 'fas_north', 'fas_east', 'expl', 'mat'], merogs: 'auto' };
    P.fascia_side = { west: '#F1F0EA', east: '#383E42', south: '#C88F5F' }; P.fascia_side_ral = { west: 'RAL 9016', east: 'RAL 7016' };
    P.parkare_side = { west: '#C5C7C4', north: '#6C6960' }; P.fasade_side = { south: { hex: '#C88F5F' }, north: { hex: '#E3D9C6', ral: 'RAL 1013' } };
    P.fasade_wall = { east: [{ u0: 0, u1: 2000, hex: '#8D4931', ral: 'RAL 8004' }, { u0: 2000, u1: 3000, hex: '#2F4538', ral: 'RAL 6005' }] };
  });
  const { browser, page, errs } = await L.open(html, { width: 1600, height: 1150 });
  const fr = await L.live(page);
  const r = await fr.evaluate(() => ({ plan: !!document.querySelector('svg.a3 g[data-block=plan]'), txt: document.body.innerText.includes('nesaietilpst'), mat: !!document.querySelector('svg.a3 g[data-block=materials]') }));
  L.ok(r.plan && r.mat && !r.txt, 'ar daudziem toņiem lapa tiek uzzīmēta (nav "nesaietilpst")', r);
  const mmv = await fr.evaluate(() => { const s = document.querySelector('svg.a3'), g = s.querySelector('g[data-block=materials]'), r = g.getBoundingClientRect(), sr = s.getBoundingClientRect(), f = s.viewBox.baseVal.width / sr.width; return [(r.left - sr.left) * f, (r.right - sr.left) * f, s.viewBox.baseVal.width]; });
  L.ok(mmv[1] < mmv[2] - 40, 'materiālu leģenda neiet zem rakstlauka', mmv);
  await browser.close(); L.done(errs);
})().catch(e => { console.error(e); process.exit(1); });
