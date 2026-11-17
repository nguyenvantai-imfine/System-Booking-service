# Bàn giao kỹ thuật — 17/11/2026

> Báo cáo này lưu kết quả V3. Kết quả mới nhất, bao gồm Docker đã chạy được và
> blocker Chrome UI, nằm tại [bàn giao V4](AI_V4_HANDOVER.md). Không dùng trạng thái
> Docker BLOCKED trong V3 để thay thế bằng chứng V4 mới hơn.

**Chưa đủ điều kiện nghiệm thu toàn bộ dự án.** Source đã được sửa và kiểm thử có
trọng tâm; luồng nghiệp vụ thực chạy đạt trong môi trường backend local kết hợp
SQL Server/RabbitMQ Docker cô lập. Docker toàn bộ còn blocker trên host; browser E2E
chưa chạy. Không commit/tag/push hoặc phát hành ra ngoài.

## Phiên bản và bảo toàn dữ liệu

- Baseline: branch `main`, HEAD `d842568464aae2f7f94e44b83d726f8563d61f39`.
- Ban đầu có đúng 16 file modified. Bản sao trước chỉnh sửa nằm trong thư mục Git
  bỏ qua `logs/takeover-baseline-20261117/`; không reset hoặc ghi đè mất bản sửa cũ.
- Giữ nguyên root/service `.env`, Windows SQL Server, Windows RabbitMQ, volume SQL
  của project Docker cũ. Không xóa database/volume, không dùng `down -v`.
- Một lần chạy nhầm test cũ `test_room_price_trust_p12.py` đã tạo booking giả trong
  database local hiện hữu `booking_service`: **ID 28, mã `BK-202611-68F1D3`**, user ID 10.
  Người dùng đã chọn **giữ nguyên để rà soát**; booking và bản ghi con được giữ nguyên.
  Không có lệnh xóa nào được thực hiện. Test này đã được sửa sang SQLite hoàn toàn;
  chỉ mock SQL Server applock trong unit test, không dùng fixture database local nữa.
- Các fixture tích hợp còn lại nằm trong project `luxestay-acceptance`, dùng port/
  volume riêng. Chỉ các fixture demo mới do phiên này tạo được sửa hash sau khi phát
  hiện lỗi tạo fixture; không chuyển đổi mật khẩu tài khoản người dùng hiện hữu.

## Thay đổi đã triển khai

| Mức | Lỗi / thay đổi | Bằng chứng |
|---|---|---|
| P0 | Bỏ chấp nhận JWT compatibility key cố định ở sáu service; thiếu key thì từ chối | Auth regressions, foreign-key token tests, Golden Flow |
| P0 | SQL entrypoint sửa file trên read-only mount | Tách `db-init`; SQL/RabbitMQ Docker chạy đạt |
| P0 | User init thiếu hai cột `ngay_cap_nhat` | Additive migration; ORM/schema comparison và login thật |
| P0 | Notification filtered index thiếu SQL SET options | Sửa init / `sqlcmd -I`; Notification chạy và tiêu thụ OTP thật |
| P1 | Payment thiếu header nội bộ khi đọc/xác nhận Booking | Gửi đúng `X-Internal-Service-Secret`; xác nhận booking thực đạt |
| P1 | Payment tiếp tục khi không xác minh được Booking | Từ chối 503; kiểm tra owner/code/amount/status/hold trước tạo |
| P1 | OTP thiếu kiểm tra chủ sở hữu; IPN public | Kiểm tra owner trước generate/verify; IPN sandbox cần admin |
| P1 | Idempotency so tiền qua float, thiếu đối chiếu đầy đủ | So Decimal, kiểm tra booking code/method; retry đồng thời đạt |
| P1 | DDL mở rộng OTP nằm trong request/startup | Bỏ DDL ngầm, thêm explicit widening migration và schema check |
| P1 | Frontend chuyển trang thành công dù Payment `SYNC_FAILED` | Chỉ chuyển khi `SUCCESS`; build production đạt |
| P1 | Sandbox HTML chèn query trực tiếp và báo success khi callback lỗi | Giới hạn mã query an toàn, kiểm tra HTTP/payment status; regression đạt |
| P2 | Dotenv phụ thuộc working directory, có thể trộn database/secret | Service-local path cố định / absolute `ENV_FILE`; tests đạt |
| P2 | Plaintext password fallback, seed account tự động | Bcrypt-only; seed demo riêng, opt-in cho User DB mới |
| P2 | Health có thể che lỗi dependency | Backend DB checks trả 503; Gateway giữ degraded state |
| P2 | Docker thiếu frontend / context chứa dotenv | Multi-stage standalone build, monorepo tracing, `.dockerignore`, Compose hai frontend |

Giữ nguyên sáu backend độc lập, gateway, quyền sở hữu dữ liệu, UI hiện hữu, công thức
giá/VAT. Không viết lại Saga hay bổ sung chức năng ngoài phạm vi ổn định hệ thống.

## Kết quả thực tế

Chi tiết máy đọc được và SHA-256 source/config/test nằm tại
[`validation/2026-11-17-results.json`](validation/2026-11-17-results.json).
Log chi tiết nằm trong `logs/` local, không đưa secret/log thô vào Git.

