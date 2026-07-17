# Cassis context — author your context through git

Your **Cassis context** is the curated semantic layer that Cassis's agent reads to turn natural-language questions into correct SQL: domains, tables and columns, joins, and governed metrics, plus the business rules that make them unambiguous.

Cassis stores the whole context as a plain YAML tree in a GitHub repository you own. That means you can build and evolve your context the way you build the rest of your data platform: in an editor, on a branch, through a pull request, with CI validation — and every merge becomes a new published context version in Cassis.

This repository documents the process and the file format, and ships working examples you can copy.

> **A note on naming:** the GitHub check-run names and the CLI command still use the word *ontology* (`cassis / ontology validation`, `cassis ontology check`). Same thing — the docs here say *context*.

## Start here

1. [How it works](docs/how-it-works.md) — what a context is, and how the git sync model works
2. [Getting started](docs/getting-started.md) — install the Cassis GitHub App, connect your repo, first sync
3. [Repository layout](docs/repository-layout.md) — the `cassis/` tree
4. [File reference](docs/file-reference.md) — every file type, field by field
5. [Authoring guide](docs/authoring-guide.md) — how to write a context that makes the agent accurate
6. [Day-to-day workflow](docs/workflow.md) — branches, pull requests, validation checks, troubleshooting

## Examples

- [`examples/minimal/`](examples/minimal/) — the smallest realistic context (a tiny Postgres schema). Copy it as your starting skeleton.
- [`examples/stallora/`](examples/stallora/) — a complete, well-authored context for Stallora, our demo marketplace dataset on Snowflake. This is what "done" looks like.

## Validate before you push

The official CLI, [`cassis-cli`](https://pypi.org/project/cassis-cli/), runs the **exact same** three-stage validation as the `cassis / ontology validation` check on your pull requests — YAML parsing, canonical round-trip, and import validation:

```bash
pip install cassis-cli
export CASSIS_API_KEY=sk-k6-...   # create one under Organization settings → API keys
cassis ontology check             # from your repo root
```

The check runs server-side via the Cassis API, so it needs network access and an API key — but it is a pure function of the files it uploads: nothing in your project is read or written, the key only authenticates the caller. Success prints `✓ YAML parsing, round-trip and import validation passed (N files).`; failures print one finding per line. Run it before you push, locally or in CI — the GitHub Action in [`.github/workflows/validate.yml`](.github/workflows/validate.yml) is a working template, and the [workflow guide](docs/workflow.md#running-the-check-in-your-own-ci) has the GitLab CI variant.

The CLI can also skip git entirely: `cassis ontology upload --project <project-id>` replaces a project's context with your local tree and publishes it. That makes bootstrapping fast — edit, upload, ask the agent, repeat, no GitHub App or merge needed — and it doubles as the publish path from CI on non-GitHub hosts. Details in the [workflow guide](docs/workflow.md#uploading-straight-to-a-project).

## The short version

```text
edit YAML under cassis/  →  open a PR  →  "cassis / ontology validation" check
        →  merge to your default branch  →  Cassis imports it  →  new context version
```

Questions? Reach out to your Cassis contact.
