import { buildIndex, decodeEmbeddings, hybridSearch, parseQuery } from "./search.js";
import { paperMatches, planCard, searchTags, stageCounts, stageFit } from "./planner.js";
import { parseHash, toHash } from "./state.js";
import { embedQuery, loadEmbeddings, semanticState } from "./semantic.js";
import { esc, renderDatasets, renderDrawer, renderEvaluation, renderGaps, renderMath, renderPapers } from "./views.js";

const DATA = window.MMU_DATA;
const { survey, papers } = DATA;
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const noun = (text) => text.replace(/^(a|an) /, "").replace(/^./, (c) => c.toUpperCase());
const byId = (items, text = (x) => x.name) => Object.fromEntries(items.map((x) => [x.id, text(x)]));
const SIDES = { forget: "Forgetting", retain: "Retained utility", robustness: "Robustness", cost: "Cost" };

const labels = {
  stage: byId(survey.stages), family: byId(survey.families),
  target: byId(survey.planner.targets, (t) => noun(t.label)),
  model: { vlm: "VLM or MLLM", clip: "CLIP-style encoder", "image-diffusion": "Image diffusion", video: "Video", audio: "Audio or speech" },
  application: byId(survey.applications), challenge: byId(survey.challenges),
  metric: Object.fromEntries(survey.dimensions.flatMap((d) => d.metrics.map((m) => [m.id, m.name]))),
  dataset: byId(survey.datasets),
  kind: { method: "Method", benchmark: "Benchmark", attack: "Attack", analysis: "Analysis", survey: "Survey" },
  review: { "peer-reviewed": "Peer reviewed", preprint: "Preprint" },
  source: { "in-survey": "In the survey", "list-only": "Only in the list" },
};
const index = buildIndex(papers, searchTags(survey));

const ctx = {
  data: DATA, survey, papers, labels, BY_KEY: new Map(papers.map((p) => [p.key, p])), state: parseHash(location.hash, DATA),
  emb: null, qvec: null, qvecFor: null, results: papers, queryKeys: null, terms: [], datasetModality: "all", gapExpanded: new Set(),
  open: openPaper, set: update, toggleFilters,
};

function update(patch) {
  Object.assign(ctx.state, patch);
  render();
  history.replaceState(null, "", toHash(ctx.state));
}

function compute() {
  const s = ctx.state;
  const q = s.query.trim();
  const ranked = q ? hybridSearch(index, q, { emb: ctx.emb, qvec: ctx.qvecFor === q ? ctx.qvec : null }) : null;
  ctx.queryKeys = ranked ? new Set(ranked.map((r) => r.key)) : null;
  ctx.terms = parseQuery(q).terms;
  const list = papers.filter((p) => paperMatches(p, survey, s) && (!ctx.queryKeys || ctx.queryKeys.has(p.key)));
  const stageIdx = Object.fromEntries(survey.stages.map((x, i) => [x.id, i]));
  const famIdx = Object.fromEntries(survey.families.map((x, i) => [x.id, i]));
  if (ranked && s.sort === "relevance") {
    const rank = new Map(ranked.map((r, i) => [r.key, i]));
    list.sort((a, b) => rank.get(a.key) - rank.get(b.key));
  } else if (s.sort === "newest") {
    list.sort((a, b) => (b.date || String(b.year)).localeCompare(a.date || String(a.year)) || a.title.localeCompare(b.title));
  } else {
    list.sort((a, b) => (stageIdx[a.stage] ?? 9) - (stageIdx[b.stage] ?? 9) || (famIdx[a.family] ?? 99) - (famIdx[b.family] ?? 99) || b.year - a.year);
  }
  ctx.results = list;
}

function fillSelect(sel, options, value) {
  if (!sel.options.length) sel.innerHTML = options.map((o) => `<option value="${esc(o.id)}">${esc(o.label)}</option>`).join("");
  sel.value = value;
  const ctx2d = (fillSelect.canvas ??= document.createElement("canvas").getContext("2d"));
  ctx2d.font = getComputedStyle(sel).font;
  sel.style.width = `calc(${Math.ceil(ctx2d.measureText(sel.selectedOptions[0].text).width)}px + 1.3em)`;
}

