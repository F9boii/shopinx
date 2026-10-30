"""Deterministic scoring. Missing categories are NOT given points; coverage lowers the score."""
WEIGHTS = {"quality": 25, "value": 20, "reviews": 15, "timing": 15,
           "features": 10, "support": 10, "seller": 5}
TIERS = [(90, "S"), (80, "A"), (70, "B"), (60, "C"), (40, "D"), (0, "F")]

def tier_for(score: float) -> str:
    s = int(score)
    for floor, t in TIERS:
        if s >= floor:
            return t
    return "F"

def score_product(ratings: dict, safety_critical=False, weights=WEIGHTS) -> dict:
    """ratings: category -> 0..1 or None (unknown)."""
    total = sum(weights.values())
    known = {k: v for k, v in ratings.items() if v is not None and k in weights}
    assessed = sum(weights[k] for k in known)
    coverage = assessed / total
    if not known:
        return {"overall_score": None, "tier": None, "confidence": "low",
                "evidence_coverage": 0.0, "assessed": [], "verdict": "INSUFFICIENT EVIDENCE"}
    raw = sum(weights[k] * max(0, min(1, v)) for k, v in known.items()) / assessed * 100
    score = round(raw * (0.7 + 0.3 * coverage), 1)  # documented coverage penalty
    if safety_critical:
        score = min(score, 39.0)
    conf = "high" if coverage >= 0.85 else "medium" if coverage >= 0.6 else "low"
    tier = tier_for(score)
    if coverage < 0.4:
        verdict = "INSUFFICIENT EVIDENCE"
    elif tier in ("S", "A"):
        verdict = "GOOD BUY AT THIS PRICE"
    elif tier in ("B", "C"):
        verdict = "BUY IF YOU NEED IT NOW"
    else:
        verdict = "NOT RECOMMENDED"
    return {"overall_score": score, "tier": tier, "confidence": conf,
            "evidence_coverage": round(coverage, 2), "assessed": sorted(known), "verdict": verdict}
