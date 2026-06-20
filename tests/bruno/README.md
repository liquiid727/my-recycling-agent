# Bruno

HTTP collection and scenario assets derived from accepted cycling-agent specs
belong here.

Bruno outputs should be treated as execution assets. The independent test console should read normalized files from `tests/results/` instead of parsing Bruno-native output directly.

If this repository later accepts a deterministic Bruno generator, generated
files should live under `tests/bruno/<specId>/` and include `bruno.json`, one
`.bru` request per endpoint, and a collection README.

## Runner Contract

The normalized contract expects API execution assets under:

```text
tests/bruno/<specId>/
```

When assets or execution adapter configuration are missing, repository docs and
results should record that honestly as blocked or not-yet-wired rather than
pretending a live runner exists.
