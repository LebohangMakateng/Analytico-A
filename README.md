Analytico
=========

A FastAPI application with an integrated Dash UI for interactive data analytics. Upload CSV or Excel files to explore your data with visualizations and download enriched Excel reports.

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
- Uses Bootstrap styling via dash-bootstrap-components for a clean UI.

## Project structure
- `Preprocessing-api/` - FastAPI + Dash application
  - `process.py` - Main application entry point
  - `processManager.py` - Data processing utilities and chart generation
  - `requirements.txt` - Python dependencies

## Getting started
1) Install dependencies (Python 3.10+):
```
pip install -r Preprocessing-api/requirements.txt
```
2) Run the API (from `Preprocessing-api/`):
```
uvicorn process:app --reload
```
3) Open the Dash UI in your browser:
```
http://localhost:8000/dash/
```
4) Or use the API endpoint directly:
```
curl -X POST http://localhost:8000/csv_to_excel_with_description/ -F "file=@yourfile.csv"
```

## API Endpoints
- `GET /` - Welcome message
- `GET /dash/` - Interactive Dash UI for file upload and exploration
- `POST /csv_to_excel_with_description/` - Upload a CSV and receive an enriched Excel file