| Kiểm tra | Kết quả / phạm vi |
|---|---|
| Python compileall | PASS |
| Offline regression | PASS: 13 suite gồm 77 unittest case và một script Gateway contracts |
| API client | PASS: 7 Node test |
| Customer / Admin TypeScript và build production | PASS cả hai |
| Standalone frontend HTTP | PASS: 12 route và static assets |
| Compose config với env acceptance | PASS; root dotenv cũ thiếu internal secret |
| SQL Server / RabbitMQ Docker cô lập | PASS: readiness và database init sau sửa lỗi |
| SQL ORM column comparison | PASS: đủ cột ở sáu database acceptance |
| Golden Flow / API integration | PASS: 19 nhóm kiểm tra, backend local + SQL/RabbitMQ Docker + mock email |
| SQL booking concurrency | PASS: hai request cùng phòng → một 201, một 409 |
| SQL payment concurrency | PASS: hai retry cùng idempotency key → cùng một transaction |
| Persistence qua restart | PASS: số dòng sáu database và tên durable queue giữ nguyên |
| Docker build / chạy đủ chín ứng dụng | BLOCKED trên host, chưa nghiệm thu |
| Browser UI interaction / authenticated admin UI | NOT RUN; HTTP route test không thay thế thao tác browser |
| SMTP thực / payment production | NOT RUN; email mock / thanh toán sandbox |

Golden Flow đã kiểm tra: đúng/sai login; từ chối quyền admin và IPN ẩn danh; tìm khách
sạn và phòng trống thật; booking hold; phòng đã giữ bị từ chối; ownership; sai số tiền;
idempotency tuần tự/đồng thời; OTP qua RabbitMQ thật tới mock sink trong bộ nhớ; hash
SHA-256; OTP sai/đúng/hết hạn/tái sử dụng; notification lưu OTP đã che; xác nhận Payment
và Booking nhất quán; booking history; hold hết hạn; admin payment stats.

Offline tests kiểm tra thêm dependency failure, `SYNC_FAILED` không phát success
event, plaintext rejection, JWT cấu hình thiếu/sai key, startup schema checks,
notification retries/idempotency/dead-letter, CORS và price trust. Những assertion
giá phòng cũ được sửa theo contract an toàn đang có: giá thay đổi trả 409; mất Room
Service trả 503 và không tạo booking, thay vì coi fallback tin giá client là hợp lệ.

Các script integration cũ không nằm trong runner cô lập chưa được coi là PASS trên
source mới. Không chạy lại `run-tests.ps1` trên database hiện hữu để lấy kết quả đẹp.

## Blocker và giới hạn còn lại

1. **Docker host/image runtime:** image Python `python:3.11-slim-bookworm` mới tải về
   báo `exec format error`; image Node `node:24-bookworm-slim` báo `input/output error`
   trước khi chạy code dự án. BuildKit export và isolated builder bootstrap báo EOF.
   Image backend cũ vẫn chạy Python được. Gateway build riêng đã thành công nhưng
   điều đó không chứng minh các image còn lại chạy được. Chưa thay đổi/reset Docker
   storage hoặc xóa cache/volume để khắc phục, nhằm giữ dữ liệu hiện có.
2. **Docker frontend:** Dockerfile và Compose đã có, build production local/standalone
   đạt; chưa chạy được image frontend để nghiệm thu container networking/browser.
3. **Distributed transaction:** SQL locks/idempotency và retry không tạo giao dịch
   phân tán atomic. `SYNC_FAILED` cần kiểm tra và đối soát thủ công; chưa có worker
   tự động được xác minh. Chưa có transactional outbox đảm bảo event sau commit.
4. **Cấu hình local cũ:** dotenv giữa service còn khác nhau. Cần quản lý thống nhất
   JWT/internal secret trước khi dùng launcher local cũ; phiên này không ghi đè env.
5. **Tài khoản legacy plaintext:** bị từ chối; cần reset/migration bcrypt được duyệt.
   Demo account chỉ dùng cho DB test mới. Standalone HTML sandbox không tự mang JWT;
   demo chính dùng Customer checkout; gọi IPN mô phỏng qua API bằng admin token.
6. **Độ phủ nghiệm thu:** chưa browser E2E, chưa toàn bộ CRUD admin qua UI, chưa SMTP
   thật, chưa tích hợp payment production, chưa thử phục hồi sau mất volume. Khẳng định
   không còn lỗ hổng trên toàn source sẽ vượt bằng chứng của lần kiểm tra có trọng tâm.
7. **Rubric:** chưa có rubric cuối kỳ chính thức; không suy diễn yêu cầu/điểm số.

## Bước tiếp theo an toàn

Sửa Docker image runtime trên host hoặc dùng Docker Linux host sạch với cùng source;
giữ nguyên mọi volume cũ. Theo [Docker runbook](DOCKER_RUNBOOK.md), build lần lượt
service, chạy đủ stack, kiểm tra health, lặp Golden Flow qua container, rồi kiểm thử
browser cho checkout/history/admin. Chỉ khi các bước này có bằng chứng mới nghiệm thu
Docker toàn bộ và tiến hành bước review cuối trước commit/tag.

Giữ booking local ID 28 đúng theo quyết định của người dùng. Hạ tầng acceptance còn
chạy với volume test; các process Python/Node tạm do harness tạo đã dừng. Không có
email hay thanh toán thực được gửi ra ngoài.
