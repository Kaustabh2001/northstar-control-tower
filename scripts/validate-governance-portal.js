const fs = require("fs");
const path = require("path");

const projectRoot = path.resolve(__dirname, "..");
const portalPath = path.join(projectRoot, "docs", "ai-governance-control-tower.html");
const source = fs.readFileSync(portalPath, "utf8");

const failures = [];
const requiredViews = [
  "overview",
  "inventory",
  "lifecycle",
  "runtime",
  "security",
];

for (const view of requiredViews) {
  if (!source.includes(`id="${view}"`)) {
    failures.push(`Missing view: ${view}`);
  }
  if (!source.includes(`data-view="${view}"`)) {
    failures.push(`Missing navigation control: ${view}`);
  }
}

for (const removedView of ["cases", "value", "architecture"]) {
  if (source.includes(`data-view="${removedView}"`)) {
    failures.push(`Removed product view is still navigable: ${removedView}`);
  }
}

const requiredInventoryTypes = [
  "AI system",
  "Agentic workflow",
  "Agent",
  "Model",
  "Prompt",
  "Dataset",
  "Knowledge index",
  "MCP server",
];
for (const type of requiredInventoryTypes) {
  if (!source.includes(`data-inventory-type="${type}"`)) {
    failures.push(`Missing inventory sidebar option: ${type}`);
  }
}

for (const requiredRuntimeControl of [
  'data-run-filter="Running"',
  'data-run-filter="Human review"',
  'data-run-filter="Failed"',
  'class="button small accent run-review"',
  'class="button small run-trace"',
]) {
  if (!source.includes(requiredRuntimeControl)) {
    failures.push(`Missing runtime control: ${requiredRuntimeControl}`);
  }
}

const ids = [...source.matchAll(/id="([^"]+)"/g)].map((match) => match[1]);
const duplicates = [...new Set(ids.filter((id, index) => ids.indexOf(id) !== index))];
if (duplicates.length) {
  failures.push(`Duplicate element IDs: ${duplicates.join(", ")}`);
}

const scriptBlocks = [...source.matchAll(/<script>([\s\S]*?)<\/script>/g)];
if (scriptBlocks.length !== 1) {
  failures.push(`Expected one inline script, found ${scriptBlocks.length}`);
} else {
  try {
    new Function(scriptBlocks[0][1]);
  } catch (error) {
    failures.push(`JavaScript syntax error: ${error.message}`);
  }
}

const pairedTags = ["section", "article", "aside", "nav", "table"];
for (const tag of pairedTags) {
  const opens = (source.match(new RegExp(`<${tag}\\b`, "g")) || []).length;
  const closes = (source.match(new RegExp(`</${tag}>`, "g")) || []).length;
  if (opens !== closes) {
    failures.push(`Unbalanced <${tag}> tags: ${opens} opening, ${closes} closing`);
  }
}

if (/â|Ã|�/.test(source)) {
  failures.push("Possible mojibake detected");
}

if (failures.length) {
  console.error("Governance portal validation failed:");
  failures.forEach((failure) => console.error(`- ${failure}`));
  process.exit(1);
}

console.log("Governance portal validation passed.");
console.log(`- ${requiredViews.length} interactive views`);
console.log(`- ${ids.length} unique element IDs`);
console.log("- Inline JavaScript syntax valid");
console.log("- Required structural tags balanced");
