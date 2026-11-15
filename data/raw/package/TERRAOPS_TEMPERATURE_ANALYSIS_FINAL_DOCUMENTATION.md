# TERRAOPS — Temperature Analysis

## Assigned workstream
Temperature Analysis: prepared Mars and Earth temperature datasets, measurement types, units, observation periods, quality flags, scientific comparison validity, temperature matching method and When-to-Test feasibility.

## 1. Dataset assessment
The Earth analysis uses NASA POWER 2-m air temperature and MODIS daytime/nighttime land-surface temperature for Atacama, Iceland and Ladakh. The current daily analysis spans 1–31 July 2024.
The Mars analysis uses MEDA TIRS air and ground temperature observations and separate ATS sensor channels. TIRS per-sol summaries cover 1,751 sols. Official Ls mapping is available for 1496 of those sols.

## 2. Measurement compatibility
The primary scientifically defensible pairings are NASA POWER T2M versus MEDA TIRS air temperature, and MODIS land-surface temperature versus MEDA TIRS ground temperature.
Air temperature must not be treated as equivalent to ground or land-surface temperature. Surface-to-surface comparisons also require caution because the instruments have different footprints and measurement methods.

## 3. Temperature matching method
Mars observations are assigned to northern seasons using official solar longitude. Local-time observations are grouped into 30-minute LTST bins. Per-sol bin means are then used to construct seasonal reference distributions.
The current reference eligibility rule requires at least 10 contributing sols per seasonal local-time bin. All four seasons currently meet that threshold in the generated profiles.
Earth observations are compared against the relevant Mars temperature envelope. Daily Earth data do not automatically support exact local-time matching.

## 4. Quality and uncertainty
Per-sol TIRS air and ground uncertainty summaries and flag fractions have been generated. Flag fractions are descriptive and do not establish good/bad data quality.
Official flag semantics, irradiance definitions and rover/solar geometry still require verification against the official MEDA product documentation.

## 5. Earth–Mars comparison findings
The corrected comparison tables report 0% Earth observations inside the Mars seasonal central P05–P95 envelopes for the comparisons performed. This is an observed result for the available July Earth data and selected Mars seasonal reference distributions. It does not prove that the Earth sites are unsuitable analogs.
The Earth data cover one month only. The results therefore cannot establish a full annual analog testing calendar.

## 6. Sol 367
The Sol 367 investigation identified a substantial observation gap. The sol is retained, and no temperature interpolation is performed across the missing interval.

## 7. When-to-Test feasibility
A preliminary seasonal Mars reference framework is feasible. Preliminary Earth–Mars temperature comparisons are also feasible when measurement classes are correctly paired.
A validated annual When-to-Test feature is not yet supported by the current Earth coverage. Further temporal coverage, official quality interpretation and geometry verification are required.

## 8. Outstanding work
1. Verify official MEDA flag definitions and filtering implications.
2. Verify solar geometry and rover orientation using ancillary data.
3. Verify irradiance units, calibration and viewing geometry.
4. Expand Earth-site temporal coverage beyond July 2024.
5. Develop exact Earth local-time matching where source data allow.
6. Develop full uncertainty propagation before operational claims.

## 9. Overall task status
The main dataset audit, measurement-class separation, initial scientific comparison matrix and Mars temperature matching framework are complete. The remaining items are verification and validation limitations rather than reasons to repeat the completed full-data processing.