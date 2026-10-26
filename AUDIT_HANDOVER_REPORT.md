# Báo cáo tổng kiểm tra & bàn giao kỹ thuật

**Dự án:** `System-Booking-service`
**Ngày kiểm tra:** 25-10-2026
**Phạm vi:** 302 file được Git theo dõi: 6 backend services, FastAPI Gateway, 2 Next.js apps và packages dùng chung, 6 bộ SQL init, Docker Compose, scripts PowerShell, docs/DFD/ERD và 6 file test Python. `node_modules` không được tính là mã dự án. `contracts/` và `orchestration/` chỉ có `.gitkeep`.

## Giới hạn bằng chứng

- Đây là audit dựa trên mã nguồn/configuration trong workspace, không phải xác nhận production hoặc kiểm thử vận hành toàn hệ thống.
- Không thể khẳng định request đã thực sự nhận `200 OK`/`201 Created` từ SQL Server trong lần audit này: không khởi chạy hệ thống hoặc thay đổi dữ liệu. Các test Python kiểm tra những mã trạng thái dự kiến nhưng chưa thực thi.
- `pnpm check-types` chạy tại `front-end/`: **5/5 tác vụ thành công**. Python test collection bị chặn vì interpreter hiện tại không có module `pytest`; không cài thêm dependency trong một lượt audit.
- `.env` tồn tại ở máy audit nhưng bị Git ignore; không đọc/ghi nội dung. Với máy clone mới, cấu hình khởi chạy vẫn phải được đánh giá theo file template và cơ chế nạp cấu hình trong code.
- Ký hiệu 🟢 dưới đây đòi hỏi có bằng chứng runtime end-to-end. Vì chưa chạy hệ thống cùng SQL Server/RabbitMQ, **không gán 🟢 cho bất kỳ luồng nào**. 🟡 nghĩa là có đường code triển khai nhưng còn thiếu kiểm chứng hoặc có giới hạn; 🔴 là có lỗi/tác động nghiêm trọng đã thấy trong code; ⚪ là chưa có triển khai chức năng.

---

## I. 🏗️ Tổng quan kiến trúc và luồng thực tế

### Kiến trúc trong mã

| Thành phần | Cổng theo cấu hình | Vai trò và dữ liệu |
|---|---:|---|
| Customer Web | 3001 local | Next.js; tìm khách sạn, xem phòng, checkout, OTP, trang vé |
| Admin Dashboard | 3000 local | Next.js; quản trị users/hotels/rooms/bookings/payments |
| FastAPI Gateway | 8080 | Proxy động `/api/v1/**`, thêm/forward correlation ID và chuyển tiếp request/response |
| Hotel Service | 8000 | Khách sạn, ảnh, tiện nghi, chính sách; SQL Server `hotel_service` |
| User Service | 8001 | Đăng ký/đăng nhập, JWT, hồ sơ, admin users; SQL Server `user_service` |
| Room Service | 8002 | Loại phòng, phòng vật lý, phòng khả dụng; SQL Server `room_service` |
| Booking Service | 8003 | Tạo/hủy/xác nhận booking, giữ chỗ 15 phút, chống xung đột; SQL Server `booking_service` |
| Payment Service | 8004 | Giao dịch, OTP, IPN sandbox; SQL Server `payment_service` |
| Notification Service | 8005 | Ghi thông báo, template, RabbitMQ consumer, SMTP/mock; SQL Server `notification_service` |
| Hạ tầng | SQL 1433, RabbitMQ 5672/15672 | `docker-compose.yml` khai báo SQL Server và RabbitMQ cùng 6 service + Gateway. Compose **không khai báo hai frontend**. |

Mã nguồn Gateway FastAPI định tuyến các tiền tố `/auth`, `/users`, `/profiles`, `/admin`, `/hotels`, `/rooms`, `/bookings`, `/payments`, `/notifications` tới service tương ứng và chuyển tiếp headers, gồm Authorization (`gateway/src/main.py`, `resolve_target_url`, `proxy_api_v1`, dòng 81–169). `gateway/Dockerfile` chạy ứng dụng FastAPI; `gateway/nginx.conf` là cấu hình Nginx riêng và **không được Dockerfile này sử dụng**.

### Luồng kết nối có trong code

