import copy
import json
import re
import subprocess
import sys
from pathlib import Path

import build

ROOT = Path(__file__).resolve().parents[1]


def test_repo_data_is_valid():
    assert build.validate(*build.load()) == []


def test_validate_reports_readable_errors():
    papers, survey = build.load()
    bad = copy.deepcopy(papers)
    method = next(p for p in bad if p["kind"] == "method" and p["in_survey"])
    method["family"] = "no-such-family"
    bad[1]["added"] = {"model": ["vlmm"]}
    bad.append(copy.deepcopy(bad[0]))
    errors = build.validate(bad, survey)
    assert any(method["key"] in e and "family" in e for e in errors)
    assert any("vlmm" in e for e in errors)
    assert any("duplicate key" in e for e in errors)


def test_survey_counts_match_the_paper():
    _, s = build.load()
    assert len(s["stages"]) == 5 and len(s["families"]) == 12
    assert sum(len(f["methods"]) for f in s["families"]) == 44
    assert len(s["datasets"]) == 56 and len({d["setting"] for d in s["datasets"]}) == 11
    assert len(s["benchmarks"]) == 14
    assert len(s["dimensions"]) == 6 and sum(len(d["metrics"]) for d in s["dimensions"]) == 26
    assert len(s["applications"]) == 6
    assert sorted(c["type"] for c in s["challenges"]).count("challenge") == 6 and len(s["challenges"]) == 12


def test_generated_files_are_current():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "build.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_data_js_is_json():
    text = (ROOT / "docs" / "explorer" / "data.js").read_text()
    payload = json.loads(text[text.index("{") : text.rindex("}") + 1])
    assert len(payload["papers"]) == len(build.load()[0])


def test_readme_list_links_resolve():
    body = build.render_list(*build.load())
    anchors = {re.sub(r"[^a-z0-9 -]", "", h.lower()).strip().replace(" ", "-") for h in re.findall(r"^#{3,4} (.+)$", body, re.M)}
    assert set(re.findall(r"\]\(#([^)]+)\)", body)) <= anchors


def test_missing_embeddings_only_warn(tmp_path):
    papers, _ = build.load()
    assert build.embedding_warnings(papers, tmp_path / "none.json")


def test_validate_rejects_unsafe_values():
    papers, survey = build.load()
    bad = copy.deepcopy(papers)
    other = next(p for p in bad if not p.get("family"))
    other["stage"] = 'x)"><img src=x onerror=alert(1)>'
    bad[0]["links"] = {"paper": "javascript:alert(1)"}
    bad[1]["links"] = {"paper": "https://img.shields.io/badge/arXiv-B31B1B"}
    bad[2]["in_survey"] = "yes"
    errors = build.validate(bad, survey)
    assert any(other["key"] in e and "stage" in e for e in errors)
    assert any(bad[0]["key"] in e and "https" in e for e in errors)
    assert any(bad[1]["key"] in e and "badge" in e for e in errors)
    assert any(bad[2]["key"] in e and "in_survey" in e for e in errors)


def test_no_paper_links_to_a_badge_image():
    papers, _ = build.load()
    assert not [p["key"] for p in papers if any("img.shields.io" in v for v in p["links"].values())]
