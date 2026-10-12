"""Validate papers.yaml and survey.yaml, then regenerate the README list and docs/explorer/data.js.

    uv run scripts/build.py          # rewrite the generated files
    uv run scripts/build.py --check  # exit 1 if they are out of date (CI)
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REPO = "smsnobin77/Awesome-Multimodal-Unlearning"
EXPLORER_URL = "https://smsnobin77.github.io/Awesome-Multimodal-Unlearning/explorer/"
START, END = "<!-- papers:start -->", "<!-- papers:end -->"
KINDS = {"method", "benchmark", "attack", "analysis", "survey"}
TAG_GROUPS = {"target", "metric", "dataset", "application", "challenge"}
MODEL_LABEL = {"vlm": "VLM", "clip": "CLIP", "image-diffusion": "Diffusion", "video": "Video", "audio": "Audio"}
ARXIV_BADGE = "https://img.shields.io/badge/arXiv-B31B1B?style=flat-square&logo=arxiv&logoColor=white"
PAPER_BADGE = "https://img.shields.io/badge/paper-555555?style=flat-square&logo=readthedocs&logoColor=white"
EMBEDDINGS = ROOT / "docs" / "explorer" / "embeddings.json"


def load() -> tuple[list[dict], dict]:
    return yaml.safe_load((ROOT / "papers.yaml").read_text()), yaml.safe_load((ROOT / "survey.yaml").read_text())


def _ids(survey: dict) -> dict[str, set[str]]:
    p = survey["planner"]
    return {
        "stage": {s["id"] for s in survey["stages"]}, "family": {f["id"] for f in survey["families"]},
        "target": {t["id"] for t in p["targets"]}, "model": {m["id"] for m in p["models"]},
        "metric": {m["id"] for d in survey["dimensions"] for m in d["metrics"]},
        "dataset": {d["id"] for d in survey["datasets"]}, "application": {a["id"] for a in survey["applications"]},
        "challenge": {c["id"] for c in survey["challenges"]},
    }


def validate(papers: list[dict], survey: dict) -> list[str]:
    ids, errors, seen = _ids(survey), [], set()
    family_stage = {f["id"]: f["stage"] for f in survey["families"]}
    for i, p in enumerate(papers):
        where = p.get("key") or f"entry {i + 1}"
        for field in ("key", "title", "year", "kind", "links"):
            if not p.get(field):
                errors.append(f"{where}: missing '{field}'")
        if p.get("key") in seen:
            errors.append(f"{where}: duplicate key")
        seen.add(p.get("key"))
        if p.get("kind") not in KINDS:
            errors.append(f"{where}: kind must be one of {sorted(KINDS)}")
        if not isinstance(p.get("year"), int):
            errors.append(f"{where}: year must be a number")
        for flag in ("in_survey", "peer_reviewed"):
            if not isinstance(p.get(flag), bool):
                errors.append(f"{where}: {flag} must be true or false")
        for name, url in (p.get("links") or {}).items():
            if name == "doi":
                continue
            if not str(url).startswith("https://"):
                errors.append(f"{where}: link '{name}' must start with https://")
            elif "img.shields.io" in url:
                errors.append(f"{where}: link '{name}' points to a badge image, not the paper")
        if p.get("stage") is not None and p["stage"] not in ids["stage"]:
            errors.append(f"{where}: unknown stage '{p['stage']}'")
        fam = p.get("family")
        if p.get("kind") == "method" and p.get("in_survey") and not fam:
            errors.append(f"{where}: a method from the survey needs a 'family'")
        if fam is not None and fam not in ids["family"]:
            errors.append(f"{where}: unknown family '{fam}'")
        elif fam and p.get("stage") != family_stage[fam]:
            errors.append(f"{where}: stage must be '{family_stage[fam]}' for family '{fam}'")
        for group_name, groups, allowed in (("tags", p.get("tags") or {}, TAG_GROUPS), ("added", p.get("added") or {}, {"model", "target"})):
            for group, values in groups.items():
                if group not in allowed:
                    errors.append(f"{where}: unknown {group_name} group '{group}'")
                    continue
                for v in values:
                    if v not in ids[group]:
                        errors.append(f"{where}: unknown {group} '{v}' in {group_name}")
    known = seen | {d["key"] for d in survey["datasets"]} | set(survey.get("background", []))
    refs = [m["key"] for f in survey["families"] for m in f["methods"]] + [k for f in survey["families"] for k in f["keys"]]
    refs += [b["key"] for b in survey["benchmarks"]] + [k for d in survey["datasets"] for k in d["used_in"]]
    refs += [k for d in survey["dimensions"] for m in d["metrics"] for k in m["keys"]]
    refs += [k for group in ("applications", "challenges", "attacks") for item in survey[group] for k in item["keys"]]
    errors += [f"survey.yaml refers to unknown key '{k}'" for k in dict.fromkeys(refs) if k not in known]
    return errors


def passage(p: dict) -> str:
    return f"{p['title']}. {p.get('abstract') or ''}".strip()


def content_hash(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:12]


def embedding_warnings(papers: list[dict], path: Path = EMBEDDINGS) -> list[str]:
    if not path.exists():
        return [f"{path.name} is missing. Run: uv run --group embed scripts/embed.py"]
    data = json.loads(path.read_text())
    have = dict(zip(data["keys"], data["hashes"]))
    stale = [p["key"] for p in papers if have.get(p["key"]) != content_hash(passage(p))]
    return [f"{len(stale)} papers have no current embedding (keyword search still works). "
            f"Run: uv run --group embed scripts/embed.py"] if stale else []


def _anchor(text: str) -> str:
    return re.sub(r"[^a-z0-9 -]", "", text.lower()).strip().replace(" ", "-")


def _row(p: dict) -> str:
    date = (p.get("date") or str(p["year"])).replace("-", "&#8209;")
    name = p.get("name")
    title = p["title"].replace("|", "\\|")
    lead = f"**{name}**: " if name and not title.lower().startswith(name.lower()) else ""
    models = ", ".join(MODEL_LABEL[m] for m in (p.get("added") or {}).get("model", []))
    links = p.get("links") or {}
    badge = f"[![arXiv]({ARXIV_BADGE})]({links['arxiv']})" if links.get("arxiv") else f"[![paper]({PAPER_BADGE})]({links.get('paper', '')})"
    return f"| {date} | {lead}{title} | {models} | {badge} |"


def _table(items: list[dict]) -> list[str]:
    items = sorted(items, key=lambda p: (p.get("date") or str(p["year"]), p["title"].lower()), reverse=True)
    return ["| Date | Title | Model | Paper |", "|------|-------|-------|-------|", *map(_row, items), ""]


def render_list(papers: list[dict], survey: dict) -> str:
    groups = []
    for stage in survey["stages"]:
        fams = [(f, [p for p in papers if p.get("family") == f["id"]]) for f in survey["families"] if f["stage"] == stage["id"]]
        if any(items for _, items in fams):
            groups.append((stage["name"], fams))
    extra = [("Benchmarks", [p for p in papers if p["kind"] == "benchmark"]),
             ("Attacks", [p for p in papers if p["kind"] == "attack"]),
             ("Other work discussed in the survey", [p for p in papers if p["kind"] == "analysis"]),
             ("Surveys", [p for p in papers if p["kind"] == "survey"]),
             ("Not yet placed", [p for p in papers if p["kind"] == "method" and not p.get("family")])]
    extra = [(name, items) for name, items in extra if items]
    out = [f"We list **{len(papers)} papers**, grouped by where they act in the model pipeline (Section 3 of the survey). "
           f"Search, filter, and export them in the [interactive explorer]({EXPLORER_URL}).", ""]
    for name, fams in groups:
        out.append(f"- [{name}](#{_anchor(name)}) ({sum(len(items) for _, items in fams)})")
    out += [f"- [{name}](#{_anchor(name)}) ({len(items)})" for name, items in extra] + [""]
    for name, fams in groups:
        out.append(f"### {name}\n")
        for fam, items in fams:
            if items:
                out += [f"#### {fam['name']}\n", *_table(items)]
    for name, items in extra:
        out += [f"### {name}\n", *_table(items)]
    return "\n".join(out).rstrip() + "\n"


def render_data(papers: list[dict], survey: dict) -> str:
    payload = {"repo": REPO, "explorer": EXPLORER_URL, "survey": survey, "papers": papers}
    return "window.MMU_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n"


def splice(readme: str, body: str) -> str:
    if START not in readme or END not in readme:
        raise SystemExit(f"README.md needs the markers {START} and {END}")
    head, rest = readme.split(START, 1)
    _, tail = rest.split(END, 1)
    return f"{head}{START}\n{body}{END}{tail}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    papers, survey = load()
    if errors := validate(papers, survey):
        print("papers.yaml or survey.yaml has problems:\n  " + "\n  ".join(errors))
        sys.exit(1)
    for w in embedding_warnings(papers):
        print(f"warning: {w}")
    readme_path, data_path = ROOT / "README.md", ROOT / "docs" / "explorer" / "data.js"
    readme, data = splice(readme_path.read_text(), render_list(papers, survey)), render_data(papers, survey)
    if args.check:
        stale = [str(p.relative_to(ROOT)) for p, new in ((readme_path, readme), (data_path, data))
                 if not p.exists() or p.read_text() != new]
        if stale:
            print("Out of date: " + ", ".join(stale) + ". Run: uv run scripts/build.py")
            sys.exit(1)
        print(f"ok: {len(papers)} papers")
        return
    data_path.parent.mkdir(parents=True, exist_ok=True)
    readme_path.write_text(readme)
    data_path.write_text(data)
    print(f"wrote README.md and docs/explorer/data.js ({len(papers)} papers)")


if __name__ == "__main__":
    main()
