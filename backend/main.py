import sqlite3, time, hashlib, os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .security import safe_get, UnsafeURL
from .product_extractor import extract
from .scoring import score_product
from . import price_analyzer as pa

DB = os.getenv("DB_PATH", "shopintel.db")
app = FastAPI(title="ShopIntel")

def db():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS price_observations(
        pid TEXT, url TEXT, price REAL, currency TEXT, ts REAL, provenance TEXT)""")
    return c

class AnalyzeReq(BaseModel):
    url: str

@app.post("/api/analyze")
def analyze(req: AnalyzeReq):
    try:
        final_url, html = safe_get(req.url)
    except UnsafeURL as e:
        raise HTTPException(400, str(e))
    except Exception:
        raise HTTPException(502, "Page inaccessible; provide the product name manually.")
    p = extract(html, final_url)
    warnings = ["Web research and alternative discovery are not implemented yet."]
    if not p["name"]:
        return {"product": p, "verdict": {"label": "INSUFFICIENT EVIDENCE"}, "scoring": None,
                "warnings": warnings + ["No structured product data found; please enter the name."]}
    pid = hashlib.sha1(final_url.encode()).hexdigest()[:12]
    c = db()
    if p["price"] is not None:
        c.execute("INSERT INTO price_observations VALUES(?,?,?,?,?,?)",
                  (pid, final_url, p["price"], p["currency"], time.time(), "json-ld"))
        c.commit()
    hist = [r[0] for r in c.execute("SELECT price FROM price_observations WHERE pid=?", (pid,))]
    price = pa.analyze(p["price"], hist)
    reviews = None
    if p["rating"] and (p["review_count"] or 0) >= 10:
        reviews = (p["rating"] - 1) / 4
    scoring = score_product({"reviews": reviews, "timing": pa.timing_rating(price)})
    return {"product_id": pid, "product": p, "price_analysis": price, "scoring": scoring,
            "verdict": {"label": scoring["verdict"]}, "alternatives": [], "warnings": warnings,
            "sources": [{"url": final_url, "type": "retailer page", "claim": "price, rating"}]}

@app.get("/api/price-history/{pid}")
def history(pid: str):
    rows = db().execute("SELECT price,currency,ts FROM price_observations WHERE pid=? ORDER BY ts", (pid,)).fetchall()
    return [{"price": r[0], "currency": r[1], "ts": r[2]} for r in rows]

app.mount("/", StaticFiles(directory=Path(__file__).parent.parent / "frontend", html=True))
