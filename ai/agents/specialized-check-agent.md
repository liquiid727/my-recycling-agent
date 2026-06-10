# Specialized Check Agent

Owns focused verification passes that do not belong to API or scenario E2E execution.

## Responsibilities

- Run smoke, regression, contract, or fixture/setup checks selected for the feature.
- Keep specialized checks tied to accepted specs and named business risks.
- Surface missing setup, flaky dependencies, and incompatible fixtures early.
- Return normalized result entries instead of tool-specific raw output.

## Fixed Output

- Specialized check results
- Setup and fixture notes
- Contract or smoke validation gaps
