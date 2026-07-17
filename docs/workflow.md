# Day-to-day workflow

Once [set up](getting-started.md), evolving your context is a normal git loop. This page walks through it and lists every way it can fail and how to fix it.

## The loop

1. **Branch** — create a feature branch in your repository, as you would for any other change.
2. **Edit** — change the YAML under `cassis/` (the project's **Path** directory): add a table file, refine a description, add a metric ([file reference](file-reference.md), [authoring guide](authoring-guide.md)).
3. **Validate before you push** — run the official CLI, [`cassis-cli`](https://pypi.org/project/cassis-cli/), from your repo root:

   ```bash
   pip install cassis-cli
   cassis ontology check
   ```

   It runs the **exact same** three-stage validation as the PR check — YAML parsing, canonical round-trip, import validation — server-side via the Cassis API, so it needs network access and an API key: create one in Cassis under **Organization settings → API keys** (keys start with `sk-k6-`) and expose it as `CASSIS_API_KEY` (or pass `--api-key`). If the project exports under a custom **Path**, pass it with `--base-path` (or `CASSIS_BASE_PATH`). The check is a pure function of the files it uploads — nothing in your project is read or written.

   Success prints `✓ YAML parsing, round-trip and import validation passed (N files).`; failures print one per line as `cassis/<path>: <message> (<stage>)`. A clean run means a green PR check *and* a clean import.
4. **Open a PR** — any pull request touching files under `cassis/` gets the **`cassis / ontology validation`** check on its head commit, whatever the branch is named. The check runs three fail-fast stages: it parses every YAML file, round-trips the whole tree (deserialize, re-serialize, byte-compare) to catch anything that isn't in canonical form, then runs the same validation the post-merge import runs (metric `display_name`/`expression`, `domain_path` references, domain-path format) — so a tree that passes the check cannot fail validation when its merge is synced. Green reads "Ontology is valid". Note it validates the full tree at the head commit, not just the files the PR changed — so it also catches pre-existing problems.
5. **Merge to the default branch** — the push webhook imports the tree into Cassis and posts the **`cassis / ontology sync`** check on the merge commit:
   - **Success** — `Imported into Cassis: v{n}.` The new version is live: it's what the agent reads from now on, and it appears on the project's Versions page labeled `Synced from git` with the commit SHA.
   - **Failure** — "Ontology import failed", with the reason listed. **Cassis keeps its previous context** — nothing breaks in production. Fix the files and push again.

Direct pushes to the default branch also import — the PR is where validation happens, not a requirement. If you push directly, you skip the validation check, so run `cassis ontology check` first.

Two behaviors worth knowing:

- **Imports replace everything.** The tree fully describes the context, so an import also overwrites any unpublished edits made in the Cassis UI. If your team edits in both places, publish Cassis-side work to git before merging unrelated git changes.
- **Imports no-op when nothing changed.** If the content matches what Cassis already has and the commit SHA is already recorded, no new version is created (the sync check reads `Imported into Cassis: up to date.`).

## Running the check in your own CI

`cassis ontology check` is built for CI gates, with stable exit codes: **0** valid, **1** validation failed (findings printed), **2** usage error (missing API key, no context directory, unreadable file, oversized tree), **3** transport/API error (unreachable API, invalid key). The size ceiling — 2000 files / 5 MB — is far above any real context. Store the API key as a CI secret.

GitHub Actions (this repo's [`validate.yml`](../.github/workflows/validate.yml) is a working template — in your own repo a single `cassis ontology check` at the root replaces its two example steps):

```yaml
jobs:
  context-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install cassis-cli
      - run: cassis ontology check
        env:
          CASSIS_API_KEY: ${{ secrets.CASSIS_API_KEY }}
```

GitLab CI, if that's where your pipelines live:

```yaml
context-check:
  image: python:3.12-slim
  script:
    - pip install cassis-cli
    - cassis ontology check
  variables:
    CASSIS_API_KEY: $CASSIS_API_KEY
```

On GitHub this duplicates the `cassis / ontology validation` check Cassis already posts on your PRs — harmless, and useful if you want the verdict inside your own pipeline; on any other CI system it's the only way to get it.

## Uploading straight to a project

Since cassis-cli 0.2.0, the CLI can also push the local tree **directly into a project**, skipping git entirely:

```bash
cassis ontology upload --project <project-id>                     # replace + publish
cassis ontology upload --project <project-id> --no-publish        # replace the unpublished context only
cassis ontology upload --project <project-id> --label "release 1"  # label the published version
```

- `--project` takes the project ID — the UUID in the project's URL in Cassis (also the `CASSIS_PROJECT_ID` env var). The other flags (`--api-key`, `--api-url`, `--base-path`, `--json`) work exactly as for `check`, and the exit codes are the same: **0** uploaded, **1** validation failed (nothing imported), **2** usage error, **3** transport/API error (including a project the key's organization can't edit).
- It **replaces the project's entire context** with the uploaded tree, after the same validation as `check` — a failing tree is rejected with the reason (`Ontology upload rejected: Metric 'x': expression is required`) and the project is untouched.
- By default it **publishes immediately**: success prints `✓ Ontology uploaded and published as v{n} (… tables, … domains, … joins, … metrics).` With `--no-publish`, the tree becomes the project's unpublished context, to review and publish in Cassis — except on a never-published project, where the first upload always goes live as v1.
- Publishing is **idempotent**: re-uploading content identical to the published version reports that version instead of creating a new one, so a CI job re-running on unchanged files is a no-op.

Two places it shines:

- **Bootstrapping a context.** While building the first version, iterate without the GitHub App, a PR, or a merge: edit locally, `cassis ontology upload`, ask the agent, repeat. Wire up [git sync](getting-started.md) once the context stabilizes — see [getting started](getting-started.md#option-b--author-from-scratch) for the full bootstrap flow.
- **Publishing from CI on non-GitHub hosts.** If your repository lives where the GitHub App can't reach (GitLab, Bitbucket, …), your pipeline can replicate the whole sync loop: `check` on merge requests, `upload` on the default branch. On GitLab:

  ```yaml
  context-publish:
    image: python:3.12-slim
    rules:
      - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    script:
      - pip install cassis-cli
      - cassis ontology upload --project $CASSIS_PROJECT_ID
    variables:
      CASSIS_API_KEY: $CASSIS_API_KEY
  ```

  (The GitHub Actions equivalent is the same job gated on `if: github.ref == 'refs/heads/main'`.)

One caution: on a project connected to the GitHub App, the repository stays the source of truth — the next import (a merge to the default branch, or a manual pull) replaces whatever you uploaded. Use `upload` for bootstrap iteration or as the publish path when git sync isn't connected; don't run both against the same project.

## Cassis-managed branches

Git branch names under `cassis/` are reserved for Cassis; it creates and updates them when someone publishes from the Cassis UI. Publishing a Cassis branch named `<name>` commits to `cassis/branch/<name>` (commit message `chore(ontology): publish proposal`, or `chore(ontology): publish proposal (<label>)` when the publish carries a label) and opens a PR onto the default branch (titled "Ontology update", or "Ontology update (<label>)"). Re-publishing the same branch updates that PR in place. Merging it imports the change and marks the Cassis branch as merged.

**Don't hand-edit these branches** — your commits will be overwritten by the next publish from Cassis. Make your own changes on your own branches (or the default branch); those are yours.

By default the `cassis / ontology validation` check runs on these PRs like any other. If your review flow doesn't need it there (the tree was just written by Cassis, so it's canonical), turn off **"Run ontology checks on Cassis-created branches"** in the project's git settings — checks are then skipped for branches Cassis opens (`cassis/*`) and still run on all other branches.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Validation check fails: "N file(s) with YAML errors", files annotated with `YAML parse error: …` | Malformed YAML (bad indentation, unquoted `:` in a string, tab characters) | Fix the annotated file. `cassis ontology check` reproduces the error with details. |
| Sync check fails with `Ontology file is missing required field: 'schema_name'` (or `'table_name'`, `'name'`, `'from_schema'`, …) | A file omits a required field: tables need `schema_name` and `table_name`; columns and metrics need `name`; joins need all four endpoints (`from_schema`, `from_table`, `to_schema`, `to_table`) | Add the missing field. On a PR this surfaces earlier, as a validation-check failure titled "Ontology round-trip failed". |
| Validation check fails: "Ontology round-trip failed" / `Could not deserialize/re-serialize the ontology: …` | A value Cassis can't interpret — most often an invalid enum value, e.g. a join `cardinality` outside `one_to_one` / `one_to_many` / `many_to_one` / `many_to_many`, or a `source` outside `introspected` / `manual` | Use one of the allowed values. (On a direct push the sync check reports it as `Invalid value in ontology files: …` — another reason to go through a PR.) |
| Validation check fails: "N file(s) differ after round-trip", files annotated with `Content differs after round-trip` | Valid YAML, but not in Cassis's canonical form: different key order, flow style (`[a, b]`), quoting, redundant default values (`is_virtual: false`), or a filename that doesn't match the content | Rewrite the annotated file by hand to the [canonical form](file-reference.md#canonical-form) — usually a key-order or block-style fix. For bulk reformatting, publish from Cassis instead: every Cassis-side publish rewrites the whole tree canonically. |
| Sync check fails with `Malformed YAML in ontology files: …` | Broken YAML pushed directly to the default branch (no PR, so no validation check ran) | Fix and push again — Cassis kept the previous context. Run `cassis ontology check` before direct pushes. |
| Validation check fails: "Ontology validation failed" / `The ontology would be rejected at import: Metric 'x': display_name is required` (or `… expression is required`) | The metric file omits `display_name` or `expression` (or has it empty) — required at import, and the check enforces the same rule | Add the missing field. (On a direct push the same error fails the sync check, or a manual pull returns 400.) |
| Validation check fails: "Ontology validation failed" / `The ontology would be rejected at import: Table 'S.T' references domain 'x/y', which is not in the import payload` (same wording for `Metric '…'`) | A table's or metric's `domain_path` names a domain with no `domains/<path>/_domain.yml` in the tree — often a domain directory that was renamed or deleted without updating the references, or a missing `_domain.yml` at that level | Create `domains/<path>/_domain.yml` or fix the `domain_path`, in the same PR. |
| Validation check fails: "Ontology validation failed" / `The ontology would be rejected at import: Invalid domain path 'X': use lowercase slug segments separated by '/'` | A `domain_path` contains uppercase, spaces, or characters outside `a-z0-9_-` in a segment | Rename to lowercase slug segments separated by `/` (and rename the matching domain directory). |
| Sync or pull fails with `No ontology files found in the connected repository` | The **Path** directory (default `cassis/`) is missing or empty on the default branch — files placed at the wrong path (e.g. at the repo root) | Make sure the tree lives directly under the configured **Path** on the default branch. |
| **Every** file fails the round-trip check, and each reported path carries an extra `ontology/` segment (`cassis/ontology/…`) | The legacy layout: the repository was connected before the **Path** setting existed, so the whole tree sits one level too deep for the default Path | Set the project's **Path** to `cassis/ontology`, or re-publish from Cassis and delete the orphaned directory — see the [legacy layout note](repository-layout.md#legacy-layout). Don't merge to the default branch before fixing this: the import would read an effectively empty tree. |
| No validation check on a PR from a `cassis/*` branch | The project setting **"Run ontology checks on Cassis-created branches"** is off — checks are skipped for branches Cassis opens | Expected. Turn the toggle back on in the project's git settings if you want the check there. |
| No check runs ever appear; merges don't import | The Cassis GitHub App is not installed on this repository, or the project's configured repository doesn't match — Cassis skips events for repositories its installation can't access | On the "Organization · GitHub" page, re-check the App installation covers the repository and the project's **Repository** setting is the right `owner/name`. Saving an inaccessible repo fails with "The repository '…' is not accessible by your organization's GitHub App installation." |
| Publishing from Cassis fails with `GitHub refused to … (403). The Cassis GitHub App installation lacks the required permissions — it needs 'Contents: write' and 'Pull requests: write' on the repository.` | The App installation's repository permissions were narrowed | Accept the App's current permissions on GitHub (organization settings → GitHub Apps), then retry. |
| Publishing from Cassis fails with `Git repository or branch not found (404) … check the configured repository and that the default branch exists.` | The configured repository was renamed/deleted, or has no default branch | Fix the **Repository** setting, or push an initial commit to create the default branch. |

If a sync failed and you've fixed the cause but there's no new commit to push, you can force a re-import: `POST /api/projects/{project_id}/git-sync/pull` (organization admin) — see [getting started](getting-started.md#fallback-pulling-manually).

## See also

- [How it works](how-it-works.md) — the model behind all of this
- [Repository layout](repository-layout.md) and [file reference](file-reference.md) — what goes in each file
