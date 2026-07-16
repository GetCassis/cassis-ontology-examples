# How it works

This page explains what a Cassis context is and how the git sync model behaves: what triggers an import, what the check runs mean, and how branches map between git and Cassis.

## What a context is

Your Cassis context is everything the agent knows about your data beyond raw table names: **domains** that group related tables and carry free-form business context (`context_md`), **tables and columns** with descriptions, synonyms, and grain, **joins** that tell the agent how tables relate, and **metrics** — governed definitions of your KPIs so "revenue" always means the same SQL expression. All of it lives as plain YAML files; see the [file reference](file-reference.md) for every file type and field, and the [authoring guide](authoring-guide.md) for how to write content that makes the agent accurate.

## The git model

**Your git repository is the source of truth.** The whole context lives as a YAML tree directly under one directory of the connected repository — the project's **Path** setting, `cassis/` by default (the docs use `cassis/` throughout; substitute your own if you changed it):

```text
cassis/
├── _project.yml              # project-level context
├── domains/<path>/_domain.yml
├── tables/<schema>/<table>.yml
├── joins.yml
└── metrics/<name>.yml
```

(See [repository layout](repository-layout.md) for the full tree.)

Three properties follow from this:

- **Imports are full-replace.** The tree fully describes the context. When Cassis imports, whatever is in the tree becomes the context — adding a file adds an object, deleting a file deletes it. There is no partial merge, and edits made in the Cassis UI that were never published to git are overwritten by the next import.
- **Every successful import creates a new immutable published context version**, labeled `Synced from git`, recording the commit SHA it came from. Version history in Cassis is therefore a mirror of your default branch's history (the default branch must be named `main` — see the [prerequisites](getting-started.md#prerequisites)) for the files under `cassis/`.
- **The sync is two-way, without echo loops.** Cassis can also publish from its UI back to git (see below). A version created by a Cassis-side publish already records its commit SHA, so the webhook triggered by that commit recognizes it and does not create a duplicate version.

### git → Cassis: imports

A push to the repository's **default branch** that touches files under `cassis/` triggers an import: Cassis reads the whole tree at the branch head, replaces its context with it, and publishes a new version. This is what production reads — the agent answering questions (in the app, over MCP, or in Slack) always uses the latest published version, so merging to the default branch is your deploy step.

If the import fails (malformed YAML, missing required field), **Cassis keeps its previous context** and reports the failure on the commit instead of failing silently — see the check runs below.

### Cassis → git: publishing

Publishing from the Cassis UI writes back to the repository:

- Publishing the main context commits the full YAML tree **directly to the default branch** (commit message `chore(ontology): publish v{n}`, or `chore(ontology): publish v{n} (<label>)` when the publish carries a label).
- Publishing a Cassis branch commits to a git branch named `cassis/branch/<name>` and opens a pull request onto the default branch, so the change goes through your normal review. Nothing changes in production until that PR is merged and imported.

Git branch names under `cassis/` are managed by Cassis — treat them as read-only ([more in the workflow guide](workflow.md#cassis-managed-branches)).

## The two check runs

Cassis posts two GitHub check runs so problems surface where you work:

- **`cassis / ontology validation`** — posted on the head commit of any pull request that touches files under `cassis/`, whatever the branch. (One opt-out: the project setting **"Run ontology checks on Cassis-created branches"** — when off, the check is skipped for branches Cassis itself opens under `cassis/*`.) It runs three fail-fast stages: every YAML file must parse; the whole tree must survive a canonical round-trip (Cassis reads it and re-serializes it; the output must match byte-for-byte, which catches non-canonical formatting that would produce noisy diffs later); and the tree must pass the exact same validation the post-merge import runs (metric completeness, `domain_path` references, domain-path format). Green means "Ontology is valid" with the summary `YAML parsing, round-trip and import validation passed ({n} files).` — a tree that passes the check cannot fail validation when its merge is synced. The [CLI check](workflow.md#the-loop) gives the same verdict before you push.
- **`cassis / ontology sync`** — posted on the pushed commit after a push to the default branch. It answers "*did* this import?": success reads `Imported into Cassis: v{n}.` (or `Imported into Cassis: up to date.` when the content was already recorded); failure reads "Ontology import failed" with the reason, and Cassis keeps its previous context.

The [day-to-day workflow](workflow.md) covers both checks in detail, including a troubleshooting table for every failure mode.

## Branches

Cassis has its own lightweight branches for working on the context in isolation, and they map onto git branches:

| Cassis side | git side |
|---|---|
| Main context | The default branch (the `cassis/` tree at its head) |
| A Cassis branch named `<name>` | `cassis/branch/<name>` (lowercased, non-alphanumerics become `-`) |

Publishing a Cassis branch opens (or updates in place) a PR from its `cassis/branch/<name>` branch onto the default branch. When that PR is merged, the webhook imports the result and marks the Cassis branch as merged. In the other direction, you can simply create your own git branches and PRs — the validation check runs on any PR touching `cassis/` files, not just Cassis-created ones.

Either way, the invariant holds: **the default branch is what production reads** once imported.

## Next steps

- [Getting started](getting-started.md) — connect the GitHub App and run your first sync
- [Repository layout](repository-layout.md) and [file reference](file-reference.md) — the file format
- [Day-to-day workflow](workflow.md) — the edit → PR → merge loop
