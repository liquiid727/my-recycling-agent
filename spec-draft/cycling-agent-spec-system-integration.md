# Cycling Agent Spec System Integration

## Status

Draft for review.

## Goal

Refit this repository so the existing spec-driven workflow is anchored on the real `products/cycling-agent` product instead of a parallel SpecOS meta-example. After this change, the repository should have one clear delivery chain for the current product:

`draft -> change package -> implementation/test -> review -> accepted baseline`

## Why This Change Exists

The repository currently mixes two different source-of-truth models:

1. The real product and runtime path around `products/cycling-agent/`, `Makefile`, backend tests, frontend tests, and product docs.
2. A SpecOS-oriented workflow skeleton under `spec-draft/`, `specs/`, `tests/`, `.agents/`, `.specos/`, and `ai/workflows/`.

The second model is documented, but it is not the default execution path for day-to-day work. That makes the spec system optional in practice and confusing in scope.

## Scope

This integration change covers repository governance, structure, and validation around the current cycling-agent product.

Included:

- Rebuild `specs/current/` so it describes accepted cycling-agent baseline facts.
- Keep `spec-draft/` as intake and `specs/changes/` as the active change workspace for cycling-agent work.
- Align `.specos/manifest.yaml`, `.agents/manifest.yaml`, workflow docs, and check scripts with the actual FastAPI + React/Vite product.
- Add explicit spec validation entrypoints in the repo's operational commands.
- Reclassify `docs/design/` so it no longer competes with the active source-of-truth chain.
- Remove stray tool-generated planning/spec artifacts that live outside repo-owned source-of-truth paths.

Excluded:

- No product feature redesign in this change.
- No rewrite of the backend/frontend business logic in this change.
- No generic hosted workflow runner beyond local repository validation.

## Source Of Truth Model After Integration

### Product truth

`products/cycling-agent/` remains the runnable product surface and codebase.

### Delivery truth

The active delivery chain becomes:

1. `spec-draft/` for raw requirements and structured intake.
2. `specs/changes/<change-id>/` for active normalized change packages.
3. `products/cycling-agent/` plus `tests/` for implementation and verification.
4. `specs/current/` for accepted cycling-agent baseline facts.
5. `specs/archive/` for completed change evidence.

### Documentation truth

- `README.md` becomes the top-level map for both product runtime and spec delivery.
- `docs/product/`, `docs/technical/`, and `docs/plans/` remain supporting reference material, but they must not outrank `specs/current/` for accepted active behavior.
- `docs/design/` becomes historical/reference-only material or moves under archive if still useful.
- Ad hoc tool-generated planning/spec directories are not part of the repo contract and must not be used as delivery truth.

## Required Structural Decisions

### 1. Rebuild accepted baseline files

`specs/current/project-context.md`, `specs/current/architecture-context.md`, and `specs/current/domain-context.md` must describe cycling-agent accepted facts instead of SpecOS meta-language.

They should answer:

- What the current cycling-agent product is.
- What the active backend/frontend/runtime boundaries are.
- What domain language and accepted behavior are already stable.
- What evidence is required before new product behavior is promoted into current.

### 2. Keep workflow skeleton, but rebind it to cycling-agent reality

The existing lifecycle assets are still useful:

- `.agents/manifest.yaml`
- `.specos/workflows/spec-driven-default.yaml`
- `ai/workflows/spec-driven-request-lifecycle.md`
- `scripts/checks/validate-spec-driven-lifecycle.mjs`

But they must be rewritten so they validate cycling-agent delivery assets rather than a generic SpecOS example.

### 3. Add repo-visible operational gates

The repo must expose spec checks as real operator entrypoints. At minimum:

- a repo-level spec structure check
- a change-package check for one active change
- a sync check between workflow metadata and repository docs

These checks should be invokable from `Makefile` so the spec workflow is part of normal repo operation, not a hidden convention.

### 4. Remove stale or false executable references

If the repo references commands, generated assets, or runners that do not exist, those references must either be implemented or removed. Documentation must not advertise missing execution paths such as placeholder CLI locations or nonexistent orchestration scripts.

## Directory Policy After Integration

### Keep as active

- `spec-draft/`
- `specs/current/`
- `specs/changes/`
- `specs/archive/`
- `tests/`
- `.agents/`
- `.specos/`
- `rules/`
- `.rules/`
- `products/cycling-agent/`

### Keep as supporting reference

- `docs/product/`
- `docs/technical/`
- `docs/plans/`

### Reclassify or archive

- `docs/design/` becomes explicitly historical/reference-only and must say so in its own index.
- Stray tool-generated planning/spec artifacts outside repo-owned paths should be removed or folded into `spec-draft/`, `specs/`, or `docs/archive/` as appropriate.

## Validation Expectations

After integration:

- A repository operator should be able to identify the accepted baseline by reading `README.md` and `specs/current/`.
- A new requirement should have one obvious intake path: `spec-draft/` first, then `specs/changes/<change-id>/`.
- Repo checks should be able to fail fast when spec workflow assets drift from actual repo structure.
- Product runtime commands should remain stable and should not require a full workflow runner just to start or test the app.

## Implementation Outline

1. Rewrite top-level repo documentation and manifests around cycling-agent.
2. Rebuild `specs/current/` to represent accepted cycling-agent facts.
3. Rework `specs/changes/` examples so they support cycling-agent instead of abstract SpecOS-only workflow modeling.
4. Update validation scripts and Makefile gates.
5. Remove stray tool-generated artifacts and reclassify `docs/design/`.
6. Clean dead references to missing tools and runners.

## Risks

- If historical docs are deleted too aggressively, useful context may be lost. Archive/reference labeling is safer than blind removal unless the artifact is clearly stray tool output with no repo ownership.
- If `specs/current/` is rewritten without clear boundaries, it can become another vague summary layer. It must stay concise and accepted-facts-only.
- If spec checks are too heavy, engineers will bypass them. Initial checks should focus on structure and traceability before deeper automation.

## Success Criteria

- The repo has one clear source-of-truth chain centered on cycling-agent.
- The baseline spec files describe the real product, not SpecOS meta-concepts.
- `Makefile` exposes spec validation commands.
- `docs/design/` no longer competes with the active delivery chain.
- No tool-default planning/spec directory is treated as repo truth.
- Repo documentation no longer points to fake or missing execution paths as if they are live.
