import json, re
LD = re.compile(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', re.S | re.I)

def _walk(node):
    if isinstance(node, list):
        for n in node: yield from _walk(n)
    elif isinstance(node, dict):
        yield node
        for v in node.get("@graph", []): yield from _walk(v)

def _first(x):
    return x[0] if isinstance(x, list) and x else x

def extract(html, url):
    out = {"name": None, "brand": None, "price": None, "currency": None, "rating": None,
           "review_count": None, "image_url": None, "product_url": url, "provenance": "json-ld"}
    for block in LD.findall(html):
        try: data = json.loads(block)
        except ValueError: continue
        for n in _walk(data):
            t = n.get("@type")
            if "Product" not in (t if isinstance(t, list) else [t]): continue
            out["name"] = n.get("name")
            b = n.get("brand"); out["brand"] = b.get("name") if isinstance(b, dict) else b
            img = _first(n.get("image")); out["image_url"] = img.get("url") if isinstance(img, dict) else img
            o = _first(n.get("offers"))
            if isinstance(o, dict):
                try: out["price"] = float(o.get("price") or o.get("lowPrice"))
                except (TypeError, ValueError): pass
                out["currency"] = o.get("priceCurrency")
            r = n.get("aggregateRating")
            if isinstance(r, dict):
                try:
                    out["rating"] = float(r.get("ratingValue"))
                    out["review_count"] = int(r.get("reviewCount") or r.get("ratingCount") or 0)
                except (TypeError, ValueError): pass
            return out
    return out  # name None => caller must ask the user, never fabricate
