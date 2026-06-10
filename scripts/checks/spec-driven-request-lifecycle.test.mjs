/*
 * CN: SpecOS 生命周期测试，校验 agent manifest、workflow 和样例 change package 的契约。
 * EN: SpecOS lifecycle test that validates the agent manifest, workflow, and example change-package contract.
 */

import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

async function read(path) {
  return readFile(new URL(`../../${path}`, import.meta.url), "utf8");
}

test("manifest declares the lifecycle routing roles and reviewer gate outputs", async () => {
  const manifest = await read(".agents/manifest.yaml");

  for (const roleId of [
    "spec-draft-agent:",
    "architecture-agent:",
    "spec-agent:",
    "frontend-execution-agent:",
    "backend-execution-agent:",
    "migration-execution-agent:",
  ]) {
    assert.match(manifest, new RegExp(`\\n  ${roleId}`), `missing role ${roleId}`);
  }

  assert.match(manifest, /implementation_gate/, "reviewer must expose implementation gate mode");
  assert.match(manifest, /final_gate/, "reviewer must expose final gate mode");
  assert.match(manifest, /activation_conditions:/, "ui-design-agent must declare activation conditions");
});

test("workflow defines the lifecycle stages, states, and gate routing", async () => {
  const workflow = await read(".specos/workflows/spec-driven-default.yaml");

  for (const stageId of [
    "request-intake",
    "draft-normalize",
    "architecture-review",
    "ui-design-review",
    "spec-change-create",
    "execution-routing",
    "implementation-execution",
    "implementation-review-gate",
    "independent-test-planning",
    "independent-test-execution",
    "final-review-gate",
    "acceptance-promote-archive",
  ]) {
    assert.match(workflow, new RegExp(`id: ${stageId}`), `missing stage ${stageId}`);
  }

  for (const state of [
    "drafted",
    "architected",
    "designed",
    "changed",
    "executing",
    "implementation-reviewed",
    "test-ready",
    "tested",
    "final-reviewed",
    "accepted",
    "promoted",
    "archived",
    "blocked",
  ]) {
    assert.match(workflow, new RegExp(`- ${state}\\b`), `missing change state ${state}`);
  }

  assert.match(workflow, /route_key: frontend/, "frontend route missing");
  assert.match(workflow, /route_key: backend/, "backend route missing");
  assert.match(workflow, /route_key: migration/, "migration route missing");
  assert.match(workflow, /run: "node scripts\/checks\/validate-spec-driven-lifecycle\.mjs"/, "workflow must execute lifecycle validation");
});

test("workflow assets and example change package reflect the new lifecycle contract", async () => {
  const workflowDoc = await read("ai/workflows/spec-driven-request-lifecycle.md");
  const changeSpec = await read("specs/changes/spec-change-agent-workflow/spec.md");
  const changeArchitecture = await read("specs/changes/spec-change-agent-workflow/architecture-review.md");
  const changeDesign = await read("specs/changes/spec-change-agent-workflow/design-review.md");
  const executionPlan = await read("specs/changes/spec-change-agent-workflow/execution-plan.md");
  const implementationReview = await read("specs/changes/spec-change-agent-workflow/review-report.implementation.md");
  const finalReview = await read("specs/changes/spec-change-agent-workflow/review-report.final.md");
  const routingSummary = await read("specs/changes/spec-change-agent-workflow/routing-summary.json");
  const testSummary = await read("specs/changes/spec-change-agent-workflow/test-result-summary.md");

  assert.match(workflowDoc, /request intake -> spec-draft -> architecture\/design -> spec-change -> execution routing -> implementation review -> independent tests -> final review -> acceptance -> current promote \+ archive/);
  assert.match(changeSpec, /spec-draft-agent/i);
  assert.match(changeSpec, /architecture-agent/i);
  assert.match(changeSpec, /frontend-execution-agent/i);
  assert.match(changeSpec, /backend-execution-agent/i);
  assert.match(changeSpec, /migration-execution-agent/i);
  assert.match(changeArchitecture, /routing-summary\.json/);
  assert.match(changeDesign, /design-review\.md can be marked `not-applicable`/);
  assert.match(executionPlan, /implementation-report\.frontend\.md/);
  assert.match(executionPlan, /implementation-report\.backend\.md/);
  assert.match(executionPlan, /implementation-report\.migration\.md/);
  assert.match(implementationReview, /Implementation Review Gate/);
  assert.match(finalReview, /Final Review Gate/);
  assert.match(routingSummary, /"selectedRoutes"/);
  assert.match(testSummary, /normalized result/i);
});
