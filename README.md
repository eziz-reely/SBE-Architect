# SBE Architect

MM Homes modeļu bots kā Claude plugin. No mājas gabarītiem (garums, platums, kores augstums) uztaisa skiču projekta A3 lapu LV un EN (plāni, mansards, fasādes, eksplikācija, rakstlaukums) un Gemini vizualizācijas.

## Instalēšana

    /plugin marketplace add eziz-reely/SBE-Architect
    /plugin install sbe-architect@sbe-architect

## Komandas

- `/sbe-arhitekts`: jauns modelis. Uzdod jautājumus ar ķeksīšiem, uzģenerē plānojumu (vienmēr sāk ar 1. variantu), pārbauda un parāda apstiprināšanai. Vizualizācijas tikai pēc apstiprinājuma.
- `/editbot <komentārs>`: papildina botu (noteikumi, logu veidi, mēbeļu izkārtojums), pārbauda un saglabā šajā repo.

## Struktūra

- `bot/`: kods (`planner.py`, `rules_check.py`, `generate.py`, `build_model.py`, `ref.py`, `viz.py`), `sablons/` (SBE šablons, toņu tekstūras) un noteikumi `bot/zinasanas_mebeles_logi.md`.
- `skills/sbe-arhitekts`, `skills/editbot`: komandu instrukcijas.

## Vides prasības

Python 3, Node.js ar Playwright (pārbaudei un ekrānuzņēmumiem). Vizualizācijām vides mainīgais `GEMINI_API_KEY` (to nekad neglabā repo).

## Kā lietot (īsi)

1. **Jauns modelis:** jaunā threadā raksti `/sbe-arhitekts` (vai "jauns modelis"). Atbildi čatā uz jautājumu sarakstu ar ķeksīšiem: gabarīti (garums × platums × kores augstums), nosaukums, tonis, mansards. Pārējam ir noklusējumi.
2. **Bots uztaisa vienu plānojumu (V01)**, A3 lapu LV un EN un pārbauda to ar `rules_check` un `mm-check`. Tu redzi plāna bildi.
3. **Tu apstiprini vai labo.** Ja kaut kas nav labi, raksti `/editbot` ar numurētiem punktiem un bildi. Bots to ieraksta noteikumos un nākamie modeļi to ievēro.
4. **Tikai pēc apstiprinājuma** raksti, ka gribi vizualizācijas. Tām vajag `GEMINI_API_KEY` (iestatīts projekta vidē `gemini`).
5. Faili ir `MM System\MĀJAS\<m2>\<id>\`: `model.json`, `rasejumi/*.html`, `viz/*.png`. Tos vēlāk izmanto mājaslapai.

## Lai komandas nesajūk

- `/sbe-arhitekts`: tikai jauns modelis. Neko nemaina botā.
- `/editbot`: tikai bota plānošanas prasmju uzlabošana (noteikumi, logi, mēbeļu izkārtojums). Modeli neveido, tikai pārbauda uz pēdējā.
- Vecos konta skilus (`modelu-bots`, `sbe-arhitekts`, `editbot`, `gemini-arch-foto`, `lwdc-plani-fasades`) vajag izslēgt vai dzēst Settings > Skills, lai tie nesajūk ar šī plugin `/sbe-arhitekts` un `/editbot`.
- Vienīgā galvenā bota versija ir šis repo. Neviena cita kopija (dators, projekta faili) vairs nav jālabo.
