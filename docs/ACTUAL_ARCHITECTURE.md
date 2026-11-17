# Actual architecture — 2026-11-17

Focused review of gateway routing, six application entrypoints, configuration/security,
ORM/init schema compatibility, booking/payment/notification paths, frontend API callers,
Docker build contexts and existing tests. This is not a claim of reviewing every line.

| Component | Responsibility / persistence | Business dependencies |
|---|---|---|
| Gateway | FastAPI/httpx HTTP proxy; correlation IDs; aggregate health | Six backend HTTP APIs |
| User | Register/login/refresh, bcrypt, roles and profiles; User SQL DB | SQL Server |
| Hotel | Hotel catalog, ownership and related details; Hotel SQL DB | Shared JWT verification; SQL |
| Room | Room types, physical rooms, authoritative prices and availability; Room SQL DB | Hotel ownership HTTP; Booking overlap HTTP with internal authentication |
| Booking | Holds, availability, overlap prevention, confirmation/history; Booking SQL DB | Room authoritative price HTTP; Hotel detail HTTP; notification publisher / REST fallback |
| Payment | Sandbox transaction, amount validation, idempotency, hashed OTP; Payment SQL DB | Authenticated Booking read/confirm HTTP; RabbitMQ / Notification REST fallback |
| Notification | Durable queue consumer, idempotent notification records, email templates; Notification SQL DB | RabbitMQ; mock email by default / optional SMTP |
| Customer | Next.js customer search, checkout/OTP, success/history | Shared TypeScript API client → Gateway |
| Admin | Next.js administrative pages | Same API client → Gateway |

Six independently built backend processes own six databases on one SQL Server instance.
The gateway and two frontends remain separate applications. No monolithic replacement
or external service publication was performed.

## Contracts and Golden Flow

1. `/api/v1/auth/login` accepts `ten_dang_nhap_hoac_email` and `mat_khau`; User signs JWT.
2. `/api/v1/hotels` searches Hotel; `/rooms/available` combines Room inventory with Booking overlap.
3. `POST /api/v1/bookings` verifies authoritative room price, computes existing price/tax rules
   using Decimal, obtains transaction-owned SQL Server `sp_getapplock` locks in room order,
   and writes a `PENDING_PAYMENT` booking with a 15-minute hold.
4. `POST /payments/create-payment` validates booking owner, code, amount, status and hold;
   SQL unique filtered index protects the idempotency key. Retry reuses the transaction.
5. `POST /payments/generate-otp` checks ownership, stores SHA-256 (64 hex characters), then
   publishes `notification.otp.generated`. Notification renders email and redacts persisted OTP.
6. `POST /payments/verify-otp` checks ownership and locks payment/OTP rows, validates expiry,
   attempt count and one-time use, then calls Booking's confirmation endpoint.
7. Booking confirm requires `X-Internal-Service-Secret`; a successful call changes booking to
   `CONFIRMED`. Payment becomes `SUCCESS`; confirmation/payment notifications are published.
8. Customer reads `/bookings/{id-or-code}` and `/bookings` for ticket/history rendering.

The gateway routes `/auth`, `/users`, `/admin` to User; `/hotels` to Hotel except hotel room/type
routes; `/rooms`, `/room-types` and hotel room/type routes to Room; remaining booking/payment/
notification prefixes to their respective services. Route precedence is covered by regression.

Booking/Room internal APIs use `X-Internal-Service-Secret`. Notification internal send uses
`X-Internal-Secret` and its existing trusted-network validation. These headers are distinct
contracts even though their configured secret is shared. JWT verification accepts only the
configured key; it no longer tries a fixed compatibility key.

## Distributed state limits

Booking locks and payment idempotency are local SQL transaction guarantees. HTTP retries
are not an atomic distributed transaction. A valid OTP whose confirmation cannot be synced
produces `SYNC_FAILED`, consumes the OTP, and emits no success event. There is no verified
automatic reconciliation worker. Operators must inspect both databases and reconcile before
retrying; never change a financial state blindly. Checkout now refuses to show a success page
when the returned payment status is not `SUCCESS`.

There is no transactional outbox guaranteeing event delivery after a database commit.
Notification failures do not roll back a confirmed booking. Consumer idempotency, retries
and dead-letter handling exist and have offline regression coverage. SMTP transport and
production payment gateways were not tested; payment remains a sandbox.

Money remains Decimal in backend calculations and SQL numeric columns. Booking JSON uses
numbers for the existing frontend contract. JavaScript number precision remains a limitation
for unusually large monetary values; no price or tax formula was changed.

No official final-course rubric was supplied. No grading percentage or course-specific
completion claim is inferred from these technical results.
