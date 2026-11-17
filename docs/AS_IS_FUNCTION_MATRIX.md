# AS-IS functional baseline — V6 functional closure, 17/11/2026

Scope comes from implemented routers, services, schemas, existing UI and tests.
No feature is inferred from a typical hotel system or an unspecified course rubric.
"Verified" below applies only to the named evidence; it does not certify every input.

| Module / existing function | Implementation / dependencies | Current evidence and limits |
|---|---|---|
| Room type create/read/update/delete | `room_types.py`, `RoomTypeService`, Hotel ownership API | PASS: service regressions plus SQL create/update; V6 linked-room deletion returns 409 |
| Physical room create/read/filter | `rooms.py`, `RoomService`, hotel/type/status filters | PASS: SQL creation/list/availability, ownership, V6 duplicate 409 and filtered pagination |
| Batch room creation | Explicit list or numeric range, one DB transaction | Expanded SQL acceptance checks conflict atomicity and concurrent counter consistency |
| Room status / removal | Transition matrix; removal marks INACTIVE and retains history | PASS: transition regressions, SQL maintenance→occupied rejection, V6 UI maintenance and API removal retaining inventory counter/history |
| Availability / capacity | AVAILABLE state + type capacity + authenticated Booking overlap query | Tests date order, capacity, maintenance exclusion, held/booked IDs, malformed/offline dependency; real booking race tested |
| Room inventory counter | `so_luong_phong` counts physical rows including inactive | V4 replaces read-modify-write/recount with atomic increments; real concurrent requests verified |
| Notification email / IN_APP | Templates, email transport, notification/content tables | Mock email integration; offline SMTP transient/permanent errors; no external SMTP delivery |
| Broker consumer | Four existing queues, acknowledgements, retries, reconnect and DLQ | Existing safety/startup tests and real broker integration; no new queue/business event added |
| Cross-transport deduplication | Consumer hashes queue + NUL + raw body; V4 producer forwards same hash in internal REST header | SQL acceptance delivers same event concurrently via REST then RabbitMQ; one record/one mock delivery |
| Notification history/detail/stats | Existing endpoints scope to authenticated account | Read/ownership regressions and real owner history; stats are personal, not a global admin dashboard contract |
| Mark read / delete | Existing owner-scoped endpoints | PASS: unit tests, V6 actual Admin UI read/delete, API escaping/foreign 404 and deleted-detail 404 |
| Mark all read / resend failed UI | No matching route or existing frontend call found | Not implemented; not added speculatively. Broker retry of failed delivery already exists and is tested |
| OTP notification history | Payment events previously omitted owner account | V4 propagates validated Booking owner through broker and REST; owner's OTP history now verified |
| User auth/profile/admin | Existing registration/login/refresh/role/profile routes | PASS: validation/duplicate register, refresh, profile persistence/foreign 403; Admin create/filter/page_size, lock/unlock/login/refresh rejection/delete; actual UI lock/unlock |
| Hotel catalog / nested detail CRUD | Existing Hotel routers, own SQL database | PASS: owner/Admin create/read/update/search, foreign Partner 403, image add/delete/unique primary/cross-hotel 404, amenity create/delete, policy create/update/delete, pause/soft-delete/restore; actual UI search/pause. Not every nested input combination |
| Booking hold/history/confirm/cancel | SQL applock, date overlap, holds, Admin/internal confirmation, notifications | PASS: real concurrency/expiry/history; V6 fixes Admin JWT confirm 401, checks Customer/Partner 403 and actual UI confirm/cancel with persisted state |
| Payment sandbox / OTP / idempotency | Validated Booking HTTP dependency, payment/OTP SQL tables | PASS: wrong amount/owner, concurrent retry, wrong/expired/reused OTP, success/SYNC_FAILED regressions; V6 actual Admin UI sandbox IPN confirms Booking, Customer IPN 403 and filtered list |
| Gateway | FastAPI/httpx routes, auth/correlation forwarding, health aggregation | Route contract suite and actual cross-service flow; no nginx dependency |
| Customer UI | Search, hotel, checkout, OTP, E-ticket, history | PASS: V6 Chrome Golden Flow after hook fixes; QR URL matches confirmed Booking and authorized external QR bitmap loads. Other external images/fonts/media excluded; physical scanner NOT RUN |
| Admin UI | Login, Hotel/Room/Booking/Payment/User/Notification pages | PASS: login/6 pages plus 9 persisted UI mutations: account lock/unlock, hotel pause, booking confirm/cancel, payment IPN, notice read/delete, room maintenance. Remaining form combinations are API-tested where named, not exhaustively clicked |
| Docker deployment | Six backend images + gateway + two frontend images; SQL/broker/db-init | PASS on supported host: V6 all 9 source builds/deployment, 24 API groups, persistence; V5 no-cache representative builds remain historical evidence. Clean Linux/default BuildKit NOT VERIFIED; host builder executable fails |

V6 adds `test/run_functional_closure.py` and `test/check_admin_actions.cjs` to the
existing regression runners. PASS describes the assertions above, not all possible
inputs or production SMTP/payment. See [handover](AI_V4_HANDOVER.md) for evidence,
remaining image warnings, distributed consistency limits and Git release receipt.

## Defects traced in V4

1. **Room counter lost update:** multiple requests can load the same ORM counter;
   assigning `count+1` or replacing it with a concurrent snapshot recount loses updates.
   Atomic SQL increments preserve the existing count semantics and roll back with inserts.
2. **Notification broker/REST duplicates:** consumer had an event key but fallback did
   not pass it, so an ambiguous broker acknowledgement could cause a second email.
   Producers now forward the exact wire-event identity to authenticated internal REST.
   Event-key rows use SQL UPDLOCK/HOLDLOCK and retain locks through email/status commit.
3. **Payment notification ownership missing:** OTP/payment producer omitted the already
   validated Booking account ID, making personal notification history omit those events.
   Owner ID is propagated without trusting a client-supplied owner.
4. **Docker snapshot corruption:** exported container Python executable was zero bytes,
   while the saved layer held a 14,480-byte executable. Reconstructing saved layers
   yielded executable Python/Node snapshots. Original image tags were preserved under
   `luxestay-v4-original-*`; no volume/cache reset was performed. BuildKit still failed
   with EOF, while the legacy builder successfully built the same Dockerfiles.

SQL and SMTP are not an atomic transaction. A process crash after external SMTP
acceptance but before SQL commit can still produce a duplicate on replay; no claim
of exactly-once external email delivery is made. In-flight row locking addresses
concurrent handling, not this crash window. Permanent transport failures and operator
reconciliation remain distinct from automatic retry.