function renderPlanner() {
  const p = survey.planner;
  fillSelect($("#target"), [{ id: "any", label: "anything" }, ...p.targets], ctx.state.target);
  fillSelect($("#model"), [{ id: "any", label: "any model" }, ...p.models], ctx.state.model);
  fillSelect($("#constraint"), p.constraints, ctx.state.constraint);
}

function renderPipeline() {
  const counts = stageCounts(survey, papers, ctx.state);
  const total = papers.filter((p) => paperMatches(p, survey, { ...ctx.state, stage: null })).length;
  $("#pipeline").innerHTML = `<li class="stage stage-all"><button type="button" data-all aria-pressed="${!ctx.state.stage}">
      <span class="stage-name">All stages</span><span class="stage-n">${total} ${total === 1 ? "paper" : "papers"}</span></button></li>` + survey.stages.map((s) => {
    const fit = stageFit(survey, s.id, ctx.state.constraint);
    const n = counts[s.id];
    return `<li class="stage fit-${fit.fit}" style="--stage: var(--${s.id})"><button type="button" data-stage="${s.id}" aria-pressed="${ctx.state.stage === s.id}"
      ${fit.why ? `title="The survey says: ${esc(fit.why)}"` : ""}><span class="stage-name">${esc(s.name)}</span>
      <span class="stage-n">${n} ${n === 1 ? "paper" : "papers"}</span><span class="stage-why">${fit.fit === "fits" ? "" : esc(fit.reason)}</span></button></li>`;
  }).join("");
  $$("[data-stage]").forEach((b) => b.addEventListener("click", () => update({ stage: ctx.state.stage === b.dataset.stage ? null : b.dataset.stage })));
  $("[data-all]").addEventListener("click", () => update({ stage: null }));
}

function renderStagePanel() {
  const host = $("#stage-panel");
  const id = ctx.state.stage;
  host.hidden = !id;
  if (!id) return;
  const fit = stageFit(survey, id, ctx.state.constraint);
  host.style.setProperty("--stage", `var(--${id})`);
  host.innerHTML = `<div class="panel-head"><h2>${esc(labels.stage[id])}</h2><button type="button" class="ghost" data-close-stage>Close</button></div>
    ${fit.fit !== "fits" ? `<p class="why">${esc(fit.reason)} The survey says: "${esc(fit.why)}".</p>` : ""}
    <div class="families">${survey.families.filter((f) => f.stage === id).map((f) => `<article class="family"><h3>${esc(f.name)}</h3><p>${esc(f.mechanism)}</p>
      ${f.formula ? `<div class="formula" data-tex="${esc(f.formula)}"></div>` : ""}
      <p>${f.methods.map((m) => `<button type="button" class="link" data-open="${esc(m.key)}">${esc(m.name)}</button>`).join(", ")}</p></article>`).join("")}</div>`;
  renderMath(host);
  $$("[data-open]", host).forEach((b) => b.addEventListener("click", () => openPaper(b.dataset.open)));
  $("[data-close-stage]", host).addEventListener("click", () => update({ stage: null }));
}

function renderPlanCard() {
  const s = ctx.state;
  const host = $("#plan-card");
  host.hidden = s.target === "any" && s.model === "any";
  if (host.hidden) return;
  const plan = planCard(survey, s);
  const list = (items, fmt, empty) => (items.length ? `<ul>${items.map(fmt).join("")}</ul>` : `<p class="empty">${empty}</p>`);
  host.innerHTML = `<h2>What to read and test</h2><div class="plan-grid">
    <section><h3>Datasets (${plan.datasets.length})</h3>${list(plan.datasets.slice(0, 8), (d) => `<li>${esc(d.name)} <span class="muted">${esc(d.modality)}, ${esc(d.size)}</span></li>`,
      "The survey lists no dataset for this combination.")}${plan.datasets.length > 8 ? `<button type="button" class="link" data-goto="datasets">See all ${plan.datasets.length}</button>` : ""}</section>
    <section><h3>Benchmarks (${plan.benchmarks.length})</h3>${list(plan.benchmarks, (b) => `<li><button type="button" class="link" data-open="${esc(b.key)}">${esc(b.name)}</button></li>`,
      "No benchmark in the survey covers this combination yet.")}</section>
    <section><h3>Metrics to report</h3>${Object.entries(SIDES).map(([side, title]) => `<p><strong>${title}:</strong> ${plan.metrics[side].map((m) => esc(m.name)).join(", ") || "none listed"}</p>`).join("")}</section>
    <section><h3>Risks to check</h3>${list([...plan.attacks, ...plan.challenges], (c) => `<li>${esc(c.name)}</li>`, "")}</section></div>`;
  $$("[data-open]", host).forEach((b) => b.addEventListener("click", () => openPaper(b.dataset.open)));
  $("[data-goto]", host)?.addEventListener("click", () => update({ tab: "datasets" }));
}

