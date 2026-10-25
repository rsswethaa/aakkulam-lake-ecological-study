import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import kruskal

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_FILE = BASE_DIR / "data" / "sample_observations.csv"
DEFAULT_OUTPUT_DIR = BASE_DIR / "outputs"
PRESSURE_ORDER = ["low", "medium", "high"]
NUMERIC_METRICS = [
    "water_clarity_score",
    "litter_count",
    "vegetation_cover_pct",
    "odor_score",
]


def clean_observations(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate categories, coerce metrics and preserve missingness explicitly."""
    required = {"site_id", "nearby_urban_pressure", "visible_algae", *NUMERIC_METRICS}
    missing_columns = required.difference(df.columns)
    if missing_columns:
        raise ValueError(f"missing required columns: {', '.join(sorted(missing_columns))}")

    cleaned = df.copy()
    if "observation_date" in cleaned.columns:
        cleaned["observation_date"] = pd.to_datetime(cleaned["observation_date"], errors="coerce")

    cleaned["nearby_urban_pressure"] = (
        cleaned["nearby_urban_pressure"].astype("string").str.strip().str.lower()
    )
    invalid_pressure = cleaned.loc[
        cleaned["nearby_urban_pressure"].notna()
        & ~cleaned["nearby_urban_pressure"].isin(PRESSURE_ORDER),
        "nearby_urban_pressure",
    ].drop_duplicates()
    if not invalid_pressure.empty:
        raise ValueError(
            "invalid nearby_urban_pressure values: " + ", ".join(invalid_pressure.astype(str))
        )

    for column in NUMERIC_METRICS:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

    algae_raw = cleaned["visible_algae"].astype("string").str.strip().str.lower()
    algae_map = {
        "yes": True,
        "y": True,
        "true": True,
        "1": True,
        "no": False,
        "n": False,
        "false": False,
        "0": False,
    }
    cleaned["algae_present"] = algae_raw.map(algae_map).astype("boolean")

    missingness = pd.DataFrame(
        {
            "column": cleaned.columns,
            "missing_count": [int(cleaned[column].isna().sum()) for column in cleaned.columns],
            "missing_pct": [
                round(float(cleaned[column].isna().mean() * 100), 2)
                for column in cleaned.columns
            ],
        }
    )
    return cleaned, missingness


def bootstrap_mean_ci(values, confidence=0.95, n_boot=2000, seed=42):
    values = pd.Series(values).dropna().astype(float).to_numpy()
    if len(values) == 0:
        return np.nan, np.nan
    if len(values) == 1:
        return float(values[0]), float(values[0])
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(n_boot, len(values)), replace=True).mean(axis=1)
    alpha = (1 - confidence) / 2
    low, high = np.quantile(samples, [alpha, 1 - alpha])
    return float(low), float(high)


def group_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for pressure in PRESSURE_ORDER:
        group = df[df["nearby_urban_pressure"] == pressure]
        row = {
            "nearby_urban_pressure": pressure,
            "observations": int(len(group)),
        }
        for metric in NUMERIC_METRICS:
            values = group[metric].dropna()
            ci_low, ci_high = bootstrap_mean_ci(values, seed=42 + len(rows))
            row[f"{metric}_n"] = int(values.size)
            row[f"{metric}_mean"] = round(float(values.mean()), 3) if not values.empty else np.nan
            row[f"{metric}_median"] = round(float(values.median()), 3) if not values.empty else np.nan
            row[f"{metric}_std"] = round(float(values.std(ddof=1)), 3) if values.size > 1 else np.nan
            row[f"{metric}_ci95_low"] = round(ci_low, 3) if np.isfinite(ci_low) else np.nan
            row[f"{metric}_ci95_high"] = round(ci_high, 3) if np.isfinite(ci_high) else np.nan
        known_algae = group["algae_present"].dropna()
        row["algae_known_n"] = int(known_algae.size)
        row["algae_missing_n"] = int(group["algae_present"].isna().sum())
        row["algae_presence_pct"] = (
            round(float(known_algae.mean() * 100), 1) if not known_algae.empty else np.nan
        )
        rows.append(row)
    return pd.DataFrame(rows).set_index("nearby_urban_pressure")


def kruskal_tests(df: pd.DataFrame) -> pd.DataFrame:
    """Compare numeric metrics across low/medium/high pressure without normality assumptions."""
    rows = []
    for metric in NUMERIC_METRICS:
        groups = [
            df.loc[df["nearby_urban_pressure"] == pressure, metric].dropna().astype(float).to_numpy()
            for pressure in PRESSURE_ORDER
        ]
        usable = [group for group in groups if len(group) > 0]
        if len(usable) < 2 or len({value for group in usable for value in group}) < 2:
            statistic, p_value = np.nan, np.nan
        else:
            statistic, p_value = kruskal(*usable)
        n_total = sum(len(group) for group in usable)
        k = len(usable)
        epsilon_squared = (
            max(0.0, float(statistic - k + 1) / float(n_total - k))
            if np.isfinite(statistic) and n_total > k
            else np.nan
        )
        rows.append(
            {
                "metric": metric,
                "groups_tested": k,
                "n_total": n_total,
                "H_statistic": round(float(statistic), 4) if np.isfinite(statistic) else np.nan,
                "p_value": round(float(p_value), 6) if np.isfinite(p_value) else np.nan,
                "epsilon_squared": round(epsilon_squared, 4) if np.isfinite(epsilon_squared) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def plot_litter_with_ci(summary: pd.DataFrame, output_path: Path):
    plot_data = summary.loc[PRESSURE_ORDER]
    means = plot_data["litter_count_mean"].to_numpy(dtype=float)
    lower = means - plot_data["litter_count_ci95_low"].to_numpy(dtype=float)
    upper = plot_data["litter_count_ci95_high"].to_numpy(dtype=float) - means
    errors = np.vstack([np.maximum(lower, 0), np.maximum(upper, 0)])
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(PRESSURE_ORDER, means, yerr=errors, capsize=5)
    ax.set_title("Mean litter count by urban-pressure group (95% bootstrap CI)")
    ax.set_xlabel("Nearby urban pressure")
    ax.set_ylabel("Litter count")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def run_analysis(data_file=DEFAULT_DATA_FILE, output_dir=DEFAULT_OUTPUT_DIR):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(data_file)
    cleaned, missingness = clean_observations(raw)
    summary = group_summary(cleaned)
    tests = kruskal_tests(cleaned)

    cleaned.to_csv(output_dir / "cleaned_observations.csv", index=False)
    missingness.to_csv(output_dir / "missingness_report.csv", index=False)
    summary.to_csv(output_dir / "pressure_summary.csv")
    tests.to_csv(output_dir / "kruskal_wallis_results.csv", index=False)
    plot_litter_with_ci(summary, output_dir / "litter_by_pressure_ci.png")

    algae = summary[["algae_known_n", "algae_missing_n", "algae_presence_pct"]]
    algae.to_csv(output_dir / "algae_rate_by_pressure.csv")
    return {"cleaned": cleaned, "missingness": missingness, "summary": summary, "tests": tests}


def main():
    parser = argparse.ArgumentParser(description="Reproducible ecological observation analysis")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_FILE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    results = run_analysis(args.data, args.output_dir)
    print("Ecological observation analysis")
    print("=" * 34)
    print(results["summary"].to_string())
    print("\nKruskal-Wallis tests:\n", results["tests"].to_string(index=False))
    print("\nMissing values are reported explicitly and excluded per metric, not silently recoded.")
    print(f"Outputs saved to: {args.output_dir}")
    if Path(args.data).resolve() == DEFAULT_DATA_FILE.resolve():
        print("NOTE: bundled observations are illustrative reconstructed portfolio data, not verified field measurements.")


if __name__ == "__main__":
    main()
