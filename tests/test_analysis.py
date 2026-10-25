import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from analysis import clean_observations, group_summary, kruskal_tests, run_analysis

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
DATA = ROOT / "data" / "sample_observations.csv"


class AnalysisTestCase(unittest.TestCase):
    def test_analysis_generates_statistical_outputs(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "analysis.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("Kruskal-Wallis tests", result.stdout)
        self.assertIn("Missing values are reported explicitly", result.stdout)

        summary_path = OUTPUTS / "pressure_summary.csv"
        algae_path = OUTPUTS / "algae_rate_by_pressure.csv"
        chart_path = OUTPUTS / "litter_by_pressure_ci.png"
        tests_path = OUTPUTS / "kruskal_wallis_results.csv"
        missing_path = OUTPUTS / "missingness_report.csv"

        for path in (summary_path, algae_path, chart_path, tests_path, missing_path):
            self.assertTrue(path.exists(), path)

        summary = pd.read_csv(summary_path, index_col=0)
        self.assertAlmostEqual(float(summary.loc["high", "litter_count_mean"]), 29.667, places=3)
        self.assertAlmostEqual(float(summary.loc["low", "water_clarity_score_mean"]), 4.0, places=3)
        self.assertEqual(int(summary.loc["high", "litter_count_n"]), 3)
        self.assertIn("litter_count_ci95_low", summary.columns)
        self.assertIn("litter_count_ci95_high", summary.columns)

        tests = pd.read_csv(tests_path)
        self.assertEqual(set(tests["metric"]), {
            "water_clarity_score",
            "litter_count",
            "vegetation_cover_pct",
            "odor_score",
        })
        self.assertTrue((tests["groups_tested"] >= 2).all())
        self.assertIn("epsilon_squared", tests.columns)

    def test_missing_algae_is_not_silently_treated_as_no(self):
        frame = pd.DataFrame(
            {
                "site_id": ["A", "B", "C"],
                "nearby_urban_pressure": ["low", "low", "low"],
                "visible_algae": ["yes", "no", None],
                "water_clarity_score": [4, 3, 2],
                "litter_count": [1, 2, 3],
                "vegetation_cover_pct": [80, 70, 60],
                "odor_score": [1, 1, 2],
            }
        )
        cleaned, missingness = clean_observations(frame)
        self.assertEqual(int(cleaned["algae_present"].isna().sum()), 1)
        summary = group_summary(cleaned)
        self.assertEqual(int(summary.loc["low", "algae_known_n"]), 2)
        self.assertEqual(int(summary.loc["low", "algae_missing_n"]), 1)
        self.assertAlmostEqual(float(summary.loc["low", "algae_presence_pct"]), 50.0)
        row = missingness[missingness["column"] == "algae_present"].iloc[0]
        self.assertEqual(int(row["missing_count"]), 1)

    def test_invalid_pressure_category_is_rejected(self):
        frame = pd.read_csv(DATA)
        frame.loc[0, "nearby_urban_pressure"] = "extreme"
        with self.assertRaises(ValueError):
            clean_observations(frame)

    def test_programmatic_pipeline_supports_custom_output_directory(self):
        with tempfile.TemporaryDirectory() as tempdir:
            result = run_analysis(DATA, Path(tempdir))
            self.assertEqual(len(result["cleaned"]), 8)
            self.assertEqual(len(result["tests"]), 4)
            self.assertTrue((Path(tempdir) / "litter_by_pressure_ci.png").exists())


if __name__ == "__main__":
    unittest.main()
