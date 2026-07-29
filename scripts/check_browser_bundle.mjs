import { readFileSync, statSync } from "node:fs";
import { gzipSync } from "node:zlib";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const distRoot = resolve(root, "dist");
const manifestPath = resolve(distRoot, ".vite", "manifest.json");
const budgetPath = resolve(
  root,
  "data",
  "validation",
  "browser_bundle_budget.v1.json"
);
const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
const budget = JSON.parse(readFileSync(budgetPath, "utf8"));

if (
  budget.schema_version !== "cell.browser-bundle-budget.v1" ||
  budget.scientific_authority !== false
) {
  throw new Error("browser bundle budget contract is invalid");
}

const entries = Object.entries(manifest);
const entryMatches = entries.filter(([, record]) => record.isEntry === true);
if (entryMatches.length !== 1) {
  throw new Error(`expected one browser entry chunk, found ${entryMatches.length}`);
}

const [entryKey] = entryMatches[0];
const initialKeys = new Set();
const visitInitial = (key) => {
  if (initialKeys.has(key)) return;
  const record = manifest[key];
  if (!record) throw new Error(`manifest import is missing: ${key}`);
  initialKeys.add(key);
  for (const importedKey of record.imports ?? []) visitInitial(importedKey);
};
visitInitial(entryKey);

const fileMeasurement = (relativePath) => {
  const absolutePath = resolve(distRoot, relativePath);
  const rawBytes = statSync(absolutePath).size;
  const gzipBytes = gzipSync(readFileSync(absolutePath), { level: 9 }).length;
  return { relativePath, rawBytes, gzipBytes };
};

const initialJs = [...initialKeys]
  .map((key) => fileMeasurement(manifest[key].file))
  .sort((left, right) => left.relativePath.localeCompare(right.relativePath));
const initialCssFiles = new Set();
for (const key of initialKeys) {
  for (const cssFile of manifest[key].css ?? []) initialCssFiles.add(cssFile);
}
const initialCss = [...initialCssFiles]
  .map(fileMeasurement)
  .sort((left, right) => left.relativePath.localeCompare(right.relativePath));

const sum = (rows, field) =>
  rows.reduce((total, row) => total + row[field], 0);
const measurements = {
  initial_js_chunk_count: initialJs.length,
  initial_js_raw_bytes: sum(initialJs, "rawBytes"),
  initial_js_gzip_bytes: sum(initialJs, "gzipBytes"),
  largest_initial_js_chunk_raw_bytes: Math.max(
    ...initialJs.map((row) => row.rawBytes)
  ),
  initial_css_raw_bytes: sum(initialCss, "rawBytes"),
  initial_css_gzip_bytes: sum(initialCss, "gzipBytes")
};

const verifiedBuild = budget.last_verified_build;
if (!verifiedBuild || typeof verifiedBuild !== "object") {
  throw new Error("browser bundle budget requires a last_verified_build ledger");
}
for (const [field, observed] of Object.entries(measurements)) {
  if (verifiedBuild[field] !== observed) {
    throw new Error(
      `browser bundle verified-build ledger is stale: ${field} ` +
      `${verifiedBuild[field]} != ${observed}`
    );
  }
}

const requiredDeferred = budget.required_deferred_entries;
if (
  !Array.isArray(requiredDeferred) ||
  !requiredDeferred.every((source) => typeof source === "string")
) {
  throw new Error("required_deferred_entries must contain source strings");
}
for (const source of requiredDeferred) {
  const record = manifest[source];
  if (!record?.isDynamicEntry) {
    throw new Error(`required deferred entry is not dynamic: ${source}`);
  }
  if (initialKeys.has(source)) {
    throw new Error(`deferred entry escaped into the initial graph: ${source}`);
  }
}
if (
  verifiedBuild.required_deferred_entry_count !== requiredDeferred.length ||
  verifiedBuild.budget_gate_passed !== true
) {
  throw new Error("browser bundle verified-build deferred ledger is stale");
}

const limits = budget.limits;
const checks = [
  [
    "initial JS raw bytes",
    measurements.initial_js_raw_bytes,
    limits.maximum_initial_js_raw_bytes
  ],
  [
    "initial JS gzip bytes",
    measurements.initial_js_gzip_bytes,
    limits.maximum_initial_js_gzip_bytes
  ],
  [
    "largest initial JS chunk",
    measurements.largest_initial_js_chunk_raw_bytes,
    limits.maximum_initial_js_chunk_raw_bytes
  ],
  [
    "initial CSS raw bytes",
    measurements.initial_css_raw_bytes,
    limits.maximum_initial_css_raw_bytes
  ]
];
for (const [label, observed, maximum] of checks) {
  if (!Number.isInteger(maximum) || maximum <= 0) {
    throw new Error(`invalid browser bundle budget: ${label}`);
  }
  if (observed > maximum) {
    throw new Error(`${label} ${observed} exceeds budget ${maximum}`);
  }
}

process.stdout.write(
  `${JSON.stringify(
    {
      schema_version: budget.schema_version,
      measurements,
      limits,
      deferred_entry_count: requiredDeferred.length,
      initial_js_files: initialJs
    },
    null,
    2
  )}\n`
);
