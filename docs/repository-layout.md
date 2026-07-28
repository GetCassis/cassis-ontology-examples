# Repository layout

**Moved to [docs.getcassis.com/file-format](https://docs.getcassis.com/file-format/#layout).**

| What you were looking for | Where it is now |
|---|---|
| The `cassis/` tree, and the Path setting | [File format → Repository layout](https://docs.getcassis.com/file-format/#layout) |
| Domain directories as domain paths | [File format → Domains](https://docs.getcassis.com/file-format/#domains) |
| One file per table, one per metric, one `joins.yml` | [File format → Tables](https://docs.getcassis.com/file-format/#tables), [Joins](https://docs.getcassis.com/file-format/#joins), [Metrics](https://docs.getcassis.com/file-format/#metrics) |
| What must not be in the tree | [File format → What must not be in the tree](https://docs.getcassis.com/file-format/#not-in-tree) |
| The legacy `cassis/ontology/` layout | [File format → Repository layout](https://docs.getcassis.com/file-format/#layout) |

> **One correction.** This page used to say that non-YAML files in the ontology directory don't survive an export. They do now: a push or publish replaces only the ontology's own YAML, so a README or the managed `AGENTS.md` can live there safely.

This repository keeps the [example ontology trees](../examples/). See the [README](../README.md).
