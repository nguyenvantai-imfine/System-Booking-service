# V4 handover — 17/11/2026

## V6 functional closure — current result, 17/11/2026

V6 starts from clean local/remote main at
`c7b4cca7125717e6211426887e34c1e7d60cbfbc`. This section supersedes the historical
V5/V4 acceptance gaps below. No reproducible P0/P1 remains in the exercised scope;
the matrix records exactly which operations have evidence.

- **Verified defect fixed:** Dashboard's existing manual confirmation button sent
  an Admin JWT to a service-secret-only Booking endpoint and received 401. That
  endpoint now accepts authenticated ADMIN or internal SERVICE; CUSTOMER/PARTNER
  receive 403. Booking state changes remain in the existing business service.
  Real API, actual Dashboard clicks and an offline authorization regression pass.
- User lifecycle: registration validation/duplicates, login/refresh, profile ownership,
  Admin create/filter/pagination/lock/unlock/delete; locked login/refresh are rejected.
- Hotel lifecycle: owner/Admin updates, foreign Partner rejection, search, primary
  image uniqueness and cross-hotel isolation, amenity create/delete, policy update/
  delete, pause, soft delete and restore. All writes use newly created fixtures.
- Room/Notification: the 24-group Docker regression rechecks batch atomicity,
  counter races, Booking overlap/hold expiry, concurrent REST/broker dedup and owner
  propagation. New coverage verifies linked-type deletion protection, duplicate rooms,
  filtered pagination, INACTIVE removal preserving counters, escaped IN_APP content,
  mark-read/delete and foreign-account isolation. No messaging architecture was added.
- Actual Chrome Admin mutations: account lock/unlock, hotel pause, booking manual
  confirm/cancel, sandbox payment IPN, notification read/delete and room maintenance:
  **9 checks PASS**, with resulting state read through real APIs. Customer Golden
  Flow and six Admin page visits: **10 checks PASS**, including QR URL booking identity.
- External QR bitmap loaded with nonzero browser dimensions after explicit user
  permission to send only the newly created test booking code to `api.qrserver.com`.
  This checks image rendering and URL identity, not a physical QR scanner. Other
  external images/fonts/media remain excluded from the constrained browser runner.
- Final regression: **79 unittest cases / 15 suites** (including the standalone
  Gateway script), **7 API-client tests**, both frontend typechecks/lints, all nine
  source image builds, **24 Docker API groups**, **8 additional functional groups**,
  both Chrome runners and post-restart persistence pass. SQL table row counts across
  six databases and durable queue names survive the isolated infrastructure restart.
- Lint improved from **17 to 10 warnings, zero errors**. Stable fetch callbacks now
  track route inputs; profile prefills preserve entered values; OTP clear callback is
  stable and autofocus timer is cleaned up. Named Next configs remove export warnings.
  The remaining warnings are only image optimization: Customer hotel detail (3), home
  (2), HotelCard (1), QRCode (1); Admin Hotels (2), Users (1). Moving these external
  images to a server image proxy changes loading/caching behavior and is deferred.
  No lint/security/typecheck rules were disabled.
- Docker: all nine images rebuilt and deployed via the supported recovered-base /
  legacy-builder path. Official Python registry manifest access and linux/amd64
  metadata pass; the existing BuildKit builder still fails before application code
  (`buildkitd-entrypoint: Exec format error`). Its failed task-owned container is
  stopped. A clean Linux host/default BuildKit is **NOT VERIFIED**.

Remaining design limits: email uses mock transport, payments use sandbox; external
SMTP acceptance followed by a crash before SQL commit can duplicate a replay.
Concurrent event locking does not provide exactly-once external SMTP. `SYNC_FAILED`
remains an explicit Payment/Booking reconciliation state, covered by existing failure
regressions, without a newly invented reconciliation workflow.

All database writes target isolated acceptance fixtures. Original booking **28 /
BK-202611-68F1D3** and its children, developer databases, dotenv files and volumes are
untouched. No real payment/email, destructive Git operation or release tag is used.

Reproduce with the commands in [runbook](DOCKER_RUNBOOK.md). Current evidence stays
in ignored `logs/`: `offline-regression-results.json`, `docker-acceptance-results.json`,
`v6-functional-results.json`, `v6-admin-browser-results.json`, `v4-browser-results.json`,
`v6-qr-image-results.json`, `persistence-results.json`, and `v6-final-*`/build logs.
Runtime outputs/secrets are excluded from the release. V6's reviewed source, test and
documentation changes are intended for the authorized normal push to `origin/main`;
exact post-push commit/remote/clean-tree verification is recorded in ignored
`logs/v6-release-receipt.json` and the final response. This receipt avoids embedding
a commit's own hash in its contents.

## Historical V5 release verification

V4 historical results below are superseded by the V5 evidence in
`validation/2026-11-17-v5-results.json`. Source fingerprints matched V4 at takeover;
all local files were backed up under ignored `logs/v5-baseline/`. `origin/main`
matched local HEAD after fetch; no teammate changes were overwritten.

