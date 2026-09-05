#!/usr/bin/env python3
"""Generate taxonomy/index.json and docs/data.json from the pattern files.

index.json is the machine-readable manifest consumers should fetch first.
docs/data.json is the single bundle the GitHub Pages browser loads.
"""
import json, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
PATTERN_DIR = ROOT / "taxonomy" / "patterns"
patterns = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(PATTERN_DIR.glob("*.json"))]
patterns.sort(key=lambda p: p["id"])

index = {
    "taxonomy": "Freight & Carrier Fraud Risk Taxonomy",
    "version": "1.0.0",
    "pattern_count": len(patterns),
    "categories": sorted({p["category"] for p in patterns}),
    "indicator_count": sum(len(p["indicators"]) for p in patterns),
    "countermeasure_count": sum(len(v) for p in patterns for v in p["countermeasures"].values()),
    "patterns": [
        {
            "id": p["id"],
            "name": p["name"],
            "category": p["category"],
            "severity": p["severity"],
            "prevalence": p["prevalence"],
            "summary": p["summary"],
            "file": f"patterns/{p['id']}-{p['name'].lower().replace(' & ', '-').replace(' ', '-')}.json",
        }
        for p in patterns
    ],
}
(ROOT / "taxonomy" / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
(ROOT / "docs" / "data.json").write_text(json.dumps({"meta": {k: v for k, v in index.items() if k != "patterns"}, "patterns": patterns}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

by_cat = collections.Counter(p["category"] for p in patterns)
print(f"{len(patterns)} patterns | {index['indicator_count']} indicators | {index['countermeasure_count']} countermeasures")
print("categories: " + ", ".join(f"{k}={v}" for k, v in sorted(by_cat.items())))
