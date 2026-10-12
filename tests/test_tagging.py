from pathlib import Path

from latex import live, norm_ws, paper_text
from planner_rules import (BENCHMARK_TARGETS, MODALITY_MODELS, SETTING_TARGETS, STAGE_RULES, all_quotes)
from survey_parts import STAGES, parse_benchmarks, parse_datasets
from tagging import MODEL_WORDS, TARGET_WORDS, arxiv_id, classify, keyword_tags, match_rows, readme_rows

ROOT = Path(__file__).resolve().parents[1]
SETS = dict(methods={"m"}, benchmarks={"b", "m"}, surveys={"s"}, attacks={"a"}, datasets={"d", "b"})


def test_classify_order_and_title_fallback():
    assert classify("m", "x", **SETS) == "method"
    assert classify("b", "x", **SETS) == "benchmark"
    assert classify("d", "x", **SETS) == "dataset"
    assert classify("z", "Machine unlearning for CLIP", **SETS) == "analysis"
    assert classify("z", "Denoising diffusion probabilistic models", **SETS) == "background"


def test_keyword_tags_uses_first_text_with_a_hit():
    assert keyword_tags(MODEL_WORDS, "Speaker identity unlearning for TTS", "diffusion") == ["audio"]
    assert keyword_tags(MODEL_WORDS, "A general method", "We study text-to-image diffusion.") == ["image-diffusion"]
    assert "nsfw" in keyword_tags(TARGET_WORDS, "erasing nudity and unsafe concepts")
    assert keyword_tags(TARGET_WORDS, "a class of methods") == []


def test_readme_rows_and_matching():
    readme = ("### Vision-Language Models (VLMs)\n\n| Date | Title | Paper |\n|---|---|---|\n"
              "| 2024&#8209;05 | Single Image Unlearning: Efficient Machine Unlearning | [x](https://arxiv.org/pdf/2405.12523) |\n"
              "### Diffusion Models (DMs)\n\n| 2023&#8209;03 | Some Unknown Paper Title Here | [x](https://example.org/p.pdf) |\n")
    rows = readme_rows(readme)
    assert rows[0] == {"date": "2024-05", "title": "Single Image Unlearning: Efficient Machine Unlearning",
                       "url": "https://arxiv.org/pdf/2405.12523", "arxiv": "2405.12523", "section": "vlm"}
    matched, unmatched = match_rows(rows, {"li2024single": "Single image unlearning: efficient machine unlearning in MLLMs"},
                                    {"li2024single": None})
    assert list(matched) == ["li2024single"] and unmatched[0]["section"] == "dm"


def test_arxiv_id_from_fields():
    assert arxiv_id({"journal": "arXiv preprint arXiv:2405.12523"}) == "2405.12523"
    assert arxiv_id({"url": "https://openreview.net/forum?id=x"}) is None


def test_every_planner_quote_is_verbatim_in_the_paper():
    text = (ROOT / "data" / "paper_text.txt").read_text()
    missing = [q for q in all_quotes() if norm_ws(q) not in text]
    assert not missing, missing


def test_paper_snapshot_matches_the_latex(sections):
    assert (ROOT / "data" / "paper_text.txt").read_text() == paper_text(sections), "run: uv run --group import scripts/snapshot_paper.py"


def test_rules_cover_every_stage_setting_modality_and_benchmark(sections):
    assert set(STAGE_RULES) == {s for s, _ in STAGES}
    assert all(set(r) == {"no-retraining", "keep-weights"} for r in STAGE_RULES.values())
    ds = parse_datasets(live(sections / "dataset_table1.tex"), live(sections / "App_Datasets_table.tex"))
    assert {d["setting"] for d in ds} <= set(SETTING_TARGETS)
    assert {d["modality"] for d in ds} <= set(MODALITY_MODELS)
    assert {b["key"] for b in parse_benchmarks(live(sections / "benchmark_table.tex"))} == set(BENCHMARK_TARGETS)


def test_readme_rows_take_the_paper_link_not_the_badge():
    badge = "https://img.shields.io/badge/arXiv-B31B1B?style=flat-square&logo=arxiv&logoColor=white"
    readme = ("### Diffusion Models (DMs)\n\n"
              f"| 2023&#8209;03 | Ablating Concepts | [![arXiv]({badge})](https://arxiv.org/pdf/2303.13516.pdf) |\n")
    row = readme_rows(readme)[0]
    assert row["url"] == "https://arxiv.org/pdf/2303.13516.pdf" and row["arxiv"] == "2303.13516"


def test_prefer_readme_title_keeps_casing_only_for_the_same_title():
    from tagging import prefer_readme_title
    assert prefer_readme_title("Salun: empowering machine unlearning", "SalUn: Empowering Machine Unlearning") == "SalUn: Empowering Machine Unlearning"
    assert prefer_readme_title("Salun: empowering machine unlearning", "A different paper") == "Salun: empowering machine unlearning"


def test_a_no_verdict_never_quotes_a_sentence_that_supports_fitting():
    supports_fit = ["not weights", "without retraining", "remains fixed", "unchanged", "closed-form"]
    for stage, rules in STAGE_RULES.items():
        for constraint, rule in rules.items():
            if rule["fit"] == "no":
                assert not any(s in rule["why"] for s in supports_fit), (stage, constraint, rule["why"])
