# Implementation status — final checkpoint 2026-11-17

## V6 closure checkpoint — supersedes historical results below

- Baseline: clean main and origin/main at `c7b4cca7125717e6211426887e34c1e7d60cbfbc`.
  V5 source and evidence were retained; no teammate changes were overwritten.
- Fixed the reproducible Admin Dashboard booking-confirmation 401: allow Admin JWT
  or authenticated internal service on that existing endpoint; reject Customer/Partner.
- Added isolated User/Hotel/nested-detail/account lifecycle, Booking/Payment, Room
  removal/counter and Notification read/delete/ownership acceptance: 8 groups PASS.
  Chrome now verifies 9 actual Admin mutations plus the customer Golden Flow.
- Room/Notification concurrency, SQL locks, hold expiry, transport dedup and Payment
  event ownership remain passing in the 24-group Docker final regression. Existing
  SMTP/SQL crash-window and Payment SYNC_FAILED limits remain explicit.
- 79 unittest cases across 15 suites (one standalone Gateway script), 7 API-client
  tests, Python compilation, both frontend typechecks/lints and all 9 Docker builds
  pass. Hook/export fixes reduce warnings 17 -> 10, all image optimization, zero errors.
  No disabled checks. Checkout entered values and OTP lifecycle are preserved.
- Chrome E-ticket QR identity and actual external bitmap rendering pass; transmission
  of only a new fixture booking code was explicitly authorized by the user. Other
  external image/font/media loading is excluded; no scanner-device certification.
- Isolated SQL/RabbitMQ restart retains table row counts in all six databases and
  durable queue names. Original booking 28/children and developer data remain untouched.
- Supported recovered-base/legacy-builder deployment is rebuilt and running. Registry
  manifest access/platform metadata pass; default BuildKit fails at its own executable
  on this host. Clean Linux/default BuildKit acceptance remains NOT VERIFIED.
- Existing four handover/runbook/matrix documents are updated. Ignored logs retain
  runtime evidence; the release contains source, reusable tests and documentation only.
  Authorized normal commit/push follows the passing checks; exact remote hash and
  clean-tree result are in the final response and ignored `logs/v6-release-receipt.json`.

Detailed evidence, lint locations and limitations: [current handover](AI_V4_HANDOVER.md).

## Historical V5 release checkpoint

- All V4 source fingerprints matched; modified/untracked files and complete diff
  backed up in ignored `logs/v5-baseline/` and `logs/v5-baseline.patch` before fetch.
  `origin/main` initially matched local main; no conflicts or teammate divergence.
- Docker Desktop was stopped at takeover and restarted. Current full-stack runtime,
  24 Docker API groups, Room/Notification races and dedup, persistence and health
  recovery have been reverified. No existing database/volume or booking 28 was removed.
- 78 unittest cases, 7 API-client tests, both frontend typechecks and lint passed.
  Lint retains 17 warnings, no disabled rules. All nine source images rebuilt under
  separate verification tags. No-cache Room/frontend builds and fresh-image SQL/HTTP
  smoke checks also passed without replacing active deployment containers.
- Chrome UI E2E PASS after test-only fixes: scoped customer login selector and native
  fetch `ok` property. The test now clicks hotel search/availability/room selection,
  verifies Payment SUCCESS / Booking CONFIRMED, confirmed E-ticket and matching history.
  Admin login/six pages pass. Image/font/media requests remain excluded from QA.
- Release gate targets the V5 criteria, not exhaustive feature or production SMTP/
  payment certification. Supported reproducibility is the recovered-base/legacy
  builder host; clean Linux/default BuildKit remains unverified.
- Release files are selected explicitly; working/staged content scanner rejects live
  dotenv values, private keys, tokens and runtime artifacts. Commit and normal push
  to main are authorized by V5 only after checks pass; never force-push or tag.
- Final acceptance evidence: `validation/2026-11-17-v5-results.json`. Post-push commit,
  remote verification and clean-tree receipt: ignored `logs/v5-release-receipt.json`
  and the final response. Historical V3/V4 records below remain unchanged as history.

## Historical V4 checkpoint

## V4 current checkpoint — supersedes historical table below

- Starting source matched every prior validation fingerprint. All 69 initial
  modified/untracked file entries were preserved under ignored `logs/v4-baseline/`.
  HEAD/branch unchanged; no stash/reset/commit/push/tag or data deletion.
- Room: fixed concurrent counter lost updates, verified batch conflict atomicity,
  invalid state transitions and real Booking overlap/concurrency. Docker build/start PASS.
- Notification: fixed cross-transport event identity, concurrent send locking,
  validated owner propagation from Payment and failed-publication connection cleanup.
  Real concurrent REST + RabbitMQ dedup, read/ownership and mock email PASS. Docker PASS.
- Docker root cause: bad unpacked snapshots had zero-byte executables despite valid
  saved layers. Reconstructed snapshots run; original bases retained. BuildKit EOF
  persists, but all nine applications build with the verified legacy builder path.
  Full Compose deployment: eleven running/healthy containers and initializer exit 0.
