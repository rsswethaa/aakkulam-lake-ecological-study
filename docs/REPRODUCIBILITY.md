# Reproducibility Checklist

1. Create and activate a Python virtual environment.
2. Install dependencies from `requirements.txt`.
3. Confirm `data/sample_observations.csv` is present.
4. Run `python analysis.py`.
5. Check the generated `outputs/pressure_summary.csv`.
6. Check `outputs/algae_rate_by_pressure.csv`.
7. Check `outputs/litter_by_pressure.png`.

## Expected behaviour
The script should complete without external services or credentials. Results are derived only from the included illustrative CSV file.

## Review checks
- no negative litter values
- clarity remains within 1–5
- odor remains within 0–5
- vegetation remains within 0–100%
- urban-pressure labels use low, medium or high
- outputs can be regenerated from a clean environment

## Provenance
The sample data is intentionally labelled reconstructed/illustrative throughout the repository so it cannot reasonably be mistaken for the original academic field measurements.
