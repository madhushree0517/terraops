# TERRAOPS Data Gap Report

## Inventory Evidence

The inventory was run against `data/raw/` on 2026-11-14. That directory was absent at run time, so the inventory contained **0 files and 0 read errors**. The generated `data/raw_inventory.csv` has the inventory headers and no data rows. No raw inputs are available in this workspace to match to the contract. The statements below describe missing evidence and questions, not inferred source datasets.

## Contract File Gaps

### `sites.geojson`

- Raw inputs that could feed it: none observed.
- Missing: site features, stable `site_id` values, body labels, decimal-degree coordinates, and site notes.
- CRS mismatch: not assessable; no raw vector files or coordinate metadata were inventoried.
- Questions: Are the source site locations points or boundaries? Which exact site identifiers should be used for joins, and what CRS/datum should be recorded?

### `terrain_parameters.csv`

- Raw inputs that could feed it: none observed. No raster or vector terrain files were inventoried.
- Missing: elevation and slope statistics, roughness metric and definition, DEM source, and spatial resolution.
- Unit/CRS mismatch: not assessable. In particular, the Mars and Earth elevation datums, vertical units, horizontal CRS, and resolutions are unknown.
- Questions: What vertical datum applies to each DEM? Are Mars and Earth elevation values comparable after a documented datum conversion? Which roughness metric and units are intended?

### `temperature_monthly.csv`

- Raw inputs that could feed it: none observed. No CSV or NetCDF measurements were inventoried.
- Missing: monthly summaries for each site and variable, Celsius values, observation counts, source, and observation periods.
- Variable/unit mismatch: not assessable. No evidence establishes whether any temperature source is air temperature or surface temperature, or whether source values need conversion to Celsius.
- Questions: What instrument/product defines each variable? At what height or surface layer? How should months and missing observations be aggregated?

### `mars_temperature_envelope.json`

- Raw inputs that could feed it: none observed.
- Missing: Mars envelope bounds, source, method, and caveats.
- Variable/unit mismatch: not assessable; no Mars temperature variable or units are present to compare against Earth data.
- Questions: Is the intended envelope for `surface_temp` or `air_temp`, and what Mars product, period, and derivation define its bounds?

### `analogy_gaps.json`

- Raw inputs that could feed it: none observed. The inventory cannot identify engineering notes or reviewed analogy assessments.
- Missing: reviewed factors, rehearsal applicability, and scoped explanations.
- Questions: Which engineering notes are approved for inclusion, and who will review the boolean rehearsal judgments?

### `datasets_catalogue.csv`

- Raw inputs that could feed it: none observed.
- Missing: dataset names, providers, URLs, formats, spatial/temporal resolution, observation periods, units, CRS, limitations, citations, and licence terms.
- Unit/CRS mismatch: not assessable because no raw files or source metadata were found.
- Questions: Where are the source metadata records, and what citation/licence text should accompany each dataset?

## Required Follow-Up

Place the reviewed source files in `data/raw/` without editing them, then rerun `python -m scripts.inventory_raw_data`. Revisit this report using the resulting metadata; do not populate processed contract files until unresolved variable, unit, CRS, datum, and provenance questions have evidence-backed answers.