function renderChips() {
  const s = ctx.state;
  const chips = [];
  if (s.stage) chips.push([`Stage: ${labels.stage[s.stage]}`, () => update({ stage: null })]);
  for (const [facet, values] of Object.entries(s.filters)) {
    for (const v of values) {
      chips.push([labels[facet]?.[v] ?? v, () => {
        const filters = { ...s.filters, [facet]: values.filter((x) => x !== v) };
        if (!filters[facet].length) delete filters[facet];
        update({ filters });
      }]);
    }
  }
  if (s.query) chips.push([`Search: "${s.query}"`, () => { $("#search").value = ""; update({ query: "" }); }]);
  const host = $("#chips");
  host.innerHTML = chips.map(([text], i) => `<button type="button" class="chip" data-i="${i}" aria-label="Remove ${esc(text)}">${esc(text)} ×</button>`).join("");
  $$("[data-i]", host).forEach((b) => b.addEventListener("click", chips[Number(b.dataset.i)][1]));
}

function renderTabs() {
  for (const b of $$(".tabs [role=tab]")) {
    const on = b.dataset.tab === ctx.state.tab;
    b.setAttribute("aria-selected", String(on));
    b.tabIndex = on ? 0 : -1;
  }
  for (const v of $$(".view")) v.hidden = v.id !== `view-${ctx.state.tab}`;
}

function render() {
  compute();
  renderPlanner();
  renderPipeline();
  renderStagePanel();
  renderPlanCard();
  renderChips();
  renderTabs();
  ({ papers: renderPapers, datasets: renderDatasets, evaluation: renderEvaluation, gaps: renderGaps })[ctx.state.tab](ctx);
  renderDrawer(ctx);
}

function openPaper(key) {
  if (ctx.BY_KEY.has(key)) update({ paper: key });
}

function closeDrawer() {
  const key = ctx.state.paper;
  update({ paper: null });
  $(`.paper[data-key="${CSS.escape(key || "")}"]`)?.focus({ preventScroll: true });
}

function toggleFilters(open) {
  $("#filters").classList.toggle("is-open", open);
  $(".filters-toggle").setAttribute("aria-expanded", String(open));
}

const setStatus = (text) => { $("#search-status").textContent = text; };

function semanticFor(q) {
  if (q.split(/\s+/).filter(Boolean).length < 3) return;
  if (!ctx.emb) return setStatus("Semantic search is off; keyword search still works.");
  if (semanticState() !== "ready") setStatus("Loading semantic search (34 MB, once).");
  embedQuery(q).then((v) => {
    if (!v) return setStatus("Semantic search is off; keyword search still works.");
    setStatus("");
    if (ctx.state.query.trim() === q) {
      ctx.qvec = v;
      ctx.qvecFor = q;
      render();
    }
  });
}

function exportBib() {
  const text = ctx.results.filter((p) => p.bibtex).map((p) => p.bibtex).join("\n\n") + "\n";
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], { type: "text/x-bibtex" }));
  a.download = "multimodal-unlearning-papers.bib";
  a.click();
  URL.revokeObjectURL(a.href);
}

