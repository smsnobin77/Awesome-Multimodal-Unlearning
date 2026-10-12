"""Import the survey's papers and fixed views from its LaTeX sources. Run once by the authors:

    uv run --group import scripts/import_survey.py --paper-dir ../_paper

After this, edit papers.yaml and survey.yaml by hand. Re-running overwrites manual edits.
"""

import argparse
import re
from collections import defaultdict
from pathlib import Path

import yaml

from abstracts import fetch_abstracts
from latex import cite_keys, live, parse_bib, plain, slug
from planner_rules import (BENCHMARK_MODELS, BENCHMARK_TARGETS, CONSTRAINTS, DATASET_TARGETS, GAP_LINKS, METRIC_MODELS,
                           MODALITY_MODELS, MODELS, SETTING_TARGETS, STAGE_RULES, TARGETS)
from survey_parts import (APPLICATIONS, ATTACKS, CHALLENGES, DIRECTIONS, STAGES, parse_benchmarks, parse_datasets,
                          parse_family_text, parse_metrics, parse_named, parse_taxonomy, survey_table_keys)
from tagging import MODEL_WORDS, TARGET_WORDS, arxiv_id, classify, keyword_tags, match_rows, readme_rows

ROOT = Path(__file__).resolve().parents[1]
TITLE = "Multimodal Unlearning Across Vision, Language, Video, and Audio: Survey of Methods, Datasets, and Benchmarks"
SECTION_MODEL = {"vlm": "vlm", "dm": "image-diffusion"}
VENUES = [(r"Computer Vision and Pattern Recognition|\bCVPR", "CVPR"), (r"International Conference on Computer Vision|\bICCV", "ICCV"),
          (r"European Conference on Computer Vision|\bECCV", "ECCV"), (r"Neural Information Processing|NeurIPS", "NeurIPS"),
          (r"Learning Representations|\bICLR", "ICLR"), (r"International Conference on Machine Learning|\bICML", "ICML"),
          (r"Findings of the Association", "Findings"), (r"Annual Meeting of the Association|\bACL\b", "ACL"),
          (r"Empirical Methods|EMNLP", "EMNLP"), (r"North American Chapter|Nations of the Americas Chapter|NAACL", "NAACL"),
          (r"Security and Privacy Workshops", "IEEE S&P"), (r"AAAI", "AAAI"),
          (r"Interspeech|INTERSPEECH", "Interspeech"), (r"Acoustics, Speech and Signal Processing|ICASSP", "ICASSP"),
          (r"ACM International Conference on Multimedia|ACM MM", "ACM MM"), (r"Winter Conference on Applications|WACV", "WACV"),
          (r"Transactions on Machine Learning Research|TMLR", "TMLR"), (r"Pattern Analysis and Machine Intelligence", "TPAMI"),
          (r"Security Symposium", "USENIX Security"), (r"Symposium on Security and Privacy", "IEEE S&P"),
          (r"Computer and Communications Security", "ACM CCS"), (r"Joint Conference on Artificial Intelligence|IJCAI", "IJCAI"), (r"SIGIR", "SIGIR"), (r"\bWWW\b|Web Conference", "WWW")]


def unique(xs):
    return list(dict.fromkeys(xs))


def author_name(name: str) -> str:
    last, comma, first = name.partition(",")
    return plain(f"{first} {last}" if comma else name)


def short_venue(v: str) -> str:
    short = next((s for pat, s in VENUES if re.search(pat, v, re.I)), v)
    return f"{short} Workshop" if re.search(r"workshop", v, re.I) and short != v else short


def arxiv_date(aid: str | None) -> str | None:
    return f"20{aid[:2]}-{aid[2:4]}" if aid else None


def list_key(row: dict) -> str:
    return "list-" + slug(row["title"])[:48].strip("-")


def load_survey(sec: Path) -> dict:
    L = lambda name: live(sec / name)
    text = parse_family_text(L("3_Methods.tex"))
    families = [{**f, **text[f["id"]]} for f in parse_taxonomy(L("structure.tex"))]
    datasets = parse_datasets(L("dataset_table1.tex"), L("App_Datasets_table.tex"))
    for d in datasets:
        d["targets"] = DATASET_TARGETS.get(d["name"], SETTING_TARGETS[d["setting"]])
        d["models"] = MODALITY_MODELS[d["modality"]]
    benchmarks = parse_benchmarks(L("benchmark_table.tex"))
    for b in benchmarks:
        b["targets"], b["models"] = BENCHMARK_TARGETS[b["key"]], BENCHMARK_MODELS[b["modality"]]
    dims = parse_metrics(L("metrics_tree.tex"), L("App_Evaluation.tex"))
    for d in dims:
        for m in d["metrics"]:
            m["models"], m["why"] = (list(x) for x in METRIC_MODELS.get(m["id"], ([], [])))
    challenges = ([{**c, "type": "challenge"} for c in parse_named(L("App_Challenges.tex"), CHALLENGES)]
                  + [{**c, "type": "direction"} for c in parse_named(L("6_Conclusion.tex"), DIRECTIONS)])
    return {
        "title": TITLE,
        "stages": [{"id": sid, "name": name, "families": [f["id"] for f in families if f["stage"] == sid]} for sid, name in STAGES],
        "families": families,
        "settings": [{"name": s, "targets": t} for s, t in SETTING_TARGETS.items()],
        "datasets": datasets,
        "benchmarks": benchmarks,
        "dimensions": dims,
        "applications": parse_named(L("App_Applications.tex"), APPLICATIONS),
        "challenges": challenges,
        "attacks": parse_named(L("App_Robustness_Control.tex"), ATTACKS),
        "surveys": survey_table_keys(L("1_Introduction.tex")),
        "planner": {"targets": TARGETS, "models": MODELS, "constraints": CONSTRAINTS, "stage_rules": STAGE_RULES,
                    "gap_links": GAP_LINKS},
    }