1. **Luồng mặc định của frontend không đi qua Gateway.** `front-end/apps/customer-web/src/lib/api.ts` và `front-end/apps/admin-dashboard/src/lib/api.ts` khai báo URL mặc định trực tiếp tới cổng 8000–8005. `front-end/packages/api-client/src/index.ts` giữ các URL theo service và `gatewayUrl`, nhưng các hàm service dùng URL riêng; `gatewayUrl` chỉ được gán, không được dùng để tạo request (dòng 83–100, 320 trở đi). Vì vậy đường phổ biến trong cấu hình hiện tại là:

   `Browser → service URL trực tiếp (8000–8005) → service → SQL Server`

   Gateway chỉ nằm trên luồng khi client hoặc người gọi bên ngoài chủ động gửi tới cổng 8080. README mô tả Gateway là entry point mặc định, nhưng không khớp với URL mặc định của API client.

2. **Gateway → service:** `/api/v1/auth|users|admin → User`; `/hotels → Hotel`; `/rooms → Room`; `/bookings → Booking`; `/payments → Payment`; `/notifications → Notification`. Trong Compose, các service URL nội bộ dùng service DNS trên network Docker; SQL config được truyền bằng environment variables.

3. **Service → SQL Server:** mỗi service có database riêng và SQLAlchemy model/session. Các SQL init scripts tạo database/table. Không có bằng chứng về transaction liên database; các quan hệ giữa service chủ yếu là ID/HTTP.

4. **Booking/Payment → Notification:** Booking xác nhận/hủy và Payment tạo OTP/xác nhận thanh toán có publish event qua RabbitMQ; Notification consumer đăng ký các queue `notification.*`. Email mặc định là simulation/mock, không chứng minh email thật đã được gửi.

### Các giới hạn kiến trúc cần bàn giao

- Frontend đang mặc định gọi microservice trực tiếp, khác tuyên bố Gateway là cổng duy nhất.
- `gateway/nginx.conf` không nằm trong đường chạy Docker hiện tại.
- Docker Compose không chạy Customer Web/Admin Dashboard.
- CORS ở Gateway và nhiều service cho phép origin `*`; cần giới hạn theo môi trường trước khi public.
- `contracts/` chưa có contract/API schema được quản lý; hiện chỉ có `.gitkeep`.

---

## II. 📊 Bảng ma trận đánh giá chức năng

