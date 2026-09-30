<p align="center"><img src="assets/jk-brand-banner.png" alt="Jeevan Siddhabhaktula — Risk. Governance. AI." width="280"></p>

# Freight & Carrier Fraud Risk Taxonomy

An open, structured taxonomy of fraud and cargo-loss patterns in European road freight.

**[Browse it here →](https://jeevan-0508.github.io/freight-fraud-taxonomy/)**

Most published material on cargo crime stops at naming the threat. This taxonomy is built around the
part that is actually hard in practice: knowing which signals genuinely reveal a pattern, where each
signal can be observed, and — critically — which innocent explanations produce the same signal.

`12` patterns · `87` indicators · `31` documented false positives · `138` countermeasures

## Why the false positives matter

Every pattern entry carries a `false_positives` block. This is deliberate and it is the part most
comparable references omit.

In freight risk work, the expensive mistakes are rarely missed detections — they are confident wrong
calls. A driver disproportionately assigned to one lane will show a disproportionate shortage rate.
A regional GNSS interference event looks identical to a tracker being jammed. A last-minute dispatch
reallocation looks identical to double brokering at the gate. Acting on any of those without ruling
out the benign explanation damages a supplier relationship, or a person's career, for nothing.

So each pattern states what it looks like, what it usually turns out to be, and the specific check
that separates the two.

## Structure

```
taxonomy/
  schema.json          JSON Schema (draft-07) every pattern must satisfy
  index.json           generated manifest — fetch this first
  patterns/*.json      one file per pattern
scripts/
  validate.py          schema + cross-reference validation, no dependencies
  build_index.py       regenerates index.json and docs/data.json
docs/                  the GitHub Pages browser
```

Each pattern contains:

| Field | What it holds |
|---|---|
| `how_it_works` | The mechanics, in order |
| `indicators` | Signal, the **phase** it appears in (`pre_award`, `in_transit`, `post_event`), where it is **observable**, and a weight from 1 (contextual) to 5 (near-conclusive) |
| `false_positives` | Looks like / usually actually / how to rule out |
| `countermeasures` | Split into `preventive`, `detective`, `responsive` |
| `regulatory_hooks` | The provision the pattern engages — LkSG, CSDDD, CMR, Mobility Package |
| `references` | Public sources |

Indicators are tagged by phase because the phase determines whether you can prevent the loss or only
explain it afterwards. A pattern whose only weight-5 indicators sit in `post_event` is, by
construction, one you cannot currently stop — and that is useful to know explicitly.

## Patterns

| ID | Pattern | Category | Severity | Prevalence | Indicators |
|---|---|---|---|---|---|
| `FFT-001` | [Double Brokering](taxonomy/patterns/FFT-001-double-brokering.json) | contractual | high | common | 7 |
| `FFT-002` | [Phantom Carrier](taxonomy/patterns/FFT-002-phantom-carrier.json) | identity | critical | common | 9 |
| `FFT-003` | [Carrier Identity Takeover](taxonomy/patterns/FFT-003-carrier-identity-takeover.json) | identity | critical | occasional | 6 |
| `FFT-004` | [Fictitious Pickup](taxonomy/patterns/FFT-004-fictitious-pickup.json) | cargo loss | critical | occasional | 7 |
| `FFT-005` | [Systematic Pilferage](taxonomy/patterns/FFT-005-systematic-pilferage.json) | cargo loss | medium | endemic | 6 |
| `FFT-006` | [Unsecured Parking Theft](taxonomy/patterns/FFT-006-unsecured-parking-theft.json) | cargo loss | high | endemic | 6 |
| `FFT-007` | [Seal Tampering and Reseal Fraud](taxonomy/patterns/FFT-007-seal-tampering-and-reseal-fraud.json) | documentary | medium | common | 6 |
| `FFT-008` | [GPS Spoofing and Telematics Manipulation](taxonomy/patterns/FFT-008-gps-spoofing-and-telematics-manipulation.json) | digital | high | occasional | 6 |
| `FFT-009` | [Insider Collusion](taxonomy/patterns/FFT-009-insider-collusion.json) | insider | critical | occasional | 6 |
| `FFT-010` | [Transport Document Fraud](taxonomy/patterns/FFT-010-transport-document-fraud.json) | documentary | medium | common | 6 |
| `FFT-011` | [Insurance Certificate Fraud](taxonomy/patterns/FFT-011-insurance-certificate-fraud.json) | financial | high | common | 6 |
| `FFT-012` | [Undisclosed Subcontracting Chain](taxonomy/patterns/FFT-012-undisclosed-subcontracting-chain.json) | regulatory | high | common | 6 |

Categories: cargo loss (3), contractual (1), digital (1), documentary (2), financial (1), identity (2), insider (1), regulatory (1)

## Using the data

`taxonomy/index.json` is the manifest; `docs/data.json` is every pattern in one bundle.

```python
import json, urllib.request
B = "https://raw.githubusercontent.com/Jeevan-0508/freight-fraud-taxonomy/main/"
data = json.load(urllib.request.urlopen(B + "docs/data.json"))

# indicators you could act on before the cargo moves
for p in data["patterns"]:
    early = [i for i in p["indicators"] if i["phase"] == "pre_award" and i["weight"] >= 4]
    if early:
        print(p["id"], p["name"])
        for i in early:
            print("   ", i["weight"], i["signal"], "->", i["observable_in"])
```

## Validating a change

```bash
python3 scripts/validate.py      # schema, enums, weights, duplicate ids, dangling `related`
python3 scripts/build_index.py   # regenerate index.json and docs/data.json
```

`validate.py` has no third-party dependencies. It implements the subset of JSON Schema this taxonomy
uses, plus the cross-file checks a generic validator cannot do: duplicate IDs, `related` entries
pointing at patterns that do not exist, and filenames disagreeing with the ID inside them.

CI runs both on every push and pull request.

## Candidate handoff contract

`contracts/candidate-mo-v1.schema.json` defines an interchange format for candidate
patterns exported by the synthetic Fraud Watch simulator. Its example fixture is
illustrative test data, not a real freight incident or a claim that a new fraud
pattern exists. Every export is labelled `synthetic_simulation` and
`unverified_export`; correlation indices are explicitly not probabilities.

The contract preserves the source repository revision when known, the taxonomy
version and optional pinned source/snapshot hashes, candidate lifecycle, and the
case provenance supplied with the export. A missing source revision or taxonomy
hash remains `null` rather than being guessed. A missing current classification
reason also remains `null`; the candidate provenance does not retain a historical
reason snapshot. Promotion is outside this contract:
it requires a separately reviewed change to this taxonomy. CI validates the
example against the schema and checks that real-world, promotion, and unknown-field
mutations are rejected.

## Scope and provenance

Compiled from public industry, law-enforcement and regulatory sources — TAPA EMEA, Europol, IRU,
ESPORG, EUSPA, UNECE, BAFA and the EU legal instruments cited in each entry.

**This repository contains no confidential, proprietary or employer-specific material.** No internal
detection thresholds, case data, identifiers or process documentation from any organisation are
included. Where a countermeasure refers to a threshold, it refers to the concept of having one, never
to a real value.

Severity and prevalence are qualitative judgements about European road freight, offered as a starting
baseline. They are not derived from a proprietary dataset and should be recalibrated against your own
loss history before being used to make decisions.

Not legal advice. The regulatory hooks indicate where a pattern engages an obligation; they are not a
compliance opinion.

## Contributing

Corrections are especially welcome on the `false_positives` blocks — a benign explanation this
taxonomy has not accounted for is the most valuable thing you can add. See
[CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

[CC BY 4.0](LICENSE) for the taxonomy content. Use it, adapt it, cite it.
## Simulator capability recipes

Taxonomy 1.1.0 optionally carries a strict `simulation_recipe` on a pattern. Fraud Watch consumes these authored recipes using its existing allowlisted disruption and position primitives. Adding a compatible recipe enables that pattern without a second hardcoded pattern list. `generation_order` preserves seeded ordering; unknown primitives or versions fail closed. Patterns without a recipe remain visible as unsupported simulator coverage, rather than receiving invented behavior. FFT-011 currently has no executable recipe.

These recipes describe synthetic laboratory scenarios. They do not establish real-world occurrence, incident frequency, source reliability, or fraud probability. The existing qualitative severity/prevalence descriptors and indicator weights are expert-authored inputs. Candidate exports remain synthetic hypotheses and cannot represent taxonomy promotion.