def survey_tags(survey: dict) -> dict:
    tags = defaultdict(lambda: defaultdict(list))

    def tag(key, group, *values):
        for v in values:
            if v not in tags[key][group]:
                tags[key][group].append(v)

    for d in survey["datasets"]:
        for k in d["used_in"]:
            tag(k, "dataset", d["id"])
            tag(k, "target", *d["targets"])
    for b in survey["benchmarks"]:
        tag(b["key"], "target", *b["targets"])
    for dim in survey["dimensions"]:
        for m in dim["metrics"]:
            for k in m["keys"]:
                tag(k, "metric", m["id"])
    for group, items in (("application", survey["applications"]), ("challenge", survey["challenges"])):
        for item in items:
            for k in item["keys"]:
                tag(k, group, item["id"])
    return tags


def family_of(survey: dict) -> dict[str, str]:
    fam = {}
    for f in survey["families"]:
        for m in f["methods"]:
            fam.setdefault(m["key"], f["id"])
    for f in survey["families"]:
        for k in f["keys"]:
            fam.setdefault(k, f["id"])
    return fam


def bib_entry(key, e, kind, fam, stage, names, tags, row, ab) -> dict:
    f = e["fields"]
    title = plain(f.get("title", ""))
    venue = plain(f.get("booktitle") or f.get("journal") or "")
    preprint = not venue or bool(re.search(r"arxiv|preprint|corr", venue, re.I))
    aid = arxiv_id(f) or ab.get("arxiv") or (row or {}).get("arxiv")
    family = fam.get(key) if kind == "method" else None
    paper_tags = {g: sorted(v) for g, v in sorted(tags.get(key, {}).items()) if v}
    model = keyword_tags(MODEL_WORDS, title, ab.get("abstract")) or ([SECTION_MODEL[row["section"]]] if row else [])
    target = [t for t in keyword_tags(TARGET_WORDS, title) if t not in paper_tags.get("target", [])]
    paper = f.get("url") or (f"https://doi.org/{f['doi']}" if f.get("doi") else None)
    return {
        "key": key, "name": names.get(key), "title": title,
        "authors": [author_name(a) for a in re.split(r"\s+and\s+", f.get("author", "")) if a.strip()],
        "year": int(re.sub(r"\D", "", f.get("year", "0"))[:4] or 0), "date": (row or {}).get("date") or arxiv_date(aid),
        "venue": "arXiv" if preprint else short_venue(venue), "peer_reviewed": not preprint, "kind": kind,
        "stage": stage[family] if family else None, "family": family, "tags": paper_tags,
        "added": {g: v for g, v in {"model": model, "target": target}.items() if v}, "in_survey": True,
        "links": {k: v for k, v in {"paper": paper, "arxiv": f"https://arxiv.org/abs/{aid}" if aid else None,
                                    "doi": f.get("doi")}.items() if v},
        "abstract": ab.get("abstract"), "bibtex": e["raw"],
    }


def list_entry(row: dict, ab: dict) -> dict:
    key, title = list_key(row), row["title"]
    model = keyword_tags(MODEL_WORDS, title, ab.get("abstract")) or [SECTION_MODEL[row["section"]]]
    target = keyword_tags(TARGET_WORDS, title)
    return {
        "key": key, "name": None, "title": title, "authors": [], "year": int(row["date"][:4]), "date": row["date"],
        "venue": "arXiv" if row["arxiv"] else "", "peer_reviewed": False,
        "kind": "benchmark" if "bench" in title.lower() else "method", "stage": None, "family": None, "tags": {},
        "added": {g: v for g, v in {"model": model, "target": target}.items() if v}, "in_survey": False,
        "links": {k: v for k, v in {"paper": row["url"],
                                    "arxiv": f"https://arxiv.org/abs/{row['arxiv']}" if row["arxiv"] else None}.items() if v},
        "abstract": ab.get("abstract"),
        "bibtex": f"@misc{{{key},\n  title = {{{title}}},\n  year = {{{row['date'][:4]}}},\n  url = {{{row['url']}}}\n}}",
    }