| Phân hệ (Service/App) | Chức năng / Endpoint | UI (Frontend) | API Gateway | Logic Backend | CSDL SQL Server | Trạng thái kỹ thuật |
|---|---|---|---|---|---|---|
| Customer Web / Hotel | Trang chủ, tìm kiếm khách sạn | Có gọi `getHotels`, nhưng trả danh sách giả khi API lỗi/rỗng; destination và ảnh tĩnh | Không dùng theo URL mặc định | Hotel search có query/filter | Có `hotel_service` | 🔴 Hiển thị có thể là dữ liệu giả, không phản ánh DB |
| Customer Web / Hotel | Chi tiết khách sạn, loại phòng, phòng trống | Có gọi Hotel/Room API; fallback hotel/type và `room_id=21` | Không dùng mặc định | Hotel detail và availability có code | Có `hotel_service`, `room_service` | 🔴 Fallback có thể dẫn checkout bằng ID phòng/giá không có thật |
| Customer Web / Auth | Register/Login/Refresh | Có form, lưu token trong localStorage, gọi User Service | Có route nhưng app mặc định gọi cổng 8001 | JWT + DB user; mật khẩu plain text | Có `user_service`; ORM lệch DDL | 🔴 Không đạt yêu cầu bảo vệ credential/schema hiện tại |
| Customer Web / Booking | Tạo booking và trang thành công | Gọi booking, payment, OTP; trang vé hiển thị fallback cố định nếu lỗi | Không dùng mặc định | Booking lưu DB, giữ 15 phút, kiểm tra giao thoa | Có `booking_service` | 🔴 Sai công thức giá; endpoint tin dữ liệu client và không bắt buộc xác thực |
| Admin / Users | Danh sách, tạo, khóa, xóa tài khoản | Có các thao tác API | Không dùng mặc định | User Service có `require_admin` | `user_service` | 🔴 DDL thiếu cột ORM; ngoài ra lưu password plain text |
| Admin / Hotels | CRUD, đổi trạng thái, xóa/restore | Có thao tác API CRUD và lọc | Không dùng mặc định | Hotel Service dùng SQLAlchemy và partner/admin dependency | `hotel_service` | 🟡 Code path DB có; JWT demo fallback cần gỡ và chưa kiểm thử runtime |
| Admin / Rooms | Quản lý loại phòng/phòng, batch, status | Có gọi Room API | Không dùng mặc định | Có tạo/xóa/cập nhật/phòng khả dụng; startup seed 2 loại/10 phòng giả nếu DB trống | `room_service` | 🟡 Có code DB; seed mẫu và fallback token số cần loại bỏ |
| Admin / Bookings | Danh sách, xác nhận, hủy | Có gọi Booking API | Không dùng mặc định | Có state transition và event notification | `booking_service` | 🔴 Các API quản trị booking không yêu cầu quyền; list/detail/cancel/confirm mở |
| Customer/Admin / Payments | Khởi tạo payment, OTP, sandbox IPN, stats/list | Checkout/Admin gọi API; Admin có nút simulate IPN | Không dùng mặc định | Idempotency/OTP có code; startup chèn payment SUCCESS mẫu nếu DB trống; không có gateway thanh toán thật | `payment_service` | 🔴 Sandbox-only; API không yêu cầu auth; amount do client cung cấp |
| Payment / Refund | Hoàn tiền | Không có màn hình được xác nhận | Không có route refund | Có model `HoanTienModel`, nhưng không thấy nghiệp vụ/endpoint hoàn tiền | Có bảng/model hoàn tiền | 🟡 Có schema, chưa có thao tác hoàn tiền |
| Admin / Dashboard | Thống kê, biểu đồ | API cho dữ liệu tổng, nhưng một số chỉ số/chuỗi biểu đồ được tự dựng | Không dùng mặc định | Payment stats lấy từ API, một số số liệu suy diễn | Dữ liệu gốc có | 🔴 Không dùng để đối soát doanh thu theo ngày/khách sạn |
| Notification | Gửi/lưu/list/stats/preview và RabbitMQ | Có API client, không thấy trang UI notification đang dùng các method này | Có route | Template + DB + consumer; email mock mặc định | Có `notification_service` | 🟡 Lưu trữ/event có code; gửi email thật/SMS chưa có |
| Hotel Reviews | Gửi và lưu đánh giá | Chưa có UI chức năng | Không có route | Không tìm thấy model/service/router đánh giá | Không có bảng trong init SQL tương ứng | ⚪ DFD khách sạn có chức năng đánh giá nhưng chưa có code |
| Notification SMS | Gửi SMS | Chưa có UI được xác nhận | Chưa có luồng provider | Chỉ gửi qua SMTP/email; chưa thấy SMS client/provider | Có log notification tổng quát | ⚪ Có trong DFD/tài liệu, chưa có triển khai SMS |
| Gateway | Proxy/health/correlation ID | Không được app dùng mặc định | Có FastAPI proxy; có config Nginx không được dùng | Chuyển tiếp HTTP tới 6 service | Không truy cập DB trực tiếp | 🟡 Có code; chưa phải đường mặc định của frontend |
| Infrastructure | SQL init, RabbitMQ, Compose | Không áp dụng | Gateway container có | Container cho 6 service | Init 6 database | 🟡 Backend stack được khai báo; frontend không nằm trong Compose |

---

## III. 🔍 Phân tích chi tiết theo trạng thái

### 1. 🟢 Tính năng hoàn thiện end-to-end

**Không có luồng nào được xác nhận 🟢 trong lần audit này.** Đây không đồng nghĩa không có triển khai: các service có endpoint, service logic, ORM và SQL init; tests cũng có assertions mong đợi các response. Nhưng chưa chạy các tests/system với SQL Server và RabbitMQ nên không thể kết luận đã đi từ nút UI tới DB và trả đúng `200/201`.

Code-level paths có thể bàn giao để tiếp tục kiểm thử:

- User: `/api/v1/auth/register`, `/login`, `/refresh` → `AuthService` → SQLAlchemy user/profile models (`services/user-service/src/api/v1/endpoints/auth.py`, `AuthService.register/login/refresh`).
- Hotel/Room: search/detail/CRUD và room availability → SQLAlchemy service/repository → database riêng.
- Booking: `create_booking` ghi booking/details/guest/history trong transaction và tạo hold 15 phút.
- Payment: tạo payment, idempotency, OTP; Payment Service gọi Booking Service sau verify.
- Notification: event queue → consumer → ghi log/template trong DB.

