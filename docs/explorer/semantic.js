const LIB = "https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.3.0";
const MODEL = "Xenova/bge-small-en-v1.5";
export const QUERY_PREFIX = "Represent this sentence for searching relevant passages: ";

let extractor = null;
let loading = null;
let failed = false;
const cache = new Map();

export const semanticState = () => (failed ? "off" : extractor ? "ready" : loading ? "loading" : "idle");

export function loadModel() {
  loading ??= import(LIB)
    .then(({ pipeline }) => pipeline("feature-extraction", MODEL, { dtype: "q8" }))
    .then((e) => { extractor = e; })
    .catch((err) => { failed = true; console.warn("Semantic search is off:", err); });
  return loading;
}

export async function embedQuery(q) {
  if (cache.has(q)) return cache.get(q);
  await loadModel();
  if (!extractor) return null;
  const out = await extractor(QUERY_PREFIX + q, { pooling: "cls", normalize: true });
  const v = Float32Array.from(out.data);
  cache.set(q, v);
  return v;
}

export async function loadEmbeddings(url = "embeddings.json") {
  try {
    const r = await fetch(url);
    return r.ok ? await r.json() : null;
  } catch {
    return null;
  }
}
