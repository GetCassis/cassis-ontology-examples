# tools/validate.py

A standalone linter for your Cassis context tree. It runs the same checks Cassis posts on your pull requests as the `cassis / ontology validation` check, so you can catch problems before pushing. Python 3.10+, PyYAML only.

```bash
pip install pyyaml
python tools/validate.py .          # repo root, cassis/ dir, or ontology/ dir all work
python tools/validate.py . --fix    # rewrite non-canonical files in place
```

What it checks:

- every `.yml` file parses as YAML (and only `.yml` files are present)
- required fields: tables need `schema_name` + `table_name`, columns `name`, joins `from_schema`/`from_table`/`to_schema`/`to_table`, metrics `name`
- enum values (`source`: `introspected`/`manual`; `cardinality`: `one_to_one`/`one_to_many`/`many_to_one`/`many_to_many`), field types, unknown fields, file locations matching content
- **canonical form**: re-serializing each file reproduces it byte-for-byte — exactly what the PR check enforces. `--fix` rewrites offending files to the canonical form (key order, block scalars, stripped defaults).
- **import-only rules the PR check misses** (report-only — `--fix` cannot fix these): metrics must carry a non-empty `display_name` and `expression`, and every `domain_path` must be a valid lowercase-slug path naming a domain that exists in the tree

Exit code 0 when everything passes, 1 otherwise; problems print one per line as `file: problem`.
