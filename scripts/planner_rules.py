"""Planner vocabulary and the rules that map the survey's tables to targets, models, and constraints."""

TARGETS = [{"id": "identity", "label": "a face or identity"}, {"id": "voice", "label": "a voice or speaker"},
           {"id": "style", "label": "an art style or copyrighted work"}, {"id": "nsfw", "label": "NSFW or harmful content"},
           {"id": "class", "label": "an object class"}, {"id": "knowledge", "label": "a fact or private knowledge"},
           {"id": "backdoor", "label": "a backdoor or poisoned data"}, {"id": "preference", "label": "a user preference"}]
MODELS = [{"id": "vlm", "label": "a VLM or MLLM"}, {"id": "clip", "label": "a CLIP-style encoder"},
          {"id": "image-diffusion", "label": "an image diffusion model"}, {"id": "video", "label": "a video model"},
          {"id": "audio", "label": "an audio or speech model"}]
CONSTRAINTS = [{"id": "none", "label": "any limit"}, {"id": "no-retraining", "label": "retraining"},
               {"id": "keep-weights", "label": "changing the base weights"}]

SETTING_TARGETS = {
    "Identity Unlearning": ["identity"], "Affect and Video Unlearning": ["class"], "Personalization Setup": ["identity"],
    "Copyright Unlearning": ["style"], "Knowledge QA and Instruction Probes": ["knowledge"],
    "Segmentation and I2I Unlearning": ["class"], "Recommender Unlearning": ["preference"],
    "Speech Unlearning": ["voice"], "Safety Robustness Unlearning": ["nsfw"],
    "Web-Scale Data Hygiene via Unlearning": ["backdoor"], "Class Unlearning": ["class"],
}
DATASET_TARGETS = {"VoxCeleb1": ["voice"], "UnlearnCanvas": ["style"], "WikiArt": ["style"]}
MODALITY_MODELS = {"Image": ["clip", "vlm", "image-diffusion"], "Image-Text": ["clip", "vlm", "image-diffusion"],
                   "Audio": ["audio"], "Audio-Text": ["audio"], "Video": ["video"], "Video-Text": ["video"],
                   "Text": ["vlm"], "Text-Graph": [], "Text-Metadata": []}
ALL_TARGETS = [t["id"] for t in TARGETS]
BENCHMARK_TARGETS = {
    "cheng2024mu": ALL_TARGETS, "liu2025protecting": ["identity", "knowledge"], "xu2025pebench": ["identity", "knowledge"],
    "wang2025umu": ["knowledge"], "dontsov2024clear": ["identity"], "ma2024benchmarking": ["identity"],
    "koudounas2025alexa": ["voice"], "ma2024dataset": ["style", "identity"], "zhang2024unlearncanvas": ["style"],
    "moon2024holistic": ["nsfw", "style", "class"], "ren2025six": ["nsfw", "style", "identity", "class"],
    "li2024single": ["class"], "patilunlearning2024": ["knowledge"], "chen2025safeeraser": ["nsfw"],
}
BENCHMARK_MODELS = {"Multimodal": [m["id"] for m in MODELS], "VLM": ["vlm"], "Audio": ["audio"], "DM": ["image-diffusion"]}
METRIC_MODELS = {  # metric id -> (models it applies to, sentences in the paper that say so); missing = all models
    "fa-k": (["clip", "vlm"], ["For VLMs with zero-shot prediction"]),
    "clip-cls-drop": (["image-diffusion"], ["Concept erasure in image generation"]),
    "clip-sim-drop": (["image-diffusion"], ["CLIP image-text similarity provides a continuous signal of residual concept alignment"]),
    "inappropriate-content-rate": (["image-diffusion"], ["In image generation, a standard protocol samples outputs"]),
    "refusal-rate": (["vlm"], ["evaluation set of harmful text-image inputs"]),
    "sim": (["audio"], ["In speech unlearning, privacy evaluation"]),
    "spk-zrf": (["audio"], ["In speech unlearning, privacy evaluation"]),
    "bleu": (["vlm"], ["For VLMs that perform question answering or caption generation"]),
    "fid": (["image-diffusion", "video"], ["To ensure image generation quality is retained", "Fréchet Video Distance (FVD)"]),
    "lpips": (["image-diffusion"], ["comparing generations from the unlearned model to those of the original model"]),
}
STAGE_RULES = {
    "data-side": {
        "no-retraining": {"fit": "no", "reason": "It changes what future training sees.",
                          "why": "reduce the learnability of targeted clusters"},
        "keep-weights": {"fit": "no", "reason": "It acts before or during training, not on a deployed model.",
                         "why": "edits inputs, not weights"}},
    "training-time": {
        "no-retraining": {"fit": "no", "reason": "It updates the model by optimization.",
                          "why": "updates parameters so that responses on the forget set degrade"},
        "keep-weights": {"fit": "no", "reason": "It changes the weights.",
                         "why": "updates parameters so that responses on the forget set degrade"}},
    "architecture": {
        "no-retraining": {"fit": "no", "reason": "Pruning is followed by light fine-tuning.",
                          "why": "modality-aware pruning with light fine-tuning"},
        "keep-weights": {"fit": "no", "reason": "It changes the network structure.",
                         "why": "modifying network structure through pruning, freezing, or controlled regrowth"}},
    "training-free": {
        "no-retraining": {"fit": "fits", "reason": "It uses closed-form edits instead of training.",
                          "why": "replaces iterative optimization with closed-form edits in parameter space"},
        "keep-weights": {"fit": "partly", "reason": "Projecting activations keeps the weights; weight-space edits change them.",
                         "why": "Instead of updating model parameters, these methods suppress target concepts by projecting internal activations"}},
    "decoding-time": {
        "no-retraining": {"fit": "fits", "reason": "It changes the sampler, not the model.",
                          "why": "modifying the sampler rather than the model parameters"},
        "keep-weights": {"fit": "fits", "reason": "The base checkpoint stays fixed.",
                         "why": "The base checkpoint remains fixed"}},
}
GAP_LINKS = {"audio": "temporal-dynamic", "video": "temporal-dynamic", "default": "cross-modal-generalization"}


def all_quotes() -> list[str]:
    quotes = [r["why"] for rules in STAGE_RULES.values() for r in rules.values()]
    return quotes + [q for _, whys in METRIC_MODELS.values() for q in whys]
