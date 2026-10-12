import { facetValues } from "./planner.js";

export const TABS = ["papers", "datasets", "evaluation", "gaps"];
export const FACETS = ["stage", "family", "model", "target", "application", "risk", "kind", "year", "review", "source"];
const SORTS = ["relevance", "newest", "survey"];

export function defaultState() {
  return { tab: "papers", query: "", target: "any", model: "any", constraint: "none", stage: null, filters: {}, sort: "relevance", paper: null };
}

export function parseHash(hash, data) {
  const s = defaultState();
  const [path, qs] = (hash || "").replace(/^#/, "").split("?");
  const p = new URLSearchParams(qs || "");
  const plan = data.survey.planner;
  const has = (list, v) => v !== null && list.some((x) => x.id === v);
  if (TABS.includes(path)) s.tab = path;
  s.query = p.get("q") || "";
  if (has(plan.targets, p.get("target"))) s.target = p.get("target");
  if (has(plan.models, p.get("model"))) s.model = p.get("model");
  if (has(plan.constraints, p.get("without"))) s.constraint = p.get("without");
  if (has(data.survey.stages, p.get("stage"))) s.stage = p.get("stage");
  if (SORTS.includes(p.get("sort"))) s.sort = p.get("sort");
  if (data.papers.some((x) => x.key === p.get("paper"))) s.paper = p.get("paper");
  for (const facet of FACETS) {
    const values = p.getAll(`f-${facet}`).filter((v) => data.papers.some((x) => facetValues(x, facet).includes(v)));
    if (values.length) s.filters[facet] = values;
  }
  return s;
}

export function toHash(s) {
  const p = new URLSearchParams();
  if (s.query) p.set("q", s.query);
  if (s.target !== "any") p.set("target", s.target);
  if (s.model !== "any") p.set("model", s.model);
  if (s.constraint !== "none") p.set("without", s.constraint);
  if (s.stage) p.set("stage", s.stage);
  if (s.sort !== "relevance") p.set("sort", s.sort);
  for (const [facet, values] of Object.entries(s.filters)) for (const v of values) p.append(`f-${facet}`, v);
  if (s.paper) p.set("paper", s.paper);
  const qs = p.toString();
  return `#${s.tab}${qs ? `?${qs}` : ""}`;
}

export function activeChips(s, labels) {
  const name = (group, v) => labels[group]?.[v] ?? v;
  const chips = [];
  if (s.target !== "any") chips.push({ text: `Forget: ${name("target", s.target)}`, patch: { target: "any" } });
  if (s.model !== "any") chips.push({ text: `Model: ${name("model", s.model)}`, patch: { model: "any" } });
  if (s.constraint !== "none") chips.push({ text: `Without: ${name("constraint", s.constraint)}`, patch: { constraint: "none" } });
  if (s.stage) chips.push({ text: `Stage: ${name("stage", s.stage)}`, patch: { stage: null } });
  for (const [facet, values] of Object.entries(s.filters)) {
    for (const v of values) {
      const filters = { ...s.filters, [facet]: values.filter((x) => x !== v) };
      if (!filters[facet].length) delete filters[facet];
      chips.push({ text: name(facet, v), patch: { filters } });
    }
  }
  if (s.query) chips.push({ text: `Search: "${s.query}"`, patch: { query: "" } });
  return chips;
}
