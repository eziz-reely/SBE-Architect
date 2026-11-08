"""SBE projektu arhīvs: viens logs ar visiem projektiem (nosaukums, laukums, plāna un fasādes miniatūra).

Mapju struktūra (uzņēmums, tad projekts):

    PROJEKTI/
      Uznemums A/
        MM-100-01/model.json
        Kaut kas-cits/model.json
      Uznemums B/
        ...

Lietošana:
    python3 bot/arhivs.py PROJEKTI                      uzbūvē PROJEKTI/arhivs.html (atver ar Chrome vai Edge)
    python3 bot/arhivs.py PROJEKTI --pievienot model.json --uznemums "Uzņēmums A"
                                                        ieliek modeli arhīvā un pārbūvē arhīvu
    python3 bot/arhivs.py PROJEKTI --uznemums "Jauns"   tikai izveido uzņēmuma mapi

Miniatūras un redaktora lapa tiek uzbūvētas tikai tad, ja model.json ir jaunāks nekā iepriekš uzbūvētais.
Vajag Python 3, Node.js ar Playwright (kā pārējam botam).
"""
import argparse, html, json, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
THUMBS = 'miniaturas'

SHOT_JS = r"""
const { chromium } = require('playwright');
(async () => {
  const [file, outDir] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 2 });
  await p.goto('file://' + file); await p.waitForTimeout(1800);
  const fr = p.frames().find(f => f.url().startsWith('about:srcdoc'));
  const shot = async (sel, name) => {
    const h = await fr.$(sel); if (!h) return;
    try { await h.screenshot({ path: outDir + '/' + name + '.png' }); } catch (e) {}
  };
  await shot('[data-block="plan"]', 'plans');
  await shot('[data-block="elev-south"]', 'fasade');
  await b.close();
})();
"""


def find_projects(root):
    out = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in (THUMBS, 'rasejumi', 'viz', 'node_modules', '.git')]
        if 'model.json' in fn:
            rel = os.path.relpath(dp, root).split(os.sep)
            company = rel[0] if len(rel) > 1 else 'Bez uzņēmuma'
            out.append((company, dp))
    return sorted(out, key=lambda x: (x[0].lower(), os.path.basename(x[1]).lower()))


def needs(model, target):
    return not os.path.exists(target) or os.path.getmtime(target) < os.path.getmtime(model)


def build_one(pdir):
    mp = os.path.join(pdir, 'model.json')
    m = json.load(open(mp, encoding='utf-8'))
    ed = os.path.join(pdir, 'rasejumi', f"{m['id']}_LV_redaktors.html")
    if needs(mp, ed):
        subprocess.run([sys.executable, os.path.join(HERE, 'redaktors.py'), mp], check=True, stdout=subprocess.DEVNULL)
    td = os.path.join(pdir, THUMBS)
    os.makedirs(td, exist_ok=True)
    if needs(mp, os.path.join(td, 'plans.png')):
        js = os.path.join(HERE, '_miniatura.mjs.cjs')
        open(js, 'w').write(SHOT_JS)
        env = dict(os.environ)
        try:
            env['NODE_PATH'] = subprocess.run(['npm', 'root', '-g'], capture_output=True, text=True).stdout.strip() + os.pathsep + env.get('NODE_PATH', '')
        except Exception:
            pass
        try:
            subprocess.run(['node', js, os.path.abspath(ed), td], check=True, cwd=HERE, timeout=120, env=env, stderr=subprocess.DEVNULL)
        except Exception as e:
            print('Miniatūras neizdevās:', pdir, e)
        finally:
            try: os.remove(js)
            except OSError: pass
    return m, ed


def txt(v):
    return ', '.join(str(x) for x in v if x) if isinstance(v, (list, tuple)) else (str(v) if v else '')


def card(root, company, pdir, m, ed):
    P = m.get('projekts') or {}
    rel = lambda p: os.path.relpath(p, root).replace(os.sep, '/')
    name = P.get('modela_nosaukums') or m.get('nosaukums') or m['id']
    area = (m.get('platiba_grupa') or '').replace('m2', ' m²')
    meta = ' · '.join(x for x in [area, f"{m['W'] / 1000:.1f} × {m['D'] / 1000:.1f} m", txt(P.get('adrese')), txt(P.get('faze'))] if x)
    when = time.strftime('%d.%m.%Y', time.localtime(os.path.getmtime(os.path.join(pdir, 'model.json'))))
    img = lambda n: (f'<img loading="lazy" src="{html.escape(rel(os.path.join(pdir, THUMBS, n + ".png")))}" alt="">'
                     if os.path.exists(os.path.join(pdir, THUMBS, n + '.png')) else '<span class="no">nav</span>')
    q = html.escape((company + ' ' + name + ' ' + m['id'] + ' ' + meta).lower())
    return (f'<a class="c" data-co="{html.escape(company)}" data-q="{q}" href="{html.escape(rel(ed))}">'
            f'<div class="th"><div>{img("plans")}</div><div>{img("fasade")}</div></div>'
            f'<b>{html.escape(name)}</b><small>{html.escape(m["id"])} · {html.escape(meta)}</small><small class="d">{when} · {html.escape(company)}</small></a>')


