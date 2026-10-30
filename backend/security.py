import ipaddress, socket
from urllib.parse import urlparse, urljoin
import httpx

class UnsafeURL(ValueError):
    pass

def check_url(url: str) -> str:
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        raise UnsafeURL("Only http(s) URLs with a host are allowed")
    try:
        infos = socket.getaddrinfo(p.hostname, p.port or (443 if p.scheme == "https" else 80))
    except socket.gaierror:
        raise UnsafeURL("Host cannot be resolved")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:  # loopback, private, link-local, reserved, metadata
            raise UnsafeURL(f"Blocked non-public address {ip}")
    return url

def safe_get(url: str, max_bytes=2_000_000, max_redirects=4, timeout=8.0) -> tuple[str, str]:
    """Fetch HTML with SSRF checks on every redirect hop, size and type limits."""
    with httpx.Client(follow_redirects=False, timeout=timeout,
                      headers={"User-Agent": "ShopIntelBot/0.1"}) as c:
        for _ in range(max_redirects + 1):
            check_url(url)
            r = c.get(url)
            if r.is_redirect:
                url = urljoin(url, r.headers.get("location", ""))
                continue
            if "html" not in r.headers.get("content-type", ""):
                raise UnsafeURL("Unsupported content type")
            if len(r.content) > max_bytes:
                raise UnsafeURL("Response too large")
            return str(r.url), r.text
    raise UnsafeURL("Too many redirects")
