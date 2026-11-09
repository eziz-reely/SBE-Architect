# Arhitektūras piezīmes

Īss pārskats, lai nelasītu visu kodu. Visi ceļi no repo saknes.

## Datu plūsma
`generate.py <garums> <platums> <augstums>` → `model.json` (`MĀJAS/<m2>/<id>/`) → `build_model.py` → `rasejumi/<id>_LV.html` un `_EN.html`.
Ar `--varianti N` plānojumu veido `planner.py` (formas II/L/T), katrs variants iet cauri `rules_check.py`.
`model.json` galvenās atslēgas: `id, W, D, jumts, rooms, doors, windows, furniture, axes, innerDims, wallTags, sections, gableWins, ceiling, planNotes, projekts` (`projekts`: faze, revizija, adrese, modela_nosaukums, pamati, griesti, piragi). Mēbele ir masīvs `["nosaukums", ...argumenti]`; pagriezta: `["_rot", grādi, cx, cy, [mēbele]]`.

## Lapas būve
`build_model.py` ņem šablonu `bot/sablons/sbe/plani/` (`planojuma-varianti.html`, `cad.js`, `ar.js`), ieliek modeļa bloku (`rev_block`, REV=100), sienu biezumus no `bot/sablons/mm-config.json` un raksta HTML ar iegultiem fontiem. Šablona failus nemaina. `cad.js` zīmē plānu, fasādes, mēbeļu simbolus (kopīgi A3 lapām un redaktoram).

## Redaktors
`redaktors.py` no `lapa.html` (UI, CSS slāņi pēc kārtas, jaunākie beigās), `iframe.js` (rasējuma loģika, `apply`, `drawGuides`), `viz3d.js` + `three.min.js` (3D, Gemini references) saliek vienu HTML failu. Modeli un šablonu ieliek kā JSON marķieros `__MM_MODEL__`, `__MM_TEMPLATE__`. Pārbaudes noteikumus ņem no `mm-check.mjs`. Tālummaiņa ir CSS transform uz body, tāpēc `vector-effect: non-scaling-stroke` nestrādā; biezumus rēķina px (`pxU()`).
Cilne Māja: tēmas Izmēri | Jumts | Izskats | Konstrukcijas (`MAJA_SEC`). Konstrukcijas nosaukumi `projekts.piragi_names`.
Ikonas: `IC` + `icon()`. Eksporti: PDF, SVG, DXF, SketchUp .rb (`skp.py`), `model.json`.

## Serveris un arhīvs
`app.py`: `ThreadingHTTPServer` uz 127.0.0.1:8737 (`SBE_PORT`). Maršruti GET: `/api/projects`, `/api/files/`, `/file/`, `/lv/<key>`, `/pf/` (tikai `miniaturas/`, `viz/`), `/edit/<key>`, `/api/company-spec`, `/api/ping`. POST: `/api/export/`, `/api/thumb/`, `/api/viz/`, `/api/viz-del/`, `/api/sent/`, `/api/save/`, `/api/company`, `/api/new`, `/api/open`.
Saglabāšana: `/api/save/` ieraksta `model.json` (vecais → `model.json.bak`) un fonā pārbūvē LV/EN. Lietotnes lapa `bot/sablons/arhivs/app.html`.
Mapes: `<arhīvs>/<uzņēmums>/<projekts>/model.json`; apakšmapes `eksports`, `rasejumi`, `viz`, `miniaturas`, `3d`, `ref` nav projekti (`SKIP`). Uzņēmuma sienu spec. `<uzņēmums>/uznemums.json`. Iestatījumi `~/.sbe-arhivs.json` (`root`, `companies`; "MM Homes" = `Desktop\MM System\MĀJAS`).
`arhivs.py` ir vecais statiskais arhīva ģenerators (`PROJEKTI/arhivs.html`).

## Noteikumi un zināšanas
Mēbeļu un logu noteikumi: `bot/zinasanas_mebeles_logi.md` (avoti [MM], [MyCabin], [prakse]). Skaitļi un slēdži `R` vārdnīcā `planner.py`; sliekšņi augšā `rules_check.py`. Jauns noteikums: pievieno `rules_check.py`, ja pārbaudāms, un ieraksti zināšanu failā ar avotu.
