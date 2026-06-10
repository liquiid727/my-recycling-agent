# Repository Adaptation

Use this file when preparing the skill for another team.

## What Usually Needs Customization

- artifact names:
  - map the destination repo's planning, testing, review, and sync artifacts to this skill's expected inputs
- review gate:
  - decide whether `push` or `PR` is allowed before formal review completes
- sync gate:
  - decide whether semantic doc sync is required and whether it blocks merge
- commit convention:
  - replace the default format if the destination repo has a stricter rule
  - confirm whether the team uses the provided emoji map as-is or has custom emoji per type
  - confirm whether the team prefers `fix` or a nonstandard `bug` type
  - decide whether merge-readiness evaluations should leave `commit_messages` as `none` and whether hand-written merge commit messages are ever required
- pre-commit policy:
  - decide whether `pre-commit` is advisory or blocking
- PR template path:
  - default is `.github/pull_request_template.md`
- extra gates:
  - add repo-specific checks such as `make lint`, `go test`, `npm test`, `cargo test`, or security scans

## Minimal Install Paths

Choose one:

1. Copy this folder to `~/.codex/skills/team-ci-agent`
2. Commit this folder into a shared repository and install it with `$skill-installer` from a GitHub tree URL

After install, restart Codex so the new skill is discovered.

## Invocation Examples

- `Use $team-ci-agent to validate this change before commit.`
- `Use $team-ci-agent to check PR readiness and emit a CI Record.`
- `Use $team-ci-agent to tell me whether this merge is blocked and why.`

## Recommended Team Bundle

If the destination team wants the same workflow shape as RealDesk, share this CI skill together with:

- a routing skill
- a planning skill
- a reviewer skill
- a documentation-sync skill

This CI skill still works on its own, but it gets stronger when those upstream artifacts already exist.
