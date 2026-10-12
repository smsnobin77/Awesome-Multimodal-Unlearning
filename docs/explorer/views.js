import { facetValues, gapLink, gapMatrix, paperMatches, planCard } from "./planner.js";
import { similarPapers } from "./search.js";
import { FACETS } from "./state.js";

const FACET_TITLES = { stage: "Stage", family: "Method family", model: "Model", target: "What is forgotten",
  application: "Application", risk: "Risk or open challenge", kind: "Type", year: "Year", review: "Status", source: "Source" };
const SIDES = { forget: "Forgetting", retain: "Retained utility", robustness: "Robustness", cost: "Cost" };
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

export const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
export const shortCite = (p) => `${p.name ? `${p.name}, ` : ""}${p.authors[0] ? p.authors[0].split(" ").pop() : "Unknown"} et al., ${p.year}`;
const label = (ctx, facet, v) => ctx.labels[facet]?.[v] ?? v;
const citeButtons = (ctx, keys) => keys.filter((k) => ctx.BY_KEY.has(k))
  .map((k) => `<button type="button" class="link" data-open="${esc(k)}">${esc(shortCite(ctx.BY_KEY.get(k)))}</button>`).join("; ");

function bindOpen(ctx, root) {
  $$("[data-open]", root).forEach((b) => b.addEventListener("click", (e) => { e.stopPropagation(); ctx.open(b.dataset.open); }));
}

export function highlight(text, terms) {
  let out = esc(text);
  for (const t of terms.filter((x) => x.length > 2)) {
    out = out.replace(new RegExp(`\\b(${t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\w*)`, "gi"), "<mark>$1</mark>");
  }
  return out;
}

export function renderMath(root) {
  for (const el of $$("[data-tex]", root)) {
    if (window.katex) window.katex.render(el.dataset.tex, el, { displayMode: true, throwOnError: false });
    else el.textContent = el.dataset.tex;
  }
}

export function renderFilters(ctx) {
  const host = $("#filters");
  const wasOpen = new Set($$("details[open]", host).map((d) => d.dataset.facet));
  const s = ctx.state;
  const base = ctx.queryKeys ? ctx.papers.filter((p) => ctx.queryKeys.has(p.key)) : ctx.papers;
  const parts = [`<div class="filters-head"><h2>Filter</h2><button type="button" class="link" data-clear>Clear</button></div>`];
  for (const facet of FACETS) {
    const others = { ...s, filters: { ...s.filters, [facet]: [] } };
    const counts = new Map();
    for (const p of base) if (paperMatches(p, ctx.survey, others)) for (const v of facetValues(p, facet)) counts.set(v, (counts.get(v) || 0) + 1);
    const values = [...new Set(ctx.papers.flatMap((p) => facetValues(p, facet)))];
    if (!values.length) continue;
    const order = { stage: ctx.survey.stages, family: ctx.survey.families }[facet]?.map((x) => x.id);
    values.sort(facet === "year" ? (a, b) => b.localeCompare(a) : order ? (a, b) => order.indexOf(a) - order.indexOf(b)
      : (a, b) => (counts.get(b) || 0) - (counts.get(a) || 0) || label(ctx, facet, a).localeCompare(label(ctx, facet, b)));
    const sel = new Set(s.filters[facet] || []);
    const open = wasOpen.has(facet) || sel.size > 0 || facet === "stage";
    parts.push(`<details data-facet="${facet}" ${open ? "open" : ""}><summary>${FACET_TITLES[facet]}</summary><ul>${values.map((v) => {
      const n = counts.get(v) || 0;
      return `<li class="${n || sel.has(v) ? "" : "zero"}"><label><input type="checkbox" data-facet="${facet}" value="${esc(v)}"${sel.has(v) ? " checked" : ""}><span>${esc(label(ctx, facet, v))}</span><span class="n">${n}</span></label></li>`;
    }).join("")}</ul></details>`);
  }
  parts.push(`<div class="filters-done"><button type="button" class="primary" data-done>Show ${ctx.results.length} papers</button></div>`);
  host.innerHTML = parts.join("");
  $$("input[data-facet]", host).forEach((input) => input.addEventListener("change", () => {
    const cur = new Set(ctx.state.filters[input.dataset.facet] || []);
    if (input.checked) cur.add(input.value);
    else cur.delete(input.value);
    const filters = { ...ctx.state.filters, [input.dataset.facet]: [...cur] };
    if (!cur.size) delete filters[input.dataset.facet];
    ctx.set({ filters });
  }));
  $("[data-clear]", host).addEventListener("click", () => ctx.set({ filters: {} }));
  $("[data-done]", host).addEventListener("click", () => ctx.toggleFilters(false));
}

