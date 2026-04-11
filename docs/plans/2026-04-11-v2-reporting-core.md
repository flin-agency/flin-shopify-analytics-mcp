# V2 Reporting Core Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add five reporting-focused Shopify analytics tools that expose overview KPIs, time series, top products, top customers, and discount analysis.

**Architecture:** Extend the existing order GraphQL query and order mapping so every reporting tool can run on one normalized enriched order shape. Add analytics helpers in a single module, then expose the new aggregations through MCP tool declarations and dispatch.

**Tech Stack:** Python 3.10+, stdlib, Shopify Admin GraphQL, unittest

---

### Task 1: Persist the approved design

**Files:**
- Create: `docs/plans/2026-04-11-v2-reporting-core-design.md`
- Create: `docs/plans/2026-04-11-v2-reporting-core.md`

**Step 1: Write the design and implementation plan files**

Save the approved `v2` design and this plan into `docs/plans/`.

**Step 2: Commit the docs**

Run:

```bash
git add docs/plans/2026-04-11-v2-reporting-core-design.md docs/plans/2026-04-11-v2-reporting-core.md
git commit -m "docs: add v2 reporting core design"
```

### Task 2: Add failing analytics tests

**Files:**
- Modify: `py_tests/test_analytics.py`

**Step 1: Write failing tests for the new aggregations**

Cover:
- sales overview KPI calculation
- time bucket aggregation
- top products ranking
- top customers ranking
- discount analysis

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m unittest py_tests.test_analytics -v
```

Expected: FAIL because the new analytics functions do not exist yet.

### Task 3: Implement analytics helpers

**Files:**
- Modify: `flin_shopify_analytics_mcp/analytics.py`
- Test: `py_tests/test_analytics.py`

**Step 1: Add minimal shared helpers**

Implement helpers for:
- money conversion
- date parsing
- previous-period calculation
- bucket labeling
- customer classification

**Step 2: Implement analytics functions**

Add:
- `sales_overview`
- `sales_timeseries`
- `top_products`
- `top_customers`
- `discount_analysis`

**Step 3: Run analytics tests**

Run:

```bash
python3 -m unittest py_tests.test_analytics -v
```

Expected: PASS

### Task 4: Add failing MCP exposure tests

**Files:**
- Modify: `py_tests/test_mcp_server.py`

**Step 1: Extend the fake client**

Add methods for the five new reporting tools.

**Step 2: Write failing tests**

Verify:
- `tools/list` contains the five new tool names
- `tools/call` returns structured output for at least one overview/reporting tool

**Step 3: Run MCP tests to verify failure**

Run:

```bash
python3 -m unittest py_tests.test_mcp_server -v
```

Expected: FAIL because `tools.py` does not expose the new tools yet.

### Task 5: Register and dispatch the new tools

**Files:**
- Modify: `flin_shopify_analytics_mcp/tools.py`
- Test: `py_tests/test_mcp_server.py`

**Step 1: Add tool definitions**

Define schemas for all five `v2` tools with consistent date and filter inputs.

**Step 2: Add dispatch implementation**

Wire each tool to either a client method or analytics helper.

**Step 3: Run MCP tests**

Run:

```bash
python3 -m unittest py_tests.test_mcp_server -v
```

Expected: PASS

### Task 6: Add failing order enrichment tests

**Files:**
- Modify: `py_tests/test_shopify_client_auth.py`
- Optionally create: `py_tests/test_shopify_client_orders.py`

**Step 1: Write tests for enriched order mapping**

Verify that mapped orders now expose:
- `subtotalAmount`
- `discountAmount`
- `refundedAmount`
- `grossSales`
- `netSales`
- `unitsSold`
- `discountCodes`
- enriched item pricing fields

**Step 2: Run the targeted tests**

Run:

```bash
python3 -m unittest py_tests.test_shopify_client_orders -v
```

Expected: FAIL because the query/mapping do not provide those fields yet.

### Task 7: Enrich the Shopify order query and mapping

**Files:**
- Modify: `flin_shopify_analytics_mcp/shopify_client.py`
- Test: `py_tests/test_shopify_client_orders.py`

**Step 1: Extend the GraphQL order query**

Add the reporting fields described in the design.

**Step 2: Extend line item mapping**

Map both quantity and pricing fields into a stable item shape.

**Step 3: Extend order mapping**

Compute normalized per-order KPI fields.

**Step 4: Run targeted client tests**

Run:

```bash
python3 -m unittest py_tests.test_shopify_client_orders -v
```

Expected: PASS

### Task 8: Run the full Python suite

**Files:**
- Modify if needed: any failing file

**Step 1: Run all tests**

Run:

```bash
python3 -m unittest discover -s py_tests -v
```

Expected: PASS

### Task 9: Update public docs

**Files:**
- Modify: `README.md`

**Step 1: Add the new `v2` reporting tools to the README**

Document what each tool does and what questions it answers.

**Step 2: Verify docs reflect current scope**

Read the updated README section and ensure naming matches the implementation.

### Task 10: Build and commit the implementation

**Files:**
- Modify: all changed implementation and test files

**Step 1: Build the package**

Run:

```bash
uv build
```

Expected: sdist and wheel build successfully.

**Step 2: Commit the feature**

Run:

```bash
git add README.md flin_shopify_analytics_mcp py_tests
git commit -m "feat: add v2 reporting core analytics"
```
