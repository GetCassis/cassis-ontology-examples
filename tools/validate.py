#!/usr/bin/env python3
"""Validate a Cassis context tree (the YAML files under cassis/ontology/).

Runs the same checks Cassis runs on your pull requests ("cassis / ontology
validation"): every file parses as YAML, required fields are present, enum
values are valid, and every file is in canonical form — i.e. re-serializing
the tree reproduces your files byte-for-byte.

Also enforces the rules Cassis only checks at import time (the PR check does
not catch these, but the sync — or a manual pull — rejects the tree): metrics
must carry a non-empty display_name and expression, and every domain_path must
be a valid lowercase-slug path naming a domain that exists in the tree.

Usage:
    python tools/validate.py <path> [--fix]

<path> may be your repo root, the cassis/ directory, or the ontology/
directory itself; the tree root is auto-detected by locating _project.yml.
--fix rewrites non-canonical files in place (only files that parse and pass
the required-field checks).

Requires Python 3.10+ and PyYAML (pip install pyyaml). No other dependencies.
Exit code 0 when every tree is valid, 1 otherwise.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: pip install pyyaml")

# ---------------------------------------------------------------------------
# Canonical form — transcribed from Cassis's serializer so output matches
# byte-for-byte. Do not "improve" formatting here: the point is byte-identity.
# ---------------------------------------------------------------------------

SOURCE_VALUES = ("introspected", "manual")
CARDINALITY_VALUES = ("one_to_one", "one_to_many", "many_to_one", "many_to_many")

_UNSAFE_FILENAME_RE = re.compile(r"[^\w\-.]", re.ASCII)
_DOMAIN_PATH_RE = re.compile(r"^[a-z0-9_-]+(/[a-z0-9_-]+)*$")


class _BlockStringDumper(yaml.SafeDumper):
    """Render multi-line strings as literal block scalars (``|``)."""


def _represent_str(dumper: _BlockStringDumper, data: str) -> yaml.Node:
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


_BlockStringDumper.add_representer(str, _represent_str)


def dump_yaml(data: Any) -> str:
    """Deterministic YAML serialization, identical to Cassis's exporter."""
    return yaml.dump(
        data,
        Dumper=_BlockStringDumper,
        default_flow_style=False,
        sort_keys=True,
        allow_unicode=True,
        width=120,
    )


def _safe_filename(name: str) -> str:
    return _UNSAFE_FILENAME_RE.sub("_", name)


def _strip(d: dict[str, Any], defaults: dict[str, Any] | None = None) -> dict[str, Any]:
    """Remove keys with None, empty list, empty string, or default values."""
    out: dict[str, Any] = {}
    for k, v in d.items():
        if v is None or (isinstance(v, (list, str)) and len(v) == 0):
            continue
        if defaults and k in defaults and v == defaults[k]:
            continue
        out[k] = v
    return out


def canon_domain(d: dict[str, Any]) -> dict[str, Any]:
    return _strip(
        {
            "display_name": d.get("display_name", ""),
            "description": d.get("description"),
            "context_md": d.get("context_md"),
        }
    )


def canon_column(c: dict[str, Any]) -> dict[str, Any]:
    return _strip(
        {
            "data_type": c.get("data_type"),
            "description": c.get("description"),
            "name": c["name"],
            "nullable": c.get("nullable", True),
            "ordinal": c.get("ordinal"),
            "source": c.get("source", "introspected"),
            "synonyms": list(c.get("synonyms") or []),
            "unit": c.get("unit"),
        },
        {"nullable": True, "source": "introspected"},
    )


def canon_table(t: dict[str, Any]) -> dict[str, Any]:
    columns = sorted(
        t.get("columns") or [],
        key=lambda c: (c.get("ordinal") if c.get("ordinal") is not None else float("inf"), c.get("name", "")),
    )
    return _strip(
        {
            "approximate_row_count": t.get("approximate_row_count"),
            "columns": [canon_column(c) for c in columns] or None,
            "description": t.get("description"),
            "domain_path": t.get("domain_path"),
            "grain": list(t.get("grain") or []),
            "is_virtual": t.get("is_virtual", False),
            "lineage_description": t.get("lineage_description"),
            "schema_name": t["schema_name"],
            "source_sql": t.get("source_sql"),
            "source_tables": list(t.get("source_tables") or []),
            "sql": t.get("sql"),
            "synonyms": list(t.get("synonyms") or []),
            "table_name": t["table_name"],
            "table_type": t.get("table_type"),
        },
        {"is_virtual": False},
    )


