# GitLab LOC Analyzer - Functional Requirements Document

**Version:** 1.0  
**Date:** February 6, 2026  
**Status:** Production-Ready

---

## Executive Summary

The GitLab Lines of Code (LOC) Analyzer is a batch application designed to provide accurate measurement of code changes between software releases. It addresses a critical business need for tracking development velocity and code churn while eliminating common measurement inaccuracies found in standard Git analysis tools.

---

## Business Purpose

### Primary Goal
Enable accurate tracking of development metrics across Program Increment (PI) cycles by calculating gross lines of code added and deleted between release branches.

### Business Problems Solved

| Problem | Business Impact | Solution |
|---------|----------------|----------|
| Double-counting from merge commits | Inflated LOC metrics, inaccurate velocity tracking | Exclude merge commits by default |
| Including non-code files | Metrics skewed by documentation, configs, vendor code | File-level filtering |
| Process failures requiring restarts | Lost work, manual intervention | Resume-from-failure capability |
| Manual error tracking | Missed issues, incomplete reporting | Automated error collection and notification |

---

## Functional Requirements

### 1. Release Comparison

**FR-001:** The system shall compare two specified Git references (branches or tags) to calculate LOC changes.

**FR-002:** The system shall default to comparing `rel_1` to `rel_2` but allow configuration of any two references.

**FR-003:** The system shall process all commits between the two references sequentially.

---

### 2. Merge Commit Handling

**FR-004:** The system shall exclude merge commits by default to prevent double-counting of code changes.

**FR-005:** A merge commit is defined as any commit with more than one parent commit.

**FR-006:** The system shall count only individual (non-merge) commits that represent actual development work.

**Rationale:** Merge commits represent integration operations, not development work. Including them would:
- Count the same code changes twice
- Include integration-only operations that don't represent team output
- Inflate metrics for release-to-release comparisons

---

### 3. Project Scope Management

**FR-007:** The system shall support project discovery through explicit project IDs.

**FR-008:** The system shall support project discovery through GitLab group IDs.

**FR-009:** The system shall automatically remove duplicate projects when both methods are used together.

**FR-010:** The system shall process projects in ascending ID order for deterministic results.

---

### 4. Metrics Calculation

**FR-011:** The system shall calculate the following metrics for each commit:
- Lines of code added
- Lines of code deleted
- Total changes (additions + deletions)

**FR-012:** The system shall capture commit metadata:
- Commit SHA
- Commit title
- Author name and email
- Commit date
- Source and target branch names

**FR-013:** The system shall associate all metrics with the project path (namespace/project).

**FR-014:** The system shall use diff-based calculation for file-level accuracy.

**FR-015:** If diff calculation fails, the system shall fall back to GitLab commit statistics.

---

### 5. File Filtering (Optional)

**FR-016:** The system shall support filtering based on file paths when enabled.

**FR-017:** The system shall exclude documentation, configuration, and vendor files from calculations when filtering is enabled.

---

### 6. Error Handling and Recovery

**FR-018:** The system shall classify errors into two categories:

**Hard Errors** (Stop Processing):
- GitLab API unavailability
- Authentication failures
- Database connection failures
- Corrupt API responses

**Soft Errors** (Continue Processing):
- Missing branches or tags
- No commits between references
- Diff unavailable for specific commits
- Individual commit processing failures

**FR-019:** The system shall collect all soft errors during execution.

**FR-020:** The system shall continue processing remaining projects when soft errors occur.

---

### 7. Checkpoint and Resume

**FR-021:** The system shall write a checkpoint after each successfully completed project.

**FR-022:** The checkpoint shall record the last completed project ID.

**FR-023:** The system shall read the checkpoint on startup and resume from the next project.

**FR-024:** The system shall clear the checkpoint after successful completion of all projects.

**FR-025:** If the checkpointed project is not found in the current project list, the system shall warn and start from the beginning.

---

### 8. Output Generation

