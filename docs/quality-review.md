# Quality review

This review records the current portfolio-facing state without implying live production operation.

## Presentation review

| Dimension | Assessment | Notes |
|---|---:|---|
| First impression | 8/10 | The README leads with a focused hero, a clear live-taxonomy CTA, concrete counts and a useful explanation of why false positives matter. |
| Product clarity | 9/10 | A visitor can understand the pattern → signal → false-positive → countermeasure workflow quickly. |
| Visual consistency | 8/10 | The README uses the shared portfolio language while the taxonomy keeps its own blue, dark reference-tool identity. |
| Credibility | 9/10 | Scope, provenance, licensing and the synthetic candidate boundary are explicit. |
| Mobile readability | 8/10 | The README tables are compact and the live page is responsive; very wide taxonomy detail tables remain easier on desktop. |

## Technical review

The repository contains a generated static browser page, JSON source records, a schema, and dependency-free Python validation scripts. The visible page includes heading and metadata, image alt text, search/filter controls, pattern detail panels, false-positive explanations and countermeasure sections.

The main review risks are data freshness and deployment drift: `docs/data.json` must be regenerated after source changes, and `inspect_site.py` should be run against the deployed URL after publication. No application server, authentication layer, telemetry or live carrier feed is present in this repository.

## Validation commands

The intended checks are:

```bash
python3 scripts/validate.py
python3 scripts/check_figures.py
python3 scripts/inspect_site.py
```

Python was not available on the Windows environment used for this documentation pass (`python3` and `py` were not on PATH), so these commands were documented from the repository's own scripts but could not be executed here. No pass is claimed for them.

## Honest scope

This is a structured reference and investigation aid. It does not calculate a carrier score, establish that a fraud event occurred, provide legal advice, or replace local investigation policy and operational expertise. The counts in the README describe the current checked-in dataset, not a claim about industry prevalence.
