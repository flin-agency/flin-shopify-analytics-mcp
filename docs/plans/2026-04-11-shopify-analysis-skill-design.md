# Shopify Analysis Skill Design

**Date:** 2026-04-11

## Goal

Add a repo-local skill that helps Claude use this repository's Shopify MCP tools for fast, executive-style shop analysis.

## User Intent

The skill should not be a tool catalog. It should act as a practical playbook that tells Claude:

- which tools to call first
- how to sequence the checks
- how to summarize results quickly
- how to avoid overclaiming when data quality is weak

The output language should follow the user's language. If the user's language is unclear, Claude can default to English.

## Recommended Scope

Create one repo-local skill:

- `skills/shopify-analysis-playbook/SKILL.md`

The skill should cover these fast analysis modes:

1. Revenue snapshot
2. Product performance snapshot
3. Customer / retention snapshot
4. Attribution sanity check
5. Sales drop diagnosis

## Response Style

The skill should optimize for speed and readability:

- `Summary`
- `Findings`
- `Next checks`

The skill should prefer short answers with only the highest-signal findings.

## Guardrails

The skill must teach Claude to:

- state the date range used
- avoid dumping raw tool output
- start attribution work with `shopify_attribution_quality_summary`
- warn when attribution is sparse or mostly `unattributed`
- warn when retention or new-customer attribution may be incomplete without broad order history
- avoid treating discounts, refunds, or AOV changes in isolation

## Structure

The skill should stay in a single file unless a second support file becomes necessary. For this use case, one `SKILL.md` is enough.

## Success Criteria

The skill is successful if a future Claude instance can quickly answer questions like:

- "How is the shop doing this month?"
- "What drove the revenue change?"
- "Which products or customers matter most?"
- "Is retention healthy?"
- "Can we trust the attribution data?"

without defaulting to a long analyst-style walkthrough.
