# Cassis ontology examples

Two complete, working ontology trees you can copy as a starting point, plus the CI check that validates them.

**The documentation lives at [docs.getcassis.com](https://docs.getcassis.com/).** This repository is only the examples.

## Examples

- [`examples/minimal/`](examples/minimal/): the smallest realistic ontology, a tiny Postgres schema. Copy its `cassis/` directory as your starting skeleton.
- [`examples/stallora/`](examples/stallora/): a complete, well-authored ontology for Stallora, our demo marketplace dataset on Snowflake. This is what "done" looks like.

Both trees are canonical for the current CLI, and both carry the managed `cassis/AGENTS.md` modeling guide, so a copy arrives in your repository with the doctrine already in place.

Copy one, point it at your own warehouse, and validate it:

```bash
pip install cassis-cli            # 1.3.0 or newer
export CASSIS_API_KEY=sk-k6-...   # Organization settings → API keys
cassis schema pull                # gitignored .schema.json snapshot of your source schema
cassis ontology fmt               # canonical formatting, refreshes cassis/AGENTS.md
cassis ontology check             # the same validation as the pull request check
```

In a checkout bound to a project (`cassis/project.yml`, `--project`, or `CASSIS_PROJECT_ID`), `check` also cross-checks the tree against your source schema: references to tables or columns the warehouse doesn't have print as **advisory warnings** — they never fail the check. A freshly copied example will warn about every table until you remodel it onto your own schema; that's expected.

## Domains are Markdown files

Domains changed format in cassis-cli 1.1.0. Each one is the `README.md` of a directory under `cassis/domains/`, with YAML frontmatter for the structured fields and the domain's prose in the body. Tables, joins and metrics stay YAML.

Cassis still reads the old `_project.yml` and `_domain.yml` files, so an un-migrated repository keeps working. `cassis ontology fmt` converts it and removes them. See [file format → Domains](https://docs.getcassis.com/file-format/#domains).

## Documentation

| Topic | Where |
|---|---|
| The file format, field by field | [docs.getcassis.com/file-format](https://docs.getcassis.com/file-format/) |
| Keeping the ontology in git: the sync model, connecting a repo, the pull request loop, troubleshooting | [docs.getcassis.com/git](https://docs.getcassis.com/git/) |
| The CLI, including copy-paste CI recipes for GitHub Actions and GitLab CI | [docs.getcassis.com/cli](https://docs.getcassis.com/cli/) |
| Letting AI agents curate the ontology | [docs.getcassis.com/agents](https://docs.getcassis.com/agents/) |
| How to write an ontology that makes the agent accurate | `cassis/AGENTS.md`, in both examples and in your own checkout |

The `docs/` directory here is kept as stubs pointing at the pages above, so older links still lead somewhere.

Questions? Reach out to your Cassis contact.
