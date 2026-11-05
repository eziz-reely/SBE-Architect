// SVG -> PNG ar Playwright: node png.mjs a.svg b.svg ...  (PNG blakus SVG)
let pw;
try { pw = await import('playwright'); } catch { pw = await import('/opt/node22/lib/node_modules/playwright/index.mjs'); }
import { readFileSync } from 'fs';
const b = await pw.chromium.launch();
const p = await b.newPage({ viewport: { width: 1536, height: 1024 } });
for (const f of process.argv.slice(2)) {
  await p.setContent(`<html><body style="margin:0">${readFileSync(f, 'utf8')}</body></html>`);
  await p.screenshot({ path: f.replace(/\.svg$/, '.png'), clip: { x: 0, y: 0, width: 1536, height: 1024 } });
}
await b.close();