function setupTheme() {
  const btn = $("[data-theme-toggle]");
  const current = () => document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  const show = () => {
    const dark = current() === "dark";
    btn.textContent = dark ? "Light" : "Dark";
    btn.setAttribute("aria-label", `Switch to ${dark ? "light" : "dark"} theme`);
  };
  try {
    const saved = localStorage.getItem("mmu-theme");
    if (saved) document.documentElement.dataset.theme = saved;
  } catch { /* storage blocked: follow the OS setting */ }
  show();
  btn.addEventListener("click", () => {
    const next = current() === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("mmu-theme", next); } catch { /* ignore */ }
    show();
  });
}

function setupSuggest() {
  const dlg = $("#suggest-dialog");
  const options = [...survey.stages.map((s) => s.name), "Benchmark or dataset", "Evaluation or attack", "Not sure"];
  $("#suggest-section").innerHTML = options.map((o) => `<option>${esc(o)}</option>`).join("");
  $("[data-open-suggest]").addEventListener("click", () => dlg.showModal());
  $("[data-close-suggest]").addEventListener("click", () => dlg.close());
  $("#suggest-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const params = new URLSearchParams({ template: "add-paper.yml", title: `[Paper] ${fd.get("paper-title")}` });
    for (const k of ["paper-title", "link", "section", "reason"]) if (fd.get(k)) params.set(k, fd.get(k));
    window.open(`https://github.com/${DATA.repo}/issues/new?${params}`, "_blank", "noopener");
    dlg.close();
    e.target.reset();
  });
}

function init() {
  $("#search").value = ctx.state.query;
  if (matchMedia("(max-width: 720px)").matches) $("#search").placeholder = "Search papers";
  for (const [id, key] of [["#target", "target"], ["#model", "model"], ["#constraint", "constraint"]]) {
    $(id).addEventListener("change", (e) => update({ [key]: e.target.value }));
  }
  let timer;
  $("#search").addEventListener("input", (e) => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      const q = e.target.value;
      update({ query: q, ...(q.trim() ? { sort: "relevance" } : {}) });
      semanticFor(q.trim());
    }, 150);
  });
  $("#sort").addEventListener("change", (e) => update({ sort: e.target.value }));
  $("[data-export]").addEventListener("click", exportBib);
  $(".filters-toggle").addEventListener("click", () => toggleFilters(!$("#filters").classList.contains("is-open")));
  $("[data-close-drawer]").addEventListener("click", closeDrawer);
  $$(".tabs [role=tab]").forEach((b) => b.addEventListener("click", () => update({ tab: b.dataset.tab })));
  $(".tabs").addEventListener("keydown", (e) => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    const tabs = $$(".tabs [role=tab]");
    const i = tabs.findIndex((t) => t.dataset.tab === ctx.state.tab);
    const next = tabs[(i + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length];
    update({ tab: next.dataset.tab });
    next.focus();
  });
  document.addEventListener("keydown", (e) => {
    const typing = /INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName);
    if (e.key === "/" && !typing) {
      e.preventDefault();
      if (ctx.state.tab !== "papers") update({ tab: "papers" });
      $("#search").focus();
    } else if (e.key === "Escape" && ctx.state.paper) {
      closeDrawer();
    } else if (e.key === "Escape" && $("#filters").classList.contains("is-open")) {
      toggleFilters(false);
    } else if (ctx.state.tab === "papers" && !typing && (e.key === "ArrowDown" || e.key === "ArrowUp")) {
      const items = $$(".paper");
      if (!items.length) return;
      e.preventDefault();
      const i = items.indexOf(document.activeElement);
      items[Math.max(0, Math.min(items.length - 1, i + (e.key === "ArrowDown" ? 1 : -1)))].focus();
    }
  });
  window.addEventListener("hashchange", () => {
    ctx.state = parseHash(location.hash, DATA);
    $("#search").value = ctx.state.query;
    update({});
  });
  setupTheme();
  setupSuggest();
  update({});
  loadEmbeddings().then((json) => {
    if (json) ctx.emb = decodeEmbeddings(json);
    if (ctx.state.query.trim()) semanticFor(ctx.state.query.trim());
    render();
  });
}

init();
