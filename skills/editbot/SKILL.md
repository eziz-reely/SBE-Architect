---
name: editbot
description: SBE Architect bota papildināšana: lietotājs uzraksta komentāru vai labojumu (/editbot ...), un Claude to ieliek botā, pārbauda un saglabā repo.
---

# editbot: bota papildināšana ar vienu komandu

Lietotājs raksta `/editbot <komentāri>`, bieži ar bildi un vairākiem numurētiem punktiem. Tev tie jāieliek botā tā, lai nākamie modeļi tos ievēro paši. Atbildi latviski, īsi.

Bots ir šajā plugin repo mapē `bot/` (`planner.py`, `rules_check.py`, `generate.py`, `ref.py`, `viz.py`, `build_model.py`, `sablons/`, noteikumi `bot/zinasanas_mebeles_logi.md`). Galvenā versija ir GitHub repo `eziz-reely/SBE-Architect`.

## Soļi

1. **Saprodi visus punktus uzreiz.** Ja punkts var nozīmēt divas lietas, izvēlies ticamāko un pasaki, ko izvēlējies. Jautā tikai tad, ja atbilde maina rezultātu.
2. **Strādā repo klonā** (`add_repo` `eziz-reely/SBE-Architect`, viens `git clone`). Nokopē `bot/` uz scratchpad, labo un testē tur.
3. **Ieraksti izmaiņu minimāli.** Neaiztiec noformējumu, rakstlaukumu, krāsas, ja komentārs to neprasa. Skaitļi un slēdži: `R` vārdnīca `bot/planner.py` (vai `noteikumi.json`, ja tāds ir). Jauns noteikums: pievieno `rules_check.py`, ja pārbaudāms, un ieraksti `bot/zinasanas_mebeles_logi.md` ar avotu [MM].
4. **Pārbaudi.** Palaid botu uz pēdējā modeļa gabarītiem (`--varianti 1`, bez `--viz`), `node sablons/mm-check.mjs <html>` jābūt "OK", uzņem ekrānuzņēmumu (Playwright) un parādi lietotājam.
5. **Saglabā pēc lietotāja ok.** Commit un push uz repo (zars `main`), commit ziņā īsi uzraksti, kas mainīts. Pēc tam pasaki, ka plugin jāatjaunina (`/plugin update`).

## Neaiztiec
- Google API atslēgu neraksta failos vai ziņās (`GEMINI_API_KEY` vides mainīgais).
- Klašu atdalījumu (lidz60 / virs60), ja to neprasa lietotājs.