def canon_join(j: dict[str, Any]) -> dict[str, Any]:
    return _strip(
        {
            "cardinality": j.get("cardinality") or None,
            "column_pairs": list(j.get("column_pairs") or []),
            "condition_sql": j.get("condition_sql", ""),
            "description": j.get("description"),
            "from_schema": j["from_schema"],
            "from_table": j["from_table"],
            "parse_ok": j.get("parse_ok", True),
            "source": j.get("source", "introspected"),
            "to_schema": j["to_schema"],
            "to_table": j["to_table"],
        },
        {"parse_ok": True, "source": "introspected"},
    )


def canon_metric(m: dict[str, Any]) -> dict[str, Any]:
    return _strip(
        {
            "description": m.get("description"),
            "display_name": m.get("display_name", ""),
            "domain_path": m.get("domain_path"),
            "expression": m.get("expression", ""),
            "filters": m.get("filters"),
            "name": m["name"],
            "notes": m.get("notes"),
            "precomputed_in": m.get("precomputed_in"),
            "synonyms": list(m.get("synonyms") or []),
            "table_name": m.get("table_name"),
            "table_schema": m.get("table_schema"),
            "unit": m.get("unit"),
        }
    )


# ---------------------------------------------------------------------------
# Field specifications: {field: expected type}. Unknown fields are errors —
# the importer drops them, so the file would fail the canonical-form check.
# ---------------------------------------------------------------------------

DOMAIN_FIELDS = {"display_name": str, "description": str, "context_md": str}
COLUMN_FIELDS = {
    "name": str, "data_type": str, "nullable": bool, "ordinal": int,
    "description": str, "unit": str, "synonyms": list, "source": str,
}
TABLE_FIELDS = {
    "schema_name": str, "table_name": str, "domain_path": str, "description": str,
    "synonyms": list, "grain": list, "sql": str, "lineage_description": str,
    "source_tables": list, "source_sql": str, "is_virtual": bool,
    "table_type": str, "approximate_row_count": int, "columns": list,
}
JOIN_FIELDS = {
    "from_schema": str, "from_table": str, "to_schema": str, "to_table": str,
    "condition_sql": str, "column_pairs": list, "parse_ok": bool,
    "description": str, "cardinality": str, "source": str,
}
METRIC_FIELDS = {
    "name": str, "display_name": str, "expression": str, "domain_path": str,
    "description": str, "table_schema": str, "table_name": str, "filters": str,
    "unit": str, "synonyms": list, "notes": str, "precomputed_in": str,
}
STR_LIST_FIELDS = {"synonyms", "grain", "source_tables"}
ENUM_FIELDS = {"source": SOURCE_VALUES, "cardinality": CARDINALITY_VALUES}


