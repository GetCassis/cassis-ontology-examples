# Day-to-day workflow

Once [set up](getting-started.md), evolving your context is a normal git loop. This page walks through it and lists every way it can fail and how to fix it.

## The loop

1. **Branch** — create a feature branch in your repository, as you would for any other change.
2. **Edit** — change the YAML under `cassis/ontology/`: add a table file, refine a description, add a metric ([file reference](file-reference.md), [authoring guide](authoring-guide.md)).
3. **Validate locally** — run the validator before pushing (it's [`tools/validate.py`](../tools/validate.py) from this repo — copy it into your own repo, or run it from a checkout of this repo pointing at yours):

   ```bash
   python tools/validate.py .        # check
   python tools/validate.py . --fix  # rewrite files in canonical form
   ```

   It runs everything the PR check runs, **plus** the import-only rules the PR check misses (metric `display_name`/`expression`, `domain_path` references — see [troubleshooting](#troubleshooting)). A clean local run therefore means a green check *and* a clean import.
4. **Open a PR** — any pull request touching `cassis/` files gets the **`cassis / ontology validation`** check on its head commit, whatever the branch is named. The check parses every YAML file, then round-trips the whole tree (deserialize, re-serialize, byte-compare) to catch anything that wouldn't import cleanly or isn't in canonical form. Green reads "Ontology is valid". Note it validates the full tree at the head commit, not just the files the PR changed — so it also catches pre-existing problems.
5. **Merge to the default branch** — the push webhook imports the tree into Cassis and posts the **`cassis / ontology sync`** check on the merge commit:
   - **Success** — `Imported into Cassis: v{n}.` The new version is live: it's what the agent reads from now on, and it appears on the project's Versions page labeled `Synced from git` with the commit SHA.
   - **Failure** — "Ontology import failed", with the reason listed. **Cassis keeps its previous context** — nothing breaks in production. Fix the files and push again.

Direct pushes to the default branch also import — the PR is where validation happens, not a requirement. If you push directly, you skip the validation check, so run the validator locally first.

Two behaviors worth knowing:

- **Imports replace everything.** The tree fully describes the context, so an import also overwrites any unpublished edits made in the Cassis UI. If your team edits in both places, publish Cassis-side work to git before merging unrelated git changes.
- **Imports no-op when nothing changed.** If the content matches what Cassis already has and the commit SHA is already recorded, no new version is created (the sync check reads `Imported into Cassis: up to date.`).

## Cassis-managed branches

Branches named `cassis/branch/*` and the branch `cassis/ontology-publish` are created and updated by Cassis when someone publishes from the Cassis UI:

- Publishing a Cassis branch named `<name>` commits to `cassis/branch/<name>` (commit message `chore(ontology): publish proposal`, or `chore(ontology): publish proposal (<label>)` when the publish carries a label) and opens a PR onto the default branch (titled "Ontology update", or "Ontology update (<label>)"). Re-publishing the same branch updates that PR in place. Merging it imports the change and marks the Cassis branch as merged.
- `cassis/ontology-publish` is reserved for Cassis-side publish proposals.

**Don't hand-edit these branches** — your commits will be overwritten by the next publish from Cassis. Make your own changes on your own branches (or the default branch); those are yours.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Validation check fails: "N file(s) with YAML errors", files annotated with `YAML parse error: …` | Malformed YAML (bad indentation, unquoted `:` in a string, tab characters) | Fix the annotated file. `python tools/validate.py .` reproduces the error locally with details. |
| Sync check fails with `Ontology file is missing required field: 'schema_name'` (or `'table_name'`, `'name'`, `'from_schema'`, …) | A file omits a required field: tables need `schema_name` and `table_name`; columns and metrics need `name`; joins need all four endpoints (`from_schema`, `from_table`, `to_schema`, `to_table`) | Add the missing field. On a PR this surfaces earlier, as a validation-check failure titled "Ontology round-trip failed". |
| Validation check fails: "Ontology round-trip failed" / `Could not deserialize/re-serialize the ontology: …` | A value Cassis can't interpret — most often an invalid enum value, e.g. a join `cardinality` outside `one_to_one` / `one_to_many` / `many_to_one` / `many_to_many`, or a `source` outside `introspected` / `manual` | Use one of the allowed values. (On a direct push the sync check shows the generic "Unexpected error while importing the ontology" — another reason to go through a PR.) |
| Validation check fails: "N file(s) differ after round-trip", files annotated with `Content differs after round-trip` | Valid YAML, but not in Cassis's canonical form: different key order, flow style (`[a, b]`), quoting, redundant default values (`is_virtual: false`), or a filename that doesn't match the content | Run `python tools/validate.py . --fix` to rewrite the files canonically, and commit the result. |
| Sync check fails with `Malformed YAML in ontology files: …` | Broken YAML pushed directly to the default branch (no PR, so no validation check ran) | Fix and push again — Cassis kept the previous context. Validate locally before direct pushes. |
| Sync check fails (or a manual pull returns 400) with `Metric 'x': display_name is required` or `Metric 'x': expression is required` — **after a green validation check** | The metric file omits `display_name` or `expression` (or has it empty). The PR check only verifies format; metric completeness is enforced at import | Add the missing field. `python tools/validate.py .` catches this locally. |
| Sync check fails (or a manual pull returns 400) with `Table 'S.T' references domain 'x/y', which is not in the import payload` (same wording for `Metric '…'`) — **after a green validation check** | A table's or metric's `domain_path` names a domain with no `domains/<path>/_domain.yml` in the tree — often a domain directory that was renamed or deleted without updating the references, or a missing `_domain.yml` at that level | Create `domains/<path>/_domain.yml` or fix the `domain_path`, in the same PR. The local validator catches this. |
| Sync check fails (or a manual pull returns 400) with `Invalid domain path 'X': use lowercase slug segments separated by '/'` — **after a green validation check** | A `domain_path` contains uppercase, spaces, or characters outside `a-z0-9_-` in a segment | Rename to lowercase slug segments separated by `/` (and rename the matching domain directory). The local validator catches this. |
| Sync or pull fails with `No ontology files found in the connected repository` | The `cassis/ontology/` directory is missing or empty on the default branch — often files placed at the wrong path (e.g. `ontology/` at the repo root) | Make sure the tree lives under `cassis/ontology/` on the default branch. |
| No check runs ever appear; merges don't import | The Cassis GitHub App is not installed on this repository, or the project's configured repository doesn't match — Cassis skips events for repositories its installation can't access | On the "Organization · GitHub" page, re-check the App installation covers the repository and the project's **Repository** setting is the right `owner/name`. Saving an inaccessible repo fails with "The repository '…' is not accessible by your organization's GitHub App installation." |
| Publishing from Cassis fails with `GitHub refused to … (403). The Cassis GitHub App installation lacks the required permissions — it needs 'Contents: write' and 'Pull requests: write' on the repository.` | The App installation's repository permissions were narrowed | Accept the App's current permissions on GitHub (organization settings → GitHub Apps), then retry. |
| Publishing from Cassis fails with `Git repository or branch not found (404) … check the configured repository and that the default branch exists.` | The configured repository was renamed/deleted, or has no default branch | Fix the **Repository** setting, or push an initial commit to create the default branch. |

If a sync failed and you've fixed the cause but there's no new commit to push, you can force a re-import: `POST /api/projects/{project_id}/git-sync/pull` (organization admin) — see [getting started](getting-started.md#fallback-pulling-manually).

## See also

- [How it works](how-it-works.md) — the model behind all of this
- [Repository layout](repository-layout.md) and [file reference](file-reference.md) — what goes in each file
