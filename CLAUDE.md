# CLAUDE.md

## What this project is

`dashboard_ai_ml_api` (a.k.a. `srd-ai-ml-api`) is a **FastAPI ML + statistics backend** for the
Suicide Risk Dashboard (SRD). It exposes HTTP endpoints that train and evaluate classification
models, make predictions, explain them with SHAP, run survey-weighted regression, compute
fairness and feature-importance statistics, and return correlation matrices — over survey
datasets (YRBS/NSDUH-style, with survey weights) pulled from S3 by `datasetId`. Trained models
and results are persisted to disk and cached in Redis.

It is one of two backends behind the SRD React frontend
(`git@github.com:mcsilver-aihub/srd-frontend.git`, at `/Users/johndixon/AI_Hub/suicide_risk_dashboard/srd-frontend`):
this **ML API** (default port 8000) and a Node **core API** (auth + datasets, port 3000). The
frontend calls this service via its axios `mlClient` (`src/services/mlService.js`) at `/classify`,
`/predict`, `/feature-importance`, `/weighted-regression`, `/fairness-metrics`, and `/correlation`.

### Endpoints (all defined directly in `app/main.py`)

| Method | Path | Purpose |
| ------ | ---- | ------- |
| GET | `/health` | Service health check. |
| GET | `/` | Root; basic service info. |
| POST | `/classify` | Train + evaluate a classifier (logistic regression, random forest, XGBoost) with cross-validation + metrics + SHAP. |
| POST | `/predict` | Predict with a previously trained/persisted model (returns probability + SHAP). |
| POST | `/weighted-regression` | Survey-weighted regression (linear/logistic/polynomial) — **delegated to the R plumber API over HTTP**. |
| POST | `/fairness-metrics` | Fairlearn `MetricFrame` fairness metrics across sensitive features (uses the stored model/predictions from `/classify`). |
| POST | `/feature-importance` | Chi-Squared feature importance for a predictor/dataset. |
| POST | `/correlation` | Correlation matrix for a dataset. |
| POST | `/clearall` | Admin: delete all saved models/results and flush Redis. |

Swagger UI is at `/docs`.

### Project rules (keep in mind on every change)

- **`app/main.py` is the live entrypoint** — all endpoints are defined there. **`app/main_new.py`
  is an unused alternate implementation; do NOT use, run, or edit it.**
- **`app/api/v1/routes/*` is an in-progress modular refactor that is NOT wired into `main.py`.**
  Changes to live behavior go in `main.py` (and the `app/services/*` it calls), not the v1 routers,
  unless you are deliberately advancing that migration.
- **Pydantic is v1 (`1.10.x`)** and **FastAPI is `0.95.1`** — use v1 model syntax and APIs that
  match those versions, not Pydantic v2 / newer FastAPI idioms.
- **Weighted regression is not Python** — it runs in the separate R plumber service; the Python
  endpoint validates/loads data and forwards over HTTP (see below).
- **Simplicity first.** Make the smallest change that fixes the root cause; no temporary patches.

## Tech stack and layout

- **Python** `>=3.10` (Docker uses `python:3.10-slim`; the local `app/venv/` is 3.13). Deps are
  managed with **pip-tools** (`requirements.in` → compiled `requirements.txt`; plus
  `requirements-dev.txt` / `requirements-ci.txt`). Not Poetry/PDM despite `pyproject.toml`.
- **Web:** FastAPI `0.95.1`, Starlette `0.26.1`, Uvicorn, **Pydantic v1** `1.10.x`.
- **ML / stats:** scikit-learn, XGBoost, LightGBM, CatBoost, imbalanced-learn, SHAP
  (explainability), Fairlearn (fairness), numpy/pandas/scipy, matplotlib/plotly.
- **R bridge:** an external **R plumber** HTTP service (no in-process R); R side uses
  `survey`, `dplyr`, `redux`, `aws.s3`.
- **Infra:** Redis (caching, shared by Python + R), boto3/S3 (dataset storage), joblib/cloudpickle
  (model persistence), Docker.

Repository layout (`app/`):

- `app/main.py` — the FastAPI app and **all live endpoints** (the driver).
- `app/services/` — business logic: `classification_service*.py`, `prediction_service.py`,
  `regression_service.py` (R-API client), `fairness_service.py`, `feature_importance_service.py`,
  `shap_service.py`, `model_service.py` (persistence), `s3_service.py` (S3 dataset fetch),
  `dataset_api_service.py` (resolves display names by `datasetId`), `system_service.py`.
- `app/core/` — `config.py` (`settings`, incl. `CORS_ORIGINS`), `constants.py`, `exceptions.py`.
- `app/models/` — Pydantic schemas (`requests.py`, `responses.py`).
- `app/config/` — `logger.py` (the shared `logger`).
- `app/utils/` — `hashing.py` (`hash_ml_request` cache keys), `encoding.py`, `serialization.py`.
- `app/exceptions/` — custom exceptions (`not_found.py`). `app/validation.py` — request validators.
- `app/api/v1/routes/` — modular router refactor (NOT wired into `main.py` yet).
- `app/survey_api.R`, `app/run_API.R` — the R plumber service. `app/start_*.sh` — run scripts.
- `app/tests/`, `tests/` — pytest suites. `Dockerfile`, `compose.yml` — containerization.

