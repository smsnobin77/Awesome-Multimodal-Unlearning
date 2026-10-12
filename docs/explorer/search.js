export const STOP = new Set(("a an and are as at be by for from how in into is it its of on or that the this to with we our " +
  "via using what when which").split(" "));
const FIELDS = [["name", 3], ["title", 2.5], ["tagtext", 1.5], ["abstract", 1]];
const K1 = 1.2;
const B = 0.75;

export function tokenize(s) {
  return (s || "").toLowerCase().normalize("NFKD").replace(/[^\p{L}\p{N}]+/gu, " ").split(" ")
    .filter((t) => t && !STOP.has(t));
}

export function parseQuery(q) {
  const text = q || "";
  const phrases = [...text.matchAll(/"([^"]+)"/g)].map((m) => m[1].toLowerCase().trim()).filter(Boolean);
  return { phrases, terms: tokenize(text.replace(/"[^"]+"/g, " ").replace(/"/g, " ")) };
}

export function buildIndex(papers, tagText = () => "") {
  const docs = papers.map((p) => {
    const fields = { name: tokenize(p.name), title: tokenize(p.title), tagtext: tokenize(tagText(p)), abstract: tokenize(p.abstract) };
    const tf = new Map();
    let len = 0;
    for (const [field, weight] of FIELDS) {
      for (const t of fields[field]) {
        tf.set(t, (tf.get(t) || 0) + weight);
        len += weight;
      }
    }
    return { key: p.key, tf, len, name: (p.name || "").toLowerCase(), lower: `${p.name || ""} ${p.title} ${p.abstract || ""}`.toLowerCase() };
  });
  const df = new Map();
  for (const d of docs) for (const t of d.tf.keys()) df.set(t, (df.get(t) || 0) + 1);
  const avg = docs.reduce((a, d) => a + d.len, 0) / Math.max(1, docs.length);
  return { docs, df, avg, vocab: [...df.keys()] };
}

const idf = (ix, t) => Math.log(1 + (ix.docs.length - (ix.df.get(t) || 0) + 0.5) / ((ix.df.get(t) || 0) + 0.5));

export function keywordRanking(ix, query) {
  const { phrases, terms } = parseQuery(query);
  if (!terms.length && !phrases.length) return [];
  const expand = (t, last) => {
    if (!last || t.length < 3) return [t];
    const hits = ix.vocab.filter((v) => v.startsWith(t)).slice(0, 30);
    return hits.length ? hits : [t];
  };
  const out = [];
  for (const d of ix.docs) {
    if (phrases.some((ph) => !d.lower.includes(ph))) continue;
    let score = 0;
    let matched = 0;
    terms.forEach((t, i) => {
      let best = 0;
      for (const v of expand(t, i === terms.length - 1)) {
        const f = d.tf.get(v);
        if (f) best = Math.max(best, idf(ix, v) * (f * (K1 + 1)) / (f + K1 * (1 - B + B * d.len / ix.avg)));
      }
      if (best > 0) matched++;
      score += best;
    });
    if (terms.length && matched < Math.ceil(terms.length * 0.6)) continue;
    out.push({ key: d.key, score: score + phrases.length * 5 });
  }
  return out.sort((a, b) => b.score - a.score);
}

export function rrf(rankings, k = 60) {
  const fused = new Map();
  for (const ranking of rankings) ranking.forEach((key, rank) => fused.set(key, (fused.get(key) || 0) + 1 / (k + rank + 1)));
  return fused;
}

export function decodeEmbeddings(json) {
  const bin = atob(json.data);
  const data = new Int8Array(bin.length);
  for (let i = 0; i < bin.length; i++) data[i] = (bin.charCodeAt(i) << 24) >> 24;
  return { dim: json.dim, keys: json.keys, hashes: json.hashes || [], data, row: new Map(json.keys.map((k, i) => [k, i])) };
}

export function semanticRanking(emb, qvec) {
  const out = emb.keys.map((key, i) => {
    let s = 0;
    const offset = i * emb.dim;
    for (let j = 0; j < emb.dim; j++) s += qvec[j] * emb.data[offset + j];
    return { key, score: s / 127 };
  });
  return out.sort((a, b) => b.score - a.score);
}

export function hybridSearch(ix, query, { emb = null, qvec = null, top = 30 } = {}) {
  const rankings = [keywordRanking(ix, query).map((r) => r.key)];
  if (emb && qvec) rankings.push(semanticRanking(emb, qvec).slice(0, top).map((r) => r.key));
  const q = (query || "").trim().toLowerCase();
  const exact = q ? ix.docs.filter((d) => d.name && d.name === q).map((d) => d.key) : [];
  const ranked = [...rrf(rankings).entries()].sort((a, b) => b[1] - a[1]).map(([key, score]) => ({ key, score }));
  return [...exact.map((key) => ({ key, score: Infinity })), ...ranked.filter((r) => !exact.includes(r.key))];
}

export function similarPapers(emb, key, k = 5) {
  const i = emb?.row.get(key);
  if (i === undefined) return [];
  const q = Float32Array.from(emb.data.subarray(i * emb.dim, (i + 1) * emb.dim), (v) => v / 127);
  return semanticRanking(emb, q).filter((r) => r.key !== key).slice(0, k).map((r) => r.key);
}
