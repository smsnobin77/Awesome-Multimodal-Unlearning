import { test } from "node:test";
import assert from "node:assert/strict";
import { gapMatrix, paperMatches, planCard, stageCounts, stageFit } from "../../docs/explorer/planner.js";
import { defaultState } from "../../docs/explorer/state.js";
import { DATA } from "./data.mjs";

const { survey, papers } = DATA;
const state = (patch = {}) => ({ ...defaultState(), ...patch });

test("stage fit follows the survey rules", () => {
  assert.equal(stageFit(survey, "decoding-time", "keep-weights").fit, "fits");
  assert.equal(stageFit(survey, "training-time", "keep-weights").fit, "no");
  assert.equal(stageFit(survey, "training-free", "keep-weights").fit, "partly");
  assert.equal(stageFit(survey, "training-time", "none").fit, "fits");
});

test("default counts cover every placed paper", () => {
  const counts = stageCounts(survey, papers, state());
  assert.equal(Object.values(counts).reduce((a, b) => a + b, 0), papers.filter((p) => p.stage).length);
});

test("no retraining removes training-time methods but keeps benchmarks", () => {
  const s = state({ constraint: "no-retraining" });
  assert.ok(!papers.some((p) => p.stage === "training-time" && paperMatches(p, survey, s)));
  assert.ok(papers.some((p) => p.kind === "benchmark" && paperMatches(p, survey, s)));
});

test("plan for identity and audio", () => {
  const ids = planCard(survey, state({ target: "identity" }));
  assert.ok(ids.datasets.some((d) => d.name === "CelebA"));
  assert.ok(ids.benchmarks.some((b) => b.name === "CLEAR"));
  const audio = planCard(survey, state({ model: "audio" }));
  assert.ok(audio.metrics.forget.some((m) => m.id === "sim"));
  assert.ok(!audio.metrics.retain.some((m) => m.id === "fid"));
});

test("empty plan does not throw", () => {
  const s = state({ target: "voice", model: "image-diffusion", constraint: "keep-weights" });
  const plan = planCard(survey, s);
  assert.equal(plan.datasets.length, 0);
  assert.doesNotThrow(() => stageCounts(survey, papers, s));
});

test("gap matrix has every stage and family", () => {
  const g = gapMatrix(survey, papers);
  assert.equal(g.rows.length, 5);
  assert.equal(g.rows.flatMap((r) => r.families).length, 12);
  assert.ok(g.rows.every((r) => g.models.every((m) => Number.isInteger(r.cells[m]))));
});
