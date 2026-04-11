# V3 Retention CRM Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add four retention-focused Shopify analytics tools for repeat-purchase KPIs, time-to-second-order metrics, and inactivity summaries.

**Architecture:** Build a customer-history layer from enriched order records, then implement retention aggregations on top of that history. Expose the new analytics through MCP tools without changing the transport or auth layer.

**Tech Stack:** Python 3.10+, stdlib, Shopify Admin GraphQL, unittest

---

### Task 1: Persist the approved design

**Files:**
- Create: `docs/plans/2026-04-11-v3-retention-crm-design.md`
- Create: `docs/plans/2026-04-11-v3-retention-crm.md`

**Step 1: Save the design and plan files**

Write the approved `v3` design and implementation plan to `docs/plans/`.

**Step 2: Commit the docs**

Run:

```bash
git add docs/plans/2026-04-11-v3-retention-crm-design.md docs/plans/2026-04-11-v3-retention-crm.md
git commit -m "docs: add v3 retention crm design"
```

### Task 2: Add failing analytics tests

**Files:**
- Modify: `py_tests/test_analytics.py`

**Step 1: Add failing tests for retention analytics**

Cover:
- retention overview
- repeat purchase windows
- time to second order
- inactive customer summary

**Step 2: Run the targeted analytics tests**

Run:

```bash
python3 -m unittest py_tests.test_analytics -v
```

Expected: FAIL because the retention analytics functions do not exist yet.

### Task 3: Implement customer-history analytics

**Files:**
- Modify: `flin_shopify_analytics_mcp/analytics.py`
- Test: `py_tests/test_analytics.py`

**Step 1: Add customer-history helpers**

Implement:
- tracked customer key resolution
- customer history builder
- days-to-second-order calculation
- inactivity day calculations

**Step 2: Implement retention analytics functions**

Add:
- `retention_overview`
- `repeat_purchase_windows`
- `time_to_second_order`
- `inactive_customer_summary`

**Step 3: Run the targeted analytics tests**

Run:

```bash
python3 -m unittest py_tests.test_analytics -v
```

Expected: PASS

### Task 4: Add failing MCP exposure tests

**Files:**
- Modify: `py_tests/test_mcp_server.py`

**Step 1: Extend the fake client and expected tool list**

Add enough order history fields to support the new tools.

**Step 2: Add failing MCP tests**

Verify:
- `tools/list` includes the new retention tools
- `tools/call` returns structured content for at least one retention tool

**Step 3: Run MCP tests**

Run:

```bash
python3 -m unittest py_tests.test_mcp_server -v
```

Expected: FAIL because `tools.py` does not expose the retention tools yet.

### Task 5: Register and dispatch the retention tools

**Files:**
- Modify: `flin_shopify_analytics_mcp/tools.py`
- Test: `py_tests/test_mcp_server.py`

**Step 1: Add the four tool definitions**

Use clear schemas with `dateFrom`, `dateTo`, `asOfDate`, and `limit` where appropriate.

**Step 2: Add dispatch logic**

Load order history up to `asOfDate`, then route into the retention analytics helpers.

**Step 3: Run MCP tests**

Run:

```bash
python3 -m unittest py_tests.test_mcp_server -v
```

Expected: PASS

### Task 6: Update documentation

**Files:**
- Modify: `README.md`

**Step 1: Document the new `v3` tools**

Add a short section describing what each new retention KPI tool answers.

**Step 2: Add data caveats**

State clearly that these metrics depend on sufficient historical order coverage and work best with `read_all_orders`.

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
git commit -m "feat: add v3 retention crm analytics"
```
