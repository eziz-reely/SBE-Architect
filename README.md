# SBE Architect

MM Homes modeļu bots kā Claude plugin. No mājas gabarītiem (garums, platums, kores augstums) uztaisa skiču projekta A3 lapu LV un EN (plāni, mansards, fasādes, eksplikācija, rakstlaukums) un Gemini vizualizācijas.

## Instalēšana

    /plugin marketplace add eziz-reely/SBE-Architect
    /plugin install sbe-architect@sbe-architect

## Komandas

- `/sbe`: jauns modelis. Uzdod jautājumus ar ķeksīšiem, uzģenerē plānojumu (vienmēr sāk ar 1. variantu), pārbauda un parāda apstiprināšanai. Vizualizācijas tikai pēc apstiprinājuma.
- `/editbot <komentārs>`: papildina botu (noteikumi, logu veidi, mēbeļu izkārtojums), pārbauda un saglabā šajā repo.

## Struktūra

- `bot/`: kods (`planner.py`, `rules_check.py`, `generate.py`, `build_model.py`, `ref.py`, `viz.py`), `sablons/` (SBE šablons, toņu tekstūras) un noteikumi `bot/zinasanas_mebeles_logi.md`.
- `skills/sbe`, `skills/editbot`: komandu instrukcijas.

## Vides prasības

Python 3, Node.js ar Playwright (pārbaudei un ekrānuzņēmumiem). Vizualizācijām vides mainīgais `GEMINI_API_KEY` (to nekad neglabā repo).
