# Getting started

This walkthrough takes you from nothing to a context that syncs between GitHub and Cassis. If you haven't yet, skim [how it works](how-it-works.md) first — the rest assumes you know that the git repo is the source of truth and that merges to the default branch are imports.

## Prerequisites

- A Cassis account with the **organization admin** role — the GitHub settings pages are admin-only.
- Permission to **install a GitHub App** on the GitHub organization (or personal account) that owns the repository.
- A **repository**. A dedicated repo works well, but an existing one (your dbt repo, for instance) is fine too: Cassis only reads and writes files under the project's **Path** directory (`cassis/` by default — see step 2), and never touches anything else in the repository. The flip side: don't keep anything else *inside* that directory — every export from Cassis replaces it wholesale.
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
2. In the **Repository** field, enter the repository as `owner/name` (the placeholder shows the format: `owner/repo`).
3. In the **Path** field, leave the default `cassis` unless you want the context exported under a different repo directory. Nested paths work (`dbt/cassis`); segments may only contain letters, digits, `.`, `-` and `_`. Cassis writes the whole context tree **directly under** this directory and replaces its contents on every export, so pick a directory that contains nothing else. (Repositories connected before the Path setting existed have their tree at `cassis/ontology/` — see the [legacy layout note](repository-layout.md#legacy-layout).)
4. Leave **Run ontology checks on Cassis-created branches** on unless the PR validation check gets in your way on Cassis-opened branches — when off, it is skipped for branches Cassis opens (`cassis/*`) and still runs on all other branches.
5. Click **Save**.

A repository can be connected to **one project only** — saving a repo that another project already uses fails with "This repository is already connected to another project. Disconnect it there first."

Cassis also verifies that its App installation can actually access the repository. If it can't, saving fails with:

> The repository 'owner/repo' is not accessible by your organization's GitHub App installation. Install the Cassis GitHub App on that repository's account, or choose a repository it owns.

— go back to step 1 and grant the App access to that repository.

## Step 3 — seed the repository

Two ways to get the first `cassis/` tree into git, depending on where your context lives today.

### Option A — you already have a context in Cassis

Publish it, and it lands in git:

1. In your project, open the **Versions** page.
2. Click **Publish changes** (or **Publish first version** if you've never published). The dialog confirms: "This will publish the ontology and commit the changes to *owner/repo*."
3. Cassis commits the full YAML tree directly to the repository's default branch (commit message `chore(ontology): publish v{n}`, or `chore(ontology): publish v{n} (<label>)` if you gave the publish a label) and records the new version.

If the repository is empty, Cassis bootstraps it with an initial README commit first. Because the published version already records this commit's SHA, the follow-up webhook does not create a duplicate — the commit's `cassis / ontology sync` check will read `Imported into Cassis: up to date.`, which is expected.

> **Note:** the publish button is only enabled when there is something to publish (unpublished changes, or a never-published project). If your context is fully published with no pending changes, make any small edit and publish that — every publish commits the full tree, so the repo ends up complete either way.

From here on, the repo and Cassis agree, and you can move to the [day-to-day workflow](workflow.md).

### Option B — author from scratch

You don't need the GitHub App to get started: while you iterate on the first version, the CLI can push your working tree straight into the project, and you wire up git sync once the context has taken shape.

1. Copy [`examples/minimal/`](../examples/minimal/)'s `cassis/` directory into the root of your repository (or any local directory, to begin with).
2. Set up the CLI: `pip install cassis-cli`, create an API key in Cassis under **Organization settings → API keys** (keys start with `sk-k6-`), and expose it as `CASSIS_API_KEY`.
3. Edit the tree to match your warehouse — schema and table names must match exactly (see the [file reference](file-reference.md) and [authoring guide](authoring-guide.md)).
4. Validate: `cassis ontology check` (add `--base-path` if you changed the project's **Path** setting).
5. Iterate straight into the project: `cassis ontology upload --project <project-id>` replaces the project's context with your tree and publishes it, so you can ask the agent right away. The project ID is the UUID in the project's URL. Edit → upload → ask, as many rounds as it takes — re-uploading unchanged content is a no-op, and a broken tree is rejected without touching the project ([details](workflow.md#uploading-straight-to-a-project)).
6. When the context stabilizes, connect the GitHub App (steps 1–2 at the top of this page), commit the tree to your repository, and push to the **default branch** (or open a PR and merge it — any route that lands the files on the default branch works).

The push triggers the first git import. From then on the repository is the source of truth — the next merge overwrites anything uploaded with the CLI, so switch your iteration to the [day-to-day git loop](workflow.md#the-loop).

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
