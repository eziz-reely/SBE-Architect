// Rakstlaukumā neuzraksta uzņēmuma "INDIVIDUAL" (arhīva mapes nosaukums), citi uzņēmumi paliek
const L = require('./lib.js');
const txt = async (uz) => {
  const html = L.build(__dirname + '/modeli/lievenis-stabi.json', m => { m.projekts = m.projekts || {}; m.projekts.uznemums = uz; m.projekts.titul = { stils: 'neitrals' }; m.projekts.kompozicija = { orient: 'l', elementi: ['plan', 'fas_south', 'fas_west', 'expl', 'mat'] }; });
  const { browser, page, errs } = await L.open(html); await L.ready(page);
  const t = await (await L.live(page)).evaluate(() => [...document.querySelectorAll('svg text')].map(e => e.textContent).join(' | '));
  await browser.close(); return t;
};
(async () => {
  const a = await txt('INDIVIDUAL'), b = await txt('Testa SIA');
  L.ok(!/INDIVIDUAL/.test(a), 'rakstlaukumā nav uzraksta INDIVIDUAL', (a.match(/.{0,30}INDIVIDUAL.{0,30}/) || [''])[0]);
  L.ok(/TESTA SIA/i.test(b), 'cits uzņēmums rakstlaukumā paliek', (b.match(/.{0,20}Testa.{0,20}/i) || [''])[0]);
  L.done([]);
})();
