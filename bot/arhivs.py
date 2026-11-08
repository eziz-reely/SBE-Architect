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
import argparse, html, json, os, re, shutil, subprocess, sys, time

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


def entry(root, company, pdir, m, ed):
    P = m.get('projekts') or {}
    rel = lambda p: os.path.relpath(p, root).replace(os.sep, '/')
    th = lambda n: rel(os.path.join(pdir, THUMBS, n + '.png')) if os.path.exists(os.path.join(pdir, THUMBS, n + '.png')) else ''
    mm = re.match(r'\d+', m.get('platiba_grupa') or '')
    digits = mm.group(0) if mm else ''
    return {
        'name': P.get('modela_nosaukums') or m.get('nosaukums') or m['id'], 'id': m['id'], 'company': company, 'href': rel(ed),
        'plan': th('plans'), 'fasade': th('fasade'), 'mtime': int(os.path.getmtime(os.path.join(pdir, 'model.json'))),
        'area': int(digits) if digits else 0, 'w': round(m['W'] / 1000, 1), 'd': round(m['D'] / 1000, 1),
        'foundation': 'Betona plātne' if P.get('pamati') == 'platne' else 'Stabu pamati',
        'pitch': (m.get('jumts') or {}).get('pitch') or 0, 'loft': 'Jā' if m.get('loft') else 'Nē',
        'rooms': len(m.get('rooms') or []), 'phase': txt(P.get('faze')), 'rev': txt(P.get('revizija')), 'address': txt(P.get('adrese')),
    }


