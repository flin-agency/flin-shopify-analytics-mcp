# V4 Attribution Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add source- and UTM-based attribution analytics for Shopify orders, including explicit attribution quality metrics.

**Architecture:** Extend the normalized order shape with attribution fields, add a small attribution-normalization layer, then build five attribution aggregations on top. Keep the implementation read-only and data-quality-aware.

**Tech Stack:** Python 3.10+, stdlib, Shopify Admin GraphQL, unittest

---

### Task 1: Persist the approved design

**Files:**
- Create: `docs/plans/2026-04-11-v4-attribution-design.md`
- Create: `docs/plans/2026-04-11-v4-attribution.md`

**Step 1: Save design and plan files**

Write the approved attribution design and implementation plan to `docs/plans/`.

**Step 2: Commit the docs**

Run:

```bash
git add docs/plans/2026-04-11-v4-attribution-design.md docs/plans/2026-04-11-v4-attribution.md
git commit -m "docs: add v4 attribution design"
```

### Task 2: Add failing analytics tests

**Files:**
- Modify: `py_tests/test_analytics.py`

**Step 1: Add failing tests for attribution analytics**

Cover:
- attribution quality summary
- sales by source
- sales by utm
- new customers by attribution
- landing page analysis

**Step 2: Run analytics tests**

Run:

```bash
python3 -m unittest py_tests.test_analytics -v
```

Expected: FAIL because the attribution functions do not exist yet.

### Task 3: Implement attribution analytics

**Files:**
- Modify: `flin_shopify_analytics_mcp/analytics.py`
- Test: `py_tests/test_analytics.py`

**Step 1: Add attribution normalization helpers**

Implement:
- source normalization
- UTM parsing from landing URLs when available
- source/utm presence flags

**Step 2: Add analytics functions**

Implement:
- `attribution_quality_summary`
- `sales_by_source`
- `sales_by_utm`
- `new_customers_by_attribution`
- `landing_page_analysis`

**Step 3: Run analytics tests**

Run:

```bash
python3 -m unittest py_tests.test_analytics -v
```

Expected: PASS

### Task 4: Add failing MCP exposure tests

**Files:**
- Modify: `py_tests/test_mcp_server.py`

**Step 1: Extend fake order data with attribution fields**

Add `sourceName`, `landingPage`, `referringSite`, and UTM-capable values.

**Step 2: Add failing tests**

Verify:
- the five new attribution tools appear in `tools/list`
- one attribution tool returns structured content

**Step 3: Run MCP tests**

Run:

```bash
python3 -m unittest py_tests.test_mcp_server -v
```

Expected: FAIL because `tools.py` does not expose attribution tools yet.

### Task 5: Register and dispatch the attribution tools

**Files:**
- Modify: `flin_shopify_analytics_mcp/tools.py`
- Test: `py_tests/test_mcp_server.py`

**Step 1: Add tool definitions**

Define schemas for the five attribution tools.

**Step 2: Add dispatch logic**

Load orders for the requested date range and route them through the attribution analytics functions.

**Step 3: Run MCP tests**

Run:

```bash
python3 -m unittest py_tests.test_mcp_server -v
```

Expected: PASS

### Task 6: Update README

**Files:**
- Modify: `README.md`

**Step 1: Document attribution scope**

Add the `v4` tools and explain that attribution depends on available Shopify order fields.

**Step 2: Add quality caveat**

State that attribution reports are only as reliable as the underlying tracking data.

### Task 7: Run full verification

**Files:**
- Modify if needed: any failing file

**Step 1: Run all tests**

Run:

```bash
python3 -m unittest discover -s py_tests -v
```

Expected: PASS

**Step 2: Build the package**

Run:

```bash
uv build
```

Expected: sdist and wheel build successfully.

### Task 8: Commit the implementation

**Files:**
- Modify: all touched implementation, tests, and docs

**Step 1: Commit the feature**

Run:

```bash
git add README.md docs/plans flin_shopify_analytics_mcp py_tests
git commit -m "feat: add v4 attribution analytics"
```
