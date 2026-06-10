# Example: Nginx Config Page

## Scenario

Operators edit reverse-proxy routing, TLS, and upstream timeout settings.

## Layout

- Header: `Nginx Gateway Config`, environment badge, linked source rule/spec.
- Status strip: active config version, last applied time, validation state.
- Main editor:
  - `Server blocks`
  - `Upstream pools`
  - `TLS certificates`
  - `Timeout and retry policy`
- Right rail:
  - Config diff preview
  - Validation results
  - Recent apply history

## States

- Empty: no server blocks; offer `Import config` and `Create server block`.
- Loading: skeleton cards for server blocks and validation panel.
- Success: validation passed with generated config preview.
- Failure: syntax error, duplicate server name, missing certificate, upstream unreachable.

## Safety

- Require `Validate` before `Apply`.
- Show generated config diff before apply.
- Keep `Rollback to previous version` in a separate danger section.
