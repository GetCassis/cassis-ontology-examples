# Authoring guide

**This guide now ships with the CLI, into your own repository.**

`cassis ontology fmt` and `cassis ontology pull` write the Cassis ontology modeling guide into your checkout as `cassis/AGENTS.md`, and Cassis writes it alongside every ontology push to a synced repository. It is versioned with cassis-cli, so upgrading the CLI updates the doctrine:

```bash
pip install -U cassis-cli
cassis ontology fmt        # writes cassis/AGENTS.md
```

Keeping it in the repository rather than on a docs site means a repo-aware coding agent picks it up by convention. Commit it alongside your ontology changes. Details: [docs.getcassis.com/cli#agents-md](https://docs.getcassis.com/cli/#agents-md) and [docs.getcassis.com/agents#agents-md](https://docs.getcassis.com/agents/#agents-md).

The schema, as opposed to what to write in it, is at [docs.getcassis.com/file-format](https://docs.getcassis.com/file-format/).

For a worked example of good authoring, read [`examples/stallora/`](../examples/stallora/) in this repository.
