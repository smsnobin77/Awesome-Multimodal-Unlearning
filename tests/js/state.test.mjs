import { test } from "node:test";
import assert from "node:assert/strict";
import { defaultState, parseHash, toHash } from "../../docs/explorer/state.js";
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