- Current tests: 14 offline suites / 78 unittest cases plus Gateway script; 7 API
  client tests; both Docker production builds and TypeScript checks; frontend lint
  exit 0 with 13 Customer / 4 Admin warnings; 24 full Docker API check groups PASS.
  Persistence and all-service/frontend health after infrastructure restart PASS.
- UI E2E BLOCKED: Chrome reports ERR_INSUFFICIENT_RESOURCES. Two attempts failed;
  host had ~304,248 KiB physical and 249,952 KiB virtual memory free. Do not claim
  browser checkout/E-ticket/admin CRUD PASS. No external SMTP/payment used.
- Booking 28 / BK-202611-68F1D3 and children remain untouched per user decision.
- All application containers remain running; temporary inbox/browser processes are
  stopped, and Notification is restored to its normal command with mock email.
- Latest function baseline: `AS_IS_FUNCTION_MATRIX.md`; handover: `AI_V4_HANDOVER.md`;
  sanitized evidence/inventory/hashes: `validation/2026-11-17-v4-results.json`.
- Next safe action: free host resources or use a clean Docker/Chrome host; rerun
  `python test/run_isolated_acceptance.py --allow-test-writes --docker --browser`.
  Complete unverified nested Hotel/User/admin CRUD cases from the matrix. Review
  retained SMTP/SQL crash window, SYNC_FAILED reconciliation, and lint warnings before
  final acceptance. Overall project is not declared DONE.

## Historical V3 checkpoint

Baseline: `main`, HEAD `d842568464aae2f7f94e44b83d726f8563d61f39`.
Working tree remains uncommitted. Initial 16 local modifications were backed up
under ignored `logs/takeover-baseline-20261117/`. No commit/tag/push/reset performed.

| Stage | Status | Evidence / remaining work |
|---|---|---|
| Baseline safety / environment | Completed | Git inventory, original files preserved, runtime/volume/port checks |
| Focused source and integration review | Completed within stated scope | `ACTUAL_ARCHITECTURE.md`; no claim of reading 100% of source |
| Corrective implementation | Completed for proven defects | JWT/config/security, SQL/schema, payment contracts, frontend success guard, health checks |
| Full Dockerization source/config | Implemented; runtime Blocked | Six backend Dockerfiles, gateway, two frontend builds, Compose, db-init, volumes/health |
| Offline / local production verification | Completed | 13 suites: 77 unittest cases + Gateway contract script; 7 API-client tests; both production builds; 12 HTTP routes |
| Isolated SQL/RabbitMQ integration | Completed | 19 API workflow groups, real booking/payment concurrency, mock email; persistence after restart |
| Full Docker acceptance | Blocked | New Python/Node images fail before application code; BuildKit EOF. Do not mark PASS |
| Browser Golden Flow / all admin UI CRUD | Not Started | Standalone HTTP test does not prove browser interactions |
| External SMTP / production payment | Not Run, outside local acceptance | Email mock and sandbox only |
| Documentation / handover | Completed | README, Docker runbook, actual architecture, final handover, sanitized JSON evidence |

## Files changed

- Existing configuration/security modules in gateway and six services; monetary
  Booking response serialization preserved from local work.
- Payment service/endpoint/startup logic, read-only health in five backends,
  Gateway aggregated health, User read-only startup and optional demo seeds.
- User/Notification initialization corrections; explicit User/Payment migrations.
- Six backend Docker base tags and secret-excluding Docker contexts; frontend
  Dockerfile/standalone configurations; Compose infrastructure and two frontends.
- Customer checkout success guard; selected legacy JWT test fixtures and price
  regression isolation; new safe offline/integration/persistence/frontend runners.
- Documentation and `docs/validation/2026-11-17-results.json` with code fingerprints.

Full changed-file list is available from `git status --short`; source/config/test
SHA-256 values are in the validation JSON. Root/service dotenv values were not
overwritten; new generated secrets are ignored and never included in reports.

## Data incident and explicit user decision

A legacy price-trust test was mistakenly executed before full fixture isolation.
It committed one synthetic booking to pre-existing local `booking_service`:
ID **28**, code **BK-202611-68F1D3**, user ID 10. The user explicitly chose
**keep unchanged for review**. Booking and child records remain; no cleanup was
attempted. The offending test now uses SQLite and passed all six cases. Other
integration fixtures are confined to the dedicated acceptance databases.

## Current environment / next safe action

Docker Desktop is running. Original project resources remain. Dedicated
`luxestay-acceptance` SQL/RabbitMQ are healthy, initializer exited 0, and test
volumes remain. Temporary local Python/Node application processes have stopped.

Resolve Docker image execution/export on this host or use a clean Linux Docker
host without deleting old volumes. Follow `DOCKER_RUNBOOK.md`, build services
individually, run the entire Compose stack, repeat the real Golden Flow through
containers, then perform browser checkout/history/admin acceptance. Review
remaining distributed-state limits and legacy local env/account migration needs.
Do not commit/tag or declare the project complete before final acceptance.
