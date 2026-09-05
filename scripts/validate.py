#!/usr/bin/env python3
"""Validate every pattern file against taxonomy/schema.json.

Deliberately dependency-free: it implements the subset of JSON Schema draft-07
this taxonomy actually uses, plus the cross-file integrity checks a generic
validator cannot do (duplicate ids, dangling `related` references, filename
agreement).
"""
import json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "taxonomy" / "schema.json").read_text(encoding="utf-8"))
PATTERN_DIR = ROOT / "taxonomy" / "patterns"

errors = []


def err(where, msg):
    errors.append(f"{where}: {msg}")


def check(node, spec, where):
    if "enum" in spec:
        if node not in spec["enum"]:
            err(where, f"{node!r} not one of {spec['enum']}")
        return
    t = spec.get("type")
    if t == "object":
        if not isinstance(node, dict):
            return err(where, "expected object")
        for k in spec.get("required", []):
            if k not in node:
                err(where, f"missing required key {k!r}")
        props = spec.get("properties", {})
        if spec.get("additionalProperties") is False:
            for k in node:
                if k not in props:
                    err(where, f"unexpected key {k!r}")
        for k, v in node.items():
            if k in props:
                check(v, props[k], f"{where}.{k}")
    elif t == "array":
        if not isinstance(node, list):
            return err(where, "expected array")
        if len(node) < spec.get("minItems", 0):
            err(where, f"needs at least {spec['minItems']} item(s), has {len(node)}")
        for i, v in enumerate(node):
            if "items" in spec:
                check(v, spec["items"], f"{where}[{i}]")
    elif t == "string":
        if not isinstance(node, str):
            return err(where, "expected string")
        if len(node) < spec.get("minLength", 0):
            err(where, f"shorter than minLength {spec['minLength']}")
        if "pattern" in spec and not re.match(spec["pattern"], node):
            err(where, f"{node!r} does not match {spec['pattern']}")
        if spec.get("format") == "uri" and not node.startswith(("http://", "https://")):
            err(where, f"{node!r} is not an absolute URL")
    elif t == "integer":
        if not isinstance(node, int) or isinstance(node, bool):
            return err(where, "expected integer")
        if "minimum" in spec and node < spec["minimum"]:
            err(where, f"{node} below minimum {spec['minimum']}")
        if "maximum" in spec and node > spec["maximum"]:
            err(where, f"{node} above maximum {spec['maximum']}")


files = sorted(PATTERN_DIR.glob("*.json"))
if not files:
    print("no pattern files found", file=sys.stderr)
    sys.exit(1)

loaded = {}
for f in files:
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(f.name, f"invalid JSON: {e}")
        continue
    check(data, SCHEMA, f.name)
    pid = data.get("id")
    if pid:
        if pid in loaded:
            err(f.name, f"duplicate id {pid}")
        loaded[pid] = data
        if not f.name.startswith(pid + "-"):
            err(f.name, f"filename does not start with its id {pid}")

for pid, data in loaded.items():
    for rel in data.get("related", []):
        if rel not in loaded:
            err(pid, f"related references unknown pattern {rel}")
        if rel == pid:
            err(pid, "related references itself")

print(f"checked {len(files)} pattern file(s), {len(loaded)} unique id(s)")
if errors:
    print(f"\n{len(errors)} problem(s):", file=sys.stderr)
    for e in errors:
        print("  " + e, file=sys.stderr)
    sys.exit(1)
print("all patterns valid")
