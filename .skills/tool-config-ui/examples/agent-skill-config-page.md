# Example: Agent Skill Config Page

## Scenario

SpecOS users configure which skills an agent can use, their source order, guardrails, and validation expectations.

## Layout

- Header: `Agent Skill Configuration`, agent role badge, source manifest link.
- Status strip: selected agent, enabled skill count, last validated time.
- Main editor:
  - agent role summary
  - enabled skills switchboard
  - source-order policy
  - guardrail checklist
  - validation commands
- Right rail:
  - skill trigger preview
  - missing traceability warnings
  - generated handoff summary

## States

- Empty: no skills assigned; offer `Add skill` and recommended defaults.
- Loading: skeleton role summary and switchboard rows.
- Success: configuration validated and saved as draft.
- Failure: missing `SKILL.md`, duplicate skill name, unresolved source path, unsafe guardrail.

## Safety

- Show exact files the agent can modify or reference.
- Validate skill metadata before enablement.
- Require confirmation before disabling required traceability or validation skills.