Đây là **các luồng có code**, không phải kết quả runtime đã chứng minh. `test/test_booking_concurrency.py`, `test/test_payment_idempotency.py`, `test/test_payment_otp.py`, `test/test_notification_otp.py`, `test/test_gateway_flow.py`, `test/test_correlation_tracing.py` có kiểm tra status/assertion; test suite chưa được chạy.

### 2. 🟡 Dở dang / nối thiếu / dữ liệu giả

#### Frontend fallback che lỗi backend hoặc dữ liệu DB rỗng

- Customer homepage `HomePage` gọi `apiClient.getHotels`, nhưng khi DB rỗng hoặc request lỗi tự đặt danh sách khách sạn mẫu: `front-end/apps/customer-web/src/app/page.tsx`, `HomePage`, dòng 26–86. Danh sách điểm đến/số lượng khách sạn và ảnh cũng hardcode trong component này, dòng 92 trở đi.
- Search `SearchContent` tạo danh sách 3 hotel mẫu khi kết quả rỗng; khi API lỗi tạo một hotel “Test JWT”: `front-end/apps/customer-web/src/app/search/page.tsx`, `SearchContent`, dòng 41–100.
- Hotel detail fallback thông tin khách sạn và loại phòng; nếu không có phòng trống, `handleBookNow` dùng `room_id=21`: `front-end/apps/customer-web/src/app/hotels/[id]/page.tsx`, `HotelDetailContent`, dòng 45–129 và 145–150. Hình khách sạn/phòng là URL Unsplash tĩnh, dòng 136–142 và 336 trở đi.
- Booking success khi không lấy được booking thật vẫn dựng vé `CONFIRMED`, giá/ngày/khách sạn/khách/loại phòng cố định: `front-end/apps/customer-web/src/app/booking/success/[code]/page.tsx`, `BookingSuccessPage`, dòng 30–65. UI này có thể hiển thị “đặt thành công” cho mã không tồn tại.
- Admin dashboard không tính một số dữ liệu từ DB: `todayRevenue` được gán theo tỷ lệ 35%; biểu đồ ngày booking dùng số cố định; biểu đồ doanh thu ngày chia tỷ lệ tổng hiện tại, và có danh sách khách sạn mẫu khi không có dữ liệu. File `front-end/apps/admin-dashboard/src/app/page.tsx`, `fetchDashboardData`, dòng 160–234.
- Checkout có default hotel/room/date/price từ query string, gồm room ID 21 (`front-end/apps/customer-web/src/app/booking/checkout/page.tsx`, `CheckoutContent`, dòng 28–44). Các query này do trình duyệt điều khiển, không phải giá/room ID được backend xác nhận.

#### Seed dữ liệu mẫu trực tiếp vào SQL

- Room Service tự seed 2 loại phòng và 10 phòng vật lý khi bảng loại phòng trống; seed gán `hotel_id=1` mà không có seed hotel tương ứng trong Hotel DB (`services/room-service/src/main.py`, `lifespan`, dòng 21–31; `services/room-service/src/services/room_service.py`, `RoomService.seed_default_data`, dòng 274–355).
- Booking Service seed booking mã `BK-202610-8912`, trạng thái `CONFIRMED`, số tiền/khách/phòng mẫu khi DB booking trống (`services/booking-service/src/main.py`, `lifespan`, dòng 35–49; `services/booking-service/src/services/booking_service.py`, `BookingService.seed_default_bookings`, dòng 405–450). Seed gán `id_tai_khoan=4` dù SQL init seed 3 user mẫu (`services/user-service/database_init.sql`, dòng 61–90); không có FK liên DB để xác nhận định danh.
- Payment Service seed một giao dịch `SUCCESS` và URL sandbox khi DB payment trống (`services/payment-service/src/main.py`, `lifespan`, dòng 22–32; `services/payment-service/src/services/payment_service.py`, `PaymentService.seed_default_payments`, dòng 532–550). Đây không phải bằng chứng giao dịch thật đã thanh toán.
- Đây là dữ liệu mẫu được ghi vào SQL, không chỉ là mock ở giao diện. Báo cáo dashboard và list API có thể hiển thị chúng như giao dịch/booking thật.

#### Checkout – booking – payment lệch giá

