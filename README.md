# Smart Financial Planner

An agentic, LLM‑powered financial planning app that researches assets, evaluates risk/return tradeoffs, and generates rich reports. The repository follows Ready Tensor’s professional‑grade structure and documentation standards to make the project easy to run, test, and extend.

---

## Features

- Multi‑agent pipeline (research → analysis → report)
- Clean, professional repo layout (README, LICENSE, SECURITY, CONTRIBUTING, CHANGELOG)
- Tests: unit/integration, smoke, load (benchmarks), and evaluation criteria checks
- CI: GitHub Actions to run tests on PRs
- Config via `.env` (no secrets in code) using `python-dotenv`

---

## Project Layout

```
app/            # Core package: agents, graph, services, UI entrypoints
datasets/       # Sample inputs
prompts/        # LLM prompt templates
outputs/        # Generated reports, charts, metrics (gitignored)
tests/          # unit/, smoke/, load/, eval/
docs/           # Developer & user docs
.github/        # CI workflows
```

---

## Quickstart

### 1) Set up Python & deps
```bash
python -m venv .venv
# mac/linux
source .venv/bin/activate
# windows (powershell)
.venv\Scripts\Activate.ps1

pip install -r requirements.txt -r requirements-dev.txt
```

### 2) Configure environment
Create a `.env` in the repo root (or copy `.env.example`) and set at minimum:
```
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-4o-mini
```
The app reads key‑value pairs from `.env` at runtime via `python-dotenv`.

---

## Running the Application (Dev)

Use the Flask CLI to start the dev server:

```bash
flask --app app.main run --port 5011 --debug
```

Open http://localhost:5011/ to use the UI.

> Tip: For quick experiments you can also run `python app/main.py`, but `flask run` is recommended for development.

---

## Production (WSGI)

For production, use a WSGI server instead of the dev server, e.g. Gunicorn:

```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:5011 'app.main:app'
```

---

## Testing

This repo includes smoke, load, and evaluation tests in addition to unit tests.

### Run everything
```bash
pytest
```

### Smoke tests (sanity)
```bash
pytest tests/smoke -q
```

### Load tests / benchmarks
```bash
pytest tests/load -q
# (optional) save JSON results
pytest tests/load --benchmark-save=latest
```

### Evaluation criteria
```bash
pytest tests/eval -q
```
These tests assert presence/shape of key metrics (e.g., CAGR, Sharpe, drawdown, win‑rate) produced by the pipeline.

---

## Configuration & Secrets

- All runtime configuration lives in `.env` (never commit real secrets). `python-dotenv` loads these into environment variables at startup.
- Common settings:
  - `OPENAI_API_KEY` – LLM provider key
  - `MODEL_NAME` – model identifier
  - Optional feature flags as needed by your agents

---

## Outputs

Generated artifacts (HTML/PDF reports, PNG charts, JSON metrics) are written to `outputs/` (gitignored). The UI links directly to the latest run’s files.

---

## CI

GitHub Actions workflow `.github/workflows/ci.yml` installs dependencies and executes the test suite on pushes and pull requests.

---

## Contributing

See `CONTRIBUTING.md` for guidelines (branching, tests, conventional commits). Be respectful and collaborative per `CODE_OF_CONDUCT.md`.

---

## Security

If you discover a vulnerability, please disclose responsibly as described in `SECURITY.md`.

---

## License

This project is licensed under the MIT License (see `LICENSE`).

---

## References

- Ready Tensor publication & repo guidelines.
- Flask CLI & Quickstart; production deployment guidance (Gunicorn).
- `python-dotenv` docs.
- `pytest` docs & `pytest-benchmark` docs.
