/*
 * CN: SpecOS 生命周期校验脚本，供 workflow 直接执行并快速发现缺失资产。
 * EN: SpecOS lifecycle validator script used by workflows to fail fast on missing assets.
 */

import { access, readFile } from "node:fs/promises";

const requiredFiles = [
  ".agents/manifest.yaml",
  ".specos/workflows/spec-driven-default.yaml",
  "ai/workflows/spec-driven-request-lifecycle.md",
  "ai/agents/spec-draft-agent.md",
  "ai/agents/architecture-agent.md",
  "ai/agents/spec-agent.md",
  "ai/agents/frontend-execution-agent.md",
  "ai/agents/backend-execution-agent.md",
  "ai/agents/migration-execution-agent.md",
  "specs/changes/spec-change-agent-workflow/routing-summary.json",
  "specs/changes/spec-change-agent-workflow/review-report.implementation.md",
  "specs/changes/spec-change-agent-workflow/review-report.final.md",
  "specs/changes/spec-change-agent-workflow/test-result-summary.md",
];

function assertMatch(source, pattern, message) {
  if (!pattern.test(source)) {
    throw new Error(message);
  }
}

for (const path of requiredFiles) {
  await access(path);
}

const manifest = await readFile(".agents/manifest.yaml", "utf8");
assertMatch(manifest, /\n  spec-draft-agent:/, "manifest missing spec-draft-agent");
assertMatch(manifest, /\n  architecture-agent:/, "manifest missing architecture-agent");
assertMatch(manifest, /\n  spec-agent:/, "manifest missing spec-agent");
assertMatch(manifest, /\n  frontend-execution-agent:/, "manifest missing frontend-execution-agent");
assertMatch(manifest, /\n  backend-execution-agent:/, "manifest missing backend-execution-agent");
assertMatch(manifest, /\n  migration-execution-agent:/, "manifest missing migration-execution-agent");
assertMatch(manifest, /implementation_gate/, "manifest missing reviewer implementation gate");
assertMatch(manifest, /final_gate/, "manifest missing reviewer final gate");
assertMatch(manifest, /activation_conditions:/, "manifest missing ui-design-agent activation conditions");

const workflow = await readFile(".specos/workflows/spec-driven-default.yaml", "utf8");
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
  assertMatch(workflow, new RegExp(`id: ${stageId}`), `workflow missing stage ${stageId}`);
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
  assertMatch(workflow, new RegExp(`- ${state}\\b`), `workflow missing change state ${state}`);
}

for (const routeKey of ["frontend", "backend", "migration"]) {
  assertMatch(workflow, new RegExp(`route_key: ${routeKey}`), `workflow missing route ${routeKey}`);
}

console.log("spec-driven-lifecycle-validated");
