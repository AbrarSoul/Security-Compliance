# Sprint 2 — Step 1: Database schema (reference)

This document explains **Sprint 2 Step 1** tables added in Alembic revision **007**, how they connect to **Sprint 1** entities, what each stores, and why it exists. **RBAC enforcement is not implemented yet** — only schema and default **roles** seed data.

---

## How new tables connect to Sprint 1

| Sprint 1 entity | Relationship to Sprint 2 |
|-----------------|---------------------------|
| **`users`** | `user_roles.user_id` → assigns Admin/User/Auditor. `audit_logs.actor_user_id` → who performed an action. `execution_requests.user_id` → who requested validation. `compliance_* .created_by_user_id` → optional audit of author. |
| **`files`** | `execution_requests.file_id` → which dataset the execution intent targets. |
| **`scans`** | `execution_requests.scan_id` (optional) → link to the compliance scan used as input context (risk, findings) for validation. |
| **`reports`** | No direct FK in this step. A future migration can add `report_id` to `execution_requests` or `audit_logs` if reports must tie to execution outcomes. |

---

## Table reference

### 1. `roles`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID | PK |
| `name` | VARCHAR(64) | **UNIQUE** slug: `admin`, `user`, `auditor` |
| `display_name` | VARCHAR(128) | Human label |
| `description` | TEXT | nullable |
| `is_system` | BOOLEAN | default true — seeded roles |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

**Why:** Normalized role catalog for RBAC (enforcement in a later step).

**Seed:** Three rows inserted idempotently (`WHERE NOT EXISTS` on `name`).

---

### 2. `permissions`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID | PK |
| `code` | VARCHAR(128) | **UNIQUE** (e.g. `policy:write`) |
| `description` | TEXT | nullable |
| `created_at` | TIMESTAMPTZ | |

**Indexes:** unique on `code`.

**Why:** Fine-grained capability strings. **No `role_permissions` table in this step** — link roles to permissions in a follow-up migration when RBAC logic is implemented.

---

### 3. `user_roles`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID | PK |
| `user_id` | UUID | FK → `users.id` **ON DELETE CASCADE** |
| `role_id` | UUID | FK → `roles.id` **ON DELETE CASCADE** |
| `created_at` | TIMESTAMPTZ | |

**Constraints:** **UNIQUE** `(user_id, role_id)`.

**Indexes:** `user_id`, `role_id`.

**Why:** Many-to-many user ↔ role. Users have **zero** rows until a later step assigns default `user` or admin bootstrap.

---

### 4. `compliance_rules`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID | PK |
| `code` | VARCHAR(128) | **UNIQUE** stable identifier |
| `name`, `description` | VARCHAR / TEXT | |
| `category` | VARCHAR(64) | e.g. data_leakage, model_trust |
| `severity` | VARCHAR(16) | e.g. low … critical |
| `priority` | INTEGER | default 0 — ordering for engine |
| `condition_json` | JSONB | nullable — rule DSL (evaluator later) |
| `action` | VARCHAR(16) | allow / warn / block |
| `is_enabled` | BOOLEAN | default true |
| `metadata_json` | JSONB | nullable |
| `created_by_user_id` | UUID | FK → `users` **SET NULL** |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

**Indexes:** `code` (unique), `category`, `severity`, `action`, `is_enabled`.

**Why:** Configurable rules beyond Sprint 1’s hard-coded scoring/recommendations.

---

### 5. `compliance_policies`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID | PK |
| `name`, `description` | VARCHAR / TEXT | |
| `policy_type` | VARCHAR(32) | `data` \| `execution` \| `model` |
| `definition_json` | JSONB | default `{}` — thresholds, weights, includes |
| `is_active` | BOOLEAN | default true |
| `severity_default` | VARCHAR(16) | nullable |
| `created_by_user_id` | UUID | FK → `users` **SET NULL** |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

**Indexes:** `policy_type`, `is_active`.

**Why:** Admin-defined bundles of behavior and thresholds for the policy engine.

---

### 6. `policy_rules`

| Column | Type | Notes |
|--------|------|--------|
| `policy_id` | UUID | PK part 1, FK → `compliance_policies` **CASCADE** |
| `rule_id` | UUID | PK part 2, FK → `compliance_rules` **CASCADE** |
| `sort_order` | INTEGER | default 0 |
| `created_at` | TIMESTAMPTZ | |

**Primary key:** `(policy_id, rule_id)`.

**Why:** Many-to-many **with ordering** so policies compose multiple rules deterministically.

---

