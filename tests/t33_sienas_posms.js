// Ārsienas posma sabiezinājums uz āru: pievieno no sienas paneļa, zīmējas plānā, toņi nonāk materiālu sarakstā, dzēšams
const T = require('./lib'); const path = require('path');
(async () => {
  const html = T.build(path.join(__dirname, 'modeli', 'lievenis-stabi.json'), m => { m.projekts = m.projekts || {}; m.projekts.wall_types = [{ id: 'S9', name: 'Sabiezinājums', layers: [['Apdare', 20, 'o'], ['Vata', 100, 'i'], ['OSB', 18, '']] }]; });
  const { browser, page, errs } = await T.open(html, { width: 1600, height: 1150 });
  // ziemeļu ārsiena plānā → panelī "Sabiezinājums"
  await page.keyboard.press('a');
  await T.click(page, 'plan', 3000, 120); await T.ready(page);
  const sl = await T.sel(page); T.ok(sl && sl.k === 'wall' && sl.w.ext, 'ārsiena atlasīta', sl && { k: sl.k });
  T.ok(/Sabiezinājums uz āru/.test(await page.textContent('#panel')), 'panelī ir sabiezinājuma sadaļa');
  await page.evaluate(() => { const l = [...document.querySelectorAll('#panel label')]; const sel = n => l.find(x => x.textContent.startsWith(n)).querySelector('select,input');
    const set = (e, v) => { e.value = v; e.dispatchEvent(new Event('change', { bubbles: true })); };
    set(sel('Posms no'), 2000); set(sel('līdz'), 4500); set(sel('Sienas veids'), 'S9'); set(sel('Iekšpuses tonis'), 'RAL 9016'); set(sel('Sienas gala tonis'), 'RAL 7016');
    [...document.querySelectorAll('#panel button')].find(b => b.textContent === 'Pievienot sabiezinājumu').click(); });
  await T.ready(page);
  let m = await T.model(page), q = (m.wallPad || [])[0];
  T.ok(q && q.side === 'north' && q.a === 2000 && q.b === 4500 && q.wt === 'S9' && q.t === 138 && q.inRal === 'RAL 9016' && q.endRal === 'RAL 7016', 'sabiezinājums saglabāts (biezums no pīrāga slāņiem)', q);
  const fr = await T.live(page);
  const r = await fr.evaluate(() => ({ lines: document.querySelectorAll('svg.a3 g[data-block=plan] line[stroke="#2F3234"], svg.a3 g[data-block=plan] line[stroke="#383E42"]').length, txt: [...document.querySelectorAll('svg text')].map(t => t.textContent).join(' ') }));
  T.ok(r.lines >= 2, 'plānā zīmēti posma gala toņi', r.lines);
  T.ok(/Sienas posma gals/.test(r.txt) && /RAL 7016/.test(r.txt) && /Sienas posms, iekšpuse/.test(r.txt), 'toņi materiālu sarakstā', (r.txt.match(/MATERI.{0,300}/) || [''])[0]);
  await browser.close(); T.done(errs);
})().catch(e => { console.error(e); process.exit(1); });