- Frontend tính `roomTotal = pricePerNight * nights`, rồi gửi `gia: roomTotal` trong `bookingPayload`; Payment nhận `finalTotal` đã cộng 10% phí (`front-end/apps/customer-web/src/app/booking/checkout/page.tsx`, `CheckoutContent`, dòng 42–44, 77–130).
- Backend lại cộng `r.gia` như giá một đêm rồi nhân tiếp với số đêm (`services/booking-service/src/services/booking_service.py`, `BookingService.create_booking`, dòng 157–158). Hệ quả từ code: booking total bị nhân số đêm lần hai; payment total lại có thêm 10% fee. Hai tổng không được đối chiếu với nhau.
- `BookingService.create_booking` dùng giá và room details từ payload thay vì lấy giá/ownership/availability chính thức từ Room Service; code hiện chỉ tra xung đột booking hiện có (`services/booking-service/src/services/booking_service.py`, `create_booking`, dòng 89–158, 181 trở đi). `PaymentService.create_payment` cũng lưu `payload.so_tien` (`services/payment-service/src/services/payment_service.py`, `create_payment`, dòng 222–227, 334–344). Đây là rủi ro sai giá và toàn vẹn thanh toán.

#### Notification / Payment sandbox

- `MOCK_EMAIL_SEND=True` là default (`services/notification-service/src/core/config.py`, `Settings`, dòng 28–35); `EmailSender.send_email` trả thành công giả nếu mock bật hoặc SMTP_USER rỗng (`services/notification-service/src/core/email_sender.py`, `send_email`, dòng 11–28). Do đó trạng thái `SENT` có thể chỉ là log console.
- Email fallback dùng địa chỉ cố định nếu queue payload thiếu email (`services/notification-service/src/services/notification_service.py`, `NotificationService.handle_message_queue_event`, khoảng dòng 105–145). Không được coi fallback này là người nhận xác thực.
- Khi Payment Service không gọi được Booking Service để kiểm tra booking/hold, `create_payment` chỉ log warning rồi vẫn tiếp tục tạo payment (`services/payment-service/src/services/payment_service.py`, dòng 279–328). Không nên cho phép bỏ qua xác thực booking do dependency unavailable.
- Notification callback bắt lỗi xử lý trong `handle_message_queue_event` và không ném lại (`services/notification-service/src/services/notification_service.py`, dòng 116–151); consumer sau đó ack message (`services/notification-service/src/core/rabbitmq_consumer.py`, dòng 83–96). Một lỗi lưu/gửi có thể bị ack như đã xử lý và không được RabbitMQ retry.
- Payment tích hợp sandbox, endpoint `simulate-ipn` và checkout URL localhost, không phải VNPay/MoMo/ATM thật (`services/payment-service/src/api/v1/endpoints/payments.py`, `simulate_ipn` dòng 69–78; `services/payment-service/src/services/payment_service.py`, `create_payment` dòng 334 trở đi).

### 3. 🔴 Lỗi cấu hình, bảo mật và toàn vẹn dữ liệu

#### A. Schema SQL Server lệch ORM – User Service (có khả năng chặn hoạt động)

- DDL `tai_khoan` và `nguoi_dung` không khai báo `ngay_cap_nhat` (`services/user-service/database_init.sql`, bảng `tai_khoan` dòng 17–36, `nguoi_dung` dòng 39–57).
- ORM khai báo cột này ở cả hai model (`services/user-service/src/models/tai_khoan.py`, `TaiKhoanModel`, dòng 40–43; `services/user-service/src/models/nguoi_dung.py`, `NguoiDungModel`, dòng 26–29). ORM còn khai báo `email String(100)` trong khi DDL là `NVARCHAR(150)` (`tai_khoan.py` dòng 22; `database_init.sql` dòng 22).
- `User Service` gọi `Base.metadata.create_all()` lúc khởi động (`services/user-service/src/main.py`, `lifespan`, dòng 22–35). `create_all` không phải migration để thêm cột vào bảng đã tồn tại; vì SQL init tạo bảng trước, chênh lệch cột không tự được sửa. Query/insert có thể gặp lỗi `Invalid column name ngay_cap_nhat`.
- User ORM–DDL là drift đã xác nhận; chưa thực hiện đối chiếu tự động từng column cho toàn bộ 6 service, nên không tuyên bố không có drift khác.

#### B. Credential không được bảo vệ

