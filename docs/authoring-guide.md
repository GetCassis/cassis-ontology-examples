# Authoring guide

How to write a context the agent can actually use. The [file reference](file-reference.md) tells you what each field is; this guide tells you what to put in it — and, just as importantly, what to leave out. Every rule here follows from one principle:

> **Each fact lives in exactly one place, at the most specific level that owns it. Never duplicate across layers. Never hand-write what Cassis already shows the agent.**

All examples below are verbatim from the [Stallora demo context](../examples/stallora/), a complete, well-authored tree you can browse alongside this guide.

## 1. How the agent reads your context

When the agent opens a domain, Cassis automatically assembles and shows it:

- the domain's hand-written `context_md` — **the only part you write as prose**;
- every **direct child domain**, with its path, display name, and description;
- every **table** in the domain, with its description, grain, and synonyms;
- every **metric** in the domain, with its expression, filters, unit, and synonyms;
- when it inspects a table: the table's columns and **all joins** touching it, each with its column pairs, cardinality, and description.

The consequence drives everything else in this guide: **never restate in `context_md` what the structured fields already carry.** A "Tables in this domain: …" list, a re-pasted metric formula, a "joins to X on Y" note — the agent already sees all of that, assembled from your YAML. Restating it wastes the agent's attention, and when the copies drift (they will), the prose version silently lies.

`context_md` is for the connective tissue the structured fields *can't* carry: routing between similar tables, cross-table business rules, vocabulary, disambiguation.

## 2. The placement ladder

Put each fact at the most specific level that fully owns it:

```
column synonym                    (vocabulary that maps to one column)
  → column description            (single-column facts: value lists, semantics, caveats)
    → table description           (single-table facts: grain, scope, gotchas, "use this not that")
      → domain context_md         (cross-table routing and rules within one area)
        → root context_md         (_project.yml — truly global rules only)
```

A fact written one level too high is redundant — the agent already sees the lower level — or gets stranded where the agent won't look for it. A fact written one level too low can't express a cross-object relationship.

One rung each, from Stallora:

**Column synonym** — routes a word to a column, nothing more:

```yaml
- name: ORDER_VALUE
  synonyms:
  - order total
  - basket value
```

**Column description** — value lists, semantics, single-column caveats:

```yaml
- name: ORDER_STATUS
  description: 'Fulfillment status of the order. Values: delivered, shipped,
    canceled, unavailable, invoiced, processing, created, approved. About 97%
    of orders are delivered. Realized sales are status ''delivered''.'
```

