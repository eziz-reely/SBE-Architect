// Jauns mērs plānā pielīp ārējai (automātiskajai) mēru ķēdei
const T = require('./lib'); const path = require('path');
(async () => {
  const html = T.build(path.join(__dirname, 'modeli', 'lievenis-stabi.json'));
  const { browser, page, errs } = await T.open(html);
  const fr = await T.live(page);
  const chains = await fr.evaluate(() => [...document.querySelectorAll('svg.a3 g[data-block=plan] [data-chain]')].map(e => e.getAttribute('data-chain')));
  T.ok(chains.length > 0, 'ārējām ķēdēm ir data-chain', chains);
  const top = chains.filter(c => c.startsWith('x:')).map(c => +c.slice(2)).filter(y => y < 0).sort((a, b) => b - a)[0];
  await page.evaluate(() => [...document.querySelectorAll('#libOpen button')].find(x => /Mērs/.test(x.textContent)).click());
  await T.click(page, 'plan', 1500, -250); await T.click(page, 'plan', 3500, -250);
  const m = await T.model(page); const d = (m.userDims || []).slice(-1)[0] || ((m.levels && m.levels[0] && m.levels[0].userDims) || []).slice(-1)[0];
  T.ok(d && d[0] === 'x' && d[1] === top, 'mērs pielīp augšējai ķēdei', [d, top]);
  await browser.close(); T.done(errs);
})();