- `hash_password` trả lại nguyên văn password; bcrypt bị comment/TODO (`services/user-service/src/core/security.py`, `hash_password`, dòng 7–15). SQL init cũng seed ba tài khoản mẫu bằng plain text (`services/user-service/database_init.sql`, dòng 61–90). Đây là lỗi bảo mật nghiêm trọng, không phù hợp dữ liệu thật.
- JWT secret, SA password, SQL credentials có giá trị mặc định phát triển trong `.env.example`, các `core/config.py` và Compose. Nếu dùng mặc định khi deploy, secret có thể đoán được/tái sử dụng; cần bắt buộc secret riêng theo môi trường và không phát hành credential mặc định.
- User Service `generic_exception_handler` trả `str(exc)` trong response body (`services/user-service/src/main.py`, dòng 81–88); tránh lộ chi tiết nội bộ ở môi trường public.

#### C. Kiểm soát quyền và endpoint nhạy cảm

- Booking endpoint list/detail/confirm/cancel/release-expired chỉ phụ thuộc DB; không có dependency role/auth (`services/booking-service/src/api/v1/endpoints/bookings.py`, `get_bookings` dòng 39–61, `get_booking_detail` 69–78, `confirm_booking` 81–91, `cancel_booking` 94–104, `release_expired_holds` 107 trở đi). `create_booking` nhận user không xác thực và fallback `id_tai_khoan` về 1 (`BookingService.create_booking`, dòng 166).
- Toàn bộ Payment routes, gồm list/stats, simulate IPN, verify OTP và create-payment, chỉ yêu cầu body/header idempotency; không thấy dependency xác thực/phân quyền trong `services/payment-service/src/api/v1/endpoints/payments.py`, dòng 21–126. Đặc biệt IPN simulation không được khóa admin/internal.
- Notification `send/list/detail/preview` cũng không có auth dependency (`services/notification-service/src/api/v1/endpoints/notifications.py`, handlers dòng 18–88); preview trả HTML nội dung đã lưu.
- Room dependency chấp nhận token số nguyên như tài khoản `ADMIN` (`services/room-service/src/api/v1/dependencies.py`, `get_current_user_payload`, dòng 13–40); Hotel fallback token số nguyên thành partner ID mà không còn xác thực role (`services/hotel-service/src/api/dependencies.py`, `get_current_partner_id`, dòng 82–90). Đây là đường demo phải loại bỏ trước triển khai.
- Booking dependency có fallback token số nguyên và trả role CUSTOMER (`services/booking-service/src/api/v1/dependencies.py`, dòng 14–28); nhưng endpoint tạo booking vẫn không bắt buộc dependency và fallback user ID 1.
- API client có callback token và gắn Authorization khi có token (`front-end/packages/api-client/src/index.ts`, `ApiClient.request`, dòng 108–116); vấn đề chính không phải thiếu header ở client mà là các endpoint nhạy cảm phía trên không bắt buộc xác thực. Nên sửa ở server; không dựa vào việc UI ẩn nút.

#### D. Cấu hình Gateway/Frontend và môi trường chạy

- `.env.example` là root template; script local chạy mỗi service với working directory là thư mục service (`start-services-local.ps1`, danh sách service dòng 32–40, `Start-Process` dòng 52–64). Settings khai báo `env_file=".env"` tương đối theo working directory. Root `.env` vì vậy không tự được tìm thấy khi service khởi chạy; các `services/*/.env.example` riêng cũng không được script tự copy thành `.env`.
- Cấu hình local mặc định không đồng nhất: `init-databases-local.ps1` mặc định SQL Windows Authentication (`-E`, dòng 43), trong khi nhiều service default SQL authentication/credentials và notification/booking/payment có default instance `localhost\SQLEXPRESS`. `.env.example` root lại cấu hình `DB_SERVER=sqlserver`, thích hợp DNS Compose hơn local process. Dev mới cần chỉnh cấu hình service tương ứng; chạy nguyên script không đảm bảo app trỏ cùng SQL instance/user/password với bước init.
- `setup-environment.ps1` kiểm tra sự tồn tại của Python/Node chứ không enforce version; nếu pip/pnpm fail, script vẫn tiếp tục/có thể chỉ in warning (`setup-environment.ps1`, dòng 16–31, 34–57). Script chỉ tạo root `.env`, không tạo `.env` trong service dirs.
- `init-databases-local.ps1` in “hoàn tất” sau vòng lặp kể cả khi `sqlcmd` lỗi hoặc thiếu file (dòng 26–57); exit code lỗi không dừng toàn script.
- `start-services-local.ps1` tự `Stop-Process` mọi PID đang listen trên các port cấu hình (dòng 17–27), có thể dừng tiến trình không thuộc dự án. Process Node không redirect stdout/stderr vào log như backend Python (dòng 52–69). Trạng thái startup chỉ kiểm tra listener sau 4 giây (dòng 83 trở đi), không probe readiness thực chất.
- Có `.env` local trong workspace audit nhưng file ignored; không đọc giá trị. Máy clone mới chỉ có `.env.example`.

