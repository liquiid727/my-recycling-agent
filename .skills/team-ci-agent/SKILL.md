---
name: team-ci-agent
description: Portable Git and change-validation coordinator for multi-agent repositories: verify commit, push, PR, and merge readiness, constrain staged scope, reuse planning, test, review, and sync evidence when available, and emit a stable CI Record. Use when a task involves change validation, review readiness, commit, push, PR, or merge.
metadata:
  short-description: Portable CI gate skill for Git action readiness
---

# Team CI Agent

Use this skill when a repository wants a reusable delivery gate between implementation work and Git actions.

This skill owns:

- reading `git status` and the active diff
- deciding whether the requested Git action has enough validation evidence
- constraining stage scope to task-related files
- suggesting commit message format
- emitting a stable `CI Record`

This skill does **not** replace implementation, testing, review, or documentation sync. It summarizes readiness and calls out missing evidence instead of inventing it.

## Read Order

1. `references/ci-record-template.md`
2. `references/repo-adaptation.md`
3. repo-local contribution rules if present, in this order:
   - `AGENTS.md`
   - `CONTRIBUTING.md`
   - `README.md`
4. `.github/pull_request_template.md` when PR work is requested
5. current `git status --short`
6. recent delivery artifacts if present:
   - `Task Plan`
   - `Test Plan`
   - `Test Report`
   - `Findings` or reviewer output
   - `Sync Handoff` or equivalent doc-sync handoff

When searching the repository, prefer focused searches such as:

- `rg -n "^## (Task Plan|Test Plan|Test Report|Findings|Sync Handoff|CI Record)" -g '*.md'`
- `rg -n "change validation|review readiness|CI Record" -g '*.md'`

Use the most recent artifact that belongs to the current task. Do not rely on stale records from unrelated work.

## Activate This Skill When

- the user asks for `change validation`
- the user asks for `review readiness`
- the user asks for `commit`
- the user asks for `push`
- the user asks for `PR`
- the user asks for `merge`

If the user only wants analysis or explanation, do not force this skill.

## Workflow

1. Classify the request as `change`, `review`, `analysis`, or `release`.
2. Inspect the working tree and separate task files from unrelated edits.
3. Gather available validation evidence:
   - planning artifact
   - test artifact(s)
   - reviewer output
   - sync evidence for semantic changes
4. Apply repository-specific policy if one exists.
5. Fall back to the default rules in this skill when the repository has no stricter policy.
6. Emit a `CI Record`.
7. If the user asked for `commit`, `push`, `PR`, or `merge`, answer clearly whether the action is ready or blocked.

## Default Rules

### 1. `intent_class`

- `change`: feature, fix, refactor, or semantic documentation change moving toward delivery
- `review`: readiness evaluation without executing the final Git action
- `analysis`: explanation only, with no delivery action requested
- `release`: release, rollout, or production delivery closure

### 2. `change_validation_status`

- `pass`
  - required evidence for the requested action is present
  - test and review gates are satisfied according to repository policy
  - sync evidence is present when semantic changes require it
- `partial`
  - some evidence exists, but not enough for the requested Git action
  - common when the user asks for readiness evaluation before review or sync is finished
- `fail`
  - a required gate is missing or failed
  - blocking reviewer findings still exist
  - the requested action would include unrelated or unsafe changes
- `not_applicable`
  - no delivery action exists for the task

When in doubt, prefer `partial` over `pass`.

### 3. Stage Scope

- stage only files related to the current task
- exclude unrelated formatting, debug prints, generated noise, and historical edits
- never silently mix unrelated user changes into the same commit
- keep the proposed commit boundary small and reviewable

### 4. Pre-commit

- treat `pre-commit` as recommended by default
- record `passed`, `failed`, `not_run`, or `not_applicable`
- only make it blocking when the repository explicitly says so

### 5. Review and Merge Readiness

- code or behavior changes default to `review_required: true`
- `commit`, `push`, and `PR` may still be allowed with `review_status: pending` if the repository permits that flow
- `merge` requires completed review and no remaining blocking items
- for merge-readiness evaluation, the primary outputs are `merge_ready` and `blocking_items`; if no new commit message is being proposed, write `none` under `commit_messages`

### 6. Sync and Semantic Change Handling

- if repository policy requires documentation or knowledge sync for semantic changes, treat missing sync evidence as a gate
- if the repository has no explicit sync discipline, record the missing sync check under `skipped_checks` instead of inventing compliance

### 7. Commit Messages

Use repository format if one exists. Otherwise use this default:

`<emoji> <type>(scope): local-language summary; English summary`

- `scope` should use the affected module, directory, or subsystem; omit it when no clear scope exists
- keep the local-language summary action-led, concise, and free of trailing punctuation
- use `fix` instead of `bug` unless the destination repository explicitly standardizes `bug`

Recommended default mappings:

| Type | Emoji | Meaning |
|---|---|---|
| `init` | `:tada:` | project initialization |
| `feat` | `:sparkles:` | new feature |
| `fix` | `:lady_beetle:` | bug fix |
| `docs` | `:page_with_curl:` | documentation change |
| `style` | `:rainbow:` | formatting-only change |
| `refactor` | `:unicorn:` | code refactor |
| `perf` | `:balloon:` | performance improvement |
| `test` | `:test_tube:` | test-related change |
| `build` | `:wrench:` | build system or dependency change |
| `ci` | `:horse:` | CI configuration change |
| `chore` | `:spouting_whale:` | repository maintenance or helper tooling |
| `revert` | `:right_arrow_curving_left:` | revert a prior commit |

`chore` guidance:

- use it for scaffolding, helper scripts, dependency housekeeping, generated artifact refreshes, or non-business config cleanup
- do not hide feature work or bug fixes inside `chore`; prefer `feat`, `fix`, `docs`, `test`, `build`, or `ci` when those better describe the change
- example: `:spouting_whale: chore(team): align CI record guidance; Align CI record guidance`

`merge` guidance:

- `merge` is not a normal Conventional Commit business type and should not replace `feat`, `fix`, `chore`, or other semantic commit types
- when this skill handles a merge request, default to evaluating merge readiness instead of inventing a new commit message
- if the destination repository explicitly requires a hand-written merge commit message, an allowed exception format is `:twisted_rightwards_arrows: merge(<target-branch>): merge <source-branch>; Merge <source-branch> into <target-branch>`
- merge commit text should describe the branch merge only; business meaning should stay in the original commits or PR title

### 8. Breaking Changes

- allow `type!` when the repository uses that syntax
- or include `BREAKING CHANGE: ...` in the commit body
- always state scope of impact and upgrade guidance

## Output Rules

- Reuse the exact `CI Record` schema from `references/ci-record-template.md` unless the destination repository already has an equivalent stable schema.
- Do not report green status when required evidence is missing.
- If no structured task artifacts exist in the destination repository, still emit a `CI Record` based on:
  - `git status`
  - executed checks
  - skipped checks
  - stage scope
  - blocking items

## Packaging Guidance

Before sharing this skill with another team, read `references/repo-adaptation.md`.

The minimum portable bundle is:

- `SKILL.md`
- `agents/openai.yaml`
- `references/ci-record-template.md`
- `references/repo-adaptation.md`

If the destination team already uses routing, planning, review, and sync skills, this CI skill can be installed by itself. If not, it still works as a standalone Git readiness gate.
