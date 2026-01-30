# Job Flow – GitLab LOC Analyzer

## High-Level Flow

Start
 → Load configuration
 → Load checkpoint
 → Discover projects
 → Deduplicate projects
 → Sort projects
 → Resume logic
 → Process each project
 → Save checkpoint
 → Generate output
 → Insert DB (optional)
 → Email soft errors
 → Cleanup checkpoint
End

---

## Detailed Flow

For each project:
- Deduplicate project list by `id` (avoids double counting across explicit project IDs and group projects)
- Validate refs (soft error if missing)
- Compare refs
- For each commit:
  - Apply filters (merge, author, regex)
  - Calculate LOC using diff
  - Fallback to stats if diff fails
- Save checkpoint after project completion

---

## Resume Logic

Checkpoint file example:
{
  "last_completed_project_id": 12345,
  "timestamp": "ISO8601"
}

Behavior:
- Resume from next project after failure
- If checkpoint project no longer exists, resume mode is disabled
- Checkpoint deleted after successful run

---

## Error Classification

Hard Errors:
- API unreachable or auth failure
- Database failures

Soft Errors:
- Missing branch
- Empty compare result
- Diff failures
- Commit-level issues

---

## Module Responsibilities

- `analysis_orchestration.py`: Entry point; loads config/checkpoint, discovers & dedupes projects, sorts, applies resume logic, runs metrics per project, writes CSV, optional DB insert, optional error email, clears checkpoint.
- `api_client.py`: Thin GitLab REST client with retry/backoff and pagination helpers.
- `project_discovery.py`: Fetches projects by explicit IDs and group IDs, deduping by `id` to avoid duplicate processing.
- `metrics_calculation.py`: Compares refs, filters commits, computes LOC via diffs with stats fallback, records soft errors per commit.
- `output_generation.py`: Writes CSV; optionally inserts rows into Oracle (expects table name and column order from config).
- `email_notifier.py`: Formats and sends soft-error digest via SMTP (supports optional STARTTLS/auth when credentials provided).
- `checkpoint.py`: Persists last completed project ID with timestamp; used for resumable runs; cleared on success.
- `error_collector.py`: Aggregates soft errors keyed by project with timestamps and context.
- `config.py`: Central configuration; includes GitLab, scope, comparison refs, filters, DB and email settings, output target.

---

## Config Requirements (DB & Email)

- Database (when `DATABASE.ENABLED=True`): `HOST`, `PORT`, `SERVICE`, `USER`, `PASSWORD`, `TABLE`, `COLUMNS` must be set; table/columns must align with row keys.
- Email (when `EMAIL.ENABLED=True`): `FROM`, `TO`, `SMTP_SERVER`, `PORT`; optional `USERNAME`, `PASSWORD` (enables STARTTLS+login when provided).

---

## API Retry Behavior (429 best practice without hard errors)

- Respect `Retry-After` when present; otherwise use exponential backoff with jitter and a max cap.
- Keep retries bounded; after final retry, return a safe fallback (e.g., empty page for pagination) and log the condition instead of raising.
- Ensure callers handle empty/partial data gracefully to avoid crashes while staying polite to the API.

---

## Guarantees

- Deterministic execution
- No duplicate LOC counts
- Safe restarts
- Production-grade batch behavior
