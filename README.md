# GitLab LOC Analyzer (PSI-Aware)

## Overview

GitLab LOC Analyzer is a production-grade batch Python application designed to
accurately calculate gross lines of code (LOC) added and deleted between releases
in GitLab repositories.

It is built specifically for PSI (Program Increment) cycles and avoids
double-counting caused by merge commits.

---

## Key Problems Solved

### Merge Commit Duplication
Merge commits often repeat LOC statistics already present in feature commits.
This tool excludes merge commits by default to ensure accurate metrics.

### File-Level Accuracy
Diff-based LOC calculation allows exclusion of docs, configs, generated files,
and vendor code.

### Operational Reliability
- Resume-from-failure using checkpoints
- Hard vs soft error separation
- Email notification for soft errors

---

## PSI / Git Workflow Assumption

1. Feature branches are merged into master
2. Release branch (e.g. rel_1) is created and frozen
3. Development continues on master
4. Next release branch (e.g. rel_2) is created
5. LOC is compared between rel_1 → rel_2

---

## Features

- Merge commit exclusion (default)
- Diff-based file filtering
- Resume-from-failure checkpointing
- CSV output
- Optional DB insert
- Soft error email notification
- Sequential deterministic processing

---

## Error Handling

### Hard Errors (Stop Job)
- GitLab API unavailable or auth failure
- Database connection / insert failure
- Corrupt API response

### Soft Errors (Continue)
- Missing branch or tag
- No commits between refs
- Diff unavailable
- Commit-level processing failures

Soft errors are collected and emailed at the end of the run.

---

## Resume-from-Failure

- Resume granularity: per project
- Checkpoint written only after successful project completion
- Checkpoint automatically removed after successful full run

---

## How to Run

```bash
python analysis_orchestration.py
```

---

## Configuration

### SCOPE Settings

The analyzer discovers projects using two mechanisms in `config.py`:

- `PROJECT_IDS`: List of explicit GitLab project IDs to analyze.
- `GROUP_IDS`: List of GitLab group IDs whose projects will be discovered and analyzed.

#### Behavior

| PROJECT_IDS | GROUP_IDS | Result |
|-------------|-----------|--------|
| Empty       | Empty     | **No projects processed** (run completes with no output) |
| Filled      | Empty     | Only the listed project IDs are processed |
| Empty       | Filled    | All projects under the listed groups are processed |
| Filled      | Filled    | Both explicit projects and group projects are processed (duplicates are removed automatically) |

#### Examples

```python
# Only specific projects
SCOPE = {"PROJECT_IDS": [123, 456, 789], "GROUP_IDS": []}

# Entire groups
SCOPE = {"PROJECT_IDS": [], "GROUP_IDS": [42, 99]}

# Mixed (duplicates automatically removed)
SCOPE = {"PROJECT_IDS": [123], "GROUP_IDS": [42]}  # If project 123 is in group 42, it will only be processed once
```

**Important**: If both are empty, the analyzer will complete successfully but process no projects.

---

## Testing

### Single Project Test

To test with one project quickly, update `config.py`:

```python
SCOPE = {"PROJECT_IDS": [12345], "GROUP_IDS": []}
```

Replace `12345` with your actual GitLab project ID, then run:

```bash
python analysis_orchestration.py
```

This will process only that project and generate `gitlab_loc_report.csv`.

---

## Design Principles

- Accuracy over speed
- No double counting
- Fail only when continuation is impossible
- Clean state after successful completion
