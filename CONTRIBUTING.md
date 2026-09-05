# Contributing

## What is most useful

1. **A false positive we missed.** A benign explanation that produces the same signal as a fraud
   pattern. This is the highest-value contribution, because a wrong call is more expensive than a
   missed one.
2. **A correction to an indicator's weight or phase.** If a signal you rely on is more or less
   conclusive than stated, or is observable earlier than we claim, say so.
3. **A new pattern**, with a real mechanism, indicators that are actually observable, and at least
   one documented false positive.
4. **A better public reference** for an existing claim.

## Hard rules

- **Public sources only.** Nothing confidential, proprietary or employer-specific. No internal
  thresholds, case data, identifiers, screenshots or process documentation from any organisation.
- **No real threshold values.** Refer to the existence of a threshold, never to a number in use
  somewhere.
- **Every indicator needs an `observable_in`.** If you cannot say where a signal is actually visible
  — a field, a document, a system, a physical check — it is not yet an indicator.
- **Every pattern needs at least one false positive.** If a pattern has none, it has not been
  thought through.

## Before opening a pull request

```bash
python3 scripts/validate.py
python3 scripts/build_index.py
```

Commit the regenerated `taxonomy/index.json` and `docs/data.json`. CI will reject a change where
they are stale.

## Weights

| Weight | Meaning |
|---|---|
| 1 | Contextual. Only meaningful alongside others. |
| 2 | Weak. Slightly raises suspicion. |
| 3 | Moderate. Worth a look on its own. |
| 4 | Strong. Justifies holding a movement or an award. |
| 5 | Near-conclusive. Alone, sufficient to act. |

Be conservative. Inflated weights make the taxonomy useless for prioritisation, which is most of what
it is for.