**FR-026:** The system shall generate a CSV file containing all calculated metrics.

**FR-027:** The CSV shall include column headers.

**FR-028:** The system shall optionally insert metrics into a database when database output is enabled.

**FR-029:** The system shall validate database configuration before attempting inserts.

---

### 9. Email Notification

**FR-030:** The system shall send an email notification if soft errors occurred during processing.

**FR-031:** The email notification shall include:
- List of projects with errors
- Error descriptions
- Associated commit information

**FR-032:** Email notification shall be optional and controlled by configuration.

---

## Assumptions and Constraints

### Git Workflow Assumption
The tool assumes the following release workflow:
1. Feature branches are merged into master/main
2. Release branches (e.g., `rel_1`) are created and frozen
3. Development continues on master/main
4. Next release branch (e.g., `rel_2`) is created
5. LOC is compared between `rel_1` and `rel_2`

### Constraints
- Requires GitLab API access with authentication token
- Processes projects sequentially (not parallelized)
- Designed for batch execution, not real-time analysis
- Metrics are point-in-time snapshots, not cumulative tracking

---

## User Scenarios

### Scenario 1: Single Release Analysis
**User:** Release Manager  
**Goal:** Calculate LOC changes between two releases  
**Process:**
1. Configure FROM_REF as previous release tag
2. Configure TO_REF as current release tag
3. Run analysis
4. Review CSV report for metrics

**Expected Result:** Accurate count of actual development work, excluding merge operations.

---

### Scenario 2: Multi-Project Analysis
**User:** Engineering Manager  
**Goal:** Compare metrics across multiple projects in a group  
**Process:**
1. Configure GROUP_IDS to include all relevant projects
2. Run analysis
3. System discovers and processes all projects in the group

**Expected Result:** Consolidated report showing metrics for all projects in the group.

---

### Scenario 3: Resume After Failure
**User:** Operations Team  
**Goal:** Complete analysis after network interruption  
**Process:**
1. System fails during project 15 of 50
2. System writes checkpoint with project 14 completed
3. Operations team restarts the system
4. System reads checkpoint and resumes from project 15

**Expected Result:** No duplicate processing, no lost work.

---

### Scenario 4: Error Investigation
**User:** Development Lead  
**Goal:** Investigate why specific commits couldn't be analyzed  
**Process:**
1. System completes with soft errors on 3 projects
2. System sends email with error details
3. User reviews error log file for technical details
4. User addresses issues (missing branches, permissions, etc.)

**Expected Result:** Complete visibility into processing issues without stopping the entire job.

---

## Success Criteria

The system is considered successful when:

1. ✅ LOC metrics accurately reflect development work (no double counting)
2. ✅ Merge commits are excluded from all calculations
3. ✅ Processing can resume from any point of failure
4. ✅ All soft errors are collected and reported
5. ✅ Output is available in CSV format for analysis
6. ✅ Database output works when enabled and configured
7. ✅ No hard errors cause incomplete analysis runs

---

## Configuration Summary

| Setting | Purpose | Default |
|---------|---------|---------|
| FROM_REF | Source reference for comparison | rel_1 |
| TO_REF | Target reference for comparison | rel_2 |
| PROJECT_IDS | Explicit list of projects to analyze | [] |
| GROUP_IDS | Groups whose projects should be analyzed | [] |
| EXCLUDE_MERGE_COMMITS | Filter out merge commits | True |
| USE_DIFF_FILE_FILTERING | Enable file path filtering | True |
| CSV_FILE | Output file path | gitlab_loc_report.csv |
| DATABASE.ENABLED | Enable database output | False |
| EMAIL.ENABLED | Enable error notification | False |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Feb 6, 2026 | - | Initial requirements document |

---

## Related Documents

- **MERGE_COMMITS_GUIDE.md** - Technical guide on merge commit handling
- **MASTER_PROMPT.md** - Q&A summary from requirements analysis
- **README.md** - Technical usage documentation
