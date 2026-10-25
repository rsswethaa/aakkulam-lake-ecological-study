"""Reproducibly download and profile the official LAWA lake-quality workbook.

The downloader intentionally does not invent a mapping from LAWA's national schema
into the local Aakkulam portfolio schema. It records workbook sheets, columns,
row counts and a SHA-256 checksum so downstream analysis can be adapted against the
actual source structure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
import requests

LAWA_LAKE_URL = (
    "https://www.lawa.org.nz/media/1eygt2eh/"
    "lawa-lake-quality-dataset__16dec2025.xlsx"
)
DEFAULT_DESTINATION = Path(__file__).resolve().parent / "data" / "external" / "lawa_lake_quality_2004_2024.xlsx"
DEFAULT_MANIFEST = Path(__file__).resolve().parent / "data" / "external" / "lawa_lake_quality_manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_lawa_workbook(destination: Path = DEFAULT_DESTINATION, timeout: int = 60) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(
        LAWA_LAKE_URL,
        timeout=timeout,
        headers={"User-Agent": "rsswethaa-portfolio-research/1.0"},
    )
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    if "spreadsheet" not in content_type and not destination.suffix.lower().endswith("xlsx"):
        raise ValueError(f"unexpected LAWA response content type: {content_type}")
    destination.write_bytes(response.content)
    return destination


def profile_workbook(workbook: Path) -> dict:
    workbook = Path(workbook)
    excel = pd.ExcelFile(workbook)
    sheets = []
    for sheet_name in excel.sheet_names:
        frame = pd.read_excel(workbook, sheet_name=sheet_name)
        sheets.append(
            {
                "sheet": sheet_name,
                "rows": int(len(frame)),
                "columns": [str(column) for column in frame.columns],
            }
        )
    return {
        "source": "Land Air Water Aotearoa (LAWA)",
        "source_url": LAWA_LAKE_URL,
        "dataset": "Lake water quality dataset (2004-2024)",
        "published": "2025-12-16",
        "sha256": sha256_file(workbook),
        "sheets": sheets,
        "licensing_note": (
            "Check the workbook metadata and LAWA terms before redistribution. "
            "LAWA asks users to acknowledge LAWA and relevant partner agencies."
        ),
    }


def write_manifest(workbook: Path, manifest_path: Path = DEFAULT_MANIFEST) -> dict:
    manifest = profile_workbook(workbook)
    manifest_path = Path(manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Download/profile official LAWA lake-quality data")
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--profile-only", action="store_true")
    args = parser.parse_args()

    workbook = args.destination
    if not args.profile_only:
        workbook = download_lawa_workbook(workbook)
    if not workbook.exists():
        raise FileNotFoundError(workbook)
    manifest = write_manifest(workbook, args.manifest)
    print(f"LAWA workbook: {workbook}")
    print(f"SHA-256: {manifest['sha256']}")
    for sheet in manifest["sheets"]:
        print(f"{sheet['sheet']}: {sheet['rows']} rows, {len(sheet['columns'])} columns")


if __name__ == "__main__":
    main()
