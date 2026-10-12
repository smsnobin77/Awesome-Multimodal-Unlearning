import { test } from "node:test";
import assert from "node:assert/strict";
import { activeChips, defaultState, parseHash, toHash } from "../../docs/explorer/state.js";
import { DATA } from "./data.mjs";

test("round trip keeps every field", () => {
  const p = DATA.papers[0];
  const s = { ...defaultState(), tab: "gaps", query: "erase nudity", target: "nsfw", model: "image-diffusion",
              constraint: "no-retraining", stage: "decoding-time", sort: "newest", paper: p.key,
              filters: { kind: [p.kind] } };
  assert.deepEqual(parseHash(toHash(s), DATA), s);
});

test("parseHash drops unknown values", () => {
  const s = parseHash("#nope?paper=zzz&target=moon&stage=x&model=vlm&f-kind=bogus&f-model=nope&sort=up", DATA);
  assert.deepEqual(s, { ...defaultState(), model: "vlm" });
});

test("default state has an empty hash", () => {
  assert.equal(toHash(defaultState()), "#papers");
});

const LABELS = { target: { identity: "Face or identity" }, model: { audio: "Audio or speech" },
  constraint: { "keep-weights": "Changing the base weights" }, stage: { "decoding-time": "Decoding-time" }, kind: { method: "Method" } };

test("every planner choice becomes a removable chip", () => {
  const s = { ...defaultState(), target: "identity", model: "audio", constraint: "keep-weights", stage: "decoding-time",
              filters: { kind: ["method"] }, query: "voice" };
  const chips = activeChips(s, LABELS);
  assert.deepEqual(chips.map((c) => c.text), ["Forget: Face or identity", "Model: Audio or speech", "Without: Changing the base weights",
    "Stage: Decoding-time", "Method", 'Search: "voice"']);
  assert.deepEqual(chips[0].patch, { target: "any" });
  assert.deepEqual(chips[2].patch, { constraint: "none" });
  assert.deepEqual(chips[4].patch, { filters: {} });
});

test("the default state has no chips", () => {
  assert.deepEqual(activeChips(defaultState(), LABELS), []);
});

test("risk filters survive the URL", () => {
  const key = DATA.papers.find((p) => (p.tags.challenge || []).length).tags.challenge[0];
  assert.deepEqual(parseHash(`#papers?f-risk=${key}`, DATA).filters, { risk: [key] });
});
