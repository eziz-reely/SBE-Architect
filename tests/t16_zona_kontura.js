// Zona no vairākiem taisnstūriem: atlasot rāda vienu ārējo kontūru, ne katru taisnstūri atsevišķi
const L = require('./lib.js');
(async () => {
  const S = __dirname + '/modeli/lievenis-stabi.json';
  const m0 = JSON.parse(require('fs').readFileSync(S, 'utf8')); const ri = m0.rooms.findIndex(r => r.r.length >= 3) >= 0 ? m0.rooms.findIndex(r => r.r.length >= 3) : m0.rooms.findIndex(r => r.r.length >= 2);
  const { browser, page, errs } = await L.open(L.build(S));
  const m = await L.model(page), rr = m.rooms[ri].r;
  L.ok(ri >= 0 && rr.length >= 2, 'telpa no vairākiem taisnstūriem', rr.length);
  const q = rr[0]; await L.click(page, 'plan', q[0] + q[2] / 2, q[1] + q[3] / 2);
  const fr = await L.live(page);
  const n = await fr.evaluate(() => ({ paths: document.querySelectorAll('g.mm-ov path[stroke-dasharray]').length, dashedRects: [...document.querySelectorAll('g.mm-ov rect')].filter(r => r.getAttribute('stroke-dasharray') && r.getAttribute('stroke-dasharray') !== 'none').length }));
  L.ok(n.paths >= 1 && n.dashedRects === 0, 'viena apvienota kontūra', n);
  L.done(errs); await browser.close();
})();
