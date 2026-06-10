# CI Record Template

```markdown
## CI Record
intent_class: change | review | analysis | release
change_validation_status: pass | fail | partial | not_applicable
executed_checks:
  - <command + result, write none if empty>
skipped_checks:
  - <check + reason, write none if empty>
git_status_checked: true | false
stage_scope:
  - <files or directories that belong in this delivery, write none if empty>
unrelated_changes_excluded: true | false
pre_commit_status: passed | failed | not_run | not_applicable
review_required: true | false
review_status: pending | completed | not_applicable
commit_messages:
  - <emoji type(scope): local-language summary; English summary; write none for pure merge readiness; if the repo requires merge commits, emoji merge(target) is allowed>
merge_ready: true | false
blocking_items:
  - <blocking item, write none if empty>
```
