from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "sample_observations.csv"
OUTPUT_DIR = BASE_DIR / "outputs"


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    df = pd.read_csv(DATA_FILE, parse_dates=["observation_date"])

    print("Aakkulam Lake portfolio dataset summary")
    print("=" * 42)
    print(df.describe(include="all").to_string())

    summary = (
        df.groupby("nearby_urban_pressure")
        .agg(
            observations=("site_id", "count"),
            mean_clarity=("water_clarity_score", "mean"),
            mean_litter=("litter_count", "mean"),
            mean_vegetation=("vegetation_cover_pct", "mean"),
            mean_odor=("odor_score", "mean"),
        )
        .round(2)
    )
    summary.to_csv(OUTPUT_DIR / "pressure_summary.csv")
    print("\nSummary by nearby urban pressure:\n", summary)

    pressure_order = ["low", "medium", "high"]
    plot_data = summary.reindex(pressure_order).dropna()
    ax = plot_data["mean_litter"].plot(kind="bar", legend=False)
    ax.set_title("Illustrative mean litter count by urban pressure")
    ax.set_xlabel("Nearby urban pressure")
    ax.set_ylabel("Mean litter count")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "litter_by_pressure.png", dpi=160)
    plt.close()

    algae_rate = (
        df.assign(algae_present=df["visible_algae"].str.lower().eq("yes"))
        .groupby("nearby_urban_pressure")["algae_present"]
        .mean()
        .mul(100)
        .round(1)
    )
    algae_rate.to_csv(OUTPUT_DIR / "algae_rate_by_pressure.csv", header=["algae_presence_pct"])

    print(f"\nOutputs saved to: {OUTPUT_DIR}")
    print("NOTE: Dataset is illustrative reconstructed portfolio data, not verified original field measurements.")


if __name__ == "__main__":
    main()
