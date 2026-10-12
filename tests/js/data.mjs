import { readFileSync } from "node:fs";

const text = readFileSync(new URL("../../docs/explorer/data.js", import.meta.url), "utf8");
export const DATA = JSON.parse(text.slice(text.indexOf("{"), text.lastIndexOf("}") + 1));
