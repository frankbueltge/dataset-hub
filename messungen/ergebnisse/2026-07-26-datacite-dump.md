# Messnotiz — DataCite Public Data File (Bulk-Bootstrap-Weg)

**Datum:** 2026-07-26 · **Rohdaten:** `rohdaten/datacite-datafiles-uebersicht.html.gz`,
`rohdaten/datacite-datafiles-public-2025.html.gz` (Seiten wörtlich gesichert)

## Befund (von der Landing-Page `datafiles.datacite.org/datafiles/public-2025`)

| | |
|---|---|
| Angebot | Jahres-Dumps `public-2023`, `public-2024`, `public-2025` (+ PID-Link-Dateien) |
| Inhalt 2025 | alle DOIs im Zustand Findable bis Ende 2025, **alle Ressourcentypen** (nicht nur Datasets) |
| Umfang | **108.468.906 Records · 33 GiB komprimiert · 615 GiB entpackt** |
| Eigene Identität | DOI 10.14454/t5qb-d995; CRC32/SHA-256 publiziert |
| Zugang | Download-Link **per E-Mail-Registrierung** + Anerkennung der Data File Use Policy → Stufe `registration` |

Hübsche Selbstanwendung: Der Dump passiert die eigene Aufnahme-Schranke des Hubs
(Titel, Urheber, geprüfte Landing-URL, PID, Stufe registration).

## Konsequenz

- **Inkrementell zuerst:** Der Kern erntet ab sofort über die REST-API
  (updated-Fenster, Cursor — belegt, läuft). Damit wächst der Bestand ab heute
  vorwärts vollständig.
- **Bulk-Bootstrap = eigener, späterer Schritt:** 33 GiB Download (E-Mail-Registrierung
  durch Frank) und ~650 GiB Verarbeitungsplatz; der Dataset-Anteil (~72,7 Mio. von
  108,5 Mio.) würde die Bestandslücke vor dem Aufsetzzeitpunkt schließen. Bis dahin
  wird die Lücke ausgewiesen, nicht verschwiegen (Design §7).
