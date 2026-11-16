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
    set(sel('Posms no'), 2000); set(sel('līdz'), 4500); set(sel('Pīrāgs'), 'S9'); set(sel('Iekšpuses tonis'), 'RAL 9016'); set(sel('Sienas gala tonis'), 'RAL 7016');
    [...document.querySelectorAll('#panel button')].find(b => b.textContent === 'Pievienot sabiezinājumu').click(); });
  await T.ready(page);
  let m = await T.model(page), q = (m.wallPad || [])[0];
  T.ok(q && q.side === 'north' && q.a === 2000 && q.b === 4500 && q.wt === 'S9' && q.t === 138 && q.inRal === 'RAL 9016' && q.endRal === 'RAL 7016', 'sabiezinājums saglabāts (biezums no pīrāga slāņiem)', q);
  const fr = await T.live(page);
  const r = await fr.evaluate(() => ({ lines: document.querySelectorAll('svg.a3 g[data-block=plan] line[stroke="#2F3234"], svg.a3 g[data-block=plan] line[stroke="#383E42"]').length, txt: [...document.querySelectorAll('svg text')].map(t => t.textContent).join(' ') }));
  T.ok(r.lines >= 2, 'plānā zīmēti posma gala toņi', r.lines);
  T.ok(/Sienas posma gals/.test(r.txt) && /RAL 7016/.test(r.txt) && /Sienas posms, iekšpuse/.test(r.txt), 'toņi materiālu sarakstā', (r.txt.match(/MATERI.{0,300}/) || [''])[0]);
  // ārsienas vilkšana uz āru izveido sabiezinājumu, nemainot mājas gabarītu
  const m1 = await T.model(page); const D0 = m1.D, W0 = m1.W; await page.keyboard.press('Escape');
  await T.drag(page, 'plan', 8000, 120, 8000, -230); await T.ready(page);
  const m2 = await T.model(page), pads = (m2.wallPad || []).filter(q => q.side === 'north');
  T.ok(m2.D === D0 && m2.W === W0 && pads.length >= 2 && pads.some(q => q.t >= 200), 'vilkšana uz āru izveido sabiezinājumu, māja nemainās', { D: m2.D, pads });
  // gala rokturis: ārsienu velk aiz gala = pagarinājums (brīva siena), māja nemainās; ciparu ievade -1000 uz rietumiem
  await page.keyboard.press('Escape');
  await T.click(page, 'plan', 600, 120); await T.ready(page);
  let s0 = await T.sel(page); T.ok(s0 && s0.k === 'wall' && s0.w.ext, 'ziemeļu ārsiena atlasīta pie rietumu gala', s0 && s0.k);
  await T.drag(page, 'plan', 0, 120 + 0, -800, 120); await T.ready(page);
  let m3 = await T.model(page), fw = (m3.freeWalls || []).find(q => q[4] === 'h');
  T.ok(fw && fw[0] <= -700 && m3.W === W0 && m3.D === D0, 'gala vilkšana uz rietumiem pievieno gabalu, māja nemainās', { fw, W: m3.W });
  await T.click(page, 'plan', 3000, 120); await T.ready(page);
  const [ex, ey] = await T.pt(page, 'plan', 0, 120); await page.mouse.click(ex, ey); await page.waitForTimeout(150);
  await page.keyboard.type('-1000'); await page.keyboard.press('Enter'); await T.ready(page);
  const m4 = await T.model(page), fw2 = (m4.freeWalls || []).filter(q => q[4] === 'h');
  T.ok(m4.W === W0 && m4.D === D0 && fw2.length >= 1 && Math.min(...fw2.map(q => q[0])) <= -1000, 'klikšķis uz gala + -1000 pagarina uz rietumiem', fw2);
  // sienas gabals redzams arī fasādēs ar kontūru
  const frw = await T.live(page); const nfw = await frw.evaluate(() => document.querySelectorAll('svg.a3 g[data-block^=elev] g[data-fw]').length);
  T.ok(nfw >= 2, 'sienas gabals zīmējas fasādēs', nfw);
  // panelis: viss redzams bez ritināšanas
  await T.click(page, 'plan', 3000, 120); await T.ready(page);
  const vis = await page.evaluate(() => { const b = document.getElementById('propBar'); return b.scrollHeight <= b.clientHeight + 2; });
  T.ok(vis, 'sienas panelis ietilpst joslā bez ritināšanas');
  await browser.close(); T.done(errs);
})().catch(e => { console.error(e); process.exit(1); });
