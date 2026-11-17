# AS-IS functional baseline — V5 release verification, 17/11/2026

Scope comes from implemented routers, services, schemas, existing UI and tests.
No feature is inferred from a typical hotel system or an unspecified course rubric.
"Verified" below applies only to the named evidence; it does not certify every input.

| Module / existing function | Implementation / dependencies | Current evidence and limits |
|---|---|---|
| Room type create/read/update/delete | `room_types.py`, `RoomTypeService`, Hotel ownership API | CRUD/service regressions; SQL create/update in expanded acceptance; deletion rejects linked physical rooms |
| Physical room create/read/filter | `rooms.py`, `RoomService`, hotel/type/status filters | SQL creation/list/availability; API ownership regression; duplicate constraint exists per hotel |
| Batch room creation | Explicit list or numeric range, one DB transaction | Expanded SQL acceptance checks conflict atomicity and concurrent counter consistency |
| Room status / removal | Transition matrix; removal marks INACTIVE and retains history | Service regressions and SQL maintenance→occupied rejection; not a destructive delete |
| Availability / capacity | AVAILABLE state + type capacity + authenticated Booking overlap query | Tests date order, capacity, maintenance exclusion, held/booked IDs, malformed/offline dependency; real booking race tested |
| Room inventory counter | `so_luong_phong` counts physical rows including inactive | V4 replaces read-modify-write/recount with atomic increments; real concurrent requests verified |
| Notification email / IN_APP | Templates, email transport, notification/content tables | Mock email integration; offline SMTP transient/permanent errors; no external SMTP delivery |
| Broker consumer | Four existing queues, acknowledgements, retries, reconnect and DLQ | Existing safety/startup tests and real broker integration; no new queue/business event added |
| Cross-transport deduplication | Consumer hashes queue + NUL + raw body; V4 producer forwards same hash in internal REST header | SQL acceptance delivers same event concurrently via REST then RabbitMQ; one record/one mock delivery |
| Notification history/detail/stats | Existing endpoints scope to authenticated account | Read/ownership regressions and real owner history; stats are personal, not a global admin dashboard contract |
| Mark read / delete | Existing owner-scoped endpoints | Existing unit tests plus real read/cross-owner rejection |
| Mark all read / resend failed UI | No matching route or existing frontend call found | Not implemented; not added speculatively. Broker retry of failed delivery already exists and is tested |
| OTP notification history | Payment events previously omitted owner account | V4 propagates validated Booking owner through broker and REST; owner's OTP history now verified |
| User auth/profile/admin | Existing registration/login/refresh/role/profile routes | Wrong/right login, JWT/ownership tests, admin-page browser verification when recorded; not every account lifecycle operation covered |
| Hotel catalog / nested detail CRUD | Existing Hotel routers, own SQL database | Hotel create/search and Room ownership exercised; all nested CRUD combinations not yet exhaustively tested |
| Booking hold/history/confirm/cancel | SQL applock, date overlap, holds, internal confirmation, notifications | Real concurrency, hold expiry, history, confirmation; source preserves existing cancellation workflow |
| Payment sandbox / OTP / idempotency | Validated Booking HTTP dependency, payment/OTP SQL tables | Wrong amount/owner, concurrent retry, wrong/expired/reused OTP, success and offline SYNC_FAILED regressions |
| Gateway | FastAPI/httpx routes, auth/correlation forwarding, health aggregation | Route contract suite and actual cross-service flow; no nginx dependency |
| Customer UI | Search, hotel, checkout, OTP, E-ticket, history | V5 Chrome PASS: UI login, search, real room availability/selection, checkout, OTP, confirmed E-ticket and matching history; images/fonts/media excluded |
| Admin UI | Login, Hotel/Room/Booking/Payment/User/Notification pages | V5 Chrome login and six page navigations PASS; navigation does not certify all CRUD actions |
| Docker deployment | Six backend images + gateway + two frontend images; SQL/broker/db-init | V5 rebuilds under separate image tags, no-cache representative backend/frontend checks and current runtime are reported separately; clean-host BuildKit not certified |

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
