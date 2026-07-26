# dataset-hub

Machine-readable register of publicly available datasets — infrastructure of the
research ecology at [frankbueltge.de](https://frankbueltge.de).

Two uses, equally weighted:

1. **A hub for researchers** — findable, filterable, citable.
2. **A queryable base for machine-run research practices** — versioned snapshots
   (SQLite + Parquet as release assets) instead of re-researching every question.

The register grows continuously through gated automatic intake; everything admitted
automatically is visibly marked unverified.

**Status: Phase 1 — measurement.** No harvest adapters exist yet. Every source is
measured and gated *before* an adapter may be built; the results live in `messungen/`.

## Design

The canonical design document (German) lives in the site repository:

- Design: [`frankbueltge.de → docs/superpowers/specs/2026-07-26-dataset-hub-design.md`](https://github.com/frankbueltge/frankbueltge.de/blob/main/docs/superpowers/specs/2026-07-26-dataset-hub-design.md)
- Founding brief: [`frankbueltge.de → docs/research/2026-07-26-dataset-hub-startauftrag.md`](https://github.com/frankbueltge/frankbueltge.de/blob/main/docs/research/2026-07-26-dataset-hub-startauftrag.md)

## Binding rules (short form)

- **Invent nothing.** Missing values stay empty; a visible gap beats a plausible guess.
- **Verify identifiers, don't assume them.** Verified means an HTTP response was fetched.
- **Never construct URLs** — not even from title and pattern. Verbatim from the source.
- **Deterministic wherever possible.** Fetch, normalize, deduplicate, verify: code.
  No model API calls inside pipelines.
- **Automatic intake only through hard gates**; everything auto-admitted is marked
  unverified. Version control is the rollback.
- **Record rejections with reasons.** The rejection register measures the process
  against itself.
- **Record outages, never bridge them.** An empty result must never look like
  "nothing found" when it means "source unreachable".
- **Measure before building.** No adapter without a committed measurement protocol
  and a GO in `messungen/register.md`.

## Layout

| Path | Content |
|---|---|
| `messungen/TEMPLATE.md` | Measurement protocol template incl. gate thresholds |
| `messungen/skripte/` | Deterministic measurement scripts (Python 3, stdlib only) |
| `messungen/ergebnisse/` | Measurement results (JSON written by the scripts, reports in Markdown) |
| `messungen/rohdaten/` | Raw API samples (gzip) backing every reported number |
| `messungen/register.md` | GO / NO-GO register per source |

## Licensing

- **Code:** PolyForm Noncommercial 1.0.0
- **Catalog metadata** (the compilation, its records and enrichments created here,
  including released snapshots): **CC0 1.0**

See [`LICENSE.md`](LICENSE.md).
