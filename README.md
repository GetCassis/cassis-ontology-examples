# Cassis ontology examples

Two complete, working ontology trees you can copy as a starting point, plus the CI workflow that validates them.

**The documentation now lives at [docs.getcassis.com](https://docs.getcassis.com/).** This repository keeps the examples.

## Examples

- [`examples/minimal/`](examples/minimal/) — the smallest realistic ontology, a tiny Postgres schema. Copy its `cassis/` directory as your starting skeleton.
- [`examples/stallora/`](examples/stallora/) — a complete, well-authored ontology for Stallora, our demo marketplace dataset on Snowflake. This is what "done" looks like.

Copy one, point it at your own warehouse, and validate it:

```bash
pip install cassis-cli
export CASSIS_API_KEY=sk-k6-...   # Organization settings → API keys
cassis ontology fmt               # canonical formatting, and writes cassis/AGENTS.md
cassis ontology check             # the same validation as the pull request check
```

## Documentation

| Topic | Where |
|---|---|
| Keeping the ontology in git: the sync model, connecting a repo, the pull request loop, troubleshooting | [docs.getcassis.com/git](https://docs.getcassis.com/git/) |
| The file format, field by field | [docs.getcassis.com/file-format](https://docs.getcassis.com/file-format/) |
| The CLI | [docs.getcassis.com/cli](https://docs.getcassis.com/cli/) |
| Letting AI agents curate the ontology | [docs.getcassis.com/agents](https://docs.getcassis.com/agents/) |
| How to write an ontology that makes the agent accurate | `cassis/AGENTS.md` in your own checkout, written by `cassis ontology fmt` |

The `docs/` directory here is kept only as stubs pointing at the pages above, so older links still lead somewhere.

## The short version

```text
edit YAML under cassis/  →  open a PR  →  "cassis / ontology validation" check
        →  merge to your default branch  →  Cassis imports it  →  new ontology version
```

Questions? Reach out to your Cassis contact.
