# Simly Orbis — MongoDB Atlas Backup & Restore Procedure (P9)

## 1. Scope & Collections
Simly Orbis persists state in MongoDB (or in-memory fallback when `MONGODB_URI` is unset):
- `lab_sessions` (TTL index on `created_at` / guest retention)
- `lab_reports`
- `classes`, `class_memberships`, `assignments`, `submissions`, `teachers`, `teacher_tokens`, `student_sessions`, `schema_migrations`

## 2. Automated Atlas Snapshots (Production)
1. Enable **Continuous Cloud Backup** or **Scheduled Daily Snapshots** in MongoDB Atlas (M10+ tier) or daily `mongodump` cron for M0/M2/M5 tiers.
2. Retention target: 7 daily snapshots, 4 weekly snapshots.
3. Verify `MONGODB_URI` uses a dedicated least-privilege database user (`readWrite` on the Orbis database only, never cluster-admin).

## 3. Manual Backup (`mongodump`)
```bash
mongodump --uri="$MONGODB_URI" --archive="orbis_backup_$(date -u +%Y%m%d_%H%M%S).gz" --gzip
```
Store the resulting `.gz` archive in encrypted, access-controlled object storage. Do not commit backups to git.

## 4. Restore Procedure (`mongorestore`)
1. **Pause writes** (put app in maintenance mode or scale replicas to 0).
2. **Dry-run / test restore** into a staging database first:
   ```bash
   mongorestore --uri="$STAGING_MONGODB_URI" --archive="orbis_backup_YYYYMMDD_HHMMSS.gz" --gzip --nsFrom="orbis.*" --nsTo="orbis_staging.*"
   ```
3. **Verify counts & indexes** in staging (`classes`, `submissions`, `lab_reports`), then run `scripts/run_retention.py --dry-run` to confirm TTL/retention behavior.
4. **Restore to production** using `--drop` only after confirming the backup timestamp and staging check:
   ```bash
   mongorestore --uri="$MONGODB_URI" --archive="orbis_backup_YYYYMMDD_HHMMSS.gz" --gzip --drop
   ```
5. **Re-verify** application startup (`ensure_classroom_indexes` runs idempotently on boot) and run a smoke check on `/api/lab/experiments` and `/teacher.html`.
