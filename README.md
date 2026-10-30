# ShopIntel (vertical slice)
Run: `pip install -r requirements.txt && uvicorn backend.main:app --reload`, open http://127.0.0.1:8000
Test: `pytest`. API docs: /docs. No keys or paid services used.
Implemented: SSRF-safe fetch, JSON-LD extraction, deterministic scoring with coverage penalty, tiers, price history + percentile timing, SQLite, frontend.
NOT implemented yet: search providers/research, review analysis, alternative discovery, FX, tier-list builder, watchlists, Docker.
