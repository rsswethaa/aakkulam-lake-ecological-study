from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, render_template_string

from analysis import DEFAULT_DATA_FILE, clean_observations, group_summary, kruskal_tests

app = Flask(__name__)

PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Aakkulam Lake Ecological Study</title>
  <style>
    body{font-family:Inter,system-ui,sans-serif;margin:0;background:#f5f7f6;color:#17302b}
    main{max-width:1100px;margin:auto;padding:48px 22px}
    .hero{background:white;border-radius:20px;padding:34px;box-shadow:0 10px 30px rgba(0,0,0,.06);margin-bottom:24px}
    h1{font-size:clamp(2rem,5vw,3.5rem);margin:0 0 10px}.muted{color:#5e746e}
    .notice{padding:14px 16px;background:#fff6d8;border-radius:12px;margin:18px 0}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin:20px 0}
    .card{background:white;border-radius:16px;padding:20px;box-shadow:0 6px 20px rgba(0,0,0,.05)}
    table{width:100%;border-collapse:collapse;background:white;border-radius:14px;overflow:hidden;font-size:.92rem}
    th,td{padding:11px;border-bottom:1px solid #e5ece9;text-align:left}th{background:#eaf2ef}
    .scroll{overflow-x:auto;margin:12px 0 28px}.metric{font-size:1.7rem;font-weight:700}
  </style>
</head>
<body><main>
  <section class="hero">
    <p class="muted">Research & data-analysis portfolio project</p>
    <h1>Aakkulam Lake Ecological Study</h1>
    <p>This dashboard presents the repository's reproducible analysis of reconstructed ecological observations across low, medium and high urban-pressure groups.</p>
    <div class="notice"><strong>Data note:</strong> the bundled observations are illustrative reconstructed portfolio data, not verified environmental measurements.</div>
  </section>
  <div class="grid">
    <div class="card"><div class="muted">Observations</div><div class="metric">{{ total }}</div></div>
    <div class="card"><div class="muted">Sites</div><div class="metric">{{ sites }}</div></div>
    <div class="card"><div class="muted">Pressure groups</div><div class="metric">3</div></div>
    <div class="card"><div class="muted">Analysis method</div><div class="metric" style="font-size:1.15rem">Kruskal-Wallis + bootstrap CI</div></div>
  </div>
  <h2>Group summary</h2><div class="scroll">{{ summary|safe }}</div>
  <h2>Statistical tests</h2><div class="scroll">{{ tests|safe }}</div>
  <p class="muted">API: <code>/api/summary</code> · Health: <code>/health</code></p>
</main></body></html>
"""


def load_results():
    raw = pd.read_csv(DEFAULT_DATA_FILE)
    cleaned, _ = clean_observations(raw)
    summary = group_summary(cleaned)
    tests = kruskal_tests(cleaned)
    return cleaned, summary, tests


@app.get("/")
def index():
    cleaned, summary, tests = load_results()
    return render_template_string(
        PAGE,
        total=len(cleaned),
        sites=cleaned["site_id"].nunique(),
        summary=summary.reset_index().to_html(index=False, border=0, classes="data"),
        tests=tests.to_html(index=False, border=0, classes="data"),
    )


@app.get("/api/summary")
def api_summary():
    cleaned, summary, tests = load_results()
    return jsonify({
        "observations": len(cleaned),
        "sites": int(cleaned["site_id"].nunique()),
        "summary": summary.reset_index().to_dict(orient="records"),
        "tests": tests.to_dict(orient="records"),
        "data_note": "Illustrative reconstructed portfolio data; not verified field measurements.",
    })


@app.get("/health")
def health():
    Path(DEFAULT_DATA_FILE).stat()
    return jsonify({"status": "ok", "service": "aakkulam-lake-ecological-study"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