class TreeValidator:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.errors: list[str] = []          # unfixable problems
        self.fixable: dict[str, str] = {}    # rel path -> canonical content
        self.fixed: list[str] = []           # rel paths rewritten by --fix
        self.files: dict[str, str] = {}      # rel path -> content (as on disk)
        self.domain_paths: set[str] = {""}   # domains defined in the tree ("" = root)
        self.domain_refs: list[tuple[str, str]] = []  # (rel path, domain_path value)

    def error(self, rel: str, msg: str) -> None:
        self.errors.append(f"{rel}: {msg}")

    def check_mapping(self, rel: str, data: Any, spec: dict[str, type], required: tuple[str, ...], where: str = "") -> bool:
        at = f" ({where})" if where else ""
        if not isinstance(data, dict):
            self.error(rel, f"must be a YAML mapping{at}, got {type(data).__name__}")
            return False
        ok = True
        for field in required:
            if not isinstance(data.get(field), str) or not data[field]:
                self.error(rel, f"missing required field '{field}'{at}")
                ok = False
        for key, value in data.items():
            if key not in spec:
                self.error(rel, f"unknown field '{key}'{at} — fails the `cassis / ontology validation` check on pull requests (the field disappears on round-trip; import silently drops it)")
                ok = False
            elif value is not None:  # explicit null is treated as absent
                expected = spec[key]
                if expected is int and isinstance(value, bool) or not isinstance(value, expected):
                    self.error(rel, f"field '{key}'{at} must be a {expected.__name__}, got {type(value).__name__}")
                    ok = False
                elif key in ENUM_FIELDS and value not in ENUM_FIELDS[key]:
                    self.error(rel, f"invalid {key} '{value}'{at} — must be one of: {', '.join(ENUM_FIELDS[key])}")
                    ok = False
                elif key in STR_LIST_FIELDS and not all(isinstance(x, str) for x in value):
                    self.error(rel, f"field '{key}'{at} must be a list of strings")
                    ok = False
        return ok

    def check_table(self, rel: str, data: Any) -> dict[str, Any] | None:
        if not self.check_mapping(rel, data, TABLE_FIELDS, ("schema_name", "table_name")):
            return None
        ok = True
        for i, col in enumerate(data.get("columns") or []):
            if not self.check_mapping(rel, col, COLUMN_FIELDS, ("name",), where=f"columns[{i}]"):
                ok = False
        if not ok:
            return None
        expected = f"tables/{data['schema_name']}/{_safe_filename(data['table_name'])}.yml"
        if rel != expected:
            self.error(rel, f"file location does not match its schema_name/table_name — expected {expected}")
            return None
        return canon_table(data)

    def check_joins(self, rel: str, data: Any) -> list[dict[str, Any]] | None:
        if not isinstance(data, list):
            self.error(rel, f"must be a YAML list of joins, got {type(data).__name__}")
            return None
        ok = True
        for i, join in enumerate(data):
            where = f"join #{i + 1}"
            if not self.check_mapping(rel, join, JOIN_FIELDS, ("from_schema", "from_table", "to_schema", "to_table"), where=where):
                ok = False
                continue
            for pair in join.get("column_pairs") or []:
                if not isinstance(pair, dict):
                    self.error(rel, f"column_pairs entries must be mappings ({where})")
                    ok = False
        if not ok:
            return None
        return [canon_join(j) for j in sorted(
            data,
            key=lambda j: (j["from_schema"], j["from_table"], j["to_schema"], j["to_table"], j.get("condition_sql") or ""),
        )]

    def check_metric(self, rel: str, data: Any) -> dict[str, Any] | None:
        if not self.check_mapping(rel, data, METRIC_FIELDS, ("name",)):
            return None
        for field in ("display_name", "expression"):
            if not data.get(field):
                self.error(rel, f"metric has no {field} — the PR validation check passes without it, but import fails: \"Metric '{data['name']}': {field} is required\"")
        expected = f"metrics/{_safe_filename(data['name'])}.yml"
        if rel != expected:
            self.error(rel, f"file location does not match its name — expected {expected}")
            return None
        return canon_metric(data)

    def validate(self, fix: bool) -> bool:
        for path in sorted(p for p in self.root.rglob("*") if p.is_file()):
            rel = path.relative_to(self.root).as_posix()
            if not rel.endswith(".yml"):
                hint = "rename it to .yml" if rel.endswith(".yaml") else "only .yml files belong in the tree"
                self.error(rel, f"unexpected file — fails the `cassis / ontology validation` check on pull requests; import silently ignores it ({hint})")
                continue
            try:
                self.files[rel] = path.read_bytes().decode("utf-8")
            except UnicodeDecodeError:
                self.error(rel, "file is not valid UTF-8")

        for rel, content in self.files.items():
            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError as exc:
                self.error(rel, f"YAML parse error: {exc}")
                continue
            if data is None:
                self.error(rel, "file is empty — fails the `cassis / ontology validation` check on pull requests (import silently skips it); delete it or fill it in")
                continue

            canonical: Any = None
            if rel == "_project.yml":
                canonical = canon_domain(data) if self.check_mapping(rel, data, DOMAIN_FIELDS, ()) else None
            elif re.fullmatch(r"domains/.+/_domain\.yml", rel):
                self.domain_paths.add(rel.removeprefix("domains/").removesuffix("/_domain.yml"))
                if self.check_mapping(rel, data, DOMAIN_FIELDS, ()):
                    canonical = canon_domain(data)
                    domain_path = rel.removeprefix("domains/").removesuffix("/_domain.yml")
                    if not _DOMAIN_PATH_RE.fullmatch(domain_path):
                        self.error(rel, f"domain path '{domain_path}' must be lowercase slugs ([a-z0-9_-], slash-separated)")
                        canonical = None
            elif rel.startswith("tables/"):
                if isinstance(data, dict) and isinstance(data.get("domain_path"), str):
                    self.domain_refs.append((rel, data["domain_path"]))
                canonical = self.check_table(rel, data)
            elif rel == "joins.yml":
                canonical = self.check_joins(rel, data)
                if canonical is not None and not canonical:
                    self.error(rel, "joins.yml is empty — Cassis only writes it when joins exist; delete the file")
                    canonical = None
            elif rel.startswith("metrics/"):
                if isinstance(data, dict) and isinstance(data.get("domain_path"), str):
                    self.domain_refs.append((rel, data["domain_path"]))
                canonical = self.check_metric(rel, data)
            else:
                self.error(rel, "not a recognized context file location — fails the `cassis / ontology validation` check on pull requests; import silently drops it")

            if canonical is None:
                continue
            canonical_text = dump_yaml(canonical)
            if canonical_text != content:
                self.fixable[rel] = canonical_text

        # Import-only rules: the PR validation check does not enforce these,
        # but the import (sync on the default branch, or a manual pull) does.
        for rel, dp in self.domain_refs:
            if dp and not _DOMAIN_PATH_RE.fullmatch(dp):
                self.error(rel, f"domain_path '{dp}' is malformed — the PR validation check passes, but import fails: \"Invalid domain path '{dp}': use lowercase slug segments separated by '/'\"")
            elif dp and dp not in self.domain_paths:
                self.error(rel, f"domain_path '{dp}' has no domains/{dp}/_domain.yml in the tree — the PR validation check passes, but import fails: \"references domain '{dp}', which is not in the import payload\"")

        for rel, canonical_text in self.fixable.items():
            if fix:
                (self.root / rel).write_bytes(canonical_text.encode("utf-8"))
                self.fixed.append(rel)
            else:
                content = self.files[rel]
                diff_line = next(
                    (i + 1 for i, (a, b) in enumerate(zip(content.splitlines(), canonical_text.splitlines())) if a != b),
                    min(len(content.splitlines()), len(canonical_text.splitlines())) + 1,
                )
                self.error(rel, f"not in canonical form (first difference at line {diff_line}) — run with --fix")

        return not self.errors


