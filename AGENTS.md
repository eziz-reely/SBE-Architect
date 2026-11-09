# AGENTS.md: SBE Architect

Šo failu lasa Claude Code (caur `CLAUDE.md`), Codex un Grok. Pirms koda lasīšanas izlasi šo failu un `docs/arhitektura.md`, tad atver tikai vajadzīgos failus.

## Mērķis
MM Homes modeļu bots. No mājas gabarītiem (garums, platums, kores augstums) uztaisa `model.json`, no tā klienta projekta A3 lapu LV un EN (plāni, mansards, fasādes, eksplikācija, rakstlaukums), rasējuma redaktoru pārlūkā un vizualizācijas. Darbvirsmas programma **SBE projekti** rāda projektu arhīvu un atver redaktoru.

## Struktūra (īsi, detaļas `docs/arhitektura.md`)
- `bot/generate.py`: ieejas punkts, gabarīti → `model.json` + lapas. `bot/planner.py` plānojumu varianti, `bot/rules_check.py` noteikumu pārbaude, `bot/build_model.py` `model.json` → HTML lapa.
- `bot/redaktors.py` + `bot/sablons/redaktors/` (`lapa.html` UI, `iframe.js` zīmēšanas loģika, `viz3d.js` 3D): rasējuma redaktors, viena HTML lapa.
- `bot/sablons/sbe/plani/cad.js` (zīmēšana, mēbeļu simboli), `ar.js` (AR lapas), `bot/sablons/mm-*.js|json|mjs`: lapas šablons un MM konfigurācija.
- `bot/app.py` (serveris), `bot/app_saisne.py` (darbvirsmas saīsne), `bot/arhivs.py` + `bot/sablons/arhivs/app.html` (arhīvs).
- `bot/viz.py`, `bot/ref.py`: Gemini vizualizācijas un references. `bot/skp.py`, `bot/sketchup/`: SketchUp eksports. `bot/ingetrazo/`: IngeTrazo spraudnis.
- `MĀJAS/<m2>/<id>/`: gatavie modeļi (`model.json`, `rasejumi/`, `viz/`). `PROJEKTI/` ir klientu dati un ir ignorēts git.
- `skills/`, `.claude-plugin/`: Claude plugin komandas `/sbe-arhitekts`, `/editbot`. Citi aģenti tās nelieto.

## Palaišana un pārbaude lokāli
Vajag Python 3 un pārlūku. Windows PowerShell vispirms: `$env:PYTHONIOENCODING='utf-8'` (citādi `UnicodeEncodeError`).
- Jauns modelis: `cd bot; python generate.py 8570 3500 4000 --nosaukums Freya` (karogi: `python generate.py -h`).
- Redaktora lapa: `cd bot; python redaktors.py ..\MĀJAS\100m2\MM-100-01\model.json` → `rasejumi/<id>_LV_redaktors.html`, atver ar Chrome/Edge.
- Programma: `python bot/app.py --konsole` → http://127.0.0.1:8737. Testam citā portā: `SBE_PORT=8738`. Iestatījumi `~/.sbe-arhivs.json`.
- Noteikumi: `python bot/rules_check.py <model.json>` (vai `--visi`); jābūt 0 kļūdu.
- Lapas pārbaude: `node bot/sablons/mm-check.mjs <html>` jāatbild "OK". Uzmanību: skriptā Playwright imports ir Linux ceļš (`/opt/node22/...`); uz Windows vajag `playwright` uzinstalētu un ceļu pielāgot tikai lokāli, nesaglabājot.
- IngeTrazo ģeometrija: `python -I bot/ingetrazo/tests/test_geometry.py`.
- Automātisko testu kopas nav. Izmaiņu pārbauda, pārbūvējot lapu un apskatot to pārlūkā (ekrānuzņēmums).

## Valoda un UI
- Viss lietotāja redzamais teksts, komentāri un commit ziņas latviski (LV; EN tikai A3 lapas EN versijā).
- Redaktora palete: neitrāls grafīts + zils akcents #2266d8. Ikonas: viena kopa `IC` + `icon()` lapa.html (24×24, līnija 1.6, bez pildījuma). Nelieto brūnu/zeltu.
- Lapas noformējumu, rakstlaukumu, krāsas un `sablons/sbe` šablonu nemaini, ja uzdevums to neprasa. MM labojumi tiek ielikti būvējot (`build_model.py`), ne šablonā.
- Plānā katram logam ir smalka (5) ailas līnija arī sienas iekšpusē (`cad.js`, `v.windows.forEach`). Pēc zīmēšanas izmaiņām pārbaudi, ka tā saglabājas.
- Kores augstums tiek rēķināts no grīdas paneļa apakšas; atzīmes no ±0,000 (`augstums_0` model.json).

## Darba noteikumi
1. Pirms darba: `git pull` (fetch origin main), skaties `git status`.
2. Mazi commit, viena doma katrā, latviešu ziņa.
3. **Nepushot un neveidot PR, kamēr lietotājs to nepasaka.** Kad pasaka, fast-forward `main` un push (bez PR).
4. Neraksti API atslēgas (`GEMINI_API_KEY` tikai vides mainīgajā). Neaiztiec `PROJEKTI/` un klientu datus.
5. `.py` failos rindu beigas var būt CRLF (autocrlf); patchojot lasi ar universal newlines.
6. Kopijas citur nelabo: galvenā versija ir šis repo.
