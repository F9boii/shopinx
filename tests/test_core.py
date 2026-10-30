import pytest
from backend.scoring import tier_for, score_product
from backend.security import check_url, UnsafeURL
from backend.price_analyzer import analyze
from backend.product_extractor import extract

@pytest.mark.parametrize("s,t",[(39,"F"),(40,"D"),(59,"D"),(60,"C"),(69,"C"),(70,"B"),(79,"B"),(80,"A"),(89,"A"),(90,"S"),(100,"S")])
def test_tiers(s,t): assert tier_for(s)==t

def test_missing_data_not_rewarded():
    full=score_product({k:1.0 for k in ["quality","value","reviews","timing","features","support","seller"]})
    part=score_product({"reviews":1.0})
    assert full["overall_score"]==100 and part["overall_score"]<full["overall_score"]
    assert part["verdict"]=="INSUFFICIENT EVIDENCE"
    assert score_product({})["overall_score"] is None

def test_safety_override():
    assert score_product({k:1.0 for k in ["quality","value","reviews"]},safety_critical=True)["tier"]=="F"

@pytest.mark.parametrize("u",["http://127.0.0.1/","http://localhost/","http://169.254.169.254/latest","http://10.0.0.1/","file:///etc/passwd","ftp://x.com"])
def test_ssrf_blocked(u):
    with pytest.raises(UnsafeURL): check_url(u)

def test_no_false_low():
    r=analyze(10.0,[10.0,12.0])
    assert r["status"]=="INSUFFICIENT PRICE HISTORY" and "observed_low" not in r

def test_extract_jsonld_and_missing():
    h='<script type="application/ld+json">{"@type":"Product","name":"X","offers":{"price":"9.5","priceCurrency":"EUR"}}</script>'
    p=extract(h,"https://a.com/x"); assert p["name"]=="X" and p["price"]==9.5 and p["currency"]=="EUR"
    assert extract("<html></html>","u")["name"] is None