### 4. ⚪ Tài liệu có nhưng chưa có code

- **Đánh giá khách sạn:** DFD khách sạn mô tả “Gửi đánh giá” và “Lưu đánh giá” (`docs/DFD_hotel_muc1.drawio`, dòng 106/114; `docs/DFD_hotel_muc2.drawio`, dòng 207/222). Không thấy endpoint/model/service/DDL đánh giá trong `services/`; chưa có code.
- **SMS:** DFD Notification ghi provider Email/SMS và gửi SMS (`docs/notification-service-DFD-1.drawio`, các node/flow dòng 75, 115, 141; `docs/HoangQuan/3-sendandsavehistory-DFD2-notificationservice.drawio`, dòng 19, 34, 57). Source hiện có SMTP email sender, không có SMS adapter/provider; chưa có code gửi SMS.
- **Refund:** ERD mô tả các trường hoàn tiền (`docs/ERD.drawio`, vùng entity hoàn tiền khoảng dòng 429–438). SQL/ORM có bảng `hoan_tien`, nhưng Payment API không có endpoint refund và `PaymentService` không có method thực hiện hoàn tiền. Chỉ có persistence schema, nghiệp vụ API chưa có code.
- **Thanh toán thật:** Tài liệu/README nhắc các cổng VNPay/MoMo/ATM; implementation hiện có sandbox checkout và `simulate-ipn`, chưa có tích hợp provider xác minh chữ ký/callback thật.
- **Email thật:** Notification có SMTP code nhưng mock bật mặc định và chưa cấu hình SMTP trong template mặc định; DFD provider không đồng nghĩa đã gửi email thật.

---

## IV. ⚙️ Kiểm tra môi trường và kịch bản khởi chạy local

### `setup-environment.ps1`

- Cài root `requirements.txt` và `pnpm install`, rồi copy `.env.example` vào root nếu chưa có.
- Không tạo Python virtual environment/khóa version; dependencies cài vào interpreter dùng chung.
- Bỏ qua lỗi hoặc chỉ thông báo khi pip install thất bại; không xác minh `pnpm install` thành công trước khi báo “sẵn sàng”.
- `.env` ở root không phù hợp trực tiếp cho các tiến trình chạy trong thư mục service nếu `BaseSettings` đọc `.env` theo current working directory. Cần thống nhất nạp root env bằng đường dẫn tuyệt đối hoặc tạo service env files.

### `init-databases-local.ps1`

- Cần `sqlcmd`, SQL Server chạy, database permission phù hợp, và driver/auth mode tương thích.
- Mặc định dùng Windows Authentication nhưng service settings thường dùng SQL Authentication. Có tham số SQL username/password, tuy nhiên phải truyền giống app config.
- Có thể báo hoàn tất dù từng database init thất bại; không dùng thông báo cuối script làm tiêu chí thành công. Đọc exit code/log của từng `sqlcmd`.

### `start-services-local.ps1`

- Chạy tổng cộng 9 tiến trình local: sáu service, Gateway và hai Next app.
- Không tự khởi động SQL Server hoặc RabbitMQ. Cả hai phải chạy sẵn; Service DB và inter-service URL phải reachable.
- Cấu hình root `.env` không tự được nạp từ working directory từng service; các service env template riêng không tự cài đặt.
- Script dừng các process đang dùng port trước khi chạy; cần xác nhận port ownership trước khi chạy trên máy dùng chung.
- Node frontend không được đưa vào log redirect; dashboard/customer logs được khai báo nhưng không cấu hình redirect ở nhánh Node.
- Không có readiness probe chi tiết hay fail-fast nếu process thoát ngay sau `Start-Process`.

### Kết luận run readiness

**Không thể coi trải nghiệm “clone → chạy 3 script → toàn hệ thống sẵn sàng” là đã xác nhận.** Rủi ro đứt đoạn được chứng minh trong code là sự khác biệt auth/config SQL local, `.env` root không được service process nạp theo cwd, backend DB errors có thể bị nuốt khi startup, và script init tiếp tục sau lỗi. Docker daemon/SQL endpoint chưa được smoke-test; việc thấy executable `docker`/`sqlcmd` trong PATH không xác nhận service đang chạy.

