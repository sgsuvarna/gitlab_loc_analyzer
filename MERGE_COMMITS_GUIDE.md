# Understanding Merge Commits in GitLab LOC Analysis

## Table of Contents
1. [Introduction](#introduction)
2. [The Core Problem: Double Counting](#the-core-problem-double-counting)
3. [Why Merge Commits and Non-Merge Commits Don't Add Up](#why-merge-commits-and-non-merge-commits-dont-add-up)
4. [Your Release Branch Workflow](#your-release-branch-workflow)
5. [The Fork Merge Commit Issue](#the-fork-merge-commit-issue)
6. [Additional Scenarios to Consider](#additional-scenarios-to-consider)
7. [Recommended Configuration](#recommended-configuration)
8. [Summary: When to Include vs Exclude](#summary-when-to-include-vs-exclude)

---

## Introduction

This document explains the intricacies of merge commit handling in GitLab Lines of Code (LOC) analysis, specifically for release-to-release comparisons. Understanding when to include or exclude merge commits is critical for accurate metrics that don't double-count work.

---

## The Core Problem: Double Counting

When analyzing LOC changes between two release branches, you face a fundamental question: **Should you count merge commits or individual commits?**

### The Issue

**Merge commits contain the diff** of all changes from the merged branch, while **individual commits** also contain their own changes. When you sum both, you count the same lines twice.

**Example:**
```
Feature branch with 3 commits:
- Commit A: +10 lines
- Commit B: +5 lines  
- Commit C: +15 lines

When merged to master:
- Merge commit: +30 lines (sum of A+B+C)
- Individual commits: +10, +5, +15 lines

Total if both counted: 60 lines (WRONG - actual work was 30 lines)
```

---

## Why Merge Commits and Non-Merge Commits Don't Add Up

### Technical Explanation

A merge commit in Git has **multiple parent commits** (typically 2 or more). The diff shown in a merge commit represents the cumulative changes from all commits being merged.

```python
# In the code, merge commits are identified by:
len(c.get("parent_ids", [])) > 1
```

### The Math Doesn't Work

| Approach | Lines Counted | Result |
|----------|----------------|--------|
| Merge commits only | Cumulative diffs | May miss some details |
| Non-merge commits only | Individual diffs | **CORRECT for new work** |
| Both combined | 2x actual work | **DOUBLE COUNTING** |

---

## Your Release Branch Workflow

### Your Described Workflow

```
master → rel_1 (release branch created)
rel_1 → hotfix commits → rel_1
master → rel_2 (release branch created)  
rel_2 → hotfix commits → rel_2
```

### Correct Approach for Your Use Case

**You should look at NON-MERGE COMMITS ONLY** for release-to-release comparisons.

### Why Exclude Merge Commits for rel_2 Analysis

1. **The master → rel_2 merge** contains ALL changes from master since rel_1
2. This includes work that was already part of previous releases
3. Counting merge commits would:
   - Include feature work from master that happened between rel_1 and rel_2
   - **Double count across release cycles** if you compare rel_1 → rel_2
   - Make your metrics meaningless for "what work was done in this release"

### What You Actually Want to Count

For `rel_2` analysis, you want:
- ✅ Individual hotfix commits made directly to `rel_2`
- ❌ NOT the merge commit from master (already counted elsewhere)
- ❌ NOT merge commits that are integration operations

---

## The Fork Merge Commit Issue

### Fork Merge Commits Are Still Merge Commits

When you merge into a fork, Git creates a merge commit just like any other merge:

```
original_repo → your_fork
your_fork → feature_branch
feature_branch → your_fork (MERGE COMMIT created!)
```

**The merge into your fork IS counted as a merge commit** because it has multiple parent IDs.

### Why This Matters

If you're comparing `rel_1 → rel_2`, you might see merge commits that:
1. Were created in forks and never touched your main repository
2. Don't represent actual work in your target branch
3. Are integration operations, not development work

### Current Tool Behavior

The tool excludes ALL merge commits, which correctly handles:
- ✅ Master → release merges (prevents double counting)
- ✅ Fork merges (they don't represent work in your repo)
- ✅ Integration-only operations

---

## Additional Scenarios to Consider

### Scenario 1: Feature Branch Workflow

```
feature_branch → master → rel_2
```

**Analysis:**
- Exclude the merge commit from feature_branch → master
- Include individual commits from the feature branch
- This gives you actual feature development work

**Why:** The merge commit contains the cumulative diff of all feature branch commits. Counting both would double the feature's LOC.

---

### Scenario 2: Cherry-pick Hotfixes

```
hotfix_commit → rel_1
same_commit → cherry-pick → rel_2
```

**Analysis:**
- The same commit (same SHA) appears in both releases
- You need **deduplication logic** to avoid counting it twice
- Current tool doesn't handle this automatically

**Impact:** Without deduplication, your rel_1 + rel_2 totals will include the hotfix twice.

---

### Scenario 3: Revert Commits

**Pattern:** Commits with "revert", "reverted", or "rollback" in the title

**Analysis:**
- Revert commits show as additions/deletions in diffs
- They actually **undo** previous work
- They may inflate your LOC metrics without representing new work

**Consideration:** Should reverts count as "work done" or as "corrections"?

---

### Scenario 4: Upstream Sync Merges

```
upstream_repo → your_fork (sync merge)
```

**Analysis:**
- These are merge commits for synchronization
- They don't represent your team's actual work
- They should be excluded from your team's LOC metrics

---

### Scenario 5: Dependency Updates

```
vendor_branch → master (automated merge commit)
```

**Analysis:**
- Often created by bots or CI/CD pipelines
- May add thousands of lines of vendored code
- Not representative of your team's development work

**Consideration:** Should dependency updates be counted in "development effort"?

---

### Scenario 6: Release Branch Back-merges

```
rel_1 → master (merge to bring hotfixes back)
```

**Analysis:**
- These are merge commits but contain important work (hotfixes)
- The hotfix commits were already counted in rel_1
- Back-merge to master shouldn't count as "new work" again

---

## Recommended Configuration

For your specific use case (tracking work per release without double counting):

```python
# config.py
FILTERS = {
    "EXCLUDE_MERGE_COMMITS": True,  # Keep this True
    "USE_DIFF_FILE_FILTERING": True
}
```

### Why This Configuration is Correct

1. **Prevents double counting** (main issue you identified)
2. **Excludes fork/internal merges** that don't represent actual work in your target branch
3. **Excludes integration operations** and focuses on actual work commits
4. **Handles the fork merge commit issue** automatically

---

## Summary: When to Include vs Exclude

### Always EXCLUDE Merge Commits When:

- ✅ Comparing release branches (rel_1 → rel_2)
- ✅ Tracking "new work done" in a period
- ✅ Measuring team development effort
- ✅ Avoiding double counting across releases
- ✅ Analyzing fork workflows
- ✅ Excluding integration-only operations

### When You MIGHT Consider Merge Commits:

- ❓ Understanding total code churn (but you'll get inflated numbers)
- ❓ Auditing all integration points (for compliance)
- ❓ Analyzing merge frequency (process metrics, not LOC metrics)

---

## Key Takeaways

1. **Merge commits are for integration, individual commits are for work done**

2. **For release-to-release comparisons, exclude merge commits** to get accurate "what work was done during this period" metrics

3. **Fork merges are still merge commits** and should be excluded from main repository analysis

4. **The tool's default behavior (EXCLUDE_MERGE_COMMITS: True) is correct** for your use case

5. **Double counting happens when you sum merge + non-merge commits** - this is mathematically incorrect

6. **Consider additional edge cases**: cherry-picks, reverts, dependency updates, and back-merges may need special handling

---

## Final Answer to Your Original Question

> Can I just look at merge commits or I need to look at commits other than merge?

**Answer:** For release-to-release LOC analysis without double counting, **exclude merge commits and only count individual (non-merge) commits**. This gives you the actual lines of code that were added or deleted as work performed during that release cycle.

Merge commits are integration artifacts, not work artifacts. Counting them along with individual commits will always result in inflated, inaccurate metrics.
