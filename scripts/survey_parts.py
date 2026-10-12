"""Parse the survey's fixed parts: taxonomy, families, datasets, benchmarks, metrics, and named paragraphs."""

import re

from latex import cite_keys, display_math, first_sentence, labeled_paragraphs, plain, strip_cites, slug, subsections

STAGES = [("data-side", "Data-side"), ("training-time", "Training-time"), ("architecture", "Architecture-constrained"),
          ("training-free", "Training-free"), ("decoding-time", "Decoding-time")]
FAMILIES = [
    ("data-path", "data-side", "Data-path perturbation", "Data-Path Perturbation Unlearning"),
    ("data-hygiene", "data-side", "Data hygiene and prompt normalization", "Data Hygiene and Prompt Normalization"),
    ("direct-gradient", "training-time", "Direct gradient", "Direct Gradient"),
    ("constrained", "training-time", "Constrained updates", "Constrained Updates"),
    ("mask-driven", "training-time", "Mask-driven selective unlearning", "Mask-Driven Selective Unlearning"),
    ("distillation", "training-time", "Distillation-based", "Distillation-Based Unlearning"),
    ("architecture-editing", "architecture", "Architecture editing", "Architecture Editing Unlearning"),
    ("layer-scoped", "architecture", "Layer-scoped constrained updates", "Layer-Scoped Constrained Updates"),
    ("weight-space", "training-free", "Weight-space linear unlearning", "Weight-Space Linear Unlearning"),
    ("representation-projection", "training-free", "Representation projection", "Representation Projection Unlearning"),
    ("guidance-path", "decoding-time", "Guidance-path control", "Guidance-Path Control"),
    ("conditioning-path", "decoding-time", "Conditioning-path control", "Conditioning-Path Control"),
]
DIMENSIONS = [("forget-quality", "Forget quality and safety", "forget"),
              ("safety-content", "Safety and content forgetting", "forget"),
              ("attack-privacy", "Attack-based privacy", "forget"),
              ("utility", "Utility and faithfulness", "retain"),
              ("robustness", "Adversarial robustness", "robustness"),
              ("compute", "Compute and environment", "cost")]
METRIC_SOURCES = {  # metric id -> (Evaluation appendix paragraph or subsection, index of its formula)
    "ua": ("Unlearning Accuracy", 0), "fa-k": ("Zero-Shot Forget Accuracy (FA@k)", 0),
    "wasserstein-distance": ("Degree of Unlearning", 0), "clip-cls-drop": ("CLIP Classification Drop", 0),
    "clip-sim-drop": ("CLIP Similarity Drop", 0), "refusal-rate": ("Refusal Rate on Forbidden Prompts", 0),
    "vlm-as-judge": ("VLM-Based Judgments", 0), "inappropriate-content-rate": ("Inappropriate Content Rate", None),
    "mia": ("Membership Inference Attack and Enhanced Variants", 0), "identity-matching": ("Identity Matching", None),
    "sim": ("Voice Privacy", None), "spk-zrf": ("Voice Privacy", 1), "top-k-acc": ("Classification Accuracy", 0),
    "recall-k": ("Cross-Modal Retrieval Utility", 0), "bleu": ("Language and QA Metrics", None),
    "clip-score": ("Language and QA Metrics", None), "fid": ("Generative Output Quality", 0),
    "lpips": ("Perceptual Similarity", None), "llm-as-a-judge": ("LLM-as-a-Judge Evaluation", None),
    "human-as-judge": ("Human-Centered Evaluation", None), "attack-success-rate": ("Adversarial Perturbation Robustness", 0),
    "wct": ("Run-time and Memory Usage", None), "memory": ("Run-time and Memory Usage", None),
    "flops": ("Run-time and Memory Usage", None), "energy": ("Environmental Cost", None), "co2e": ("Environmental Cost", None),
}
APPLICATIONS = {"Privacy and Regulatory Compliance": "privacy", "Safety-Aligned Generation": "safety",
                "Copyright and Style Governance": "copyright", "Fairness and Reliability in Deployed Models": "fairness",
                "Personalization and Preference Control": "personalization", "Supply-Chain and Backdoor Security": "security"}
CHALLENGES = {"Theoretical Guarantees": "guarantees", "Cross-Modal Generalization": "cross-modal-generalization",
              "Evaluation Reliability": "evaluation-reliability", "Adversarial Robustness": "adversarial-robustness",
              "Utility Trade-offs": "utility-tradeoffs", "Unified Benchmarks": "unified-benchmarks"}
DIRECTIONS = {"Temporal and Dynamic Modalities": "temporal-dynamic", "Frontier-Scale Model Unlearning": "frontier-scale",
              "Sequential and Continual Unlearning": "continual", "Controllable and Fine-Grained Unlearning": "fine-grained",
              "Inference-Time Unlearning": "inference-time", "Cross-Modal Leakage Mitigation": "cross-modal-leakage"}