def write_review(path: Path, kinds: dict, titles: dict, papers: list[dict], unmatched: list[dict]) -> None:
    lines = ["# Import review", "", "Confirm each decision. Fix kinds in `scripts/tagging.py` (`KIND_OVERRIDES`) and re-run the import.",
             "Fix tags by editing `papers.yaml` after the last import.", "", "## Kinds decided from the title", "",
             "| Key | Kind | Title |", "|---|---|---|"]
    placed = {"method", "benchmark", "survey", "attack", "dataset"}
    lines += [f"| {k} | {kind} | {titles[k]} |" for k, kind in kinds.items() if kind not in placed]
    lines += ["", "## Methods placed from a Methods paragraph (not in the taxonomy figure)", "", "| Key | Family | Title |", "|---|---|---|"]
    lines += [f"| {p['key']} | {p['family']} | {p['title']} |" for p in papers if p["kind"] == "method" and p["in_survey"] and not p.get("name")]
    lines += ["", "## Hand tags to check (`added`)", "", "| Key | Model | Target | Title |", "|---|---|---|---|"]
    lines += [f"| {p['key']} | {', '.join(p['added'].get('model', []))} | {', '.join(p['added'].get('target', []))} | {p['title']} |"
              for p in papers if p["added"]]
    lines += ["", "## Papers without an abstract", ""] + [f"- {p['key']}: {p['title']}" for p in papers if not p["abstract"]]
    lines += ["", "## README rows not found in the survey (added as `in_survey: false`)", ""] + [f"- {r['title']}" for r in unmatched]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def dump(path: Path, obj) -> None:
    class Dumper(yaml.SafeDumper):
        pass
    Dumper.add_representer(str, lambda d, s: d.represent_scalar("tag:yaml.org,2002:str", s, style="|" if "\n" in s else None))
    path.write_text(yaml.dump(obj, Dumper=Dumper, sort_keys=False, allow_unicode=True, width=120))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper-dir", type=Path, default=ROOT.parent / "_paper")
    ap.add_argument("--out", type=Path, default=ROOT)
    ap.add_argument("--skip-fetch", action="store_true", help="reuse cached abstracts only")
    args = ap.parse_args()
    sec = args.paper_dir / "sections"
    bib = parse_bib((args.paper_dir / "custom.bib").read_text())
    cited = unique(k for f in sorted(sec.glob("*.tex")) for k in cite_keys(live(f)))
    if missing := [k for k in cited if k not in bib]:
        raise SystemExit(f"keys missing from custom.bib: {missing}")

    survey = load_survey(sec)
    fam = family_of(survey)
    stage = {f["id"]: f["stage"] for f in survey["families"]}
    names = {m["key"]: m["name"] for f in survey["families"] for m in f["methods"]}
    names |= {b["key"]: b["name"] for b in survey["benchmarks"] if b["key"] not in names}
    reactivation = next(a["keys"] for a in survey["attacks"] if a["id"] == "reactivation")
    sets = dict(methods=set(fam), benchmarks={b["key"] for b in survey["benchmarks"]}, surveys=set(survey["surveys"]),
                attacks=set(reactivation), datasets={d["key"] for d in survey["datasets"]})
    titles = {k: plain(bib[k]["fields"].get("title", "")) for k in cited}
    kinds = {k: classify(k, titles[k], **sets) for k in cited}
    keep = [k for k in cited if kinds[k] not in ("dataset", "background")]
    survey["background"] = sorted(k for k in cited if kinds[k] == "background")

    rows = readme_rows((args.out / "README.md").read_text())
    matched, unmatched = match_rows(rows, {k: titles[k] for k in keep}, {k: arxiv_id(bib[k]["fields"]) for k in keep})
    items = {k: {"title": titles[k], "arxiv": arxiv_id(bib[k]["fields"]) or (matched.get(k) or {}).get("arxiv"),
                 "doi": bib[k]["fields"].get("doi")} for k in keep}
    items |= {list_key(r): {"title": r["title"], "arxiv": r["arxiv"], "doi": None} for r in unmatched}
    abstracts = fetch_abstracts(items, args.out / "data" / "cache" / "abstracts.json", skip=args.skip_fetch)

    tags = survey_tags(survey)
    papers = [bib_entry(k, bib[k], kinds[k], fam, stage, names, tags, matched.get(k), abstracts.get(k) or {}) for k in keep]
    papers += [list_entry(r, abstracts.get(list_key(r)) or {}) for r in unmatched]
    order = {sid: i for i, (sid, _) in enumerate(STAGES)}
    papers.sort(key=lambda p: (order.get(p["stage"], len(order)), p["family"] or "", -p["year"], p["title"].lower()))

    dump(args.out / "papers.yaml", papers)
    dump(args.out / "survey.yaml", survey)
    write_review(args.out / "data" / "import_review.md", kinds, titles, papers, unmatched)
    count = lambda kind: sum(p["kind"] == kind for p in papers)
    print(f"cited={len(cited)} papers={len(papers)} methods={count('method')} benchmarks={count('benchmark')} "
          f"analysis={count('analysis')} list_only={len(unmatched)} no_abstract={sum(not p['abstract'] for p in papers)}")


if __name__ == "__main__":
    main()
