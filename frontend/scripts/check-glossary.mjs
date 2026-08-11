import { readFileSync } from "node:fs";

const source = readFileSync(new URL("../app/fieldGlossary.zh-TW.ts", import.meta.url), "utf8");
const glossaryBlock = source.match(/export const fieldGlossary = \{([\s\S]*?)\n\} satisfies/);
const columnsBlock = source.match(/export const visibleAnalyticalColumns = \[([\s\S]*?)\] as const/);
if (!glossaryBlock || !columnsBlock) throw new Error("Glossary registry structure is missing");
const keys = new Set([...glossaryBlock[1].matchAll(/^\s{2}([a-z0-9_]+):/gm)].map((match) => match[1]));
const columns = [...columnsBlock[1].matchAll(/"([a-z0-9_]+)"/g)].map((match) => match[1]);
const missing = columns.filter((column) => !keys.has(column));
if (missing.length) throw new Error(`Missing zh-TW glossary definitions: ${missing.join(", ")}`);
console.log(`Glossary completeness: ${columns.length} visible analytical columns, ${keys.size} documented fields`);
