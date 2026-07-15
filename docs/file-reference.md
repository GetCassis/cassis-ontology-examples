# File reference

Field-by-field schema for every file type in the `cassis/ontology/` tree. See [repository layout](repository-layout.md) for where each file lives, and the [authoring guide](authoring-guide.md) for what to write in the fields.

All examples are verbatim (trimmed) from the [Stallora example](../examples/stallora/).

## Two rules that apply everywhere

**Required fields.** Import fails — and the PR validation check fails — when any of these is missing:

| File type | Required fields |
|---|---|
| table | `schema_name`, `table_name` |
| column | `name` |
| join | `from_schema`, `from_table`, `to_schema`, `to_table` |
| metric | `name` |

Everything else is optional.

**Required at import.** Three rules are enforced only when Cassis *imports* the tree (the sync on the default branch, or a manual pull) — the PR validation check does not catch them, but [`tools/validate.py`](../tools/validate.py) checks all three:

- metrics must carry a non-empty `display_name` and `expression`;
- every `domain_path` (on tables and metrics) must name a domain that exists in the tree;
- domain paths are lowercase slug segments (`a-z`, `0-9`, `_`, `-`) separated by `/`.

Violating one gets a green validation check but a failing sync — the exact errors are in the [troubleshooting table](workflow.md#troubleshooting).

**Default omission.** A field whose value equals its default — or is null, an empty string, or an empty list — is **omitted from the file**, and the canonical form *requires* omitting it. You will never see `nullable: true`, `source: introspected`, `is_virtual: false`, or `parse_ok: true` in a valid tree; writing them makes the file non-canonical and fails validation (see [Canonical form](#canonical-form)). The flip side: these fields only ever appear with their non-default value (`nullable: false`, `source: manual`, `is_virtual: true`, `parse_ok: false`).

## Domain files (`_project.yml` / `_domain.yml`)

The root domain lives in `_project.yml`; every other domain in `domains/<path>/_domain.yml`. The domain's **path is the directory path** — it is not a field in the file. Both file names share the same schema:

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `display_name` | string | no | *(omitted)* | Human name shown in the UI and to the agent. Always set it. |
| `description` | string | no | *(omitted)* | One or two sentences; shown when the parent domain lists its children. |
| `context_md` | string (markdown) | no | *(omitted)* | The domain's prose context — the only field you write as free text. See the [authoring guide](authoring-guide.md). |

A domain file must contain at least one field (an empty file fails validation).

```yaml
context_md: |-
  Prospective sellers enter as marketing qualified leads; the sales team closes
  some of them into deals; a closed deal creates a seller on the marketplace.
description: 'Marketing qualified leads and closed deals: how Stallora wins new sellers.
  Bridges to marketplace sellers.'
display_name: Seller acquisition
```

## Table files (`tables/<schema>/<table>.yml`)

One file per table; columns are inline.

*Managed* fields are written by Cassis — warehouse introspection or Cassis builds; leave them as you found them.

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `schema_name` | string | **yes** | — | Physical schema, warehouse stored case (see [Identifier case](#identifier-case)). |
| `table_name` | string | **yes** | — | Physical table name, stored case. Filename derives from it. |
| `columns` | list | no | *(omitted)* | Inline column objects — see below. |
| `description` | string | no | *(omitted)* | What a row is, the grain, the gotchas. |
| `domain_path` | string | no | *(omitted)* | Path of the domain this table lives in (e.g. `marketplace`). Must name a domain that exists in the tree (a `domains/<path>/_domain.yml`), as lowercase slug segments separated by `/` — both enforced at import, not by the PR check. Absent = the table is tracked but not placed in any domain. |
| `grain` | list of strings | no | *(omitted)* | Column names that identify a row, stored case. |
| `synonyms` | list of strings | no | *(omitted)* | Alternative names users say; matching is case-insensitive. |
| `is_virtual` | bool | no | `false` *(omitted)* | See [Virtual tables](#virtual-tables). Only ever appears as `is_virtual: true`. |
| `sql` | string | virtual only | *(omitted)* | The defining `SELECT` of a **virtual** table. Never valid on a physical table. |
| `lineage_description` | string | no | *(omitted)* | *Managed.* Prose provenance of a built table. |
| `source_tables` | list of strings | no | *(omitted)* | *Managed.* Upstream tables this table is built from. |
| `source_sql` | string | no | *(omitted)* | *Managed.* The upstream SQL that builds this table (provenance). **Not** the virtual-table definition — that is `sql`. |
| `table_type` | string | no | *(omitted)* | *Managed.* Warehouse-reported type from introspection (e.g. `BASE TABLE`, `VIEW`). |
| `approximate_row_count` | integer | no | *(omitted)* | *Managed.* From introspection. |

### Columns

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `name` | string | **yes** | — | Physical column name, stored case. |
| `data_type` | string | no | *(omitted)* | Warehouse type as introspected (`TEXT`, `NUMBER`, `TIMESTAMP_NTZ`, …). |
| `description` | string | no | *(omitted)* | Value lists, semantics, caveats. |
| `nullable` | bool | no | `true` *(omitted)* | Only ever appears as `nullable: false`. |
| `ordinal` | integer | no | *(omitted)* | 0-based position from introspection. Drives the canonical column order in the file. |
| `source` | enum | no | `introspected` *(omitted)* | `introspected` \| `manual`. `manual` marks a hand-added column that warehouse sync will never overwrite or drop. Only ever appears as `source: manual`. |
| `synonyms` | list of strings | no | *(omitted)* | |
| `unit` | string | no | *(omitted)* | Free text: `EUR`, `days`, `count`, `%`, … |

Columns are ordered by `ordinal` (columns without one go last, alphabetically) — see [Canonical form](#canonical-form).

```yaml
columns:
- data_type: TEXT
  description: Product category label. Join key from PRODUCTS.CATEGORY.
  name: CATEGORY
  ordinal: 0
- data_type: TEXT
  description: 'Broad department the category rolls up to. Values: electronics, home_garden,
    fashion, health_beauty, sports_leisure, media, food_drinks, industry_tools, automotive,
    office, other.'
  name: DEPARTMENT
  ordinal: 1
  synonyms:
  - department
description: Lookup mapping each product category to a broader department. One row
  per category. LEFT JOIN from PRODUCTS on CATEGORY to roll sales up to the department
  level.
domain_path: marketplace
grain:
- CATEGORY
schema_name: STALLORA
table_name: DIM_CATEGORY
```

### Virtual tables

A virtual table is a table the warehouse doesn't have: `is_virtual: true` plus a defining `SELECT` in `sql`. To the agent it looks like any other table (with its own description, columns, grain, joins); at query time Cassis expands the reference by inlining the `sql` body. Two rules:

- **Expansion is single-level**: a virtual table's `sql` must not reference another virtual table — such a reference will not expand at query time.
- Quote **every identifier** in the `sql` body with its explicit stored case (`"STALLORA"."ORDERS"."ORDER_ID"`), including the output column aliases — bare identifiers get case-folded by the warehouse and stop matching the declared columns.

Declare the output columns inline as usual, marking them `source: manual` (they are hand-declared, not introspected). Illustrative example (not part of the Stallora tree):

```yaml
columns:
- data_type: TEXT
  name: SELLER_ID
  source: manual
- data_type: NUMBER
  description: Delivered GMV for the seller in the month, in EUR.
  name: GMV
  source: manual
  unit: EUR
description: One row per seller per month, with delivered GMV.
domain_path: marketplace
grain:
- SELLER_ID
- MONTH
is_virtual: true
schema_name: STALLORA
sql: |-
  SELECT
    "STALLORA"."ORDER_ITEMS"."SELLER_ID" AS "SELLER_ID",
    DATE_TRUNC('month', "STALLORA"."ORDERS"."ORDER_PURCHASE_TIMESTAMP") AS "MONTH",
    SUM("STALLORA"."ORDER_ITEMS"."PRICE") AS "GMV"
  FROM "STALLORA"."ORDER_ITEMS"
  JOIN "STALLORA"."ORDERS"
    ON "STALLORA"."ORDER_ITEMS"."ORDER_ID" = "STALLORA"."ORDERS"."ORDER_ID"
  GROUP BY 1, 2
table_name: SELLER_MONTHLY_SALES
```

Note the distinction from `source_sql`: `sql` is what Cassis executes in place of the table; `source_sql` is provenance metadata about how a *physical* table gets built upstream, and is managed by Cassis.

## Joins (`joins.yml`)

One file, one YAML list, every join in the context. No joins → no `joins.yml`: an empty file (or an empty list) fails validation — delete the file instead. Each item:

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `from_schema` | string | **yes** | — | Stored case. |
| `from_table` | string | **yes** | — | Stored case. |
| `to_schema` | string | **yes** | — | Stored case. |
| `to_table` | string | **yes** | — | Stored case. |
| `condition_sql` | string | no | `""` *(omitted)* | The ON-clause boolean expression, columns table-qualified, in your warehouse's dialect. A join without one is useless — always set it. |
| `column_pairs` | list of `{from_column, to_column}` | no | *(omitted)* | The equi-join pairs. **You can omit this when authoring** — Cassis derives the pairs from `condition_sql` on import, and they appear in the next Cassis-written export. |
| `cardinality` | enum | no | *(omitted)* | `one_to_one` \| `one_to_many` \| `many_to_one` \| `many_to_many`, oriented **from → to**: `many_to_one` means many `from`-rows match one `to`-row. |
| `description` | string | no | *(omitted)* | Join-specific caveats (fan-out traps, partial bridges, dedup requirements). |
| `parse_ok` | bool | no | `true` *(omitted)* | *Managed.* `false` means Cassis could not parse `condition_sql` into pairs and treats the join as opaque. Never write it. |
| `source` | enum | no | `introspected` *(omitted)* | `introspected` \| `manual`. Set `source: manual` on joins you author by hand — `introspected` joins are owned by warehouse sync (derived from foreign keys), which may reconcile them against the warehouse. |

```yaml
- cardinality: many_to_one
  column_pairs:
  - from_column: CATEGORY
    to_column: CATEGORY
  condition_sql: STALLORA.PRODUCTS.CATEGORY = STALLORA.DIM_CATEGORY.CATEGORY
  description: Maps a product's category to its department.
  from_schema: STALLORA
  from_table: PRODUCTS
  source: manual
  to_schema: STALLORA
  to_table: DIM_CATEGORY
```

## Metric files (`metrics/<name>.yml`)

One file per metric, named after `name`.

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `name` | string | **yes** | — | Stable snake_case identifier; also the filename. |
| `display_name` | string | **yes** (at import) | — | Human name. Required at import — the PR check does not enforce it, the sync will. |
| `expression` | string | **yes** (at import) | — | The SQL aggregate (`AVG("ORDER_VALUE")`). Required at import — the PR check does not enforce it, the sync will. Identifiers quoted, stored case. |
| `filters` | string | no | *(omitted)* | WHERE-clause fragment the expression assumes (`'"IS_DELIVERED" = TRUE'`). |
| `table_schema` | string | no | *(omitted)* | Schema of the base table. Note the field name — `table_schema`, not `schema_name`. |
| `table_name` | string | no | *(omitted)* | Base table the expression runs over. |
| `domain_path` | string | no | *(omitted)* | Domain the metric is listed under. Same rules as on tables: must name a domain that exists in the tree, lowercase slug segments separated by `/` (enforced at import). |
| `description` | string | no | *(omitted)* | What the metric means in business terms. |
| `notes` | string | no | *(omitted)* | Usage guidance for the agent (edge cases, what not to substitute). |
| `precomputed_in` | string | no | *(omitted)* | Where the metric already exists materialized, if anywhere. |
| `synonyms` | list of strings | no | *(omitted)* | Business vocabulary that should route to this metric. |
| `unit` | string | no | *(omitted)* | `EUR`, `%`, `sellers`, … |

```yaml
description: Share of delivered orders that arrived on or before the estimated delivery
  date, as a percentage. Around 92%.
display_name: On-time delivery rate
domain_path: marketplace
expression: 100 * AVG(CASE WHEN "IS_ON_TIME" THEN 1 ELSE 0 END)
filters: '"IS_DELIVERED" = TRUE AND "ORDER_DELIVERED_CUSTOMER_DATE" IS NOT NULL'
name: on_time_delivery_rate
synonyms:
- on time rate
- punctual delivery rate
table_name: FCT_ORDERS
table_schema: STALLORA
unit: '%'
```

## Canonical form

Every file must **round-trip byte-identically** through Cassis's serializer: Cassis parses your tree, re-serializes it, and compares the two, file by file. The `cassis / ontology validation` check on your PRs fails on any difference, naming the offending files. This is what keeps git diffs meaningful — there is exactly one way to write any given context.

The canonical form:

- **Keys sorted alphabetically** at every level.
- **2-space indentation**; list dashes sit flush with their parent key (not indented under it):

  ```yaml
  grain:
  - ORDER_ID        # canonical
  ```

  ```yaml
  grain:
    - ORDER_ID      # not canonical — fails validation
  ```

- **Block style only** — never flow style (`{a: 1}` / `[x, y]`).
- **Multi-line strings as literal blocks** (`|` / `|-`). Long single-line strings wrap at column 120 with continuation lines — don't re-wrap them by hand.
- **Unicode written literally** (é, →, …) — never `\u` escapes.
- **Defaults and empties omitted** (the rule at the top of this page).
- **Canonical ordering inside files**: columns by `ordinal` then name (no-ordinal columns last); joins sorted by `from_schema`, `from_table`, `to_schema`, `to_table`, `condition_sql`.
- **File paths derived from content**: a table file must sit at `tables/<schema_name>/<table_name>.yml`, a metric file at `metrics/<name>.yml`.
- **No YAML comments.** Comments don't survive re-serialization, so they fail the round-trip. Prose for the agent goes in `description`/`context_md`; prose for humans goes outside `cassis/ontology/`.
- **No unknown fields.** The parser ignores a field it doesn't know *silently* — it won't error, but the field disappears on re-serialization and the round-trip check fails. A typo'd field name (`synonymns:`) therefore shows up as "content differs after round-trip", not as "unknown field".
- **Exact enum values.** `cardinality: many_to_one`, not `n:1` or `MANY_TO_ONE`; `source: manual`, not `Manual`. A bad enum value fails the round-trip outright.

Don't hand-format to these rules — run [`../tools/validate.py`](../tools/validate.py) instead:

```bash
python tools/validate.py .        # check (what the PR check will say)
python tools/validate.py . --fix  # rewrite files in canonical form
```

## Identifier case

`schema_name`, `table_name`, column `name`, `grain` entries, join endpoints and `condition_sql`, and every identifier inside a metric's `expression`/`filters` or a virtual table's `sql` are **physical identifiers**: they must match the warehouse's *stored* case exactly (Snowflake typically UPPERCASE, Postgres lowercase), because Cassis quotes every identifier in generated SQL and quoted identifiers are case-sensitive. Take them verbatim from the warehouse and never retype or "prettify" them — the full rule, with the safe workflow, is in the [authoring guide](authoring-guide.md#7-identifier-case).
