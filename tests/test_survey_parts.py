from latex import live
from survey_parts import (APPLICATIONS, ATTACKS, CHALLENGES, DIRECTIONS, FAMILIES, parse_benchmarks,
                          parse_datasets, parse_family_text, parse_metrics, parse_named, parse_taxonomy,
                          survey_table_keys)


def test_taxonomy_has_12_families_and_44_methods(sections):
    tax = parse_taxonomy(live(sections / "structure.tex"))
    assert [f["id"] for f in tax] == [f[0] for f in FAMILIES]
    assert sum(len(f["methods"]) for f in tax) == 44
    assert {"name": "SalUn", "key": "fan2023salun"} in next(f for f in tax if f["id"] == "mask-driven")["methods"]


def test_every_family_has_mechanism_and_keys(sections):
    fam = parse_family_text(live(sections / "3_Methods.tex"))
    assert set(fam) == {f[0] for f in FAMILIES}
    assert fam["data-path"]["mechanism"].startswith("Data-path perturbation unlearning edits inputs, not weights")
    assert fam["representation-projection"]["formula"].startswith("h' \;=")
    assert fam["mask-driven"]["formula"] is None
    assert all(f["keys"] for f in fam.values())


def test_datasets_56_in_11_settings(sections):
    ds = parse_datasets(live(sections / "dataset_table1.tex"), live(sections / "App_Datasets_table.tex"))
    assert len(ds) == 56
    assert len({d["setting"] for d in ds}) == 11
    celeba = next(d for d in ds if d["name"] == "CelebA")
    assert celeba["setting"] == "Identity Unlearning" and celeba["modality"] == "Image" and "dontsov2024clear" in celeba["used_in"]
    assert next(d for d in ds if d["name"] == "VoxCeleb1")["modality"] == "Audio"


def test_benchmarks_14_in_3_groups(sections):
    bm = parse_benchmarks(live(sections / "benchmark_table.tex"))
    assert len(bm) == 14 and len({b["group"] for b in bm}) == 3
    assert bm[0]["name"] == "MU-Bench" and bm[0]["key"] == "cheng2024mu"


def test_metrics_6_dimensions_26_metrics(sections):
    dims = parse_metrics(live(sections / "metrics_tree.tex"), live(sections / "App_Evaluation.tex"))
    metrics = [m for d in dims for m in d["metrics"]]
    assert len(dims) == 6 and len(metrics) == 26
    by_id = {m["id"]: m for m in metrics}
    assert by_id["ua"]["formula"].startswith("\\mathrm{UA}")
    assert "spk" in by_id["spk-zrf"]["formula"] and by_id["sim"]["formula"] is None
    assert by_id["co2e"]["name"] == "CO2e"
    assert by_id["attack-success-rate"]["keys"]


def test_named_paragraphs(sections, paper_dir):
    assert len(parse_named(live(sections / "App_Applications.tex"), APPLICATIONS)) == 6
    assert len(parse_named(live(sections / "App_Challenges.tex"), CHALLENGES)) == 6
    assert len(parse_named(live(sections / "6_Conclusion.tex"), DIRECTIONS)) == 6
    assert len(parse_named(live(sections / "App_Robustness_Control.tex"), ATTACKS)) == 2
    assert len(survey_table_keys(live(sections / "1_Introduction.tex"))) == 6
