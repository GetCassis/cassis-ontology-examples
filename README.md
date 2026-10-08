# Cassis context examples

Two complete, working context trees you can copy as a starting point, plus the CI check that validates them.

**The documentation lives at [docs.getcassis.com](https://docs.getcassis.com/).** This repository is only the examples.

## Examples

- [`examples/minimal/`](examples/minimal/): the smallest realistic context, a tiny Postgres schema. Copy its `cassis/` directory as your starting skeleton.
- [`examples/stallora/`](examples/stallora/): a complete, well-authored context for Stallora, our demo marketplace dataset on Snowflake. This is what "done" looks like.

Both trees are canonical for the current CLI, and both carry the managed `cassis/AGENTS.md` modeling guide, so a copy arrives in your repository with the doctrine already in place.

Copy one, point it at your own warehouse, and validate it:

```bash
pip install "cassis-cli~=3.0"     # any 3.x release
export CASSIS_API_KEY=sk-k6-...   # Organization settings → API keys
cassis schema pull                # gitignored .schema.json snapshot of your source schema
cassis context fmt                # canonical formatting, refreshes cassis/AGENTS.md
cassis context check              # the same validation as the pull request check
```

In a checkout bound to a project (`cassis/project.yml`, `--project`, or `CASSIS_PROJECT_ID`), `check` also cross-checks the tree against your source schema: references to tables or columns the warehouse doesn't have print as **advisory warnings** — they never fail the check. A freshly copied example will warn about every table until you remodel it onto your own schema; that's expected.

## Domains are Markdown files

Domains changed format in cassis-cli 1.1.0. Each one is the `README.md` of a directory under `cassis/domains/`, with YAML frontmatter for the structured fields and the domain's prose in the body. Tables, joins and metrics stay YAML.

Cassis still reads the old `_project.yml` and `_domain.yml` files, so an un-migrated repository keeps working. `cassis context fmt` converts it and removes them. See [file format: domains](https://docs.getcassis.com/reference/schema/domains/).

## Documentation

| Topic | Where |
|---|---|
| The file format, field by field | [docs.getcassis.com/reference/schema](https://docs.getcassis.com/reference/schema/) |
| Keeping the context in Git: connecting a repo and the pull request loop | [docs.getcassis.com/build/git-workflow](https://docs.getcassis.com/build/git-workflow/) |
| The CLI command reference | [docs.getcassis.com/reference/cli](https://docs.getcassis.com/reference/cli/) |
| Copy-paste CI recipes for GitHub Actions and GitLab CI | [docs.getcassis.com/build/ci](https://docs.getcassis.com/build/ci/) |
| Letting analytics agents curate the context | [docs.getcassis.com/curate/agent](https://docs.getcassis.com/curate/agent/) |
| How to write a context that makes the agent accurate | `cassis/AGENTS.md`, in both examples and in your own checkout |

The `docs/` directory here is kept as stubs pointing at the pages above, so older links still lead somewhere.

Questions? Reach out to your Cassis contact.
