import { readFileSync } from "node:fs";
import { searchTags } from "../docs/explorer/planner.js";
import { buildIndex, decodeEmbeddings, hybridSearch } from "../docs/explorer/search.js";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const dataText = read("../docs/explorer/data.js");
const { survey, papers } = JSON.parse(dataText.slice(dataText.indexOf("{"), dataText.lastIndexOf("}") + 1));
const queries = JSON.parse(read("../eval/queries.json"));
const keys = new Set(papers.map((p) => p.key));
const missing = queries.flatMap((q) => q.expect.filter((k) => !keys.has(k)));
if (missing.length) {
  console.error(`Expected keys not in papers.yaml: ${missing.join(", ")}`);
  process.exit(1);
}

const emb = decodeEmbeddings(JSON.parse(read("../docs/explorer/embeddings.json")));
const qjson = JSON.parse(read("../eval/query_embeddings.json"));
const qemb = decodeEmbeddings({ ...qjson, keys: qjson.queries });
const index = buildIndex(papers, searchTags(survey));
const hit = (ranked, expect) => ranked.slice(0, 10).some((r) => expect.includes(r.key));

let keyword = 0;
let hybrid = 0;
queries.forEach((q, i) => {
  const qvec = Float32Array.from(qemb.data.subarray(i * qemb.dim, (i + 1) * qemb.dim), (v) => v / 127);
  const k = hit(hybridSearch(index, q.query), q.expect);
  const h = hit(hybridSearch(index, q.query, { emb, qvec }), q.expect);
  keyword += k;
  hybrid += h;
  if (!h) console.log(`miss (hybrid): ${q.query}`);
});
const n = queries.length;
console.log(`hit@10 keyword=${(keyword / n).toFixed(2)} hybrid=${(hybrid / n).toFixed(2)} (n=${n})`);
if (hybrid < keyword) {
  console.error("Hybrid search is worse than keyword search.");
  process.exit(1);
}
