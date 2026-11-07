# MM Homes lietotne (Cloudflare)

Pieteikšanās profilā, projekti sinhronizējas starp telefonu un datoru, redaktors visām mājām. Cloudflare Worker + D1 + PWA.

## Izvietošana (vienreiz, bez tokeniem)
1. Cloudflare panelī: Storage & databases -> D1 -> Create database, nosaukums `mm-homes`. Nokopē tās ID.
2. Šajā mapē `wrangler.toml` ieliec to ID laukā `database_id` (vai pasaki Claude, un viņš ieliks).
3. D1 -> mm-homes -> Console: ielīmē `schema.sql` saturu un izpildi.
4. Workers & Pages -> Create -> Import a repository -> izvēlies `SBE-Architect`. Root directory: `app`. Deploy command: `npx wrangler deploy`.
5. Settings -> Variables: `ALLOWED_EMAILS` = tavs e-pasts (komatiem atdalīti), lai neviens svešs nevarētu reģistrēties.
6. Atver adresi `*.workers.dev`, izveido kontu. Telefonā: Pievienot sākuma ekrānam.

## Jaunas mājas pievienošana
`python app/build.py` pārbūvē `public/redaktors/*.html` un `public/houses.json` no `MĀJAS/**/model.json`. Rezultātu iekomitē.

## Lokāli
`wrangler d1 execute mm-homes --local --file=schema.sql` un `wrangler dev --local`.
