# Getting started

Freight & Carrier Fraud Risk Taxonomy is a static, browser-first reference. The live experience is the generated page in [`docs/`](../docs/), backed by [`docs/data.json`](../docs/data.json).

## Browse the published taxonomy

Open the [live taxonomy](https://jeevan-0508.github.io/freight-fraud-taxonomy/), then search or filter the 12 patterns. Open a pattern to review:

- the operational description;
- observable indicators and the stage at which they appear;
- benign explanations that may create the same signal; and
- practical countermeasures and related patterns.

The false-positive section is part of the workflow. A signal is a reason to collect the next useful observation, not a verdict by itself.

## Run it locally

The browser loads `data.json` with `fetch`, so serve the repository over HTTP rather than opening `docs/index.html` directly as a `file://` URL.

```bash
python3 -m http.server 4173
```

Open <http://localhost:4173/docs/> in a browser.

## Update the generated bundle

Pattern records live in [`taxonomy/patterns/`](../taxonomy/patterns/). After editing them, rebuild the browser bundle from the repository root:

```bash
python3 scripts/build_index.py
```

The generated [`taxonomy/index.json`](../taxonomy/index.json) is the catalogue used for repository metadata and the generated [`docs/data.json`](../docs/data.json) is the single bundle consumed by the browser page. Review both before committing.

## Validate before publishing

Run the dependency-free content and contract checks:

```bash
python3 scripts/validate.py
python3 scripts/check_figures.py
python3 scripts/inspect_site.py
```

`inspect_site.py` checks the deployed URL by default. Set `SITE` when reviewing another deployment:

```bash
SITE=http://localhost:4173/docs/ python3 scripts/inspect_site.py
```

## Candidate exports are separate

The [`contracts/`](../contracts/) files describe a synthetic Fraud Watch candidate handoff. They are an interchange contract, not additional taxonomy truth and not evidence of a real incident. Promotion into the taxonomy remains a reviewed human decision.
