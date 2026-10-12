"""Embed every paper (and the eval queries) with the same ONNX model the browser uses.

    uv run --group embed scripts/embed.py
"""

import base64
import json
from pathlib import Path

import numpy as np

from build import EMBEDDINGS, ROOT, content_hash, load, passage

MODEL_REPO = "Xenova/bge-small-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
_session = None


def _model():
    global _session
    if _session is None:
        import onnxruntime as ort
        from huggingface_hub import hf_hub_download
        from tokenizers import Tokenizer

        tok = Tokenizer.from_file(hf_hub_download(MODEL_REPO, "tokenizer.json"))
        tok.enable_truncation(512)
        tok.enable_padding()
        _session = (ort.InferenceSession(hf_hub_download(MODEL_REPO, "onnx/model_quantized.onnx")), tok)
    return _session


def embed(texts: list[str], batch: int = 16) -> np.ndarray:
    sess, tok = _model()
    names = {i.name for i in sess.get_inputs()}
    out = []
    for i in range(0, len(texts), batch):
        enc = tok.encode_batch(texts[i : i + batch])
        ids = np.array([e.ids for e in enc], dtype=np.int64)
        feed = {"input_ids": ids, "attention_mask": np.array([e.attention_mask for e in enc], dtype=np.int64),
                "token_type_ids": np.zeros_like(ids)}
        hidden = sess.run(None, {k: v for k, v in feed.items() if k in names})[0]
        out.append(hidden[:, 0])
    vecs = np.concatenate(out).astype(np.float32)
    return vecs / np.linalg.norm(vecs, axis=1, keepdims=True)


def to_int8(vectors: np.ndarray) -> np.ndarray:
    return np.clip(np.round(vectors * 127), -127, 127).astype(np.int8)


def _b64(vectors: np.ndarray) -> str:
    return base64.b64encode(to_int8(vectors).tobytes()).decode()


def main() -> None:
    papers, _ = load()
    texts = [passage(p) for p in papers]
    vecs = embed(texts)
    EMBEDDINGS.write_text(json.dumps({"model": MODEL_REPO, "dim": int(vecs.shape[1]), "keys": [p["key"] for p in papers],
                                      "hashes": [content_hash(t) for t in texts], "data": _b64(vecs)}))
    queries = [q["query"] for q in json.loads((ROOT / "eval" / "queries.json").read_text())]
    qv = embed([QUERY_PREFIX + q for q in queries])
    (ROOT / "eval" / "query_embeddings.json").write_text(json.dumps({"model": MODEL_REPO, "dim": int(qv.shape[1]),
                                                                    "queries": queries, "data": _b64(qv)}))
    print(f"embedded {len(papers)} papers and {len(queries)} eval queries")


if __name__ == "__main__":
    main()
