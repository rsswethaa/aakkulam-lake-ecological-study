# Data Dictionary

| Field | Type | Description |
|---|---|---|
| `site_id` | text | Unique observation-site identifier |
| `observation_date` | date | Date of observation |
| `water_clarity_score` | integer 1–5 | Visual clarity score; higher is clearer |
| `litter_count` | integer | Visible litter items counted within the observation area |
| `vegetation_cover_pct` | numeric 0–100 | Estimated vegetation cover percentage |
| `odor_score` | integer 0–5 | Subjective odor-intensity score |
| `visible_algae` | yes/no | Whether visible algae was observed |
| `nearby_urban_pressure` | low/medium/high | Qualitative category of nearby development and human activity |
| `notes` | text | Short contextual field note |

## Validation rules
- clarity must remain between 1 and 5
- odor must remain between 0 and 5
- vegetation percentage must remain between 0 and 100
- litter count cannot be negative
- urban-pressure categories should use only the documented values

## Important provenance note
`sample_observations.csv` is reconstructed illustrative portfolio data. It exists to make the analysis workflow runnable and should not be described as the original field dataset.
