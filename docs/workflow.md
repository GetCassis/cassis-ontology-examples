# Day-to-day workflow

**Moved to [docs.getcassis.com/git](https://docs.getcassis.com/git/).**

| What you were looking for | Where it is now |
|---|---|
| The edit → validate → PR → merge loop | [Ontology in git → Day-to-day loop](https://docs.getcassis.com/git/#loop) |
| Validating before you push | [CLI → ontology check](https://docs.getcassis.com/cli/#check) |
| Running the check in your own CI | [CLI → CI recipes](https://docs.getcassis.com/cli/#ci), and [Ontology in git → Gate merges in CI](https://docs.getcassis.com/git/#ci) |
| Uploading straight to a project | [CLI → ontology upload](https://docs.getcassis.com/cli/#upload) |
| Cassis-managed branches | [Ontology in git → Cassis-managed branches](https://docs.getcassis.com/git/#managed-branches) |
| The troubleshooting table | [Ontology in git → Troubleshooting](https://docs.getcassis.com/git/#troubleshooting) |

The CLI has grown since this page was written: it now also formats (`fmt`), downloads the ontology (`ontology pull`) and a local source-schema snapshot (`schema pull`), probes questions through the agent (`ontology test`), runs your eval suite (`eval run`), and manages its cases (`eval add-case`, `eval list-cases`, `eval delete-case`). See [docs.getcassis.com/cli](https://docs.getcassis.com/cli/).

This repository keeps the [example ontology trees](../examples/). See the [README](../README.md).
