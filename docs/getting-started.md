# Getting started

This walkthrough takes you from nothing to a context that syncs between GitHub and Cassis. If you haven't yet, skim [how it works](how-it-works.md) first — the rest assumes you know that the git repo is the source of truth and that merges to the default branch are imports.

## Prerequisites

- A Cassis account with the **organization admin** role — the GitHub settings pages are admin-only.
- Permission to **install a GitHub App** on the GitHub organization (or personal account) that owns the repository.
- A **repository**. A dedicated repo works well, but an existing one (your dbt repo, for instance) is fine too: Cassis only reads and writes paths under `cassis/`, and never touches anything else in the repository.
- The repository's **default branch must be named `main`** — Cassis reads from and writes to the branch `main` specifically.

## Step 1 — connect GitHub to your Cassis organization

This is a one-time, organization-level step.

1. In the Cassis sidebar, under **Settings**, open **GitHub**. You land on the "Organization · GitHub" page.
2. In the **GitHub App** section, click **Connect GitHub**.
3. You are sent to GitHub's App installation flow. Choose the account that owns your repository, and grant the app access to the repository you plan to use (or all repositories, if you prefer).
4. GitHub redirects you back to the same Cassis page. You should see a "GitHub App connected" confirmation and the status line "GitHub App installed on your organization."

## Step 2 — pick the repository for your project

Still on the "Organization · GitHub" page:

1. In the **Project configuration** section, select your project.
2. In the **Repository** field, enter the repository as `owner/name` (the placeholder shows the format: `owner/repo`) and click **Save**.

Cassis verifies that its App installation can actually access that repository. If it can't, saving fails with:

> The repository 'owner/repo' is not accessible by your organization's GitHub App installation. Install the Cassis GitHub App on that repository's account, or choose a repository it owns.

— go back to step 1 and grant the App access to that repository.

## Step 3 — seed the repository

Two ways to get the first `cassis/ontology/` tree into git, depending on where your context lives today.

### Option A — you already have a context in Cassis

Publish it, and it lands in git:

1. In your project, open the **Versions** page.
2. Click **Publish changes** (or **Publish first version** if you've never published). The dialog confirms: "This will publish the ontology and commit the changes to *owner/repo*."
3. Cassis commits the full YAML tree directly to the repository's default branch (commit message `chore(ontology): publish v{n}`, or `chore(ontology): publish v{n} (<label>)` if you gave the publish a label) and records the new version.

If the repository is empty, Cassis bootstraps it with an initial README commit first. Because the published version already records this commit's SHA, the follow-up webhook does not create a duplicate — the commit's `cassis / ontology sync` check will read `Imported into Cassis: up to date.`, which is expected.

> **Note:** the publish button is only enabled when there is something to publish (unpublished changes, or a never-published project). If your context is fully published with no pending changes, make any small edit and publish that — every publish commits the full tree, so the repo ends up complete either way.

From here on, the repo and Cassis agree, and you can move to the [day-to-day workflow](workflow.md).

### Option B — author from scratch in git

1. Copy [`examples/minimal/`](../examples/minimal/)'s `cassis/` directory into the root of your repository.
2. Copy [`tools/validate.py`](../tools/validate.py) into your repository too (and optionally [`.github/workflows/validate.yml`](../.github/workflows/validate.yml) to run it in your CI) — the validator lives in *this* repo, not in the tree Cassis manages. Alternatively, run it from a checkout of this repo, pointing at yours: `python tools/validate.py /path/to/your-repo`.
3. Edit the tree to match your warehouse — schema and table names must match exactly (see the [file reference](file-reference.md) and [authoring guide](authoring-guide.md)).
4. Validate locally: `python tools/validate.py .`.
5. Commit and push to the **default branch** (or open a PR and merge it — any route that lands the files on the default branch works).

The push triggers the first import.

## Confirming the first sync worked

Check both sides:

- **On the commit in GitHub**: the pushed commit (or merge commit) gets a check run named `cassis / ontology sync`. Success reads `Imported into Cassis: v{n}.`. Failure reads "Ontology import failed" with the reason — Cassis kept its previous context, so fix the files and push again.
- **In Cassis**: the project's **Versions** page shows a new version labeled `Synced from git`, with the short commit SHA next to it, linked to the commit on GitHub.

Once you see both, the loop is closed: ask the agent a question and it answers using the context you just merged.

## Fallback: pulling manually

The webhook normally handles everything, but you can also trigger an import explicitly (for example after fixing webhook delivery, or to force a re-import) by calling the API as an organization admin:

```text
POST /api/projects/{project_id}/git-sync/pull
```

It imports from the default branch and responds with `synced` (a new version was created) or `up_to_date`. Note that, like any import, it overwrites unpublished edits made in the Cassis UI.

## Next steps

- [Day-to-day workflow](workflow.md) — branches, PRs, the validation check, troubleshooting
- [Repository layout](repository-layout.md) — what each file in the tree is for