def find_tree_roots(path: Path) -> list[Path]:
    """Locate context tree roots (directories holding _project.yml) under path."""
    path = path.resolve()
    if (path / "_project.yml").is_file():
        return [path]
    for candidate in (path / "cassis" / "ontology", path / "ontology"):
        if (candidate / "_project.yml").is_file():
            return [candidate]
    return sorted(
        {p.parent for p in path.rglob("_project.yml") if ".git" not in p.parts},
        key=lambda r: (len(r.parts), str(r)),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Cassis context tree (see module docstring).")
    parser.add_argument("path", help="repo root, cassis/ dir, or ontology/ dir")
    parser.add_argument("--fix", action="store_true", help="rewrite non-canonical files in place")
    args = parser.parse_args()

    base = Path(args.path)
    if not base.exists():
        print(f"error: no such path: {base}", file=sys.stderr)
        return 1
    roots = find_tree_roots(base)
    if not roots:
        print(f"error: no context tree found under {base} (no _project.yml)", file=sys.stderr)
        return 1

    all_ok = True
    for root in roots:
        display = os.path.relpath(root)
        validator = TreeValidator(root)
        ok = validator.validate(fix=args.fix)
        print(f"{display}: {len(validator.files)} YAML file(s)")
        for rel in validator.fixed:
            print(f"  fixed: {rel}")
        for error in validator.errors:
            print(f"  {error}")
        print(f"  {'OK — all files valid and canonical' if ok else 'FAIL — ' + str(len(validator.errors)) + ' problem(s)'}")
        all_ok = all_ok and ok
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
