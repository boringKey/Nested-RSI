# Changelog

Public versions record shipped content. Internal experiment iterations are not releases.

## Project rename and documentation update — 2026-10-08

- Rename the project and repository from Triad-RSI to Nested-RSI.
- Adopt “Local Improvement Loops, Global System Evolution” as the subtitle.
- Explain RSI within RSI and the prototype's bounded Data-RSI assistance loop.
- Distinguish trajectory admission, system acceptance, and rule acceptance.
- Remove the previous system-overview diagram; refresh English and Chinese documentation and repository links.
- Keep the v1 `triad_rsi` Python namespace, `triad-rsi-demo` CLI, and package version for compatibility. This documentation update does not ship the full inner-loop implementation.

## v1 / 0.1.0 — 2026-10-08

First public core preview:

- Extract cost-aware bandit policy and controlled scheduling from the research prototype.
- Publish paired acceptance and full repeated-confirmation evaluation.
- Replace the scheduler's provider coupling with a proposal callback.
- Validate invalid evaluation outcomes and policy inputs.
- Add an offline synthetic replay, behavior tests, and Python CI.
- Document architecture, evaluation assumptions, provenance, and release scope.
- Add MIT licensing and a Chinese overview.

This is a partial code release. Full training, operator backends, benchmark results, and rule trials are not included.

## Project introduction — 2026-10-08

- Initial README describing the research direction.

## Upcoming

v2 and v3 are planned, not released. See [ROADMAP.md](ROADMAP.md).