function paperItem(ctx, p) {
  const L = ctx.labels;
  const name = p.name && !p.title.toLowerCase().startsWith(p.name.toLowerCase()) ? `${esc(p.name)}: ` : "";
  const who = p.authors.length ? `${esc(p.authors[0].split(" ").pop())}${p.authors.length > 1 ? " et al." : ""}, ` : "";
  const where = p.stage ? `<span class="stage-chip" style="--stage: var(--${esc(p.stage)})">${esc(L.stage[p.stage])}</span>` : `<span>${esc(L.kind[p.kind])}</span>`;
  const fam = p.family ? `<span>${esc(L.family[p.family])}</span>` : "";
  const models = (p.added?.model || []).map((m) => `<span class="tag-added" title="Added, not from the survey">${esc(L.model[m])}</span>`).join("");
  return `<li class="paper" tabindex="0" data-key="${esc(p.key)}" aria-selected="${ctx.state.paper === p.key}">
    <p class="paper-title">${name}${highlight(p.title, ctx.terms)}</p>
    <p class="paper-meta">${who}${esc(p.venue || "")} ${p.year}${p.in_survey ? "" : ", only in the list"}</p>
    <p class="paper-tags">${where}${fam}${models}</p></li>`;
}

export function renderPapers(ctx) {
  const list = ctx.results;
  $("#result-count").innerHTML = `<strong>${list.length}</strong> of ${ctx.papers.length} papers`;
  $("#sort").value = ctx.state.sort;
  const ol = $("#paper-list");
  ol.innerHTML = list.length ? list.map((p) => paperItem(ctx, p)).join("")
    : `<li class="empty-state"><strong>No paper matches.</strong>Remove a filter, choose "anything" in the sentence above, or try fewer words.</li>`;
  $$(".paper", ol).forEach((li) => {
    li.addEventListener("click", () => ctx.open(li.dataset.key));
    li.addEventListener("keydown", (e) => { if (e.key === "Enter") ctx.open(li.dataset.key); });
  });
  renderFilters(ctx);
  const n = Object.values(ctx.state.filters).reduce((a, v) => a + v.length, 0);
  $(".filters-toggle").textContent = n ? `Filters (${n})` : "Filters";
}

