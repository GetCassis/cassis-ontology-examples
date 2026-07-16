# Minimal — the smallest realistic context

A tiny but complete context for a Postgres store: two tables (`public.customers`, `public.orders`), one domain, one join, one governed metric, and a root `_project.yml` with the global rules. Six files total under [`cassis/`](cassis/).

It shows the essentials in isolation:

- `_project.yml` — global rules in `context_md` (currency, the "revenue = completed orders" rule, how to count customers)
- `domains/sales/_domain.yml` — one domain grouping the two tables, with routing and caveat notes
- `tables/public/{customers,orders}.yml` — grain, caveats, column descriptions, `nullable: false` where it matters
- `joins.yml` — one join with `column_pairs`, a `cardinality` (`many_to_one`), and a description
- `metrics/total_revenue.yml` — `expression` + `filters` + `synonyms` + `unit`

Note the identifier case: this is Postgres, so everything is lowercase. On Snowflake it would typically be UPPERCASE — see [`../stallora/`](../stallora/). Always match the case your warehouse stores.

## Use it as your starting skeleton

```bash
cp -R examples/minimal/cassis /path/to/your-repo/cassis
cassis ontology check /path/to/your-repo   # should pass before you start editing
```

(The check is the official CLI — `pip install cassis-cli`, plus a `CASSIS_API_KEY`; setup in [the workflow guide](../../docs/workflow.md#the-loop).)

Then replace the tables with your own (schema and table names must match the file paths: `tables/<schema_name>/<table_name>.yml`), rewrite the rules in `_project.yml`, and re-run the check as you go. See the [file reference](../../docs/file-reference.md) for every field and the [authoring guide](../../docs/authoring-guide.md) for what good context looks like.
