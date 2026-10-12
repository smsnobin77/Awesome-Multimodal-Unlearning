"""Fetch abstracts: arXiv by id, arXiv by title, then Semantic Scholar, then OpenAlex. Results are cached."""

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UA = {"User-Agent": "awesome-multimodal-unlearning builder"}
MAX_WAIT = 600


class SourceExhausted(Exception):
    pass


def fetch(url: str, as_json: bool = True, max_attempts: int = 8):
    attempt = 0
    while True:
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                body = r.read()
            return json.loads(body) if as_json else body.decode()
        except urllib.error.HTTPError as e:
            if e.code in (400, 403, 404):
                return None
            if e.code not in (429, 500, 502, 503, 504):
                raise
            retry = int(e.headers.get("Retry-After") or 0)
            if retry > MAX_WAIT:
                raise SourceExhausted(f"{url.split('/')[2]} asks to wait {retry}s")
            wait = retry or min(120, 5 * 2 ** min(attempt, 5))
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            wait = min(120, 5 * 2 ** min(attempt, 5))
        attempt += 1
        if attempt >= max_attempts:
            return None
        print(f"  retry {attempt} in {wait}s: {url[:90]}", flush=True)
        time.sleep(wait)


def similar(a: str, b: str) -> bool:
    x, y = (set(re.findall(r"[a-z0-9]+", s.lower())) for s in (a, b))
    return len(x & y) / max(1, len(x | y)) > 0.7


def openalex_text(inverted: dict[str, list[int]]) -> str:
    return " ".join(w for _, w in sorted((pos, w) for w, ps in inverted.items() for pos in ps))


def _arxiv_entries(xml: str) -> list[tuple[str, str, str]]:
    out = []
    for entry in re.findall(r"<entry>(.*?)</entry>", xml or "", re.S):
        aid = re.search(r"<id>https?://arxiv.org/abs/([^<v]+)", entry)
        title = re.search(r"<title>(.*?)</title>", entry, re.S)
        summ = re.search(r"<summary>(.*?)</summary>", entry, re.S)
        if aid and title and summ:
            out.append((aid.group(1), re.sub(r"\s+", " ", title.group(1)), re.sub(r"\s+", " ", summ.group(1)).strip()))
    return out


def fetch_abstracts(items: dict[str, dict], cache_file: Path, skip: bool = False) -> dict[str, dict]:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache = json.loads(cache_file.read_text()) if cache_file.exists() else {}
    if skip:
        return cache
    need = lambda: [k for k in items if not (cache.get(k) or {}).get("abstract")]
    save = lambda: cache_file.write_text(json.dumps(cache, indent=1, ensure_ascii=False))

    by_arxiv = {items[k]["arxiv"]: k for k in need() if items[k]["arxiv"]}
    ids = list(by_arxiv)
    for i in range(0, len(ids), 50):
        chunk = ids[i : i + 50]
        xml = fetch(f"http://export.arxiv.org/api/query?id_list={','.join(chunk)}&max_results={len(chunk)}", as_json=False)
        for aid, _, summ in _arxiv_entries(xml):
            if aid in by_arxiv:
                cache[by_arxiv[aid]] = {"abstract": summ, "arxiv": aid}
        save()
        time.sleep(3)

    for k in need():
        q = urllib.parse.quote('ti:"' + " ".join(re.findall(r"[A-Za-z0-9]+", items[k]["title"])) + '"')
        for aid, title, summ in _arxiv_entries(fetch(f"http://export.arxiv.org/api/query?search_query={q}&max_results=3", as_json=False)):
            if similar(title, items[k]["title"]):
                cache[k] = {"abstract": summ, "arxiv": aid}
                save()
                break
        time.sleep(3)

    for k in need():
        q = urllib.parse.quote(re.sub(r"[^\w\s-]", " ", items[k]["title"]))
        try:
            res = fetch(f"https://api.openalex.org/works?search={q}&per-page=3") or {}
        except SourceExhausted as e:
            print(f"  skipping OpenAlex: {e}", flush=True)
            break
        hit = next((w for w in res.get("results", []) if similar(w.get("title") or "", items[k]["title"])
                    and w.get("abstract_inverted_index")), None)
        if hit:
            cache[k] = {"abstract": openalex_text(hit["abstract_inverted_index"]), "arxiv": None}
            save()
    for k in need():
        try:
            r = fetch("https://api.semanticscholar.org/graph/v1/paper/search/match?query="
                      f"{urllib.parse.quote(items[k]['title'])}&fields=title,abstract,externalIds", max_attempts=2)
        except SourceExhausted as e:
            print(f"  skipping Semantic Scholar: {e}", flush=True)
            break
        hit = ((r or {}).get("data") or [None])[0]
        if hit and hit.get("abstract") and similar(hit.get("title", ""), items[k]["title"]):
            cache[k] = {"abstract": hit["abstract"], "arxiv": (hit.get("externalIds") or {}).get("ArXiv")}
            save()
        time.sleep(2)

    save()
    return cache
