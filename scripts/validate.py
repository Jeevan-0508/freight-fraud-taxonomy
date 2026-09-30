#!/usr/bin/env python3
"""Validate taxonomy patterns and the candidate-MO interchange contract.

Deliberately dependency-free: it implements the subset of JSON Schema draft-07
used by this repository, plus cross-file integrity checks (duplicate ids,
dangling references, filename agreement, and candidate lifecycle consistency).
"""
import copy
import datetime
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "taxonomy" / "schema.json").read_text(encoding="utf-8"))
PATTERN_DIR = ROOT / "taxonomy" / "patterns"
CONTRACT_SCHEMA = ROOT / "contracts" / "candidate-mo-v1.schema.json"
CONTRACT_EXAMPLE = ROOT / "contracts" / "examples" / "candidate-mo.v1.example.json"

errors = []


def err(where, msg):
    errors.append(f"{where}: {msg}")


def check(node, spec, where, sink=None):
    sink = errors if sink is None else sink

    def report(message):
        sink.append(f"{where}: {message}")

    if "const" in spec and node != spec["const"]:
        report(f"{node!r} does not equal required constant {spec['const']!r}")
        return
    if "enum" in spec:
        if node not in spec["enum"]:
            report(f"{node!r} not one of {spec['enum']}")
        return

    if "anyOf" in spec:
        for branch in spec["anyOf"]:
            candidate_errors = []
            check(node, branch, where, candidate_errors)
            if not candidate_errors:
                return
        report("does not match any allowed schema alternative")
        return

    t = spec.get("type")
    types = t if isinstance(t, list) else [t]
    if t is not None:
        matches = any(
            (kind == "null" and node is None)
            or (kind == "object" and isinstance(node, dict))
            or (kind == "array" and isinstance(node, list))
            or (kind == "string" and isinstance(node, str))
            or (kind == "boolean" and isinstance(node, bool))
            or (kind == "integer" and isinstance(node, int) and not isinstance(node, bool))
            or (kind == "number" and isinstance(node, (int, float)) and not isinstance(node, bool))
            for kind in types
        )
        if not matches:
            report(f"expected type {t}, got {type(node).__name__}")
            return

    if t == "object":
        for k in spec.get("required", []):
            if k not in node:
                report(f"missing required key {k!r}")
        props = spec.get("properties", {})
        if spec.get("additionalProperties") is False:
            for k in node:
                if k not in props:
                    report(f"unexpected key {k!r}")
        for k, v in node.items():
            if k in props:
                check(v, props[k], f"{where}.{k}", sink)
    elif t == "array":
        if len(node) < spec.get("minItems", 0):
            report(f"needs at least {spec['minItems']} item(s), has {len(node)}")
        if "maxItems" in spec and len(node) > spec["maxItems"]:
            report(f"has more than {spec['maxItems']} allowed items")
        if spec.get("uniqueItems") and len(node) != len({json.dumps(item, sort_keys=True) for item in node}):
            report("items must be unique")
        for i, v in enumerate(node):
            if "items" in spec:
                check(v, spec["items"], f"{where}[{i}]", sink)
    elif t == "string":
        if len(node) < spec.get("minLength", 0):
            report(f"shorter than minLength {spec['minLength']}")
        if "maxLength" in spec and len(node) > spec["maxLength"]:
            report(f"longer than maxLength {spec['maxLength']}")
        if "pattern" in spec and not re.search(spec["pattern"], node):
            report(f"{node!r} does not match {spec['pattern']}")
        if spec.get("format") == "uri" and not node.startswith(("http://", "https://")):
            report(f"{node!r} is not an absolute URL")
        if spec.get("format") == "date-time":
            try:
                parsed = datetime.datetime.fromisoformat(node.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    raise ValueError("timezone required")
            except ValueError:
                report(f"{node!r} is not a timezone-qualified date-time")
    elif ((t in ("integer", "number") or (isinstance(t, list) and "number" in t))
          and isinstance(node, (int, float)) and not isinstance(node, bool)):
        if "minimum" in spec and node < spec["minimum"]:
            report(f"{node} below minimum {spec['minimum']}")
        if "maximum" in spec and node > spec["maximum"]:
            report(f"{node} above maximum {spec['maximum']}")


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

recipe_ids = set()
recipe_orders = set()
for pid, data in loaded.items():
    for rel in data.get("related", []):
        if rel not in loaded:
            err(pid, f"related references unknown pattern {rel}")
        if rel == pid:
            err(pid, "related references itself")
    recipe = data.get("simulation_recipe")
    if isinstance(recipe, dict):
        for key, seen in (("plan_id", recipe_ids), ("generation_order", recipe_orders)):
            value = recipe.get(key)
            if not isinstance(value, (str, int)):
                continue
            if value in seen:
                err(pid, f"duplicate simulation recipe {key}: {value}")
            seen.add(value)
        for step in recipe.get("steps", []):
            if not isinstance(step, dict):
                continue
            if (step.get("test") == "AT_NODE_TYPE") != ("nodeType" in step):
                err(pid, "simulation recipe nodeType must be present only for AT_NODE_TYPE")

recipe_schema = SCHEMA["properties"]["simulation_recipe"]
recipe_fixture = next((p["simulation_recipe"] for p in loaded.values() if "simulation_recipe" in p), None)
if recipe_fixture:
    for label, mutate in (
        ("executable field", lambda x: x.update(script="execute me")),
        ("unsupported primitive", lambda x: x["steps"][0].update(type="EXECUTE")),
        ("unsupported version", lambda x: x.update(version=99)),
        ("oversized steps", lambda x: x.update(steps=x["steps"] * 30)),
    ):
        trial = []
        invalid = copy.deepcopy(recipe_fixture)
        mutate(invalid)
        check(invalid, recipe_schema, label, trial)
        if not trial:
            err("simulation recipe", f"negative mutation accepted: {label}")


def contract_semantic_errors(document):
    semantic_errors = []
    if not isinstance(document, dict):
        return semantic_errors
    candidate = document.get("candidate", {})
    candidate = candidate if isinstance(candidate, dict) else {}
    simulation = document.get("simulation", {})
    simulation = simulation if isinstance(simulation, dict) else {}
    sim_time = simulation.get("sim_time_seconds_from_genesis")

    def is_number(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    lifecycle_to_source = {
        "DISCOVERED": "CANDIDATE",
        "UNDER_REVIEW": "REVIEW",
        "VALIDATED": "VALIDATED",
        "REJECTED": "REJECTED",
    }
    lifecycle = candidate.get("lifecycle_state")
    if not isinstance(lifecycle, str) or lifecycle_to_source.get(lifecycle) != candidate.get("source_state"):
        semantic_errors.append("lifecycle_state and source_state do not correspond")
    if candidate.get("id") != "fraud-watch:" + str(candidate.get("signature", "")):
        semantic_errors.append("candidate id must be namespaced from its signature")
    if is_number(candidate.get("first_seen_at")) and is_number(candidate.get("candidate_since")):
        if candidate["first_seen_at"] > candidate["candidate_since"]:
            semantic_errors.append("first_seen_at is after candidate_since")
    state = candidate.get("lifecycle_state")
    review_started = candidate.get("review_started_at")
    resolved = candidate.get("resolved_at")
    candidate_since = candidate.get("candidate_since")
    if state == "DISCOVERED" and (review_started is not None or resolved is not None):
        semantic_errors.append("DISCOVERED candidate cannot carry review or resolution timestamps")
    elif state == "UNDER_REVIEW" and (review_started is None or resolved is not None):
        semantic_errors.append("UNDER_REVIEW requires review_started_at and no resolved_at")
    elif state in ("VALIDATED", "REJECTED") and (review_started is None or resolved is None):
        semantic_errors.append("resolved candidate requires both review_started_at and resolved_at")
    if (is_number(candidate_since) and is_number(review_started)
            and review_started < candidate_since):
        semantic_errors.append("review_started_at is before candidate_since")
    if (is_number(review_started) and is_number(resolved)
            and resolved < review_started):
        semantic_errors.append("resolved_at is before review_started_at")

    candidate_times = [candidate.get(k) for k in (
        "first_seen_at", "candidate_since", "review_started_at", "resolved_at"
    ) if candidate.get(k) is not None]
    if is_number(sim_time) and any(is_number(t) and t > sim_time for t in candidate_times):
        semantic_errors.append("candidate timestamp is later than simulation time at export")

    known_ids = set(loaded)
    seen_case_ids = set()
    cases = candidate.get("supporting_cases", [])
    if not isinstance(cases, list):
        return semantic_errors
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            continue
        case_id = case.get("case_id")
        if isinstance(case_id, str) and case_id in seen_case_ids:
            semantic_errors.append(f"supporting_cases[{index}] duplicates case id {case_id}")
        if isinstance(case_id, str):
            seen_case_ids.add(case_id)
        pattern_id = case.get("related_pattern_id")
        if isinstance(pattern_id, str) and pattern_id not in known_ids:
            semantic_errors.append(f"supporting_cases[{index}] references unknown taxonomy pattern {pattern_id}")
        opened = case.get("case_opened_at")
        first_observed = case.get("first_observed_at")
        recorded = case.get("recorded_at")
        numeric_times = all(is_number(t) for t in (first_observed, opened, recorded))
        if numeric_times and first_observed > opened:
            semantic_errors.append(f"supporting_cases[{index}] first_observed_at is after case_opened_at")
        if numeric_times and opened > recorded:
            semantic_errors.append(f"supporting_cases[{index}] case_opened_at is after provenance recorded_at")
        if (is_number(candidate_since) and is_number(recorded)
                and recorded < candidate_since):
            semantic_errors.append(f"supporting_cases[{index}] provenance predates candidate creation")
        if (is_number(sim_time) and is_number(recorded)
                and recorded > sim_time):
            semantic_errors.append(f"supporting_cases[{index}] provenance recorded_at is later than simulation time at export")
    return semantic_errors


def load_contract():
    try:
        schema = json.loads(CONTRACT_SCHEMA.read_text(encoding="utf-8"))
        example = json.loads(CONTRACT_EXAMPLE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        err("candidate contract", f"cannot read schema/example: {e}")
        return None, None
    check(example, schema, "candidate contract example")

    if schema.get("$schema") != "http://json-schema.org/draft-07/schema#":
        err("candidate contract", "schema must declare JSON Schema draft-07")
    for message in contract_semantic_errors(example):
        err("candidate contract example", message)

    # Guard the core epistemic boundary: a candidate handoff must stay synthetic,
    # and this export contract cannot represent a taxonomy promotion.
    for label, mutate in (
        ("real-world data class", lambda x: x.update(data_class="incident_record")),
        ("promotion state", lambda x: x["candidate"].update(lifecycle_state="PROMOTED")),
        ("unrecognized field", lambda x: x.update(unreviewed_claim=True)),
        ("lifecycle mismatch", lambda x: x["candidate"].update(source_state="REVIEW")),
        ("unknown taxonomy id", lambda x: x["candidate"]["supporting_cases"][0].update(related_pattern_id="FFT-999")),
        ("duplicate signal type", lambda x: x["candidate"]["supporting_cases"][0].update(signal_types=["SEAL_MISMATCH", "SEAL_MISMATCH"])),
        ("future timestamp", lambda x: x["candidate"].update(candidate_since=99000)),
        ("duplicate case provenance", lambda x: x["candidate"]["supporting_cases"][1].update(case_id="MO-0012")),
        ("candidate id/signature mismatch", lambda x: x["candidate"].update(id="fraud-watch:OTHER")),
        ("observation chronology", lambda x: x["candidate"]["supporting_cases"][0].update(first_observed_at=73000)),
        ("malformed supporting case", lambda x: x["candidate"].update(supporting_cases=["not an object"])),
    ):
        invalid = copy.deepcopy(example)
        mutate(invalid)
        trial = []
        check(invalid, schema, f"candidate contract negative test ({label})", trial)
        trial.extend(contract_semantic_errors(invalid))
        if not trial:
            err("candidate contract", f"negative test unexpectedly accepted {label}")

    for lifecycle, source_state, review_at, resolved_at in (
        ("UNDER_REVIEW", "REVIEW", 85000, None),
        ("VALIDATED", "VALIDATED", 85000, 88000),
        ("REJECTED", "REJECTED", 85000, 88000),
    ):
        valid = copy.deepcopy(example)
        valid["candidate"].update(
            lifecycle_state=lifecycle, source_state=source_state,
            review_started_at=review_at, resolved_at=resolved_at,
        )
        trial = []
        check(valid, schema, f"candidate contract positive test ({lifecycle})", trial)
        trial.extend(contract_semantic_errors(valid))
        if trial:
            err("candidate contract", f"valid {lifecycle} lifecycle fixture rejected: {trial[0]}")
    nullable_reason = copy.deepcopy(example)
    nullable_reason["simulation"]["sim_time_seconds_from_genesis"] = 90000.5
    nullable_reason["candidate"]["supporting_cases"][0]["classification_reason"] = None
    trial = []
    check(nullable_reason, schema, "candidate contract nullable/fractional fixture", trial)
    trial.extend(contract_semantic_errors(nullable_reason))
    if trial:
        err("candidate contract", f"valid nullable-reason/fractional-clock fixture rejected: {trial[0]}")
    print("checked candidate-MO contract schema/example; rejected real-data, promotion, lifecycle, timestamp, taxonomy-reference, duplicate-provenance, duplicate-signal, and extra-field mutations")
    return schema, example


load_contract()

print(f"checked {len(files)} pattern file(s), {len(loaded)} unique id(s)")
if errors:
    print(f"\n{len(errors)} problem(s):", file=sys.stderr)
    for e in errors:
        print("  " + e, file=sys.stderr)
    sys.exit(1)
print("all patterns valid")
