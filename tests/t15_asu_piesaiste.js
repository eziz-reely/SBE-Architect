// Būvasu piesaiste: Māja → Izmēri → Būvasu piesaiste maina ārējās asis
const L = require('./lib.js');
(async () => {
  const { browser, page, errs } = await L.open(L.build(__dirname + '/modeli/lievenis-stabi.json'));
  const m0 = await L.model(page);
  const sel = await page.evaluateHandle(() => [...document.querySelectorAll('label')].find(l => /Būvasu piesaiste/.test(l.textContent)));
  const ok0 = !!sel.asElement();
  L.ok(ok0, 'lauks Būvasu piesaiste ir panelī');
  if (ok0) {
    await page.evaluate(() => { const l = [...document.querySelectorAll('label')].find(l => /Būvasu piesaiste/.test(l.textContent)); const s = l.querySelector('select'); s.value = 'fasade'; s.dispatchEvent(new Event('change', { bubbles: true })); });
    await L.ready(page);
    const m = await L.model(page);
    L.ok(m.axes.x[0][0] === 0 && m.axes.x[m.axes.x.length - 1][0] === m.W && m.axes.y[0][0] === 0, 'asis uz fasādes ārmalas', [m.axes.x[0][0], m.axes.x.slice(-1)[0][0], m.W]);
    L.ok(m.axes.x[1][0] === m0.axes.x[1][0], 'iekšējā ass nemainās');
  }
  L.done(errs); await browser.close();
})();
