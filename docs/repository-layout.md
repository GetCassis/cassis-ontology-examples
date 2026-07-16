# Repository layout

Your entire context lives as a YAML tree **directly under** one directory of your repository: the project's **Path** setting — `cassis/` by default, configurable per project, and nestable (`dbt/cassis` works; see [getting started](getting-started.md#step-2--pick-the-repository-for-your-project)). The docs write `cassis/` throughout; substitute your own Path if you changed it. Cassis only ever writes inside that directory — your dbt project, README, CI config, and anything else in the repo are never touched. (One exception: when you connect an **empty** repository, Cassis bootstraps it with a one-time initial commit adding a `README.md` at the repo root.) Within the Path directory, though, Cassis is the owner of record: every export is a full replacement of the directory, so after a publish it contains exactly the files described here and nothing else.

```text
cassis/
  _project.yml                    # root: project-wide context
  domains/<path>/_domain.yml      # one dir per domain, nested by path segments
  tables/<schema>/<table>.yml     # one file per table (columns inline)
  metrics/<name>.yml              # one file per metric
  joins.yml                       # ALL joins, one YAML list
```

Every file uses the `.yml` extension — not `.yaml`. See the [file reference](file-reference.md) for what goes inside each file, and the [authoring guide](authoring-guide.md) for how to write good content.

## A real tree

The [Stallora example](../examples/stallora/) (abbreviated — 15 tables, 10 metrics):

```text
cassis/
├── _project.yml
├── joins.yml
├── domains/
│   ├── marketplace/
│   │   ├── _domain.yml
│   │   ├── geography/
│   │   │   └── _domain.yml
│   │   ├── measuring-sales/
│   │   │   └── _domain.yml
│   │   └── seller-performance/
│   │       └── _domain.yml
│   └── seller_acquisition/
│       └── _domain.yml
├── metrics/
│   ├── active_sellers.yml
│   ├── average_order_value.yml
│   ├── business_volume.yml
│   ├── on_time_delivery_rate.yml
│   └── …
└── tables/
    └── STALLORA/
        ├── CUSTOMERS.yml
        ├── DIM_CATEGORY.yml
        ├── FCT_ORDERS.yml
        ├── ORDERS.yml
        ├── ORDER_ITEMS.yml
        └── …
```

## `_project.yml` — the root

The root of your context is a domain like any other — its path is the empty string, and it lives in `_project.yml` at the top of the tree instead of under `domains/`. It holds the project-wide `context_md` (global rules, glossary, data date ranges) plus a display name and description. Every tree Cassis writes has one; keep it, and treat it as the home for anything true of nearly every question (see the [authoring guide](authoring-guide.md#2-the-placement-ladder)).

## `domains/` — directory nesting is the domain path

A domain's **path is its directory path** — it is not stored anywhere inside the file. The file itself is always named `_domain.yml`:

| Domain path | File |
|---|---|
| *(root)* | `_project.yml` |
| `marketplace` | `domains/marketplace/_domain.yml` |
| `marketplace/measuring-sales` | `domains/marketplace/measuring-sales/_domain.yml` |

Consequences:

- **Moving or renaming a directory renames the domain.** Tables and metrics reference domains by path (`domain_path: marketplace`), so update those references in the same PR.
- Path segments are lowercase slugs — letters, digits, `_`, `-` (Stallora uses both styles: `measuring-sales`, `seller_acquisition`). No spaces, no uppercase.
- Give **every level** its own `_domain.yml`, including intermediate ones — a child directory without a parent domain file leaves the parent unnavigable.

## `tables/` — one file per table

Each table is one file at `tables/<schema_name>/<table_name>.yml`, with its columns inline in the same file. The schema directory is the schema name **verbatim, in the warehouse's stored case** — that's why the Stallora (Snowflake) example has `tables/STALLORA/FCT_ORDERS.yml` in all caps. A Postgres warehouse would typically give you `tables/public/orders.yml`.

The `schema_name` and `table_name` **fields inside the file** are the authoritative identity; the file path is derived from them. If they disagree — a file at the wrong path, or a renamed file whose fields still say the old name — validation fails.

## `metrics/` — one file per metric

Each metric is one file at `metrics/<name>.yml`, named after the metric's `name` field. As with tables, the field is authoritative and the filename must match it.

## `joins.yml` — all joins, one list

All joins across the whole context live in a single `joins.yml` file, as one YAML list. There are no per-table join files. The list is kept in a canonical sort order (by `from_schema`, `from_table`, `to_schema`, `to_table`, then `condition_sql`) — keep it sorted when you add a join by hand; an out-of-order list fails the round-trip check. No joins → no `joins.yml`: an empty file (or an empty list) fails validation — delete the file instead.

## File naming and sanitization

Table and metric filenames are derived from the object's name with every character outside ASCII letters, digits, `_`, `-`, and `.` replaced by `_`. A metric named `revenue/total` becomes `metrics/revenue_total.yml`. The name **field** keeps the original value; only the filename is sanitized.

## What must not be in the tree

Treat `cassis/` as containing **only** the files above:

- **Non-YAML files** (a README, `.gitkeep`, scratch notes) don't fail validation — the check and the import both ignore them — but they don't survive either: every Cassis-side export replaces the whole Path directory, deleting anything Cassis didn't write. Keep docs and scratch files anywhere else in the repo.
- **Stray YAML does fail.** A `.yml` file that isn't part of the tree fails the round-trip check, and `.yaml` files are parsed but never written back by Cassis (only `.yml` is canonical), so they fail the round-trip too.
- **No empty YAML files** — every file must contain at least one field.

## Legacy layout

Repositories connected before the **Path** setting existed have their tree one level deeper, at `cassis/ontology/`. Either set the project's **Path** to `cassis/ontology` to keep that layout, or re-publish from Cassis — which writes the flat layout under `cassis/` — and delete the orphaned `cassis/ontology/` directory.

The [day-to-day workflow](workflow.md) covers what the `cassis / ontology validation` and `cassis / ontology sync` checks do with this tree on your pull requests, and [getting started](getting-started.md) covers connecting the repo in the first place. For a copy-paste starting skeleton, see [`../examples/minimal/`](../examples/minimal/).
