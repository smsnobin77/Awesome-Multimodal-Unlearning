from pathlib import Path

import yaml

from planner_rules import MODELS, TARGETS

ROOT = Path(__file__).resolve().parents[1]


def load():
    return (yaml.safe_load((ROOT / "papers.yaml").read_text()), yaml.safe_load((ROOT / "survey.yaml").read_text()))


def test_every_figure_method_is_a_placed_method():
    papers, survey = load()
    by_key = {p["key"]: p for p in papers}
    for fam in survey["families"]:
        for m in fam["methods"]:
            p = by_key[m["key"]]
            figure_families = {f["id"] for f in survey["families"] if any(x["key"] == m["key"] for x in f["methods"])}
            assert p["kind"] == "method", m
            assert p["family"] in figure_families, m


def test_only_paper_kinds_and_valid_added_tags():
    papers, _ = load()
    assert {p["kind"] for p in papers} <= {"method", "benchmark", "attack", "analysis", "survey"}
    ok = {"model": {m["id"] for m in MODELS}, "target": {t["id"] for t in TARGETS}}
    for p in papers:
        for group, values in p["added"].items():
            assert set(values) <= ok[group], (p["key"], group, values)