export function renderDrawer(ctx) {
  const drawer = $("#drawer");
  const p = ctx.BY_KEY.get(ctx.state.paper);
  if (!p) { drawer.hidden = true; return; }
  const L = ctx.labels;
  const authors = p.authors.length > 6 ? `${p.authors.slice(0, 6).join(", ")}, and ${p.authors.length - 6} more` : p.authors.join(", ");
  const links = [["paper", "Paper"], ["arxiv", "arXiv"]].filter(([k]) => /^https:\/\//.test(p.links[k] || "") && !(k === "arxiv" && p.links.arxiv === p.links.paper))
    .map(([k, t]) => `<a href="${esc(p.links[k])}" target="_blank" rel="noopener">${t}</a>`).join("");
  const rows = p.family ? [["Method family", `${esc(L.stage[p.stage])}, ${esc(L.family[p.family])}`]] : [];
  for (const [group, title] of [["target", "What it forgets"], ["application", "Application"], ["metric", "Metrics it reports"],
    ["dataset", "Datasets it uses"], ["challenge", "Open challenge"]]) {
    const vals = (p.tags[group] || []).map((v) => esc(L[group]?.[v] ?? v));
    if (vals.length) rows.push([title, vals.join(", ")]);
  }
  const added = Object.entries(p.added || {}).flatMap(([g, vs]) => vs.map((v) => `<span class="tag-added">${esc(L[g]?.[v] ?? v)}</span>`));
  const sim = similarPapers(ctx.emb, p.key).map((k) => ctx.BY_KEY.get(k)).filter(Boolean);
  const simText = ctx.emb ? "No similar papers found." : "Similar papers appear when the paper embeddings finish loading.";
  $("#drawer-body").innerHTML = `
    <h2>${p.name && !p.title.toLowerCase().startsWith(p.name.toLowerCase()) ? `${esc(p.name)}: ` : ""}${esc(p.title)}</h2>
    <p class="muted">${esc(authors)}${authors ? "<br>" : ""}${esc(p.venue || "")} ${p.year}${p.peer_reviewed ? "" : ", preprint"}</p>
    <p class="links">${links}</p>
    ${rows.length ? `<h3>Where the survey discusses it</h3><dl>${rows.map(([t, v]) => `<dt>${t}</dt><dd>${v}</dd>`).join("")}</dl>`
      : `<p class="muted">${p.in_survey ? "The survey cites this paper but does not place it in a table or family." : "This paper is in the list but not discussed in the survey."}</p>`}
    ${added.length ? `<h3>Added tags</h3><p>${added.join(" ")}</p><p class="muted">Added by the maintainers, not from the survey.</p>` : ""}
    <h3>Abstract</h3>${p.abstract ? `<p class="abstract">${esc(p.abstract)}</p>` : `<p class="muted">No abstract was found. Follow the paper link to read it.</p>`}
    <h3>Similar papers</h3>${sim.length ? `<ul class="similar">${sim.map((x) => `<li><button type="button" class="link" data-open="${esc(x.key)}">${esc(x.title)}</button> <span class="muted">${x.year}</span></li>`).join("")}</ul>` : `<p class="muted">${simText}</p>`}
    ${p.bibtex ? `<h3>BibTeX <button type="button" class="link" data-copy>Copy</button></h3><pre class="bibtex">${esc(p.bibtex)}</pre>` : ""}`;
  bindOpen(ctx, $("#drawer-body"));
  $("[data-copy]", drawer)?.addEventListener("click", async (e) => {
    try { await navigator.clipboard.writeText(p.bibtex); e.target.textContent = "Copied"; }
    catch { e.target.textContent = "Select the text to copy"; }
    setTimeout(() => { e.target.textContent = "Copy"; }, 1600);
  });
  const wasHidden = drawer.hidden;
  drawer.hidden = false;
  if (wasHidden) $("[data-close-drawer]", drawer).focus({ preventScroll: true });
}

function benchRows(list) {
  let group = null;
  let out = "";
  for (const b of list) {
    if (b.group !== group) { group = b.group; out += `<tr class="group-row"><td colspan="6">${esc(group)}</td></tr>`; }
    out += `<tr><td><button type="button" class="link" data-open="${esc(b.key)}">${esc(b.name)}</button></td><td>${esc(b.modality)}</td>
      <td>${esc(b.target)}</td><td>${esc(b.task)}</td><td>${esc(b.stats)}</td><td>${esc(b.objective)}</td></tr>`;
  }
  return out || `<tr><td colspan="6" class="muted">No benchmark in the survey covers this combination yet.</td></tr>`;
}

export function renderDatasets(ctx) {
  const host = $("#view-datasets");
  const plan = planCard(ctx.survey, ctx.state);
  const filtered = ctx.state.target !== "any" || ctx.state.model !== "any";
  const modalities = [...new Set(ctx.survey.datasets.map((d) => d.modality))];
  const mod = ctx.datasetModality || "all";
  const ds = plan.datasets.filter((d) => mod === "all" || d.modality === mod);
  let body = "";
  for (const setting of ctx.survey.settings) {
    const rows = ds.filter((d) => d.setting === setting.name);
    if (!rows.length) continue;
    body += `<tr class="group-row"><td colspan="4">${esc(setting.name)}</td></tr>` + rows.map((d) =>
      `<tr id="ds-${esc(d.id)}"><td>${esc(d.name)}</td><td>${esc(d.modality)}</td><td>${esc(d.size)}</td><td>${citeButtons(ctx, d.used_in) || "None in this list"}</td></tr>`).join("");
  }
  host.innerHTML = `<div class="view-intro"><h2>Datasets and benchmarks</h2>
      <p class="muted">${filtered ? "Filtered by the sentence above. " : ""}From the survey's dataset tables and benchmark table.</p></div>
    <label class="inline">Modality <select id="ds-modality"><option value="all">All</option>${modalities.map((m) => `<option${m === mod ? " selected" : ""}>${esc(m)}</option>`).join("")}</select></label>
    <h3>Datasets (${ds.length})</h3>
    <div class="table-wrap"><table class="data-table"><thead><tr><th scope="col">Dataset</th><th scope="col">Modality</th><th scope="col">Size</th><th scope="col">Used in</th></tr></thead>
      <tbody>${body || `<tr><td colspan="4" class="muted">No dataset in the survey matches this combination.</td></tr>`}</tbody></table></div>
    <h3>Benchmarks (${plan.benchmarks.length})</h3>
    <div class="table-wrap"><table class="data-table"><thead><tr><th scope="col">Benchmark</th><th scope="col">Model</th><th scope="col">What is forgotten</th>
      <th scope="col">Task</th><th scope="col">Scale</th><th scope="col">Goal</th></tr></thead><tbody>${benchRows(plan.benchmarks)}</tbody></table></div>`;
  $("#ds-modality", host).addEventListener("change", (e) => { ctx.datasetModality = e.target.value; renderDatasets(ctx); });
  bindOpen(ctx, host);
}

export function renderEvaluation(ctx) {
  const host = $("#view-evaluation");
  const plan = planCard(ctx.survey, ctx.state);
  const shown = new Set(Object.values(plan.metrics).flat().map((m) => m.id));
  host.innerHTML = `<div class="view-intro"><h2>Evaluation</h2><p class="muted">The six dimensions and the metrics the survey reviews.
      ${ctx.state.model !== "any" ? "Metrics that do not apply to the chosen model are hidden." : ""}</p></div>` +
    ctx.survey.dimensions.map((d) => {
      const ms = d.metrics.filter((m) => shown.has(m.id));
      if (!ms.length) return "";
      return `<section><h3>${esc(d.name)}<span class="side">${SIDES[d.side]}</span></h3><div class="metric-grid">${ms.map((m) => {
        const cites = citeButtons(ctx, m.keys);
        return `<article class="metric" id="metric-${esc(m.id)}"><h4>${esc(m.name)}</h4><p>${esc(m.description)}</p>
          ${m.formula ? `<div class="formula" data-tex="${esc(m.formula)}"></div>` : ""}
          <p class="muted">${cites ? `Reported in: ${cites}` : "No paper in this list is cited for it."}</p></article>`;
      }).join("")}</div></section>`;
    }).join("");
  renderMath(host);
  bindOpen(ctx, host);
}

export function renderGaps(ctx) {
  const host = $("#view-gaps");
  const g = gapMatrix(ctx.survey, ctx.papers, ctx.state);
  const expanded = (ctx.gapExpanded ??= new Set());
  const cell = (row, kind, m) => {
    const n = row.cells[m];
    const cls = n ? `b${Math.min(5, Math.floor(Math.log2(n)))}` : "zero";
    return `<td class="cell ${cls}"><button type="button" data-kind="${kind}" data-id="${esc(row.id)}" data-model="${esc(m)}"
      aria-label="${esc(row.name)}, ${esc(ctx.labels.model[m])}: ${n} papers">${n}</button></td>`;
  };
  const rows = g.rows.map((r) => `<tr><th scope="row"><button type="button" class="link" data-expand="${esc(r.id)}" aria-expanded="${expanded.has(r.id)}">${esc(r.name)}</button></th>${g.models.map((m) => cell(r, "stage", m)).join("")}</tr>` +
    (expanded.has(r.id) ? r.families.map((f) => `<tr class="family-row"><th scope="row">${esc(f.name)}</th>${g.models.map((m) => cell(f, "family", m)).join("")}</tr>`).join("") : "")).join("");
  host.innerHTML = `<div class="view-intro"><h2>Gap map</h2><p class="muted">Papers per pipeline stage and model type. Select a stage name to see its families.
      Select a cell to list its papers. Hatched cells have no paper yet. Model types are partly added by the maintainers, not stated in the survey.</p></div>
    <div class="table-wrap"><table class="data-table gap-table"><thead><tr><th scope="col">Stage</th>${g.models.map((m) => `<th scope="col">${esc(ctx.labels.model[m])}</th>`).join("")}</tr></thead>
      <tbody>${rows}</tbody></table></div>
    <div class="gap-note" id="gap-note" aria-live="polite"></div>`;
  $$("[data-expand]", host).forEach((b) => b.addEventListener("click", () => {
    const id = b.dataset.expand;
    if (expanded.has(id)) expanded.delete(id);
    else expanded.add(id);
    renderGaps(ctx);
  }));
  $$("td.cell button", host).forEach((b) => b.addEventListener("click", () => {
    const { kind, id, model } = b.dataset;
    if (Number(b.textContent) > 0) return ctx.set({ tab: "papers", stage: null, filters: { [kind]: [id], model: [model] } });
    const c = ctx.survey.challenges.find((x) => x.id === gapLink(ctx.survey, model));
    const cites = citeButtons(ctx, c.keys);
    $("#gap-note", host).innerHTML = `<p><strong>No paper here yet.</strong> The survey discusses this kind of gap under "${esc(c.name)}"${cites ? `, citing ${cites}` : ""}.</p>`;
    bindOpen(ctx, $("#gap-note", host));
  }));
}
