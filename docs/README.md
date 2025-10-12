
# Smart Financial Planner — Evidence & KPI Fix

Key fixes:
1. Evidence links now show up (URLs preserved in FAISS metadata).
2. KPI robustness via web parse + yfinance fallback.

Run:
```bash
cd code
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # set OPENAI_API_KEY
export PYTHONPATH="$(pwd)"
export FLASK_APP=app.main:app
flask run --port 5011
```
