// Redaktora pārbaužu palīgi (Playwright). Lietošana: node tests/<tests>.js  [model.json]
// Redaktora lapu uzbūvē no model.json ar bot/redaktors.py pagaidu mapē; nekas netiek rakstīts MĀJAS/ vai PROJEKTI/.
const { execFileSync } = require('child_process');
const fs = require('fs'), os = require('os'), path = require('path');
let chromium; try { ({ chromium } = require('playwright')); } catch (_) { ({ chromium } = require('/opt/node22/lib/node_modules/playwright')); }
const ROOT = path.resolve(__dirname, '..');

function build(modelPath, edit) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'sbe-test-'));
  const m = JSON.parse(fs.readFileSync(modelPath, 'utf8')); if (edit) edit(m);
  const mp = path.join(dir, 'model.json'); fs.writeFileSync(mp, JSON.stringify(m));
  const out = path.join(dir, 'red.html');
  execFileSync(process.platform === 'win32' ? 'python' : 'python3', ['redaktors.py', mp, out], { cwd: path.join(ROOT, 'bot'), env: Object.assign({}, process.env, { PYTHONIOENCODING: 'utf-8' }), stdio: ['ignore', 'pipe', 'pipe'] });
  return out;
}
async function open(html, vp) {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: vp || { width: 1600, height: 950 } });
  const errs = []; page.on('pageerror', e => errs.push(e.message)); page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto('file://' + html); await ready(page);
  return { browser, page, errs };
}
// gaida, līdz rasējums pārzīmēts
async function ready(page) { await page.waitForTimeout(250); await page.waitForFunction(() => document.getElementById('busy').hidden, null, { timeout: 30000 }); await page.waitForTimeout(350); }
const frame = page => page.frames().find(f => f !== page.mainFrame() && f.parentFrame() === page.mainFrame() && !f.isDetached() && f.name() !== undefined && f._live !== false && true);
async function live(page) { const h = await page.evaluateHandle(() => window.MMAPI.frame()); return await h.asElement().contentFrame(); }
// ekrāna punkts (lapas koordinātās) rasējuma bloka lokālajam punktam: block = "plan" | "elev-south" ...
async function pt(page, block, x, y) {
  const fr = await live(page);
  const q = await fr.evaluate(([b, x, y]) => { const g = document.querySelector(`svg.a3 g[data-block=${b}][transform]`); const m = g.getScreenCTM(); const p = new DOMPoint(x, y).matrixTransform(m); return [p.x, p.y]; }, [block, x, y]);
  const box = await (await page.evaluateHandle(() => window.MMAPI.frame())).asElement().boundingBox();
  return [box.x + q[0], box.y + q[1]];
}
async function click(page, block, x, y, opt) { const [a, b] = await pt(page, block, x, y); await page.mouse.move(a, b); await page.mouse.click(a, b, opt); await page.waitForTimeout(120); }
async function drag(page, block, x0, y0, x1, y1) {
  const [a, b] = await pt(page, block, x0, y0), [c, d] = await pt(page, block, x1, y1);
  await page.mouse.move(a, b); await page.mouse.down(); for (let i = 1; i <= 8; i++) await page.mouse.move(a + (c - a) * i / 8, b + (d - b) * i / 8); await page.mouse.up(); await ready(page);
}
const model = page => page.evaluate(() => JSON.parse(JSON.stringify(window.MMAPI.model())));
const sel = page => page.evaluate(() => window.MMAPI.sel());
let fails = 0;
function ok(cond, name, extra) { if (!cond) fails++; console.log((cond ? 'OK   ' : 'KĻŪDA ') + name + (extra !== undefined ? '  ' + JSON.stringify(extra) : '')); }
function done(errs) { if (errs && errs.length) { fails++; console.log('KĻŪDA lapas kļūdas: ' + errs.join(' | ')); } console.log(fails ? `\n${fails} kļūdas` : '\nViss kārtībā'); process.exit(fails ? 1 : 0); }
module.exports = { ROOT, build, open, ready, live, pt, click, drag, model, sel, ok, done, frame };
