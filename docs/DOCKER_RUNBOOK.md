# Docker / local validation runbook

V5 validated on 2026-11-17: all eleven long-running containers are healthy,
initializer exits 0, and 24 Docker API acceptance check groups pass with mock email.
The host needed recovery of corrupt unpacked base snapshots and the legacy builder.
Default BuildKit still has the recorded host EOF limitation. V5 Chrome E2E passed
after host resources improved and two browser-script defects were corrected.
Latest evidence and limitations: [V4 handover](AI_V4_HANDOVER.md).

V5 distinguishes **current runtime PASS** from **supported-host rebuild PASS**:
all nine application images rebuilt under separate verification tags; Room and
the shared frontend build path additionally completed `docker build --no-cache`
under fresh tags. The fresh Room image connected to acceptance SQL, and the fresh
Customer image served production HTTP in a disposable container. Active deployment
images/volumes were not replaced by these smoke tests. This proves the documented
recovered-base/legacy-builder environment, not an untested clean Linux/BuildKit host.

Final verification commands also include:

```powershell
python test/check_release_content.py
python test/check_release_content.py --staged
npm install --prefix logs/v4-browser playwright@1.65.1 --no-audit --no-fund
python test/run_isolated_acceptance.py --allow-test-writes --docker --browser
```

## Current recovered host build path

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File infrastructure/Build-Images.ps1 -LegacyBuilder
docker compose --env-file .env.acceptance.local -p luxestay-acceptance up -d --no-build
python test/run_isolated_acceptance.py --allow-test-writes --docker
```

The helper builds images sequentially with resolved public build arguments, then
Compose runs them normally. It does not delete images, volumes or cache. Individual
`docker build` commands with `DOCKER_BUILDKIT=0` produced the recorded build evidence;
the helper's PowerShell syntax is validated. Clean hosts should use their normal
builder and official base pulls; no snapshot repair should be assumed necessary.

For this host only, the failed Python executable was 0 bytes in a container export,
but 14,480 bytes in its saved layer. `infrastructure/recover_image_snapshot.py IMAGE SLUG`
reconstructs saved layers into a **new** `luxestay-v4-recovered-SLUG` image. It leaves
original tags untouched. The old bases were preserved as `luxestay-v4-original-python`
and `luxestay-v4-original-node`, before pointing the local base tags to recovered
images. Both Python/Node execution and all nine application builds then succeeded
via legacy builder. This repair changes host snapshots, not application source or
database contents. Do not overwrite preserved aliases or reset storage to repeat it.

## Safe isolated configuration

Requirements: Docker Desktop in Linux container mode; Docker Compose; enough
memory for SQL Server and Next builds. Local checks additionally need Python
3.11+ with `requirements.txt`, Node 24 and pnpm 12.6.0. Windows Python 3.12.10
and installed ODBC Driver 18 were used for validation.

From repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File infrastructure/New-DockerTestEnvironment.ps1
docker compose --env-file .env.acceptance.local -p luxestay-acceptance config --quiet
docker compose --env-file .env.acceptance.local -p luxestay-acceptance up -d sqlserver rabbitmq db-init
```

The generator refuses to overwrite existing files. It creates ignored random
SQL, JWT, broker and internal credentials. Do not print or commit this file.
It deliberately uses project-specific volumes, a project network, mock email,
and ports different from the pre-existing Windows/Docker services.

| Component | Default host port | Acceptance host port | Container port |
|---|---:|---:|---:|
| SQL Server | 1433 | 11433 | 1433 |
| RabbitMQ AMQP / management | 5672 / 15672 | 15673 / 15674 | 5672 / 15672 |
| Hotel / User / Room | 8000 / 8001 / 8002 | 18000 / 18001 / 18002 | 8000 / 8001 / 8002 |
| Booking / Payment / Notification | 8003 / 8004 / 8005 | 18003 / 18004 / 18005 | 8003 / 8004 / 8005 |
| Gateway | 8080 | 18080 | 8080 |
| Admin / Customer | 3000 / 3001 | 13000 / 13001 | 3000 / 3000 |

The following are the normal Compose build commands for a healthy BuildKit host.
Use the recovered-host path above on this particular machine:

```powershell
docker compose --env-file .env.acceptance.local -p luxestay-acceptance build user-service
# Build other services individually on memory-constrained hosts.
docker compose --env-file .env.acceptance.local -p luxestay-acceptance build admin-dashboard
docker compose --env-file .env.acceptance.local -p luxestay-acceptance build customer-web
docker compose --env-file .env.acceptance.local -p luxestay-acceptance up -d --build
docker compose --env-file .env.acceptance.local -p luxestay-acceptance ps -a
```

Do not use `down -v`. Ordinary restarts preserve the named SQL/broker volumes.
No existing Windows database or original Compose volume is a substitute for
the acceptance volumes. Do not run initialization scripts against existing
databases without backup and review.

## Database initialization / migration

`sqlserver` runs the stock entrypoint; read-only mount files are never modified.
`db-init` runs after SQL readiness and exits nonzero on a SQL error. It initializes
only databases that do not exist, using each service's checked-in script.
Applications wait for successful completion. Existing databases are skipped:
there is no implicit migration or reseed at restart. If initialization fails
partway, inspect the specific schema and apply the corrected script explicitly
to the isolated database; existence alone does not prove initialization passed.

The six database names are `hotel_service`, `user_service`, `room_service`,
`booking_service`, `payment_service`, `notification_service`. Compose fixes each
service to its own database; old `*_DB_NAME` overrides are not used.