PAGE = """<!doctype html><html lang="lv"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SBE projekti</title><style>
:root{--ink:#2a2622;--bg:#f3f1ec;--card:#fff;--line:#d3cdc2;--muted:#6f675e;--gold:#A8916A;--brand:#36312D}
@media(prefers-color-scheme:dark){:root{--ink:#ece7df;--bg:#171513;--card:#24211e;--line:#3b3631;--muted:#a59c90}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.4 "Barlow","Segoe UI",system-ui,sans-serif}
header{background:var(--brand);color:#f4efe6;padding:10px 16px;display:flex;gap:14px;align-items:center;flex-wrap:wrap;position:sticky;top:0;z-index:3}
header h1{font:600 16px/1 inherit;margin:0;letter-spacing:.14em}header input{flex:1;min-width:160px;max-width:380px;padding:7px 10px;border:1px solid #5d554d;border-radius:3px;background:#2b2622;color:inherit;font:inherit}
.chips{display:flex;gap:6px;flex-wrap:wrap}.chips button{background:#4a433d;color:#f4efe6;border:1px solid #5d554d;border-radius:3px;padding:5px 10px;font:inherit;cursor:pointer}.chips button.on{background:var(--gold);color:#1f1b17;border-color:var(--gold)}
main{padding:16px;display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
.c{background:var(--card);border:1px solid var(--line);border-radius:3px;padding:8px;color:inherit;text-decoration:none;display:flex;flex-direction:column;gap:3px}.c:hover{border-color:var(--gold)}
.th{display:grid;grid-template-columns:1fr 1fr;gap:6px;height:150px;margin-bottom:4px}.th div{background:#fff;border:1px solid var(--line);display:grid;place-items:center;overflow:hidden}.th img{max-width:100%;max-height:100%;object-fit:contain}.no{color:#999;font-size:12px}
.c small{color:var(--muted)}.c .d{font-size:12px}.e{padding:30px;color:var(--muted)}
</style></head><body><header><h1>SBE PROJEKTI</h1><input id="q" type="search" placeholder="Meklēt: nosaukums, uzņēmums, adrese…"><div class="chips" id="chips"></div></header>
<main id="m">%CARDS%</main><p class="e" id="e" hidden>Nekas nav atrasts.</p>
<script>
const cards=[...document.querySelectorAll('.c')],cos=[...new Set(cards.map(c=>c.dataset.co))];let co='';
const ch=document.getElementById('chips');
['Visi',...cos].forEach((n,i)=>{const b=document.createElement('button');b.textContent=n;b.onclick=()=>{co=i?n:'';[...ch.children].forEach(x=>x.classList.toggle('on',x===b));f()};if(!i)b.classList.add('on');ch.appendChild(b)});
const q=document.getElementById('q');q.oninput=f;
function f(){const t=q.value.trim().toLowerCase();let n=0;cards.forEach(c=>{const ok=(!co||c.dataset.co===co)&&(!t||c.dataset.q.includes(t));c.hidden=!ok;if(ok)n++});document.getElementById('e').hidden=n>0}
</script></body></html>"""


def build(root):
    os.makedirs(root, exist_ok=True)
    cards = []
    for company, pdir in find_projects(root):
        try:
            m, ed = build_one(pdir)
            cards.append(card(root, company, pdir, m, ed))
        except Exception as e:
            print('Kļūda projektā', pdir, e)
    out = os.path.join(root, 'arhivs.html')
    open(out, 'w', encoding='utf-8').write(PAGE.replace('%CARDS%', '\n'.join(cards) or '<p class="e">Arhīvā vēl nav projektu.</p>'))
    print(f'Gatavs: {out} ({len(cards)} projekti)')
    return out


def main():
    ap = argparse.ArgumentParser(description='SBE projektu arhīvs')
    ap.add_argument('root', help='arhīva mape (piem. PROJEKTI)')
    ap.add_argument('--pievienot', metavar='model.json', help='ieliek modeli arhīvā (mapē <uzņēmums>/<modeļa id>)')
    ap.add_argument('--uznemums', help='uzņēmuma mapes nosaukums')
    a = ap.parse_args()
    co = a.uznemums or 'Bez uzņēmuma'
    if a.pievienot:
        m = json.load(open(a.pievienot, encoding='utf-8'))
        dest = os.path.join(a.root, co, m['id'])
        os.makedirs(dest, exist_ok=True)
        shutil.copy(a.pievienot, os.path.join(dest, 'model.json'))
    elif a.uznemums:
        os.makedirs(os.path.join(a.root, a.uznemums), exist_ok=True)
    build(a.root)


if __name__ == '__main__':
    main()
