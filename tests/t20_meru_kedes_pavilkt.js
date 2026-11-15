// Automātiskās ārējās mēru ķēdes: pavelkamas uz āru (projekts.chainOff), noklusēti sākas aiz terasēm
const L = require('./lib.js');
(async () => {
  const html = L.build(__dirname + '/modeli/lievenis-stabi.json');
  const { browser, page, errs } = await L.open(html);
  const fr = await L.live(page);
  const rows = async () => (await fr.evaluate(() => [...document.querySelectorAll('svg.a3 g[data-block=plan] [data-chain]')].map(e => e.getAttribute('data-chain')))).filter(c => c.startsWith('x:')).map(c => +c.slice(2)).filter(y => y < 0);
  const r0 = await rows(); const top0 = Math.min(...r0), at = r0.sort((a, b) => b - a)[0];
  await L.drag(page, 'plan', 6000, at, 6000, at - 500);
  const m = await L.model(page);
  L.ok(m.projekts && m.projekts.chainOff && m.projekts.chainOff.n === 500, 'ziemeļu ķēde pavilkta par 500', m.projekts && m.projekts.chainOff);
  const fr2 = await L.live(page);
  const r1 = (await fr2.evaluate(() => [...document.querySelectorAll('svg.a3 g[data-block=plan] [data-chain]')].map(e => e.getAttribute('data-chain')))).filter(c => c.startsWith('x:')).map(c => +c.slice(2)).filter(y => y < 0);
  L.ok(Math.min(...r1) === top0 - 500, 'ķēdes rasējumā pārvietotas', [top0, Math.min(...r1)]);
  L.done(errs); await browser.close();
})();