PAGE = """<!doctype html><html lang="lv"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SBE projekti</title><style>
:root{--ink:#2a2622;--bg:#f3f1ec;--card:#fff;--line:#d3cdc2;--muted:#6f675e;--gold:#A8916A;--brand:#36312D;--hov:#e8e3d9}
@media(prefers-color-scheme:dark){:root{--ink:#ece7df;--bg:#171513;--card:#24211e;--line:#3b3631;--muted:#a59c90;--hov:#2e2a26}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.4 "Barlow","Segoe UI",system-ui,sans-serif;display:flex;flex-direction:column;height:100vh}
header{background:var(--brand);color:#f4efe6;padding:8px 16px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
header h1{font:600 16px/1 inherit;margin:0 8px 0 0;letter-spacing:.14em}
header input,header select{padding:6px 9px;border:1px solid #5d554d;border-radius:3px;background:#2b2622;color:inherit;font:inherit}header input{min-width:200px}
.sp{flex:1}.tb{display:flex;gap:6px;align-items:center;color:#cdbf9f;font-size:12px}.tb label{display:flex;gap:5px;align-items:center}
.wrap{flex:1;display:flex;min-height:0}#list{flex:1;overflow:auto;padding:12px}#pane{width:300px;border-left:1px solid var(--line);background:var(--card);overflow:auto;padding:14px;display:none}
body.hp #pane{display:block}
.it{display:flex;color:inherit;text-decoration:none;border:1px solid transparent;border-radius:3px;cursor:pointer}.it:hover,.it.sel{background:var(--hov);border-color:var(--line)}
.th{display:flex;gap:6px}.th div{background:#fff;border:1px solid var(--line);display:grid;place-items:center;overflow:hidden}.th img{max-width:100%;max-height:100%;object-fit:contain}.no{color:#999;font-size:11px}
.nm{font-weight:600}.mt{color:var(--muted);font-size:12px}
.v-xl,.v-l,.v-m{display:grid;gap:12px;align-content:start}.v-xl{grid-template-columns:repeat(auto-fill,minmax(360px,1fr))}.v-l{grid-template-columns:repeat(auto-fill,minmax(250px,1fr))}.v-m{grid-template-columns:repeat(auto-fill,minmax(170px,1fr))}
.v-xl .it,.v-l .it,.v-m .it{flex-direction:column;padding:8px;gap:3px;background:var(--card);border-color:var(--line)}
.v-xl .th{height:190px}.v-l .th{height:130px}.v-m .th{height:80px}.v-m .mt,.v-m .th div+div{display:none}.v-m .th div{flex:1}.v-xl .th div,.v-l .th div{flex:1}
.v-t{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:6px}.v-t .it{padding:6px;gap:10px;align-items:center}.v-t .th{width:96px;height:64px}.v-t .th div+div{display:none}.v-t .th div{flex:1}
.v-d .it{padding:5px 8px;gap:10px;align-items:center;border-bottom:1px solid var(--line);border-radius:0}.v-d .th{width:70px;height:44px}.v-d .th div+div{display:none}.v-d .th div{flex:1}
.col{display:grid;gap:12px;align-items:center;flex:1}.v-d .col{grid-template-columns:minmax(160px,2fr) 110px 70px 100px 130px 110px 120px}
.v-d .hd{display:grid;gap:12px;padding:6px 8px 6px 88px;color:var(--muted);font-size:12px;border-bottom:1px solid var(--line);position:sticky;top:-12px;background:var(--bg);z-index:1;grid-template-columns:minmax(160px,2fr) 110px 70px 100px 130px 110px 120px}
.hd b{cursor:pointer;font-weight:500;user-select:none}.hd b:hover{color:var(--ink)}
.v-d .col .mt{font-size:13px;color:var(--ink)}
.dl{display:grid;grid-template-columns:auto 1fr;gap:3px 12px;font-size:13px}.dl dt{color:var(--muted)}.dl dd{margin:0}
#pane h2{margin:0 0 4px;font-size:16px}#pane .big{display:grid;gap:8px;margin:10px 0}#pane .big div{background:#fff;border:1px solid var(--line);display:grid;place-items:center}#pane .big img{max-width:100%}
#pane a.o{display:block;text-align:center;background:var(--gold);color:#1f1b17;text-decoration:none;padding:8px;border-radius:3px;font-weight:600;margin-top:10px}
.e{padding:30px;color:var(--muted)}
</style></head><body><header><h1>SBE PROJEKTI</h1><input id="q" type="search" placeholder="Meklēt…">
<div class="tb">Kārtot<select id="sort"></select><select id="dir"><option value="1">Augoši</option><option value="-1">Dilstoši</option></select></div>
<div class="tb">Skats<select id="view"><option value="xl">Ļoti lielas ikonas</option><option value="l">Lielas ikonas</option><option value="m">Vidējas ikonas</option><option value="t">Flīzes</option><option value="d">Detaļas</option></select>
<label><input type="checkbox" id="hp"> Detaļu panelis</label></div>
<div class="tb">Filtrs<select id="fcom"></select><select id="ffnd"></select><select id="floft"></select></div></header>
<div class="wrap"><div id="list"></div><aside id="pane"></aside></div>
<script>
const D=%DATA%;
const F={name:['Nosaukums','s'],company:['Uzņēmums','s'],mtime:['Izmaiņu datums','n'],area:['Platība, m²','n'],w:['Garums, m','n'],foundation:['Pamati','s'],pitch:['Jumta leņķis','n'],loft:['Mansards','s'],rooms:['Telpas','n'],phase:['Fāze','s']};
const $=id=>document.getElementById(id),esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let st={sort:'mtime',dir:-1,view:'xl',hp:false,com:'',fnd:'',loft:''};
try{Object.assign(st,JSON.parse(localStorage.getItem('sbeArh')||'{}'))}catch(e){}
const save=()=>{try{localStorage.setItem('sbeArh',JSON.stringify(st))}catch(e){}};
$('sort').innerHTML=Object.entries(F).map(([k,v])=>`<option value="${k}">${v[0]}</option>`).join('');
const opts=(el,all,vals)=>{el.innerHTML=`<option value="">${all}</option>`+[...new Set(vals)].filter(Boolean).sort().map(v=>`<option>${esc(v)}</option>`).join('')};
opts($('fcom'),'Visi uzņēmumi',D.map(x=>x.company));opts($('ffnd'),'Visi pamati',D.map(x=>x.foundation));opts($('floft'),'Mansards: visi',D.map(x=>x.loft));
$('sort').value=st.sort;$('dir').value=st.dir;$('view').value=st.view;$('hp').checked=st.hp;$('fcom').value=st.com;$('ffnd').value=st.fnd;$('floft').value=st.loft;
const dt=t=>new Date(t*1000).toLocaleDateString('lv-LV');
const img=(u)=>u?`<img loading="lazy" src="${esc(u)}" alt="">`:'<span class="no">nav</span>';
let selId=null;
function row(x){
  const th=`<div class="th"><div>${img(x.plan)}</div><div>${img(x.fasade)}</div></div>`;
  if(st.view==='d')return `<a class="it" data-id="${esc(x.id+x.company)}" href="${esc(x.href)}">${th}<div class="col"><span class="nm">${esc(x.name)}</span><span class="mt">${dt(x.mtime)}</span><span class="mt">${x.area} m²</span><span class="mt">${x.w} × ${x.d} m</span><span class="mt">${esc(x.foundation)}</span><span class="mt">${x.pitch}° · mansards ${x.loft}</span><span class="mt">${esc(x.company)}</span></div></a>`;
  return `<a class="it" data-id="${esc(x.id+x.company)}" href="${esc(x.href)}">${th}<div><div class="nm">${esc(x.name)}</div><div class="mt">${x.area} m² · ${x.w} × ${x.d} m · ${esc(x.foundation)}</div><div class="mt">${dt(x.mtime)} · ${esc(x.company)}</div></div></a>`;
}
function render(){
  const t=$('q').value.trim().toLowerCase(),k=st.sort,num=F[k][1]==='n';
  const r=D.filter(x=>(!st.com||x.company===st.com)&&(!st.fnd||x.foundation===st.fnd)&&(!st.loft||x.loft===st.loft)&&(!t||(x.name+' '+x.id+' '+x.company+' '+x.address+' '+x.foundation).toLowerCase().includes(t)))
    .sort((a,b)=>st.dir*(num?a[k]-b[k]:String(a[k]).localeCompare(String(b[k]),'lv')));
  const hd=st.view==='d'?`<div class="hd">${[['name','Nosaukums'],['mtime','Izmaiņu datums'],['area','Platība'],['w','Izmēri'],['foundation','Pamati'],['pitch','Jumts, mansards'],['company','Uzņēmums']].map(([k2,l])=>`<b data-s="${k2}">${l}${st.sort===k2?(st.dir>0?' ▲':' ▼'):''}</b>`).join('')}</div>`:'';
  $('list').className='v-'+st.view;$('list').innerHTML=r.length?hd+r.map(row).join(''):'<p class="e">Nekas nav atrasts.</p>';
  $('hp').parentElement.style.display='';document.body.classList.toggle('hp',st.hp);
  $('list').querySelectorAll('.hd b').forEach(b=>b.onclick=()=>{if(st.sort===b.dataset.s)st.dir=-st.dir;else{st.sort=b.dataset.s;st.dir=1}$('sort').value=st.sort;$('dir').value=st.dir;save();render()});
  $('list').querySelectorAll('.it').forEach(a=>{a.onmouseenter=()=>{if(st.hp)pane(a.dataset.id)};a.onclick=e=>{if(st.hp&&!e.detail||false){}};});
}
function pane(id){const x=D.find(y=>y.id+y.company===id);if(!x)return;
 $('pane').innerHTML=`<h2>${esc(x.name)}</h2><div class="mt">${esc(x.id)}</div><div class="big"><div>${img(x.plan)}</div><div>${img(x.fasade)}</div></div><dl class="dl"><dt>Uzņēmums</dt><dd>${esc(x.company)}</dd><dt>Izmaiņas</dt><dd>${dt(x.mtime)}</dd><dt>Platība</dt><dd>${x.area} m²</dd><dt>Izmēri</dt><dd>${x.w} × ${x.d} m</dd><dt>Pamati</dt><dd>${esc(x.foundation)}</dd><dt>Jumta leņķis</dt><dd>${x.pitch}°</dd><dt>Mansards</dt><dd>${x.loft}</dd><dt>Telpas</dt><dd>${x.rooms}</dd><dt>Fāze</dt><dd>${esc(x.phase)||'—'}</dd><dt>Versija</dt><dd>${esc(x.rev)||'—'}</dd><dt>Adrese</dt><dd>${esc(x.address)||'—'}</dd></dl><a class="o" href="${esc(x.href)}">Atvērt redaktoru</a>`}
[['q','input'],['sort','change'],['dir','change'],['view','change'],['hp','change'],['fcom','change'],['ffnd','change'],['floft','change']].forEach(([id,ev])=>$(id).addEventListener(ev,()=>{st.sort=$('sort').value;st.dir=+$('dir').value;st.view=$('view').value;st.hp=$('hp').checked;st.com=$('fcom').value;st.fnd=$('ffnd').value;st.loft=$('floft').value;save();render();if(st.hp&&D[0])pane(D[0].id+D[0].company)}));
render();if(st.hp&&D[0])pane(D[0].id+D[0].company);
</script></body></html>"""


def build(root):
    os.makedirs(root, exist_ok=True)
    cards = []
    for company, pdir in find_projects(root):
        try:
            m, ed = build_one(pdir)
            cards.append(entry(root, company, pdir, m, ed))
        except Exception as e:
            print('Kļūda projektā', pdir, e)
    out = os.path.join(root, 'arhivs.html')
    open(out, 'w', encoding='utf-8').write(PAGE.replace('%DATA%', json.dumps(cards, ensure_ascii=False).replace('</', '<\\/')))
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
