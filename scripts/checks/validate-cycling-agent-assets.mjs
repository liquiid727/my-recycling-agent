/*
 * CN: 骑行 agent 资产校验脚本，验证四层资产索引、golden dataset 基线和仓库命名不再漂移。
 * EN: Cycling-agent asset validator that checks the four-layer asset index, golden-dataset baseline, and repository naming drift.
 */

import { access, readFile, readdir } from "node:fs/promises";

const requiredFiles = [
  "specs/current/agent-asset-map.md",
  "specs/current/agent-asset-index.json",
  ".rules/project.md",
  ".rules/rule-map.yaml",
  ".agents/manifest.yaml",
  "tests/plans/cycling-agent-mvp.test-plan.json",
  "tests/scenarios/cycling-agent-golden-dataset.yaml",
  "tests/results/cycling-agent-mvp.scenario-result.example.json",
  "products/cycling-agent/data/hangzhou_routes.json",
  "products/cycling-agent/data/hangzhou_nearby_destinations.json",
  "products/cycling-agent/data/hangzhou_trip_templates.json",
];

function assertMatch(source, pattern, message) {
  if (!pattern.test(source)) {
    throw new Error(message);
  }
}

function assertIncludes(list, value, message) {
  if (!list.includes(value)) {
    throw new Error(message);
  }
}

for (const path of requiredFiles) {
  await access(path);
}

const assetMap = await readFile("specs/current/agent-asset-map.md", "utf8");
for (const heading of ["Domain Map", "Rule Library", "Knowledge Base", "Golden Dataset"]) {
  assertMatch(assetMap, new RegExp(heading), `asset map missing heading ${heading}`);
}

const assetIndex = JSON.parse(await readFile("specs/current/agent-asset-index.json", "utf8"));
assertMatch(JSON.stringify(assetIndex), /"product":"cycling-agent"/, "asset index must target cycling-agent");
assertIncludes(
  assetIndex.layers.map((layer) => layer.id),
  "golden_dataset",
  "asset index missing golden_dataset layer",
);

const rulesProject = await readFile(".rules/project.md", "utf8");
assertMatch(rulesProject, /Cycling-Agent Project Rules/, "project rules title drifted");
assertMatch(rulesProject, /products\/cycling-agent\//, "project rules must point to real product path");

const manifest = await readFile(".agents/manifest.yaml", "utf8");
assertMatch(manifest, /project: cycling-agent-docs/, "manifest project drifted");
assertMatch(manifest, /products\/cycling-agent\/frontend\//, "manifest should point UI roles at real frontend");

const testPlan = JSON.parse(await readFile("tests/plans/cycling-agent-mvp.test-plan.json", "utf8"));
assertMatch(JSON.stringify(testPlan), /"specId":"cycling-agent-mvp"/, "test plan specId drifted");
assertIncludes(
  testPlan.endpoints.map((endpoint) => endpoint.path),
  "/api/v1/ride/plan",
  "test plan must cover ride plan endpoint",
);

const goldenDataset = await readFile("tests/scenarios/cycling-agent-golden-dataset.yaml", "utf8");
for (const caseId of [
  "city-clarify-evening-vague",
  "city-success-binjing-evening",
  "weekend-success-qiandaohu-two-day",
]) {
  assertMatch(goldenDataset, new RegExp(`case_id: ${caseId}`), `golden dataset missing case ${caseId}`);
}

const scenarioResult = JSON.parse(
  await readFile("tests/results/cycling-agent-mvp.scenario-result.example.json", "utf8"),
);
assertMatch(JSON.stringify(scenarioResult), /"specId":"cycling-agent-mvp"/, "scenario result specId drifted");

const testPlanDir = await readdir("tests/plans");
if (testPlanDir.includes("reward-order.test-plan.json")) {
  throw new Error("obsolete reward-order test plan still exists");
}

console.log("cycling-agent-assets-validated");
