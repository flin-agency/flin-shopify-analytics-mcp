---
name: shopify-analysis-playbook
description: Use when analyzing a Shopify store with this repository's MCP tools and you need a fast executive read on sales, products, retention, customers, or attribution.
---

# Shopify Analysis Playbook

## Overview

Use this skill for fast Shopify analysis, not deep analyst mode.

Optimize for:

- speed
- signal
- clear business relevance

Answer in the user's language when it is clear. If the user's language is unclear, default to English.

## Response Shape

Keep the response short and structured:

- `Summary`: 2-4 bullets with the main performance read
- `Findings`: 3-6 bullets ordered by impact
- `Next checks`: 1-3 follow-ups only when they materially reduce uncertainty

Do not dump raw tool payloads unless the user explicitly asks for them.

## Core Rules

1. Always state the date range you analyzed.
2. If the user gave no date range, use a sensible default and say so.
3. Prefer a fast top-down read before drilling into edge cases.
4. Do not interpret attribution before checking attribution coverage.
5. Do not overclaim retention quality if order history may be incomplete.
6. Treat `unattributed` and `<none>` as real reporting outcomes, not as errors to hide.
7. Keep recommendations tied to evidence from the tools you actually ran.

## Default Time Windows

Use these defaults unless the user asks for something else:

- general shop health: last 30 days vs previous 30 days
- product performance: last 30 days
- retention snapshot: cohort starting in the last full 30 days, evaluated as of today
- attribution snapshot: last 30 days
- sales drop diagnosis: current 30-day window vs previous 30-day window

## Fast Workflows

### 1. Revenue Snapshot

Use:

- `shopify_sales_overview`
- `shopify_sales_timeseries`
- `shopify_top_products`
- `shopify_discount_analysis` when discount pressure may matter

Answer:

- is revenue up, down, or flat
- what changed in orders, AOV, units, refunds, and discounts
- which products drove the move

### 2. Product Performance Snapshot

Use:

- `shopify_top_products`
- `shopify_sales_overview`
- `shopify_sales_timeseries` if trend is relevant

Check:

- net sales vs units sold
- whether a few products dominate results
- whether product mix changed more than total demand

### 3. Customer and Retention Snapshot

Use:

- `shopify_retention_overview`
- `shopify_repeat_purchase_windows`
- `shopify_time_to_second_order`
- `shopify_inactive_customer_summary` if health looks weak

Check:

- repeat customer rate
- time to second order
- whether inactivity is widening

Guardrail:

If order history may be incomplete, say retention is directional rather than definitive.

### 4. Attribution Sanity Check

Always start with:

- `shopify_attribution_quality_summary`

Then use:

- `shopify_sales_by_source`
- `shopify_sales_by_utm`
- `shopify_new_customers_by_attribution`
- `shopify_landing_page_analysis`

Check:

- how much of the order base has usable source, landing page, or UTM data
- whether one source or campaign dominates
- whether the data is good enough for a confident attribution read

Guardrail:

If a large share is `unattributed`, say that clearly before discussing winners.

### 5. Sales Drop Diagnosis

Use:

- `shopify_sales_overview` with previous-period comparison
- `shopify_sales_timeseries`
- `shopify_top_products`
- `shopify_top_customers`
- `shopify_discount_analysis`

Add attribution checks only if the drop may be acquisition-driven:

- `shopify_attribution_quality_summary`
- `shopify_sales_by_source`
- `shopify_sales_by_utm`

Diagnose in this order:

1. demand change
2. mix change
3. discount or refund pressure
4. retention weakness
5. acquisition weakness

## Common Traps

- Do not treat higher revenue as healthy if refunds or discounts also spiked.
- Do not treat `sourceName` alone as full attribution truth.
- Do not assume `numberOfOrders` is enough for true new-customer analysis; prefer the dedicated attribution and retention tools.
- Do not produce a long narrative when 4-6 bullets are enough.
- Do not recommend actions that the data did not support.

## Output Heuristic

If confidence is high:

- give one clear read
- state the strongest driver
- give one or two next checks

If confidence is low:

- say what is knowable
- name the data-quality limit
- recommend the next highest-value check
