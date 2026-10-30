import statistics
def analyze(current, history):
    if current is None:
        return {"status": "unknown", "n": len(history)}
    if len(history) < 5:
        return {"status": "INSUFFICIENT PRICE HISTORY", "n": len(history),
                "note": "Limited data; no historical low is claimed."}
    pct = sum(1 for h in history if h <= current) / len(history)
    status = "BUY NOW" if pct <= 0.15 else "GOOD PRICE" if pct <= 0.4 else \
             "PRICE IS NORMAL" if pct <= 0.75 else "WAIT FOR A BETTER DEAL"
    return {"status": status, "n": len(history), "percentile": round(pct, 2),
            "observed_low": min(history), "observed_high": max(history),
            "median": statistics.median(history)}
def timing_rating(a):
    return None if "percentile" not in a else round(1 - a["percentile"], 2)