---

## V. 🎯 Lộ trình khắc phục ưu tiên

### Priority 1 — Gỡ lỗi toàn vẹn, bảo mật và cấu hình

1. Đồng bộ User ORM/DDL: thêm migration có version cho `ngay_cap_nhat` ở hai bảng hoặc bỏ cột không được dùng; sửa độ dài email; không kỳ vọng `create_all` migrate bảng hiện hữu.
2. Bật hash password bcrypt/Argon2 có salt và migrate password plaintext; loại bỏ tài khoản seed/mật khẩu dùng chung khỏi môi trường thật.
3. Bắt buộc JWT + role ở Booking, Payment và Notification; loại bỏ numeric-token demo fallback ở Hotel/Room/Booking. Chặn public `simulate-ipn`, confirm/cancel/release-expired.
4. Chuyển xác thực toàn bộ giá/room ID/hotel ownership/availability về backend; lấy giá chính thức từ Room Service và đối chiếu payment amount với booking total. Sửa công thức giá: thống nhất `gia` là giá/đêm hay tổng kỳ nghỉ; tính thuế/phí tại một nguồn tin cậy.
5. Chuẩn hóa cấu hình: một nguồn `.env`, đường dẫn nạp xác định, auth mode SQL giống nhau cho init và service; fail-fast khi thiếu secret/DB/RabbitMQ ở môi trường cần thiết. Không dùng default secret/password trong deploy.
6. Điều chỉnh `start-services-local.ps1` để chỉ dừng PID do chính script sở hữu; ghi log frontend; xác minh readiness/exit code. `init-databases-local.ps1` phải fail process nếu có database init lỗi.

### Priority 2 — Hoàn thiện API/UI và loại dữ liệu giả

1. Xóa hoặc feature-flag mọi hotel/room/booking fallback mẫu trên Customer UI; hiển thị trạng thái empty/error đúng nghĩa, không hiển thị booking thành công giả.
2. Loại dữ liệu suy diễn khỏi Admin Dashboard; bổ sung endpoint thống kê theo ngày/khách sạn hoặc tính từ tập dữ liệu đầy đủ, không lấy 100 booking đầu hoặc tỷ lệ cố định.
3. Chốt chiến lược API: cấu hình API client gọi Gateway nhất quán hoặc bỏ Gateway khỏi tài liệu; kiểm thử các URL/prefix thực tế và không expose các URL nội bộ service cho browser khi deploy.
4. Hoàn thiện review khách sạn, refund (validation, idempotency, audit/log) và SMS nếu còn trong scope; nếu không còn scope, cập nhật DFD/ERD/README và feature matrix để phản ánh đúng.
5. Cấu hình SMTP thật bằng secret runtime và mặc định `MOCK_EMAIL_SEND=False` ở staging/prod; chỉ trả `SENT` khi provider chấp nhận gửi; xử lý retry/queue dead-letter thay vì giả lập.

### Priority 3 — Nâng cấp vận hành và kiểm thử

1. Thêm migration Alembic hoặc migration có version nhất quán cho toàn bộ service; kiểm tra tự động schema drift giữa SQL init và ORM.
2. Chạy/test suite trên SQL Server thực hoặc container tích hợp; thêm regression tests cho auth/authorization, giá và phí, availability/concurrency, idempotency, payment signature, notification failure/retry, refund.
3. Thêm Docker Compose cho hai frontend, healthcheck phụ thuộc thật, secrets không commit, profiles dev/test/prod, startup ordering có readiness.
4. Kiểm thử e2e Browser → Gateway → Service → SQL Server và event RabbitMQ; lưu test evidence/status code trước khi đánh dấu luồng 🟢.
5. Thêm CI cho Python tests/lint/type check, frontend build/lint/typecheck và secret/config scanning; hiện chỉ TypeScript check đã chạy thành công trong lượt audit này.

---

## Phụ lục: bằng chứng kiểm tra

- Frontend TypeScript: `pnpm check-types` tại `front-end/` — 5 tasks successful.
- Python tests: chưa chạy; `python -m pytest --collect-only -q` lỗi vì thiếu `pytest`.
- Không khởi động SQL Server, RabbitMQ, FastAPI services hoặc frontend trong lượt audit; không tạo/sửa dữ liệu runtime.
- Các đường dẫn và line numbers trong báo cáo trỏ tới mã nguồn hiện có trong repository; line numbers có thể thay đổi sau khi sửa code.
