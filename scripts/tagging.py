"""Sort cited keys into kinds, propose keyword tags for review, and match the old README list."""

import re

from latex import plain

MODEL_IDS = ["vlm", "clip", "image-diffusion", "video", "audio"]
TARGET_IDS = ["identity", "voice", "style", "nsfw", "class", "knowledge", "backdoor", "preference"]
MODEL_WORDS = [
    ("audio", r"\b(speech|speaker|voice|audio|music|asr|tts|spoken)"),
    ("video", r"\b(video|motion)"),
    ("clip", r"\bclip\b|contrastive"),
    ("image-diffusion", r"diffusion|text-to-image|\bt2i\b|\bgans?\b|image generation"),
    ("vlm", r"multimodal large language|\bmllms?\b|\blvlms?\b|vision[- ]language model|\bvqa\b|llava|multimodal llm"),
]
TARGET_WORDS = [
    ("identity", r"identit|\bfaces?\b|facial|celebrit|portrait"),
    ("voice", r"speaker|\bvoices?\b"),
    ("style", r"\bstyles?\b|artist|artwork|copyright"),
    ("nsfw", r"nsfw|nudity|\bnude|harmful|unsafe|toxic|inappropriate|jailbreak"),
    ("class", r"\bclass(es)?[- ](unlearning|forgetting|removal|erasure)|(forget|remov|unlearn)\w* (an? |the |entire |specific |target )?class(es)?\b"),
    ("knowledge", r"knowledge|question answering|\bvqa\b|private information|sensitive information"),
    ("backdoor", r"backdoor|poison|trigger"),
    ("preference", r"recommend"),
]
UNLEARNING_WORDS = re.compile(r"unlearn|forget|eras|remov|delet|backdoor|poison|jailbreak|safe|privacy|private|protect|"
                              r"cloak|concept|attack|memoriz|attribution|steer|guidance|copyright|nsfw|harm|bias|moderat")
KIND_OVERRIDES: dict[str, str] = {}


def classify(key: str, title: str, *, methods, benchmarks, surveys, attacks, datasets) -> str:
    if key in KIND_OVERRIDES:
        return KIND_OVERRIDES[key]
    for kind, keys in (("method", methods), ("benchmark", benchmarks), ("survey", surveys), ("attack", attacks),
                       ("dataset", datasets)):
        if key in keys:
            return kind
    return "analysis" if UNLEARNING_WORDS.search(title.lower()) else "background"


def keyword_tags(rules: list[tuple[str, str]], *texts: str | None) -> list[str]:
    for text in texts:
        low = (text or "").lower()
        if found := [tag for tag, pattern in rules if re.search(pattern, low)]:
            return found
    return []


def arxiv_id(fields: dict) -> str | None:
    for name in ("eprint", "journal", "url", "doi"):
        if m := re.search(r"(\d{4}\.\d{4,5})", fields.get(name, "") or ""):
            if name == "eprint" or "arxiv" in fields.get(name, "").lower():
                return m.group(1)
    return None


def readme_rows(readme: str) -> list[dict]:
    rows, section = [], None
    for line in readme.split("\n"):
        if line.startswith("### "):
            section = {"### Vision-Language Models (VLMs)": "vlm", "### Diffusion Models (DMs)": "dm"}.get(line.strip())
        elif section and (m := re.match(r"^\| (\d{4})&#8209;(\d\d) \| (.+?) \| .*?\]\((http[^)]+)\)", line)):
            url = m.group(4)
            aid = re.search(r"arxiv\.org/(?:pdf|abs)/(\d{4}\.\d{4,5})", url)
            rows.append({"date": f"{m.group(1)}-{m.group(2)}", "title": m.group(3).strip(), "url": url,
                         "arxiv": aid.group(1) if aid else None, "section": section})
    return rows


def _tokens(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", plain(s).lower()))


def match_rows(rows: list[dict], titles: dict[str, str], arxiv_ids: dict[str, str | None]):
    by_arxiv = {a: k for k, a in arxiv_ids.items() if a}
    tok = {k: _tokens(t) for k, t in titles.items()}
    matched, unmatched = {}, []
    for row in rows:
        key = by_arxiv.get(row["arxiv"])
        if not key:
            r = _tokens(row["title"])
            best = max(tok, key=lambda k: len(r & tok[k]) / max(1, len(r | tok[k])), default=None)
            if best and len(r & tok[best]) / max(1, len(r | tok[best])) >= 0.6:
                key = best
        if key and key not in matched:
            matched[key] = row
        elif not key:
            unmatched.append(row)
    return matched, unmatched
