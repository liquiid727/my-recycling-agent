/*
 * CN: 骑行 agent 资产校验测试，确保脚本关注的关键层级和文件不会回退。
 * EN: Cycling-agent asset validation tests to keep core layer and file checks from regressing.
 */

import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

async function read(path) {
  return readFile(new URL(`../../${path}`, import.meta.url), "utf8");
}

test("asset index covers the four cycling-agent layers", async () => {
  const assetIndex = JSON.parse(await read("specs/current/agent-asset-index.json"));
  const layerIds = assetIndex.layers.map((layer) => layer.id);

  assert.deepEqual(layerIds, [
    "domain_map",
    "rule_library",
    "knowledge_base",
    "golden_dataset",
  ]);
});

test("golden test plan points at real cycling-agent endpoints", async () => {
  const testPlan = JSON.parse(await read("tests/plans/cycling-agent-mvp.test-plan.json"));
  const endpoints = testPlan.endpoints.map((endpoint) => endpoint.path);

  assert.ok(endpoints.includes("/api/v1/ride/plan"));
  assert.ok(endpoints.includes("/api/v1/ride/chat/turn"));
  assert.ok(endpoints.includes("/api/v1/admin/planning-audit/{request_no}"));
});

test("golden dataset and result example use the cycling-agent spec id", async () => {
  const goldenDataset = await read("tests/scenarios/cycling-agent-golden-dataset.yaml");
  const resultExample = JSON.parse(
    await read("tests/results/cycling-agent-mvp.scenario-result.example.json"),
  );

  assert.match(goldenDataset, /spec_id: cycling-agent-mvp/);
  assert.equal(resultExample.specId, "cycling-agent-mvp");
});
