import subprocess
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"


class AnalysisTestCase(unittest.TestCase):
    def test_analysis_generates_expected_outputs(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "analysis.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("Outputs saved to", result.stdout)

        summary_path = OUTPUTS / "pressure_summary.csv"
        algae_path = OUTPUTS / "algae_rate_by_pressure.csv"
        chart_path = OUTPUTS / "litter_by_pressure.png"

        self.assertTrue(summary_path.exists())
        self.assertTrue(algae_path.exists())
        self.assertTrue(chart_path.exists())

        summary = pd.read_csv(summary_path, index_col=0)
        self.assertAlmostEqual(float(summary.loc["high", "mean_litter"]), 29.67, places=2)
        self.assertAlmostEqual(float(summary.loc["low", "mean_clarity"]), 4.0, places=2)

        algae = pd.read_csv(algae_path, index_col=0)
        self.assertAlmostEqual(float(algae.loc["high", "algae_presence_pct"]), 100.0, places=1)


if __name__ == "__main__":
    unittest.main()
