const ANY_FIT = { fit: "fits", reason: "", why: "" };

export const tagsOf = (p, group) => [...((p.tags || {})[group] || []), ...((p.added || {})[group] || [])];

export function facetValues(p, facet) {
  switch (facet) {
    case "stage": return p.stage ? [p.stage] : [];
    case "family": return p.family ? [p.family] : [];
    case "kind": return [p.kind];
    case "year": return [String(p.year)];
    case "review": return [p.peer_reviewed ? "peer-reviewed" : "preprint"];
    case "source": return [p.in_survey ? "in-survey" : "list-only"];
    default: return tagsOf(p, facet);
  }
}

export function stageFit(survey, stageId, constraint) {
  if (!constraint || constraint === "none") return ANY_FIT;
  return survey.planner.stage_rules[stageId]?.[constraint] || ANY_FIT;
}

export function paperMatches(p, survey, state) {
  if (state.target !== "any" && !tagsOf(p, "target").includes(state.target)) return false;
  if (state.model !== "any" && !tagsOf(p, "model").includes(state.model)) return false;
  if (p.stage && stageFit(survey, p.stage, state.constraint).fit === "no") return false;
  if (state.stage && p.stage !== state.stage) return false;
  for (const [facet, values] of Object.entries(state.filters || {})) {
    if (values.length && !values.some((v) => facetValues(p, facet).includes(v))) return false;
  }
  return true;
}

export function stageCounts(survey, papers, state) {
  const counts = Object.fromEntries(survey.stages.map((s) => [s.id, 0]));
  const loose = { ...state, constraint: "none", stage: null };
  for (const p of papers) if (p.stage && paperMatches(p, survey, loose)) counts[p.stage]++;
  return counts;
}

export function planCard(survey, state) {
  const forTarget = (item) => state.target === "any" || item.targets.includes(state.target);
  const forModel = (item) => state.model === "any" || !item.models.length || item.models.includes(state.model);
  const metrics = { forget: [], retain: [], robustness: [], cost: [] };
  for (const dim of survey.dimensions) for (const m of dim.metrics) if (forModel(m)) metrics[dim.side].push(m);
  const related = new Set(["adversarial-robustness", "evaluation-reliability"]);
  if (["audio", "video"].includes(state.model)) related.add("temporal-dynamic");
  if (state.constraint !== "none") related.add("inference-time");
  if (["identity", "knowledge"].includes(state.target)) related.add("cross-modal-leakage");
  return {
    datasets: survey.datasets.filter((d) => forTarget(d) && forModel(d)),
    benchmarks: survey.benchmarks.filter((b) => forTarget(b) && forModel(b)),
    metrics,
    attacks: survey.attacks,
    challenges: survey.challenges.filter((c) => related.has(c.id)),
  };
}

export function gapMatrix(survey, papers) {
  const models = survey.planner.models.map((m) => m.id);
  const cells = (match) => Object.fromEntries(models.map((m) => [m, papers.filter((p) => match(p) && tagsOf(p, "model").includes(m)).length]));
  return {
    models,
    rows: survey.stages.map((s) => ({
      id: s.id, name: s.name, cells: cells((p) => p.stage === s.id),
      families: survey.families.filter((f) => f.stage === s.id).map((f) => ({ id: f.id, name: f.name, cells: cells((p) => p.family === f.id) })),
    })),
  };
}

export function gapLink(survey, model) {
  const links = survey.planner.gap_links;
  return links[model] || links.default;
}

export function searchTags(survey) {
  const names = (items, text = (x) => x.name) => Object.fromEntries(items.map((x) => [x.id, text(x)]));
  const stage = names(survey.stages);
  const family = names(survey.families);
  const target = names(survey.planner.targets, (t) => t.label);
  const application = names(survey.applications);
  return (p) => [stage[p.stage], family[p.family], ...((p.tags || {}).target || []).map((t) => target[t]),
    ...((p.tags || {}).application || []).map((a) => application[a])].filter(Boolean).join(" ");
}