- Runtime: the stopped Docker Desktop was restarted; the isolated Compose stack
  recovered. Six backends, Gateway, two frontends, SQL Server and RabbitMQ are healthy.
- Regression: 78 unittest cases / 14 suites plus Gateway contract script, 7 API-client
  cases, both frontend typechecks, Docker API integration, Room/Notification races and
  cross-transport deduplication passed. Post-restart persistence and health passed.
- **UI E2E now PASS:** installed Chrome completed actual login, hotel search, real
  room availability and selection, checkout, OTP, confirmed E-ticket and history.
  The response was verified as Payment SUCCESS and Booking CONFIRMED. Admin login
  and six page navigations also passed. No business API response was fabricated.
- Browser test defects uncovered after the old resource blocker cleared: ambiguous
  submit-button selector and calling native fetch's `ok` property as a function.
  Only the test was corrected. Search/room selection and matching history assertions
  were added; production application behavior was not changed for the test.
- Build verification: all nine images rebuild from source under separate
  `luxestay-release-verify-*` tags using the supported recovered-base/legacy-builder
  path. Representative Room and Customer frontend no-cache builds passed; the fresh
  Room image connected to acceptance SQL and the fresh frontend served HTTP 200 in
  a disposable container. A clean Linux host and default BuildKit are not certified.
- Release content scan checks configured secrets, environment/runtime artifacts,
  private-key/token patterns and JWT compatibility fallbacks without printing values.
  Staging is selective; logs, dotenv credentials, browser binaries and image archives
  are excluded. Git commit/push receipt is written to ignored `logs/v5-release-receipt.json`
  after remote verification; the final response identifies the exact remote commit.

Remaining limits: image/font/media loading (including external QR graphics) was
blocked during constrained-browser QA; administrative CRUD is not exhaustively
tested; SMTP is mock and payment is sandbox; SMTP/SQL crash-window atomicity and
SYNC_FAILED reconciliation remain the documented design limits. Lint still reports
17 existing warnings and zero errors, with no disabled rules. Booking 28 and child
records remain unchanged. No release tag is authorized or created.

V5 targets the specified release gate; it does not claim every possible feature/input
combination or production payment/SMTP operation is accepted.

## Historical V4 report

**Full Docker deployment runs successfully through the documented recovery / legacy
builder path. Overall final acceptance is incomplete: Chrome UI E2E is BLOCKED by
host resource exhaustion, and not every administrative/nested CRUD combination has
exhaustive functional coverage. No commit/push/tag was made.**

## Reconciled starting point

HEAD remains `d842568464aae2f7f94e44b83d726f8563d61f39`, branch `main`.
Every source fingerprint in the prior validation report matched at V4 start.
The initial inventory was 42 modified tracked files plus 27 untracked file entries,
not an assumed count of 41. Those 69 files were preserved under ignored
`logs/v4-baseline/` before edits. The full current diff is saved locally at
`logs/v4-working-diff.patch`. Existing dotenv files, database rows, volumes and
original Docker resources were not deleted/reset. Booking **28 / BK-202611-68F1D3**
and its children remain untouched, as expressly instructed.

## Proven defects fixed in V4

| Defect / root cause | Corrective implementation | Evidence |
|---|---|---|
| Room count read-modify-write loses concurrent updates | Atomic SQL increments for single and batch creation; same transaction as inserts | Two concurrent SQL API requests and batch conflict produce correct count |
| REST fallback lacks consumer event identity | Booking/Payment/OTP publishers forward SHA-256(queue + NUL + wire body) via validated internal header | Producer identity unittest; real concurrent REST + broker event yields one record/email mock |
| Concurrent notification requests can both send a PENDING event | SQL update/range locks through event-key delivery/status commit | Concurrent REST/broker SQL acceptance |
| Payment OTP/success events omit booking account | Propagate account ID from validated Booking response to both transports | Customer sees its own OTP history; foreign account read is rejected |
| Broker publication can leak open connections on failure | Confirmation/mandatory delivery and safe connection cleanup before REST fallback | Offline publisher/contract suites and Docker Golden Flow |
| Docker base snapshot executable is zero bytes | Reconstruct the original saved image layers into a new snapshot; preserve original image tags | Saved layer Python executable 14,480 bytes vs exported bad snapshot 0; recovered Python/Node execute |
| BuildKit still aborts with EOF after snapshot recovery | Use sequential legacy builder against the same unchanged Dockerfiles | All nine application image builds exit 0; full Compose startup and health pass |

Production files changed specifically in V4:

- `services/room-service/src/services/room_service.py`.
- `services/notification-service/src/api/v1/endpoints/notifications.py`.
- `services/notification-service/src/services/notification_service.py`.
- `services/booking-service/src/core/publisher.py`.
- `services/payment-service/src/core/publisher.py`.
- `services/payment-service/src/services/payment_service.py`.
- `services/payment-service/src/api/v1/endpoints/payments.py`.

