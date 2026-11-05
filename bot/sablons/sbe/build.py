# Build: injects cad.js + ar.js into the page, embeds the Barlow font, writes print pages.
#   print-h.html  – plan + facades (2 sheets)       print-ar.html – full AR set from ar-config.json
import base64, json, os
REV = 7   # revision (Rev. block in cad.js) to print
os.chdir(os.path.dirname(os.path.abspath(__file__)) + '/plani')
c = open('cad.js').read().replace('/*AR*/', open('ar.js').read())
h = open('planojuma-varianti.html').read()
m = '<!-- cad-mode -->'; h = h[:h.index(m)].rstrip() + '\n' + m + '\n<script>\n' + c + '</script>\n'
open('planojuma-varianti.html', 'w').write(h)
d = '../fonts/dl/'
font = '<style>' + ''.join(f"@font-face{{font-family:'Barlow';font-weight:{w};src:url(data:font/woff2;base64,{base64.b64encode(open(d + fn, 'rb').read()).decode()}) format('woff2');unicode-range:{ur};}}" for fn, w, ur in json.load(open(d + 'barlow.json'))) + '</style><script>window.HUMANIZED=true;</script>'
s = h.replace('<link rel="stylesheet" href="https://fonts.googleapis.com', '<link rel="x-disabled" href="https://fonts.googleapis.com', 1).replace('"Sora", "IBM Plex Sans"', '"Barlow"')
page = lambda js: '<!doctype html><html lang="lv"><head><meta charset="utf-8"><title>Rasējumi</title>' + font + f'</head><body><script>window.PRINT_MODE=true;window.PRINT_REV={REV};{js}</script>' + s + '</body></html>'
open('planojuma-varianti-humanized.html', 'w').write(font + h.replace('"Sora", "IBM Plex Sans"', '"Barlow"'))
open('print-h.html', 'w').write(page(''))
open(f'print{REV}-h.html', 'w').write(page('window.VARIANT_LABEL="2";'))
open('planonly-h.html', 'w').write(page('window.PLAN_ONLY=true;'))
if os.path.exists('ar-config.json'):
    open('print-ar.html', 'w').write(page('window.AR=' + open('ar-config.json').read() + ';'))