## Coding rules (condensed from the global standards)

- **Docstrings** on every function/method (what, Args, Returns, Raises, edge cases); keep short ones brief.
- **Type hints** on every signature; `Optional[T]` for nullable, avoid `Any`.
- **Single responsibility** — one job per function; split anything over ~20 lines of logic.
- **Errors: raise low, catch high.** No bare `except`, no silent failures; guard every file/network/S3/Redis call.
- **No magic numbers/strings** — name constants.
- Watch for AI-code smells: happy-path-only, missing input validation, undocumented assumptions.
- **Names describe behavior;** remove dead/commented-out code.
- Code must pass `ruff check` and `ruff format`.
- Prefer established libraries over custom implementations; document any exception.
- **Secret hygiene:** never hard-code/commit/log secrets (AWS keys, tokens); load from env; keep `.env` gitignored.
- Use a plain dash `-`, never an em dash.
- In long Markdown, put each sentence on its own line.
- Favor quality, robustness, and long-term maintainability over development cost.
- Fix lint/test failures and anything visibly broken you pass, even if unrelated.
- Do not auto-add an AI co-author to commits.

## Git repo

- Remote: `origin` → `git@github.com:mcsilver-aihub/srd-ai-ml-api.git` (default branch `main`).
- **GitHub account:** this repo (and the other `mcsilver-aihub` SRD repos) uses the NYU account
  **`jd5533-mcsilver`** — NOT the personal `dixonjohgithub` account. Use `jd5533-mcsilver` for all
  `git` / `gh` operations here (pushes, PRs, `gh` API). If `gh` can't resolve the repo or a PR,
  it is almost certainly authenticated as the wrong account — switch with
  `gh auth switch --user jd5533-mcsilver`.
- Do feature work on a branch; commit/push only when asked.
- **Branch naming.** Pick the prefix that matches the kind of work:
  - `fix/[THE-FIX-NAME]-[JIRA-ID]` for a bug fix, e.g. `fix/classify-threshold-tuning-SRD-433`.
  - `feature/[THE-FEATURE-NAME]-[JIRA-ID]` for a new feature, e.g. `feature/health-endpoints-SRD-123`.
  - `docs/[THE-DOCS-NAME]` for a documentation-only change, e.g. `docs/claude-md`.

  `[THE-FIX-NAME]` and `[THE-FEATURE-NAME]` describe the fix or the feature; `[THE-DOCS-NAME]`
  describes the document. Use short kebab-case. Fix and feature branches carry the Jira ID; docs
  branches do not, because a doc change usually has no ticket behind it.
- **Browser / Jira:** for anything in the browser for this repo (Jira on `nyu.atlassian.net`,
  Confluence, GitHub in a tab), always use the **NYU Chrome profile** (the `nyu.edu`-managed
  "School" profile), never the personal `dixonjoh@gmail.com` profile. Jira lives at
  `https://nyu.atlassian.net` and is only reachable from the NYU profile.
- `.env` is gitignored; `.env.example` holds placeholder keys only. Never commit live secrets.

### Related repositories

This service is the **AI/ML backend** for the Suicide Risk Dashboard, whose other repos live
under `/Users/johndixon/AI_Hub/suicide_risk_dashboard/`:

- **Frontend** — `srd-frontend/` — React 18 + Vite SPA
  (`git@github.com:mcsilver-aihub/srd-frontend.git`, `main`). Calls this ML API via its axios
  `mlClient` for classification, prediction, feature importance, weighted regression, fairness,
  and correlation.
- **Core API** — `srd-core-api/` — Node/Express backend for auth + datasets, port 3000
  (`git@github.com:mcsilver-aihub/srd-core-api.git`, `main`).

When changing an endpoint's request/response shape, check the frontend's
`srd-frontend/src/services/mlService.js` for how it is consumed.

## How to run

Three services: **FastAPI** (`8000`), the **R plumber API** (`8090`), and **Redis** (`6379`).
FastAPI serves the API and forwards `/weighted-regression` to the R service over HTTP
(`R_API_URL`, default `http://localhost:8090`); Redis is a cache shared by both.

Configuration comes from `.env` (see `.env.example`): AWS creds + `S3_DATASET_BUCKET`
(`mcsilver-dashboard-datasets`), `MODEL_DIR` / `RESULTS_DIR`, `LOG_FILE_PATH`, `R_API_URL`,
`REDIS_URL`, `API_HOST` / `API_PORT`.

### All-in-one (matches the Docker `CMD`)

```bash
cd app
./start_services.sh
# starts: redis-server (6379), Rscript run_API.R (plumber on 8090),
#         uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Individually (dev)

```bash
# 1. Redis (Docker) on 6379
./app/start_redis.sh

# 2. R plumber API on 8090
cd app && Rscript run_API.R        # or ./app/start_r_api.sh

# 3. FastAPI on 8000 (run from app/ so `main:app` resolves)
cd app && uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker

```bash
docker build -t srd-ai-ml-api .
docker run -p 8000:8000 -p 8090:8090 -p 6379:6379 --env-file .env srd-ai-ml-api
```

The image (`python:3.10-slim`) installs `r-base` + the R packages, Redis, and the Python deps,
then runs `app/start_services.sh`.

### Tests

```bash
pytest                       # from repo root (testpaths = ["tests"])
ruff check . && ruff format .
```