Infrastructure/test additions: `infrastructure/recover_image_snapshot.py`,
`infrastructure/Build-Images.ps1`, `test/test_notification_transport_identity.py`,
`test/check_browser_flow.cjs`; expanded `test/run_isolated_acceptance.py` and offline
runner. Documentation adds the AS-IS matrix and V4 report/evidence, and updates the
README, runbook, checkpoint and handover pointers. Exact current source hashes and
changed-file inventory are in `validation/2026-11-17-v4-results.json`.

## Room / Notification completion

See [function matrix](AS_IS_FUNCTION_MATRIX.md) for per-function evidence and limits.
Room preserves hotel ownership, room uniqueness, capacity/date checks, fail-closed
Booking lookup, allowed state transitions, historical inactive rows and type deletion
protection. SQL tests cover batch atomicity, counter races, overlap/hold exclusion and
concurrent bookings. Room's Docker image builds and service is healthy.

Notification preserves existing recipient/ownership checks, HTML escaping, OTP masking,
email mock vs SMTP distinction, retries/reconnect/DLQ, personal history and read action.
Broker/REST now share event identity and SQL locking; Payment notifications now carry
the correct owner. Its image builds and real broker consumption works in Docker.
No mark-all-read or manual resend endpoint/UI implementation was found; these were
not added as speculative features. Existing broker retry of failures remains tested.

SQL and SMTP cannot be committed atomically. A crash after SMTP acceptance but before
SQL commit can still duplicate an email on replay. This is an explicitly retained
distributed-system limitation, not an exactly-once guarantee. No external SMTP server
or production payment gateway was used.

## Final executed checks

| Check | Result |
|---|---|
| Python compileall | PASS |
| Offline runner | PASS: 14 suites, 78 unittest cases plus Gateway contract script |
| API-client Node tests | PASS: 7 |
| Customer/Admin Docker production build + TypeScript | PASS both |
| Customer/Admin lint | PASS exit 0: 0 errors; 13 / 4 warnings |
| Six backend + Gateway + two frontend image builds | PASS using recovered base snapshots and legacy builder |
| Full Compose deployment | PASS: 11 long-running containers healthy; db-init exits 0 |
| Golden Flow through Docker | PASS: 24 check groups, email transport mock only |
| Infrastructure restart/persistence | PASS: six DB row counts/durable queue names retained |
| Health/frontend HTTP after restart | PASS: six services UP; both frontend roots return 200 |
| Chrome browser E2E | BLOCKED: `net::ERR_INSUFFICIENT_RESOURCES` |
| Full browser admin CRUD / every nested Hotel/User operation | NOT fully verified |

Golden API flow is real HTTP/SQL/RabbitMQ through the container Gateway: login,
hotel search, availability, hold, amount/owner validation, payment idempotency,
OTP generation/hash/verification/expiry/reuse rejection, Booking confirmation,
notification, history, Room and Payment races, expired holds, Room CRUD/status/batch,
notification history/read/owner isolation and cross-transport deduplication.

Two Chrome attempts failed with resource exhaustion. One reached admin navigation
before failing at Customer; the reduced-resource retry failed at initial navigation.
Host diagnostics showed only **304,248 KiB free physical memory and 249,952 KiB free
virtual memory**. No product API was mocked to manufacture browser success. Test
browser image/font/media requests were blocked in the reduced-resource attempt;
QR image loading therefore has no browser acceptance evidence.

Lint warnings are existing hook dependency, anonymous export and `<img>` optimization
warnings. No rules were disabled. Hook warnings require deliberate callback/effect
review; adding every changing function to dependency arrays blindly can cause loops
or overwrite partially entered forms. They remain warnings, not claimed fixed.

## Run / demo

Existing acceptance config is reused without overwriting it. On this recovered host:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File infrastructure/Build-Images.ps1 -LegacyBuilder
docker compose --env-file .env.acceptance.local -p luxestay-acceptance up -d --no-build
python test/run_isolated_acceptance.py --allow-test-writes --docker
```

Admin: `http://localhost:13000`; Customer: `http://localhost:13001`;
Gateway/docs: `http://localhost:18080/docs`. Individual backend docs use
`18000`–`18005` with `/docs`; Notification schema is `/api/v1/openapi.json`.
See [runbook](DOCKER_RUNBOOK.md) for configuration and database migration details.
Keep demo accounts confined to this acceptance environment.

For browser QA after freeing host resources, install only the ignored test dependency:

```powershell
npm install --prefix logs/v4-browser playwright --no-audit --no-fund
python test/run_isolated_acceptance.py --allow-test-writes --docker --browser
```

The harness temporarily patches only email transport inside Notification to its
in-memory test inbox, then restores the normal container command. Production/mock
mode does not expose OTP through the application's API. The normal full stack stays
running; the test inbox and Chrome are stopped after each run.

## Remaining acceptance work

Free host resources or use a clean Docker/Chrome host, rerun browser checkout/OTP,
E-ticket/history and authenticated admin CRUD. Test external QR/image transport
separately if it is needed for the demo. Review uncovered account/Hotel lifecycle
operations against the matrix before claiming every existing feature accepted.
Default BuildKit EOF remains a host/tooling issue; the documented legacy build path
works, and clean hosts should use official base pulls and their normal builder.
Review the full diff and these limits before any commit. No final rubric was supplied.
