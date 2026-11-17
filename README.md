# System-Booking-service / LuxeStay

Hệ thống đặt phòng khách sạn dùng sáu microservice FastAPI, API Gateway FastAPI/httpx,
hai frontend Next.js, sáu database SQL Server và RabbitMQ.

**V6 — 17/11/2026:** toàn bộ stack chạy trong Docker Compose; 79 unittest,
7 API-client test, 24 nhóm API integration và 8 nhóm lifecycle bổ sung đạt. Đã sửa lỗi
Admin xác nhận booking bị 401; Chrome kiểm tra đạt 9 thao tác quản trị thực tế cùng
luồng tìm phòng, checkout/OTP, E-ticket, ảnh QR và lịch sử booking. Lint còn 10 cảnh báo
tối ưu ảnh, 0 lỗi. Booking 28 và các bản ghi liên quan được giữ nguyên.
Build được kiểm chứng trên host phục hồi snapshot với legacy builder; môi trường
Linux sạch/BuildKit mặc định chưa được chứng nhận. Chi tiết giới hạn và bằng chứng:
[bàn giao V6](docs/AI_V4_HANDOVER.md) và [ma trận chức năng](docs/AS_IS_FUNCTION_MATRIX.md).

| Thành phần | Port mặc định |
|---|---:|
| Hotel / User / Room | 8000 / 8001 / 8002 |
| Booking / Payment / Notification | 8003 / 8004 / 8005 |
| Gateway | 8080 |
| Admin / Customer | 3000 / 3001 |
| SQL Server | 1433 |
| RabbitMQ / Management | 5672 / 15672 |

## Khởi tạo môi trường kiểm thử Docker riêng

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File infrastructure/New-DockerTestEnvironment.ps1
docker compose --env-file .env.acceptance.local -p luxestay-acceptance config --quiet
docker compose --env-file .env.acceptance.local -p luxestay-acceptance up -d sqlserver rabbitmq db-init
# Trên host hiện tại đã phục hồi base snapshot:
powershell -NoProfile -ExecutionPolicy Bypass -File infrastructure/Build-Images.ps1 -LegacyBuilder
docker compose --env-file .env.acceptance.local -p luxestay-acceptance up -d --no-build
```

Script tạo secret ngẫu nhiên trong file được Git bỏ qua, không ghi đè `.env` sẵn có.
Môi trường này dùng port riêng: backend `18000–18005`, Gateway `18080`, Admin `13000`,
Customer `13001`, SQL `11433`, AMQP `15673`, RabbitMQ UI `15674`.
SQL và RabbitMQ dùng named volume theo project. Không chạy `down -v`.

`db-init` chỉ khởi tạo database mới. Database đã tồn tại được giữ nguyên và cần
migration có kiểm soát. Tài khoản demo chỉ được seed khi bật `SEED_DEMO_DATA=1`
cho database User mới; mặc định là `0`. Không dùng tài khoản demo cho triển khai ngoài.

## Kiểm thử

```powershell
python -m pip install -r requirements.txt
python test/run_offline_regressions.py
pnpm.cmd --dir front-end --filter customer-web build
pnpm.cmd --dir front-end --filter admin-dashboard build
pnpm.cmd --dir front-end --filter '@repo/api-client' test
node test/check_frontend_servers.mjs
python test/run_isolated_acceptance.py --allow-test-writes
python test/run_isolated_acceptance.py --allow-test-writes --docker
python test/check_isolated_persistence.py
```

Hai lệnh Python cuối chỉ dùng hạ tầng acceptance đã khởi động. Harness xác minh đúng
SQL container, chạy bảy process Python local tạm thời, giao tiếp HTTP/SQL/RabbitMQ thật,
dùng email mock trong bộ nhớ và dừng các process do nó tạo. Kết quả không thay thế
nghiệm thu toàn bộ container hoặc thao tác UI bằng browser.

Không chạy bộ test integration cũ trực tiếp trên database phát triển. Một số script
cũ dùng database từ `.env` của service; dùng các runner đã cô lập ở trên.

## Tài liệu

- [Kiến trúc hiện tại, luồng nghiệp vụ và giới hạn giao dịch](docs/ACTUAL_ARCHITECTURE.md)
- [Docker runbook, cấu hình, migrations, chạy từng service và demo](docs/DOCKER_RUNBOOK.md)
- [Trạng thái triển khai / checkpoint](docs/AI_IMPLEMENTATION_STATUS.md)
- [Bàn giao, bằng chứng kiểm thử và vấn đề còn lại](docs/AI_FINAL_HANDOVER.md)
- [Bàn giao V4 và bằng chứng Docker hiện tại](docs/AI_V4_HANDOVER.md)

Mỗi backend có `/docs` và `/health`. API nghiệp vụ đi qua Gateway `/api/v1`.
Notification dùng OpenAPI `/api/v1/openapi.json`; Gateway không gộp toàn bộ Swagger.
Gateway không thay thế xác thực/phân quyền trong service và các port backend mặc định
vẫn được publish cho mục đích phát triển.

Không có rubric cuối kỳ chính thức trong yêu cầu; báo cáo không suy diễn điểm số
hay tuyên bố hoàn tất dự án khi chưa đủ bằng chứng nghiệm thu.
