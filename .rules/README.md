# Rule Index

`.rules/` is the compact agent-facing rule entrypoint for SpecOS. Canonical detailed rule documents remain under `rules/`.

## Files

- `project.md`: repository-wide execution policy.
- `rule-map.yaml`: machine-readable mapping from work type to canonical rule files.

## Usage

Agents should read `project.md` first, then follow `rule-map.yaml` to load only the detailed rules relevant to the current task.
