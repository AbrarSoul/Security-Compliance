# Sprint 3 — Technical Documentation

Real-time compliance monitoring, guard enforcement, notifications, analytics, gap analysis, and threat detection.

## Architecture overview

```
Client / Dashboard
       │
       ▼
  FastAPI (/api/v1)
       │
       ├── Prompt / Output scan APIs
       ├── Compliance Guard (runtime enforcement)
       ├── Monitoring sessions & events
       └── Analytics / Gaps / Threats APIs
       │
       ▼
  EventDispatcher (transactional)
       ├── domain_events (append-only)
       └── event_outbox (pending → processed)
       │
       ▼
  OutboxWorker (background) ──► Handler registry
       ├── MonitoringStatusHandler
       ├── NotificationEventHandler
       └── ThreatDetectionEventHandler
       │
       ▼
  Side effects: notifications, SSE pub/sub, audit_logs, security_event_logs
```

## End-to-end workflow

| Step | Component | API / event |
|------|-----------|-------------|
| 1 | Prompt submitted | `POST /monitoring/guard/.../prompt` or `/monitoring/prompts/scan` |
| 2 | Prompt monitoring | `PromptMonitoringService` → `prompt_scanned` / `prompt.blocked` |
| 3 | Rule / policy evaluation | `ComplianceGuardService` → runtime rules + policies |
| 4 | Policy enforcement | `guard.enforced`, `policy.violation`, `execution.blocked` |
| 5 | Execution | Sprint 2 execution APIs |
| 6 | Output monitoring | `POST /monitoring/guard/.../output` → `output.blocked` |
| 7 | Alert generation | Outbox → `NotificationEventHandler` |
| 8 | Analytics update | Aggregations over `domain_events`, scans, executions |
| 9 | Audit logging | `AuditService` on guard, execution, auth |

Domain events are persisted first; the outbox guarantees at-least-once delivery to handlers.

## Modules

### Step 2 — Monitoring pipeline
- Tables: `monitoring_sessions`, `domain_events`, `event_outbox`
- Permissions: `monitoring:read`, `monitoring:read_all`, `monitoring:publish`, `monitoring:manage`
- SSE: `GET /monitoring/sessions/{id}/stream`

### Step 3 — Prompt monitoring
- Table: `prompt_scans`
- Detectors: PII, secrets, injection, jailbreak
- API: `POST /monitoring/prompts/scan`

### Step 4 — Output compliance
- Table: `output_scans`
- Mask tokens: `[EMAIL_MASKED]`, `[PASSWORD_MASKED]`, etc.
- API: `POST /monitoring/outputs/scan`

### Step 5 — Compliance guard
- Table: `guard_enforcement_logs`
- APIs: `POST /monitoring/guard/executions/{id}/prompt|output`
- Can interrupt started executions

### Step 6 — Notifications
- Tables: `notifications`, `notification_preferences`
- Email via SMTP (`SMTP_ENABLED`, `SMTP_*`)
- SSE: `GET /notifications/stream/alerts`

### Step 7 — Analytics
- Permissions: `analytics:read`, `analytics:read_all`
- API: `GET /analytics/dashboard` (aggregated charts data)

### Step 8 — Gap analysis
- Tables: `gap_analysis_runs`, `compliance_gaps`
- Permissions: `gap:read`, `gap:analyze`, `gap:read_all`
- API: `POST /gaps/analyze`

### Step 9 — Threat detection
- Tables: `threat_detection_runs`, `security_threats`, `security_event_logs`
- Permissions: `threat:read`, `threat:manage`, `threat:read_all`
- Real-time: `ThreatDetectionEventHandler` on block/violation events
- API: `POST /threats/detect`

## Configuration

| Variable | Purpose |
|----------|---------|
| `MONITORING_OUTBOX_WORKER_ENABLED` | Background outbox processing (default `true`) |
| `MONITORING_OUTBOX_POLL_SECONDS` | Worker poll interval |
| `MONITORING_OUTBOX_BATCH_SIZE` | Rows per batch |
| `SMTP_ENABLED` | Send notification emails |
| `ENCRYPTION_AT_REST_ENABLED` | Gap rule for encryption posture |

## Database

Migrations **017–025**. Performance indexes in **025** optimize:
- Outbox claims (`status`, `created_at`)
- Analytics time-range queries (`user_id`, `occurred_at`)
- Notification unread counts

## Testing

```bash
cd backend
source .venv/bin/activate
alembic upgrade head

# Sprint 3 unit + API tests
pytest tests/test_monitoring_pipeline.py tests/test_prompt_monitoring_api.py \
  tests/test_output_compliance_api.py tests/test_compliance_guard_api.py \
  tests/test_notifications_api.py tests/test_analytics_api.py \
  tests/test_gaps_api.py tests/test_threats_api.py -v

# Sprint 3 integration
pytest -m sprint3 tests/test_sprint3_integration.py -v

# Full E2E (requires PostgreSQL + migrations 016+)
pytest -m sprint3_e2e tests/test_sprint3_e2e_workflow.py -v
```

Tests set `MONITORING_OUTBOX_WORKER_ENABLED=false` and call `process_outbox()` explicitly to drain the outbox deterministically.

## Dashboard routes (frontend)

| Route | Permission |
|-------|------------|
| `/analytics` | `analytics:read` or `analytics:read_all` |
| `/gaps` | `gap:read` or `gap:read_all` |
| `/threats` | `threat:read` or `threat:read_all` |

Admin-only actions: **Run gap analysis**, **Run threat detection** (`gap:analyze`, `threat:manage`).

## Operational notes

1. Run `alembic upgrade head` after pulling Sprint 3.
2. Re-login users so JWT includes new permissions.
3. Keep outbox worker enabled in production for real-time alerts.
4. Use `GET /monitoring/status` for `outbox_pending` backlog monitoring.
