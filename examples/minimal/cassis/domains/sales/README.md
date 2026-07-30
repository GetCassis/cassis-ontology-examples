---
type: Domain
title: Sales
description: Customers and the orders they place.
---

Customers and their orders.

- Route order-level questions to orders and person-level questions to customers; join on orders.customer_id =
  customers.id (many orders per customer).
- customers.country_code is NULL for roughly 5% of rows (signups that predate the field): treat NULL as "unknown
  country", do not drop those customers from totals.

<!-- cassis:nav:begin (generated, do not edit) -->

## Tables
- [public.customers](../../tables/public/customers.yml)
- [public.orders](../../tables/public/orders.yml)

## Metrics
- [Total revenue](../../metrics/total_revenue.yml)
<!-- cassis:nav:end -->
