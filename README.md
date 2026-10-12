# iot-predictive-maint

Predictive equipment maintenance and IoT analytics dashboard (Feb 2025 – Aug 2025).

Simulated IoT sensor readings and maintenance histories go through a cleaning pipeline, feature engineering and a baseline
scikit-learn model that flags equipment likely to fail within 24 hours. Results are served through Flask endpoints and a Chart.js dashboard.

**Stack:** Python, Flask, Pandas, NumPy, scikit-learn, PostgreSQL, Chart.js, Docker

## Layout
| Path | Purpose |
|---|---|
| `app/simulate.py` | Simulated sensors (with gaps, duplicates, spikes) and maintenance history |
| `app/pipeline.py` | Cleaning (dedupe, IQR outlier removal, interpolation) and rolling-window features |
| `app/model.py` | Random forest baseline, time-ordered train/test split |
| `app/store.py` | Optional PostgreSQL persistence via `DATABASE_URL` |
| `app/__init__.py` | Flask API |
| `templates/`, `static/` | Dashboard (Chart.js) |

## Run
```bash
pip install -r requirements.txt
python wsgi.py                 # http://localhost:5000
# or with PostgreSQL:
docker compose up --build
```

## API
`GET /api/assets` · `/api/timeseries/<asset_id>?hours=168` · `/api/alerts` · `/api/maintenance` · `/api/metrics` · `/api/health`

## Test
```bash
pytest
```
