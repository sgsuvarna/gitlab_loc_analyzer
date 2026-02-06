# Master Prompt: GitLab LOC Analyzer - Merge Commits Analysis

**Date:** February 6, 2026  
**Context:** Analysis of GitLab Lines of Code (LOC) tool for release-to-release comparisons  
**Status:** Analysis Complete - No Code Changes Required

---

## Original Request

> Please analyze the code and let me know what changes are required to consider only merge commits. Don't make any changes to the code.

**Follow-up Questions:**
1. How many files will change?
2. Understanding release branch workflow and double counting
3. Fork merge commit identification

---

## Key Questions & Answers

### Q1: What changes are needed to consider ONLY merge commits (instead of excluding them)?

**Files to Change:** 2 files

**Changes Required:**

1. **`config.py`** - Add new configuration option:
```python
FILTERS = {
    "EXCLUDE_MERGE_COMMITS": False,           # Changed from True
    "INCLUDE_ONLY_MERGE_COMMITS": True,       # New option
    "USE_DIFF_FILE_FILTERING": True
}
```

2. **`metrics_calculation.py`** - Modify filtering logic (lines 14-15):
```python
# Add after existing merge commit exclusion
if cfg["FILTERS"].get("INCLUDE_ONLY_MERGE_COMMITS", False) and len(c.get("parent_ids", [])) <= 1:
    continue  # Skip non-merge commits
```

---

### Q2: When I add merge commits and non-merge commits, why don't the numbers match?

**Answer:** **Double counting occurs** because:
- Merge commits contain the cumulative diff of all merged commits
- Individual commits also contain their own changes
- Adding both = 2x actual work done

**Example:**
```
Feature with 3 commits (10+5+15 lines):
- Individual commits: 10 + 5 + 15 = 30 lines
- Merge commit: 30 lines
- Total if both counted: 60 lines (WRONG)
```

---

### Q3: Release Branch Workflow Analysis

**User's Workflow:**
```
master → rel_1 → hotfix commits → rel_1
master → rel_2 → hotfix commits → rel_2
```

**Question:** Can I just look at merge commits or do I need to look at non-merge commits for rel_2 LOC?

**Answer:** **Look at NON-MERGE COMMITS ONLY**

**Reasoning:**
- Merge commits from master → rel_2 contain ALL changes since rel_1
- This includes work from previous releases → **double counting across releases**
- Individual commits represent actual work done during that release cycle
- Fork merges are also merge commits that don't represent work in your target repo

**Correct Configuration:**
```python
FILTERS = {
    "EXCLUDE_MERGE_COMMITS": True,   # Keep as-is (correct default)
    "USE_DIFF_FILE_FILTERING": True
}
```

---

### Q4: Fork Merge Commits Issue

**Observation:** Merging into a fork creates a merge commit.

**Answer:** **TRUE**

**Implications:**
- Fork merges are counted as merge commits (multiple parent IDs)
- They don't represent work in your main repository
- They are integration operations, not development work
- The tool's default (exclude merge commits) correctly handles this

---

## Final Recommendation

**Do NOT change the code.** The current implementation is correct for release-to-release LOC analysis.

**Current Settings are Optimal:**
- `EXCLUDE_MERGE_COMMITS: True` → Prevents double counting
- Excludes fork/internal merges → Focuses on actual work
- Excludes integration operations → Counts only development work

---

## Additional Scenarios Identified

1. **Cherry-pick Hotfixes** → Same commit in multiple releases = needs deduplication
2. **Revert Commits** → May inflate metrics without representing new work
3. **Upstream Sync Merges** → Don't represent your team's work
4. **Dependency Updates** → Often automated, not development effort
5. **Release Branch Back-merges** → Already counted in source release

---

## Key Takeaways

1. **Merge commits = integration, Individual commits = work done**
2. **For release comparisons, ALWAYS exclude merge commits**
3. **Double counting happens when summing merge + non-merge commits**
4. **Fork merges are still merge commits** and should be excluded
5. **The tool's default behavior is correct** for your use case

---

## Artifacts Created

1. **MERGE_COMMITS_GUIDE.md** - Comprehensive guide covering all scenarios
2. **MASTER_PROMPT.md** (this file) - Quick reference of questions and answers

---

## Decision Summary

| Question | Decision |
|----------|----------|
| Change code to support only merge commits? | **NO** - Not needed |
| Exclude merge commits for release analysis? | **YES** - Correct approach |
| Current tool configuration? | **OPTIMAL** - No changes required |

**Next Steps:** Use the tool as-is with `EXCLUDE_MERGE_COMMITS: True` for accurate release-to-release LOC metrics.
