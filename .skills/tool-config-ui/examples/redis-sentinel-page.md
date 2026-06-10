# Example: Redis Sentinel Page

## Scenario

Operators configure Sentinel monitor groups, quorum, failover timeout, and notification hooks.

## Layout

- Header: `Redis Sentinel Policy`, cluster badge, current master status.
- Status strip: quorum health, last failover, pending draft.
- Main editor:
  - monitored masters table
  - quorum and timeout form
  - notification endpoints
  - failover simulation examples
- Right rail:
  - risk warnings
  - generated sentinel snippet
  - audit trail

## States

- Empty: no monitored master; offer `Add master` and sample policy.
- Loading: preserve table shape and show health check progress.
- Success: simulation passed and policy saved.
- Failure: quorum too low, duplicate master name, unreachable endpoint, split-brain warning.

## Safety

- Warn when quorum is below recommended threshold.
- Preview failover behavior against sample nodes.
- Require confirmation before applying production failover policy.
