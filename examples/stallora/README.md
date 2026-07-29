# Stallora — a complete, well-authored ontology

Stallora is our demo dataset: a pan-European marketplace on **Snowflake** with 15 tables, 13 joins and 10 governed metrics. This is what a finished ontology looks like — copy the *patterns*, not the content. The tree lives in [`cassis/`](cassis/):

```text
cassis/
├── _project.yml                     # root: global rules every question inherits
├── domains/
│   ├── marketplace/
│   │   ├── _domain.yml              # the transactional core
│   │   ├── geography/               # topic docs written as child domains
│   │   ├── measuring-sales/
│   │   └── seller-performance/
│   └── seller_acquisition/
├── tables/STALLORA/*.yml            # one file per table
├── joins.yml                        # all join relationships, one list
└── metrics/*.yml                    # one file per governed metric
```

## What to notice

**The root `_project.yml` carries the rules that apply to every question.** Its `context_md` states the currency-rendering rule, the "realized sales = delivered orders" default, the counting rule (distinct `CUSTOMER_UNIQUE_ID`, never the per-order `CUSTOMER_ID`), and the data's date range. It ends with the **governed-metrics rule**: it names the ten metrics and tells the agent to use their definitions exactly instead of re-deriving them. Global rules belong here and nowhere else — stating them once is what makes them consistent.

**Topic docs are child domains.** `marketplace/measuring-sales` is not a folder of tables — it is a short essay ("where money lives, the delivered-only rule, BV/GMV vocabulary, counting rules") that the agent can open like any domain. The parent `marketplace/_domain.yml` routes to these topics with relative links. When a subject needs more than a table description can hold, give it a child domain.

**Table descriptions carry grain and caveats.** Look at `tables/STALLORA/ORDERS.yml`: "One row per order", where money does *not* live, and the trap ("about 9,300 orders have no order item rows at all … LEFT JOIN from orders when item data might be absent"). Column descriptions enumerate value lists (`ORDER_STATUS`) and define derived vocabulary ("an order is late when…"). Grain, value lists, and known data gaps on the table; cross-table rules on the domain.

**Metrics pin down the business definition.** `metrics/average_order_value.yml` has an `expression` (`AVG("ORDER_VALUE")`), a `filters` clause (`"IS_DELIVERED" = TRUE`), the table it runs on, a unit, and `synonyms` ("AOV", "average basket") so the vocabulary users actually type resolves to the governed definition.

**Joins have descriptions, and the descriptions do real work.** `joins.yml` warns about the fan-out on `GEOLOCATION` ("NEVER join directly … collapse to one row per prefix first") and flags the partial bridge between acquisition and marketplace data. A join that silently multiplies rows is the classic wrong-number generator; say it where the agent will read it.

**Identifier case matches the warehouse.** This is Snowflake, so schema, tables and columns are UPPERCASE, and SQL snippets in metric expressions quote identifiers with their exact stored case (`AVG("ORDER_VALUE")`). Your ontology must use the identifier case your warehouse actually stores — compare with [`../minimal/`](../minimal/), the same format over a lowercase Postgres schema.

## Try it

```bash
cassis ontology check   # from this directory
```

(Official CLI — `pip install cassis-cli`, plus a `CASSIS_API_KEY`; setup at [docs.getcassis.com/cli](https://docs.getcassis.com/cli/#auth).) Every file here is byte-canonical: the CLI check (and the `cassis / ontology validation` check on PRs) passes.

## Learn more

- [File format](https://docs.getcassis.com/file-format/) — every file type, field by field
- [Ontology in git](https://docs.getcassis.com/git/) — the sync model and the pull request loop
- `cassis/AGENTS.md` in your own checkout — how to write an ontology that makes the agent accurate
