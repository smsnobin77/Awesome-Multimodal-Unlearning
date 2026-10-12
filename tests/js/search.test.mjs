import { test } from "node:test";
import assert from "node:assert/strict";
import { buildIndex, decodeEmbeddings, hybridSearch, keywordRanking, parseQuery, rrf, similarPapers, tokenize }
  from "../../docs/explorer/search.js";

const papers = [
  { key: "a", name: "SalUn", title: "Saliency-based unlearning for diffusion", abstract: "We erase concepts with weight saliency." },
  { key: "b", name: null, title: "Speaker unlearning for TTS", abstract: null },
  { key: "c", name: null, title: "A study of CLIP backdoors", abstract: "Backdoor triggers in contrastive models." },
];
const encode = (rows) => ({ dim: 2, keys: rows.map((r) => r[0]),
  data: btoa(String.fromCharCode(...rows.flatMap((r) => r[1].map((v) => v & 255)))) });
const emb = () => decodeEmbeddings(encode([["a", [127, 0]], ["b", [0, 127]], ["c", [90, 90]]]));

test("tokenize drops stopwords and punctuation", () => {
  assert.deepEqual(tokenize("The CLIP-based, model!"), ["clip", "based", "model"]);
});

test("unclosed quotes become plain terms", () => {
  assert.deepEqual(parseQuery('"exact phrase" and "open'), { phrases: ["exact phrase"], terms: ["open"] });
});

test("indexes papers without abstract", () => {
  assert.equal(keywordRanking(buildIndex(papers), "speaker")[0].key, "b");
});

test("exact method name goes first", () => {
  assert.equal(hybridSearch(buildIndex(papers), "salun")[0].key, "a");
});

test("phrases must match", () => {
  assert.deepEqual(keywordRanking(buildIndex(papers), '"weight saliency"').map((r) => r.key), ["a"]);
});

test("special characters do not throw", () => {
  const ix = buildIndex(papers);
  for (const q of ["FA@k (", "C++", '"unclosed', "[", "\\", "*"]) assert.doesNotThrow(() => hybridSearch(ix, q));
  assert.equal(keywordRanking(ix, '"backdoor')[0].key, "c");
});

test("rrf rewards agreement", () => {
  const f = rrf([["x", "y"], ["y", "x"], ["y"]]);
  assert.ok(f.get("y") > f.get("x"));
});

test("hybrid falls back to keyword ranking", () => {
  const ix = buildIndex(papers);
  assert.deepEqual(hybridSearch(ix, "backdoor").map((r) => r.key), keywordRanking(ix, "backdoor").map((r) => r.key));
});

test("semantic results join the ranking", () => {
  const r = hybridSearch(buildIndex(papers), "voice cloning", { emb: emb(), qvec: Float32Array.from([0, 1]) });
  assert.equal(r[0].key, "b");
});

test("similar papers exclude the paper itself", () => {
  assert.deepEqual(similarPapers(emb(), "a", 2), ["c", "b"]);
  assert.deepEqual(similarPapers(emb(), "missing"), []);
});
