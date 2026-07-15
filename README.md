# Cassis context — author your context through git

Your **Cassis context** is the curated semantic layer that Cassis's agent reads to turn natural-language questions into correct SQL: domains, tables and columns, joins, and governed metrics, plus the business rules that make them unambiguous.

Cassis stores the whole context as a plain YAML tree in a GitHub repository you own. That means you can build and evolve your context the way you build the rest of your data platform: in an editor, on a branch, through a pull request, with CI validation — and every merge becomes a new published context version in Cassis.

This repository documents the process and the file format, and ships working examples you can copy.

> **A note on naming:** the file paths and GitHub check names currently use the word *ontology* (`cassis/ontology/`, `cassis / ontology validation`). Same thing — the docs here say *context*, the paths say `ontology`.

## Start here

1. [How it works](docs/how-it-works.md) — what a context is, and how the git sync model works
2. [Getting started](docs/getting-started.md) — install the Cassis GitHub App, connect your repo, first sync
3. [Repository layout](docs/repository-layout.md) — the `cassis/ontology/` tree
4. [File reference](docs/file-reference.md) — every file type, field by field
5. [Authoring guide](docs/authoring-guide.md) — how to write a context that makes the agent accurate
6. [Day-to-day workflow](docs/workflow.md) — branches, pull requests, validation checks, troubleshooting

## Examples

- [`examples/minimal/`](examples/minimal/) — the smallest realistic context (a tiny Postgres schema). Copy it as your starting skeleton.
- [`examples/stallora/`](examples/stallora/) — a complete, well-authored context for Stallora, our demo marketplace dataset on Snowflake. This is what "done" looks like.

## Validate locally

[`tools/validate.py`](tools/validate.py) runs the same checks Cassis runs on your pull requests — YAML parsing, required fields, and canonical formatting — so you can catch problems before you push:

```bash
pip install pyyaml
python tools/validate.py .        # check
python tools/validate.py . --fix  # rewrite files in canonical form
```

The script is standalone — copy it into your own repository to run it there, or run it from a checkout of this repo pointing at yours (`python tools/validate.py /path/to/your-repo`). The GitHub Action in [`.github/workflows/validate.yml`](.github/workflows/validate.yml) shows how to run it in your own CI.

## The short version

```text
edit YAML under cassis/ontology/  →  open a PR  →  "cassis / ontology validation" check
        →  merge to your default branch  →  Cassis imports it  →  new context version
```

Questions? Reach out to your Cassis contact.
