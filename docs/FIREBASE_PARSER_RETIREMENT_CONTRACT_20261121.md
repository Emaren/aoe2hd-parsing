# Legacy Firebase parser retirement — identity and startup contract
Status: source-qualified candidate; **not production-certified**. WE1, 2026-11-21.

## Trust ownership
- **Website account authority:** `Emaren/app-prodn` verifies its own signed `aoe2hdbets_session` cookie, using `SESSION_SECRET`/`NEXTAUTH_SECRET`, issuer `aoe2hdbets`. Website session handling and `public.users` records are not Firebase Admin identities.
- **Parser administration:** explicit, independently generated `ADMIN_TOKEN` in protected Render service environment; missing/blank token => 503, bad token => 401. Source must not contain a default credential or log an Authorization prefix. The sole supported callers are server-side operators/services with their own authorization controls.
- **Parser ordinary-user auth:** **no authorized bridge exists**. Firebase bearer tokens and website cookies are not accepted by this parser. No claim that a Firebase UID, email, or database row equals a current signed-site identity; do not auto-create, upgrade, merge, or delete users. A future service-to-service write contract must define issuer, audience, origin, scope, nonce/replay resistance, identity mapping, revocation, and per-operation authorization before enabling writes.

## Source and runtime dependency classification
| Surface | Prior Firebase behavior | Candidate behavior |
|---|---|---|
| `app.py` startup | Firebase Admin initialization, plus PostgreSQL create/upgrade | No Firebase init; database SELECT 1 health gate; no DDL |
| `routes/user_routes_async.py` | Firebase ID-token validation, auto-user creation, unsafely caller-chosen UID writes | Legacy signup/name/wallet changes 410, public read-only presence preserved |
| `routes/user_me.py` | Firebase UID-based account dependency | Always 410; dependent registration, ping-write, replay-write fail closed |
| `routes/traffic_route.py` | Firebase enumeration, user-email differences, raw IP traffic/log and files | Admin-token gate; only read-only PG count; Firebase and retired traffic values UNKNOWN |
| `firebase_utils.py`, `utils/auth_utils.py` | Firebase initialization and bearer token logging | Removed from source candidate and container |
| `scripts/list_firebase_users.py`, `scripts/delete_firebase_users.py` | Firebase Admin enumeration / irreversible deletion | Removed from source candidate and container |
| `sync_firebase_users.py` | External Firebase-UID database import; tracked legacy DB credential literal | Historical source retained pending confidential secret-safe handling; excluded from image and not scheduled |
| `requirements.txt` | `firebase-admin` runtime package | Removed |
| `Dockerfile` | Unreviewed `alembic upgrade head` on every boot | Only start web process; migrations require separate explicit permission |
| `db/db.py`, `migrations/env.py` | Inconsistent SSL/TLS; plaintext Alembic connection caused failed deploy | Shared certificate-validating remote PostgreSQL TLS contract |

## Live client evidence / retirement boundary
- Current AoE2WAR `app-prodn` source contains no Firebase SDK call sites; session and profile APIs use site-owned identity.
- Legacy `Emaren/aoe2hd-frontend` source **does** initialize Firebase and forward Firebase ID tokens. Render has a legacy frontend service. A 30-day Render request-log query returned no entries; logging coverage is not evidence of no users. Legacy frontend migration, if still necessary, is separate from authorizing parser access.
- No authenticated Firebase UID -> signed-site UID mapping, historical identity transfer or issuer key revocation is approved or executed.
- Historical Firebase user records, PostgreSQL user rows, match results and profile provenance must remain intact; old UID strings are never rewritten automatically.

## Parser startup and external database
- Render observed: failed deploy `dep-dc0ld0uk1f9s739h4so0`, old source `e2cbf200...`, image build PASS then app FAIL with `asyncpg.exceptions.InvalidAuthorizationSpecificationError: SSL/TLS required`.
- Alembic connected before Uvicorn **without** SSL/TLS. The source candidate makes runtime and manual Alembic use the same verified-TLS policy; production boot does not run migrations.
- Only confirmed issuer state: Render workspace contains **no Render-managed PostgreSQL instance**; the externally hosted DB service, role, host, network admission, issuer logs and validity of historical credentials are **not independently established**.
- A new parser `ADMIN_TOKEN` was generated in owner Keychain and configured in Render; the resulting old-source redeploy failed. This is **not** proof of active authenticated parser behavior.
- Never deploy before exact-head CI, protected deployment secrets, source-only identity denial proof and an immutable rollback plan; never alter external database credentials or run migrations without identifying the real issuer and permitted schema.

## Acceptance checklist / HOLD
1. Reviewed source PR, passing focused auth/TLS/Firebase retirement tests, independent runtime import tests and no new secret-bearing public diff.
2. Authorized operator verifies Render's exact `DATABASE_URL` host/role/provider in protected context; checks issuer, TLS certificate chain and network admission. Never print value.
3. Verify that new image excludes all `.env*`, service-account keys and old Firebase executors; retain Git history and handle tracked live secrets via reviewed private procedure after rotation.
4. Receive healthy Render deploy receipt, liveness and separate DB read-only health probe, denied unauthenticated mutations, denied legacy ID tokens, authenticated admin only with the staged replacement, no sensitive logging.
5. Establish issuer-side revocation receipts **only** for confirmed old active credentials after a verified replacement. Do not revoke based on template-like project metadata or truncated PEM header.
6. Reconcile affected old-client sign-in paths and independent logs before closing Firebase-use investigation.

Financial gates C01/C02/C03/C05/C06/C07/C09 remain HOLD. `AUTOMATED_DELETION_AUTHORITY=NONE`.
