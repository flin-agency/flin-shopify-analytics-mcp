# Shopify Analysis Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a repo-local skill that guides fast, decision-oriented Shopify analysis with this repository's MCP tools.

**Architecture:** Create a single repo-local skill under `skills/shopify-analysis-playbook/` and keep the logic in one `SKILL.md`. Document when to use the skill, which tool sequences to prefer, what answer shape to use, and what data-quality caveats must be stated before interpreting retention or attribution.

**Tech Stack:** Markdown skill file, repo-local docs in `docs/plans/`

---

### Task 1: Write the design and plan docs

**Files:**
- Create: `docs/plans/2026-04-11-shopify-analysis-skill-design.md`
- Create: `docs/plans/2026-04-11-shopify-analysis-skill.md`

**Step 1: Write the design doc**

Capture:

- goal
- intended user behavior
- response shape
- analysis modes
- guardrails

**Step 2: Write the implementation plan**

Keep it short and specific to the skill file creation.

**Step 3: Review both docs**

Check that the design explicitly says this is a playbook, not a tool reference.

### Task 2: Create the repo-local skill

**Files:**
- Create: `skills/shopify-analysis-playbook/SKILL.md`

**Step 1: Write the frontmatter**

Add:

- `name`
- `description`

The description should be about when to use the skill, not about its internal workflow.

**Step 2: Write the playbook**

Include:

- overview
- response shape
- core rules
- fast workflows
- common traps

**Step 3: Keep the skill lean**

Avoid long narratives, deep theory, or per-tool encyclopedic explanations.

### Task 3: Verify and publish the repo change

**Files:**
- Review: `skills/shopify-analysis-playbook/SKILL.md`
- Review: `docs/plans/2026-04-11-shopify-analysis-skill-design.md`
- Review: `docs/plans/2026-04-11-shopify-analysis-skill.md`

**Step 1: Verify file structure**

Run file listing and inspect the new skill file.

**Step 2: Review diff**

Confirm only the new docs and skill folder are included.

**Step 3: Commit**

Use a focused commit message such as:

```bash
git add docs/plans/2026-04-11-shopify-analysis-skill-design.md docs/plans/2026-04-11-shopify-analysis-skill.md skills/shopify-analysis-playbook/SKILL.md
git commit -m "docs: add shopify analysis playbook skill"
```
