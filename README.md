Analytico
=========

A RESTful Flask API that runs ad‑hoc data analytics jobs and serves interactive dashboards. It integrates with Jupyter notebooks for execution and supports popular Python data tools (Pandas, Plotly, Bokeh, etc.).

## What this solution does
- Exposes a FastAPI backend with a mounted Dash UI for interactive, in-browser exploration.
- Lets users upload CSV/XLSX files and immediately see:
  - Rendered data table with paging.
  - Missing-value bar chart and outlier box plots for numeric columns.
  - Summary statistics table plus `DataFrame.info()` details.
- Generates downloadable Excel workbooks containing:
  - Raw data sheet with auto-sized columns.
  - Descriptive statistics sheet.
  - Missing-values chart sheet (auto handles no-missing-data case).
- Provides a `/csv_to_excel_with_description/` API endpoint that accepts a CSV upload and returns the enriched Excel file.
- Keeps layout components styled via Bootstrap and basic card styling for readability.

## Project structure
- `Preprocessing-api/`: Flask service entrypoints and job orchestration
- `notebooks/`: example analysis notebooks executed by the API
- `data/`: sample datasets (gitignored in production)

## Getting started
1) Install dependencies (Python 3.10+):
```
pip install -r requirements.txt
```
2) Run the API (from `Preprocessing-api/`):
```
flask --app app.py run
```
3) Send a test request:
```
curl -X POST http://localhost:5000/process -H "Content-Type: application/json" -d "{\"notebook\":\"example.ipynb\"}"
```

## Development notes
- Configure env vars in `.env` (e.g., `NOTEBOOK_DIR`, `DATA_DIR`).
- Keep notebooks idempotent; output is captured and returned by the API.
- For plotting, prefer lightweight figures (Plotly/Bokeh) to keep responses fast.

## Testing
Run unit tests from repo root:
```
pytest
```