Existing deployments need review/backups before explicitly applying:

- User: `services/user-service/migrations/20261117_profile_timestamps.sql`.
- Payment: `services/payment-service/migrations/20261117_otp_hash_width.sql`.
- Notification: `services/notification-service/migrations/20261102_add_event_key_idempotency.sql`.

Connect explicitly to the owning database with `sqlcmd -d <database> -C -I -b -i <migration>`.
Inject credentials through the process environment / secret store, not command
arguments. Never substitute another service's database. User and Payment startup
check schemas without altering them; Room and Notification retain their read-only
startup checks. Booking still uses `create_all` for missing tables, not migration.

Demo accounts are separate in `services/user-service/database_demo_seed.sql`.
`SEED_DEMO_DATA=0` is the default. The acceptance generator opts in with `1`;
seeding occurs only when a new User database is created. Consult that demo-only
SQL file for fixture credentials. It must not be used for an external deployment.
Existing plaintext passwords are rejected. They require an explicit account
reset or reviewed bcrypt migration; no existing account was silently converted.

## Environment precedence and URLs

| Setting | Purpose |
|---|---|
| `SA_PASSWORD` | SQL container bootstrap and service database password |
| `JWT_SECRET_KEY` | One random signing/verification key shared by all six services |
| `INTERNAL_SERVICE_SECRET` | Separate shared key for authenticated internal APIs |
| `RABBITMQ_USER`, `RABBITMQ_PASSWORD` | Broker credentials shared with publishers/consumer |
| `MOCK_EMAIL_SEND` | `True` for local acceptance; real SMTP was not exercised |
| `SEED_DEMO_DATA` | Explicit opt-in to fresh demo accounts |
| `CORS_ORIGINS` | JSON array of browser origins matching the chosen frontend ports |
| `NEXT_PUBLIC_GATEWAY_URL` | Browser-visible gateway API URL; baked into Next builds |
| `ENV_FILE` | Optional absolute dotenv path for local application startup |

Application process environment takes precedence over dotenv. Without `ENV_FILE`,
each application reads its own service/gateway `.env`, anchored to source location;
the caller's working directory has no influence. Root `.env` is for Compose.
Existing root/service dotenv files were preserved and still need operator-managed
alignment before using the old Windows launcher. The root dotenv currently lacks
the required internal secret; use the generated acceptance file for testing.

Containers use service DNS names for backend calls. The browser must use a URL it
can reach (e.g. `http://localhost:18080/api/v1`), not `http://gateway:8080`.
Changing a `NEXT_PUBLIC_*` value requires rebuilding the frontend. Payment sandbox
links use `PUBLIC_API_URL`, set to the same public gateway API URL in Compose.
JWT/internal/database/SMTP secrets are excluded from frontend build arguments.

## Running one component

```powershell
docker compose --env-file .env.acceptance.local -p luxestay-acceptance up -d user-service
```

This starts SQL + one-shot initializer + User, not both frontends or every backend.
Room also starts Hotel for ownership checks. Booking/Payment/Notification require
RabbitMQ in Compose. Their business dependencies are in `ACTUAL_ARCHITECTURE.md`.
An isolated health check does not prove a complete booking workflow.

Every backend exposes `/health`; database outages return 503. Notification also
checks the broker. Gateway `/health` aggregates them and preserves degraded status.
Swagger is `/docs` on each backend; Notification OpenAPI is
`/api/v1/openapi.json`; others use `/openapi.json`. Gateway proxies business routes;
its Swagger does not merge every backend's schema.

## Reproducing checks

```powershell
python -m pip install -r requirements.txt
python test/run_offline_regressions.py
pnpm.cmd --dir front-end --filter customer-web build
pnpm.cmd --dir front-end --filter admin-dashboard build
pnpm.cmd --dir front-end --filter '@repo/api-client' test
node test/check_frontend_servers.mjs
python test/run_isolated_acceptance.py --allow-test-writes
python test/check_isolated_persistence.py
```

The integration harness verifies the SQL container hostname, uses acceptance ports,
launches seven temporary **local** Python processes, and terminates its children.
It exercises real service HTTP, SQL Server locks, RabbitMQ, templates and persistence.
Only email transport is patched to an in-memory localhost mock sink; OTP is randomly
generated and never printed. Fixtures stay in the acceptance databases.
This is distinct from a fully containerized or browser-driven E2E run.

The additional `--docker` mode runs the same real business checks through the full
Compose stack and temporarily overrides only Notification email transport to a
protected in-memory test inbox. It restores the normal Notification command afterward.
`--docker --browser` adds installed-Chrome UI QA. V5 passed actual login/search/room
selection/checkout/OTP/E-ticket/history through this path. It blocks image/font/media
requests to conserve resources; QR graphics/external image loading are not accepted
by this test. Read the browser JSON result separately from Docker API evidence.

The persistence check restarts only the acceptance SQL/broker containers and compares
all six database row counts and durable queue names. It does not test disaster
recovery or recreate volumes. The frontend check starts standalone production output,
checks 12 routes and static assets, and stops its own Node processes; it does not
exercise browser interactions or authenticated admin operations through the UI.

Older `run-tests.ps1` and legacy integration scripts can connect to developer
databases and some still contain obsolete assumptions. Use the reviewed runners
above. `test_room_price_trust_p12.py` now uses SQLite with only `sp_getapplock` mocked;
real SQL locking is covered separately by the isolated acceptance harness.