### 7. `audit_logs`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID | PK |
| `created_at` | TIMESTAMPTZ | indexed — append-only “timestamp” |
| `actor_user_id` | UUID | FK → `users` **SET NULL** (retain log if user deleted) |
| `action` | VARCHAR(128) | e.g. `file.upload`, `execution.blocked` |
| `resource_type` | VARCHAR(64) | nullable |
| `resource_id` | UUID | nullable polymorphic target |
| `risk_level` | VARCHAR(16) | nullable |
| `status` | VARCHAR(32) | success, failure, blocked, … |
| `metadata_json` | JSONB | nullable — structured context (no secrets) |
| `request_id` | VARCHAR(64) | nullable — HTTP correlation |
| `ip_address` | VARCHAR(45) | nullable |
| `user_agent` | TEXT | nullable |

**Indexes:** `created_at`, `actor_user_id`, `action`, `resource_type`, `resource_id`, `risk_level`, `status`, `request_id`, composite `(resource_type, resource_id)`, `(actor_user_id, created_at)`.

**Why:** Security and compliance **evidence trail** for uploads, scans, policy changes, execution decisions, auth events (writers added in later steps).

---

### 8. `model_validations`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID | PK |
| `execution_request_id` | UUID | FK → `execution_requests` **CASCADE**, **UNIQUE** (one row per request) |
| `status` | VARCHAR(32) | default `pending` — pending / completed / failed |
| `risk_score` | SMALLINT | nullable |
| `flags_json` | JSONB | nullable — e.g. external API, deployment class |
| `details_json` | JSONB | nullable — structured check output |
| `validated_at` | TIMESTAMPTZ | nullable |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

**Indexes:** `status`; unique on `execution_request_id`.

**Why:** Isolates **model-side** compliance (external vs local, risky provider, etc.) from final merged **execution_result**.

---

### 9. `execution_requests`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID | PK |
| `user_id` | UUID | FK → `users` **CASCADE** |
| `file_id` | UUID | FK → `files` **CASCADE** |
| `scan_id` | UUID | FK → `scans` **SET NULL** — optional scan snapshot |
| `model_provider`, `model_name` | VARCHAR | nullable — declared model |
| `model_endpoint_url` | TEXT | nullable |
| `is_external_api` | BOOLEAN | default false |
| `status` | VARCHAR(32) | default `pending` — workflow state |
| `notes` | TEXT | nullable |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

**Indexes:** `user_id`, `file_id`, `scan_id`, `status`, composite `(user_id, status)`.

**Why:** Canonical **“intent to execute”** record: dataset + declared model + optional Sprint 1 scan context. Drives `model_validations` and `execution_results`.

---

### 10. `execution_results`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID | PK |
| `execution_request_id` | UUID | FK → `execution_requests` **CASCADE**, **UNIQUE** |
| `decision` | VARCHAR(16) | nullable until evaluated — allow / warn / block |
| `risk_score` | SMALLINT | nullable |
| `reason_codes_json` | JSONB | default `[]` |
| `evaluation_summary_json` | JSONB | nullable — merged policy/rule output |
| `status` | VARCHAR(32) | default `pending` — row lifecycle |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

**Indexes:** `decision`, `status`; unique on `execution_request_id`.

**Why:** Stores **final** allow/warn/block outcome and machine-readable reasons for UI, API, and audit correlation.

---

## Migration file

- **`backend/alembic/versions/007_sprint2_rbac_policy_execution_audit.py`**
- **Revision:** `007` → **`down_revision`:** `006`

Apply when PostgreSQL is available:

```bash
cd backend && source .venv/bin/activate && alembic upgrade head
```

---

## ORM modules

| Model | Module |
|-------|--------|
| `Role` | `app/models/role.py` |
| `Permission` | `app/models/permission.py` |
| `UserRole` | `app/models/user_role.py` |
| `ComplianceRule` | `app/models/compliance_rule.py` |
| `CompliancePolicy` | `app/models/compliance_policy.py` |
| `PolicyRule` | `app/models/policy_rule.py` |
| `AuditLog` | `app/models/audit_log.py` |
| `ExecutionRequest` | `app/models/execution_request.py` |
| `ModelValidation` | `app/models/model_validation.py` |
| `ExecutionResult` | `app/models/execution_result.py` |

Sprint 1 **`User`**, **`File`**, **`Scan`** models include **inverse relationships** for `user_roles`, `execution_requests`, and (for `Scan`) `execution_requests` so the ORM graph is navigable when services are added later.

---

## Step 2 (implemented): RBAC

- Migration **008**: `role_permissions` + seeded permissions + role mappings; backfills `user` role for existing accounts.
- Default **`user`** role assigned on signup; JWT includes `roles` and `permissions`.
- Dependencies: `require_permission`, `require_role`, `require_any_permission` in `app/auth/rbac.py`.
- Example routes: `/api/v1/rbac/admin/*`, `/api/v1/rbac/user/*`, `/api/v1/rbac/auditor/*`.
- Core APIs (`files`, `scans`, `reports`, `scoring`) enforce permissions.

## Next steps (after Step 2)

- Audit logging writers (Step 3+).
- Services: policy/rule evaluation, execution pipeline writing `model_validations` + `execution_results` + `audit_logs`.