ATTACKS = {"Adversarial Reactivation Attacks": "reactivation", "Inference-time Defenses": "inference-defenses"}

_ROW_END = re.compile(r"\\\\\s*$")


def _unique(keys: list[str]) -> list[str]:
    return list(dict.fromkeys(keys))


def _name(cell: str) -> str:
    return plain(strip_cites(cell)).strip(", ")


def parse_taxonomy(structure_tex: str) -> list[dict]:
    forest = structure_tex[structure_tex.index("\\begin{forest}") : structure_tex.index("\\end{forest}")]
    leaves = [line.replace("\\\\", " ") for line in forest.split("\n") if "\\cite{" in line]
    if len(leaves) != len(FAMILIES):
        raise ValueError(f"expected {len(FAMILIES)} taxonomy leaves, found {len(leaves)}")
    return [{"id": fid, "stage": stage, "name": name,
             "methods": [{"name": plain(n).strip(", "), "key": k.strip()}
                         for n, k in re.findall(r"([^,{}\[]+?)~\\cite\{([^}]+)\}", leaf)]}
            for (fid, stage, name, _), leaf in zip(FAMILIES, leaves)]


def parse_family_text(methods_tex: str) -> dict[str, dict]:
    by_label = {label: fid for fid, _, _, label in FAMILIES}
    out = {}
    for label, body in labeled_paragraphs(methods_tex):
        if label in by_label:
            maths = display_math(body)
            out[by_label[label]] = {"mechanism": first_sentence(body), "formula": maths[0] if maths else None,
                                    "keys": _unique(cite_keys(body))}
    if missing := set(by_label.values()) - set(out):
        raise ValueError(f"family paragraphs not found: {sorted(missing)}")
    return out


def parse_datasets(*texts: str) -> list[dict]:
    out, setting, modality = [], None, None
    for text in texts:
        for line in text.split("\n"):
            s = line.strip()
            if m := re.search(r"\\textbf\{([^}]*)\}\\rule", s):
                setting = plain(m.group(1))
            elif m := re.match(r"\\multirow\{\d+\}\{\*\}\{([^}]*)\}", s):
                modality = plain(m.group(1))
            elif s.startswith("&") and "\\cite{" in s:
                name_cell, size, used = [c.strip() for c in _ROW_END.sub("", s).split("&")][1:4]
                name = _name(name_cell)
                out.append({"id": slug(name), "name": name, "key": cite_keys(name_cell)[0], "setting": setting,
                            "modality": modality, "size": plain(size), "used_in": _unique(cite_keys(used))})
    return out


def parse_benchmarks(text: str) -> list[dict]:
    out, group = [], None
    for line in text.split("\n"):
        s = line.strip()
        if m := re.match(r"\\multicolumn\{6\}\{c\}\{\\textbf\{([^}]*)\}\}", s):
            group = plain(m.group(1))
        elif "\\cite{" in s and "&" in s:
            c = [x.strip() for x in _ROW_END.sub("", s).split("&")]
            out.append({"key": cite_keys(c[0])[0], "name": _name(c[0]), "group": group, "modality": plain(c[1]),
                        "target": plain(c[2]), "task": plain(c[3]), "stats": plain(c[4]), "objective": plain(c[5])})
    return out


def parse_metrics(tree_tex: str, eval_tex: str) -> list[dict]:
    forest = tree_tex[tree_tex.index("\\begin{forest}") : tree_tex.index("\\end{forest}")]
    leaves = [m.group(1) for line in forest.split("\n") if (m := re.match(r"^\[\s*\{(.*)\}\s*\]$", line.strip()))]
    if len(leaves) != len(DIMENSIONS):
        raise ValueError(f"expected {len(DIMENSIONS)} metric groups, found {len(leaves)}")
    bodies = dict(labeled_paragraphs(eval_tex)) | dict(subsections(eval_tex))
    dims = []
    for (did, dname, side), leaf in zip(DIMENSIONS, leaves):
        metrics = []
        for raw in leaf.replace("\\\\", " ").split(","):
            name = plain(raw)
            mid = slug(name)
            label, idx = METRIC_SOURCES[mid]
            body = bodies[label]
            maths = display_math(body)
            metrics.append({"id": mid, "name": name, "description": first_sentence(body),
                            "formula": maths[idx] if idx is not None and idx < len(maths) else None,
                            "keys": _unique(cite_keys(body))})
        dims.append({"id": did, "name": dname, "side": side, "metrics": metrics})
    return dims


def parse_named(text: str, labels: dict[str, str]) -> list[dict]:
    return [{"id": labels[label], "name": label, "keys": _unique(cite_keys(body))}
            for label, body in labeled_paragraphs(text) if label in labels]


def survey_table_keys(intro_tex: str) -> list[str]:
    table = intro_tex[intro_tex.index("\\begin{tabular}") : intro_tex.index("\\end{tabular}")]
    return _unique(cite_keys(table))