**Table description** — grain, scope, single-table gotchas (more on this in [section 5](#5-descriptions-that-earn-their-place)):

```yaml
description: 'A purchase placed by a customer. One row per order. An order
  contains one or more order items. Status tracks the order through
  fulfillment; money lives on ORDER_ITEMS, not here. ...'
```

**Domain `context_md`** — rules that span the domain's tables. Stallora's `marketplace/measuring-sales` domain owns the money rules, because they involve three tables at once:

> Sale amounts live on ORDER_ITEMS, one row per order line: PRICE is the item sale amount, FREIGHT_VALUE the shipping charged on that line. […] The curated FCT_ORDERS carries the same money pre-summed to one ORDER_VALUE per order, and FCT_SALES_MONTHLY pre-sums GMV by month […] The three reconcile; never sum more than one of them together.

**Root `context_md`** (`_project.yml`) — only rules that apply to nearly every question:

> - Monetary amounts are in EUR. Always render amounts with the EUR currency (the euro symbol or 'EUR'); never use '$' or any other currency symbol.
> - Realized sales are delivered orders: unless the user asks otherwise, restrict revenue, sales and business-volume questions to orders whose status is 'delivered'.

### Deliberate double placement

"One fact, one home" is the default, but a handful of rules earn two. Stallora's most dangerous trap — customer ids are per-order, so counting `CUSTOMER_ID` overcounts people — appears both on the columns themselves:

```yaml
- name: CUSTOMER_ID
  description: Per-order identifier of the customer. Unique per row; one is
    created for each order. Never count people with this column.
- name: CUSTOMER_UNIQUE_ID
  description: Stable identifier of the real person across all their orders.
    Count distinct customers (people) with this column.
```

*and* as a global rule in `_project.yml`:

> A customer id is issued per order, so the same real person appears under many customer ids over time. Count distinct customers by CUSTOMER_UNIQUE_ID, never by the per-order CUSTOMER_ID.

That duplication is deliberate, and rare. Promote a fact to a second home only when getting it wrong would **silently corrupt most answers** and the agent might act before reaching the specific home. When you do, keep the wording consistent so the copies can't drift apart in meaning. Everything else: one home, and a link from anywhere else that needs it.

## 3. The rules

What to cut from `context_md`, and where the content goes instead.

**Don't enumerate child domains.** The agent sees each child with its description automatically. If a child's description is too thin to stand alone, fix the description — don't compensate with a "Sub-domains:" list in the parent. What a parent *may* add is which-child-for-which-question routing that no single child description can carry.

**Don't restate the table list, grains, or synonyms.** The agent sees them. Per-table facts (grain nuance, scope, data-quality gotchas, "use this table, not that one" when it concerns one table) belong on the table's own `description`. What stays in `context_md` is genuinely *cross-table* routing — see how Stallora's `marketplace` domain does it: each line positions a table relative to its siblings ("ORDERS is the hub […] money does NOT live here", "ORDER_ITEMS is the sale grain […] Use this table for any breakdown of sales") rather than repeating the table's own description. A routing map earns its place; an inventory does not.

**Don't restate metric expressions, filters, or units.** The agent sees the full metric definition next to your prose. Keep only cross-metric guidance: which metric to prefer, how two metrics reconcile, which vocabulary maps where.

**Put topic content in the most specific domain.** A rule about seller acquisition sitting in the root, or in `marketplace`, must move down to `seller_acquisition`. Content placed too high dilutes the global rules and is easy to miss when the agent is deep in the tree.

**Root `context_md` holds only truly global rules.** Currency and rendering conventions, the fiscal calendar, global counting rules, default population filters, data date ranges, cross-cutting glossary that maps to no single domain. Stallora's root has exactly four bullets under "Rules that apply to every question" — that's the right order of magnitude. Everything domain-specific moves down.

**One home per fact.** The same rule tends to creep into three or four places. Pick the single most specific home; everywhere else, drop it or leave a one-line link. (The narrow exception is [above](#deliberate-double-placement).)

**Don't write join-key prose.** Joins are structured objects with column pairs, cardinality, and a description, and the agent sees every join touching a table when it inspects that table. "A.x joins B.y" sentences in `context_md` or table descriptions are pure redundancy — delete them. A caveat about *one* join belongs on that join's `description`:

```yaml
- cardinality: many_to_one
  column_pairs:
  - from_column: CUSTOMER_ZIP_CODE
    to_column: ZIP_CODE
  condition_sql: STALLORA.CUSTOMERS.CUSTOMER_ZIP_CODE = STALLORA.GEOLOCATION.ZIP_CODE
  description: 'Customer area coordinates. Many-to-one holds only after dedup — GEOLOCATION has many rows per prefix: NEVER
    join directly (fan-out). Collapse to one row per prefix first, then LEFT JOIN.'
```

The only join content that belongs in prose is a **multi-step join + filter recipe that no single join expresses** — e.g. Stallora's `seller_acquisition` domain explains that the acquisition-to-marketplace bridge is partial ("only about 4,560 of the 10,104 closed-deal sellers appear in the marketplace tables") and tells the agent to state the caveat whenever combining the two domains. That's a cross-domain pattern; no single join object could carry it alone.

## 4. What TO write in `context_md`

Don't over-strip. After the redundant material is gone, `context_md` is where the highest-value content lives:

- **Routing and disambiguation between similar tables** — especially raw vs curated rollups. Stallora's root settles it in three sentences: the raw tables are the source of truth, four curated rollups are pre-aggregated for common questions, "Prefer the table whose grain matches the question; raw and curated reconcile to the same governed metrics."
- **Business rules that span objects** — scope caveats, temporal caveats, aggregation traps ("never sum more than one of them together").
- **Glossary and vocabulary** that maps to no single table — Stallora's measuring-sales domain: "BV, GMV, gross merchandise value, revenue and sales all mean the same thing here."
- **A short orientation paragraph** for a navigational domain — one or two sentences saying what the area is for, like `seller_acquisition`'s opener: "Prospective sellers enter as marketing qualified leads; the sales team closes some of them into deals; a closed deal creates a seller on the marketplace."
- **Markdown links to child and sibling domains**, using resolvable domain paths — the agent can follow them. Stallora's style:

  ```markdown
  - [marketplace](marketplace): the transactional core (orders, order items, products, ...).
  - [Measuring sales](marketplace/measuring-sales): where money lives, the delivered-only rule, ...
  ```

  The link target is the **domain path** (`marketplace/measuring-sales`), not a file name — never link to `_domain.yml` or a `.md` file.

## 5. Descriptions that earn their place

Descriptions are where most of the agent's per-object knowledge comes from. The bar: after reading the description, the agent should know what the object is, at what grain, and what will bite it.

**Table descriptions** state the grain, what a row is, where related facts live, and the gotchas. Stallora's ORDERS is the model:

```yaml
description: 'A purchase placed by a customer. One row per order. An order
  contains one or more order items. Status tracks the order through
  fulfillment; money lives on ORDER_ITEMS, not here. About 9,300 orders have
  no order item rows at all (mostly canceled or unavailable): LEFT JOIN from
  orders when item data might be absent.'
```

Four things in four sentences: what a row is, the grain, where the money is *not*, and a data gap with the exact defensive move (LEFT JOIN). For curated tables, also state **lineage** — what the rollup is built from and what it precomputes — so the agent knows when raw and curated should reconcile (see `FCT_ORDERS.yml` in the example).

**Column descriptions** carry value lists, semantics, and caveats — the `ORDER_STATUS` and `CUSTOMER_UNIQUE_ID` examples in [section 2](#2-the-placement-ladder). If a column encodes a business rule ("An order is late when ORDER_DELIVERED_CUSTOMER_DATE is after this date"), the column description is that rule's home.

**Verify every example against the real data.** Any literal value, value list, or SQL fragment you put in a description will be pasted into WHERE clauses. If you write `Values: delivered, shipped, ...` and the warehouse actually stores `DELIVERED`, the agent's filter matches zero rows and the answer is silently wrong — no error, just an empty result presented with confidence. Before committing, check every example value and snippet against the warehouse (`SELECT DISTINCT`, a quick profile query). A wrong example is worse than no example.

## 6. Metrics: governed definitions

A metric file is a governed definition: the expression, filters, and unit live in the YAML, and synonyms route the business vocabulary to it.

```yaml
description: Average sales value of a delivered order, in EUR (mean of
  FCT_ORDERS.ORDER_VALUE over delivered orders). Excludes freight.
display_name: Average order value (AOV)
domain_path: marketplace
expression: AVG("ORDER_VALUE")
filters: '"IS_DELIVERED" = TRUE'
name: average_order_value
synonyms:
- AOV
- average basket
- average basket size
table_name: FCT_ORDERS
table_schema: STALLORA
unit: EUR
```

Three habits make metrics work:

1. **Synonyms carry the vocabulary.** "AOV", "average basket", "average basket size" all land on this one definition. If your teams say it, list it.
2. **The root context declares the governance rule once.** Stallora's `_project.yml` names its governed metrics and instructs: "When a question uses one of these terms, use the metric definition exactly; do not re-derive or approximate it." Without that instruction, the agent may rebuild the calculation from raw tables and drift from your definition.
3. **Never re-paste the formula in prose.** Domain `context_md` may say *which* metric answers which vocabulary ("Average basket questions map to the average_order_value metric") — it must not repeat the expression or filters. The metric file is the single source of truth; a re-pasted formula is a future contradiction.

## 7. Identifier case

Cassis **quotes every identifier** in generated SQL (`"STALLORA"."ORDERS"."ORDER_ID"`), and quoted identifiers are case-sensitive in Snowflake and Postgres. So every physical identifier in your context must match the warehouse's **stored** case exactly, or generated SQL fails outright (`Schema "stallora" does not exist`).

Physical fields — must match stored case:

- `schema_name`, `table_name`, column `name`
- `grain` entries
- join endpoints and `condition_sql`
- metric `table_schema` / `table_name`, and every identifier inside `expression` and `filters`

Logical fields — natural language, any case you like:

- domain paths and display names
- descriptions and `context_md`
- **synonyms** (matching is case-insensitive; write them the way people talk)

What "stored case" means in practice: Snowflake folds unquoted DDL to **UPPERCASE**, Postgres folds it to **lowercase** — which is why the Stallora tree is all-caps (`STALLORA.ORDER_ITEMS.PRICE`). The safe workflow is to take identifiers verbatim from the warehouse (information schema, `SHOW COLUMNS`, or your dbt artifacts) and never retype them. In particular, **never hand-lowercase names that came from the warehouse** to make the YAML "look nicer" — that single edit breaks every query touching the table.

## 8. Quick self-check

Before committing, run each line you wrote through these six questions:

1. **Will the agent already see this?** A child domain's description, a table's grain or synonyms, a metric's expression, a join — all shown automatically. If yes: delete it.
2. **Does it concern exactly one column, table, metric, or join?** Put it on that object's description, not in `context_md`.
3. **Is it global to almost every query?** Root `context_md`. Otherwise: the most specific domain that owns it.
4. **Is the same fact already written somewhere more specific?** Link to it; don't copy it — unless it's one of the rare rules that earns [deliberate double placement](#deliberate-double-placement).
5. **Is every example value and SQL snippet verified against the warehouse**, and every physical identifier in its stored case? Unverified examples produce silently wrong queries; wrong case produces failing ones.
6. **Is this guidance for humans authoring the repo rather than for the agent answering questions?** Then it belongs in your README or PR description, not in the context.

Next: [repository layout](repository-layout.md) for where each file goes, [file reference](file-reference.md) for every field, and the [Stallora example](../examples/stallora/) to see all of this applied end to end.
