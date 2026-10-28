# System-Booking-service (Hệ thống Quản lý & Đặt phòng Khách sạn Trực tuyến)

Hệ thống đặt phòng khách sạn trực tuyến áp dụng kiến trúc **Microservices / SOA** kết hợp **Monorepo** và **API Gateway**, đáp ứng đầy đủ nghiệp vụ cho cả Khách hàng (Customer), Chủ khách sạn (Partner) và Quản trị viên hệ thống (Admin):

| Dịch vụ / Ứng dụng | Công nghệ | Cổng (Port) | Chức năng chính |
| :--- | :--- | :---: | :--- |
| **API Gateway** | FastAPI / Nginx Reverse Proxy | `8080` | Điểm truy cập duy nhất, định tuyến động, gom cụm CORS, bảo vệ backend |
| **Hotel Service** | FastAPI + SQLAlchemy 2 + SQL Server | `8000` | Quản lý thông tin khách sạn, tiện nghi, quy tắc, xếp hạng, hình ảnh |
| **User Service** | FastAPI + SQLAlchemy 2 + SQL Server | `8001` | Xác thực JWT 3 vai trò (Admin, Partner, Customer), phân quyền, hồ sơ người dùng |
| **Room Service** | FastAPI + SQLAlchemy 2 + SQL Server | `8002` | Quản lý hạng phòng, kho phòng vật lý, kiểm tra trạng thái phòng trống khả dụng |
| **Booking Service** | FastAPI + SQLAlchemy 2 + SQL Server | `8003` | Quy trình đặt phòng, khóa giữ chỗ 15 phút, chống Overbooking đồng thời |
| **Payment Service** | FastAPI + SQLAlchemy 2 + SQL Server | `8004` | Cổng thanh toán giả lập Sandbox (VNPAY, MoMo, ATM), Webhook IPN Callback |
| **Notification Service** | FastAPI + RabbitMQ + SMTP | `8005` | Tiêu thụ message queue, gửi email HTML xác nhận kèm mã QR check-in |
| **Message Broker** | RabbitMQ + Management UI | `5672` / `15672` | Hàng đợi tin nhắn bất đồng bộ (`notification.*`) |
| **Admin Dashboard** | Next.js 16 + React 19 + TailwindCSS v4 | `3000` | Giao diện quản trị toàn diện: Khách sạn, Phòng, Người dùng, Đơn đặt, Dòng tiền |
| **Customer Web App** | Next.js 16 + React 19 + TailwindCSS v4 | `3001` | Ứng dụng web đặt phòng khách hàng: Tìm kiếm thông minh, Xem phòng, Checkout, E-Ticket |

---

## 🌐 ĐỊNH TUYẾN TẬP TRUNG QUA API GATEWAY (`http://localhost:8080`)

Toàn bộ ứng dụng Client (Web Khách hàng, Mobile App, Admin Dashboard) chỉ cần gọi vào **một cổng duy nhất `http://localhost:8080/api/v1/...`**:

- 🔹 `/api/v1/auth/**`, `/api/v1/users/**`, `/api/v1/admin/**` ➔ `http://user-service:8001`
- 🔹 `/api/v1/hotels/**` ➔ `http://hotel-service:8000`
- 🔹 `/api/v1/rooms/**`, `/api/v1/room-types/**` ➔ `http://room-service:8002`
- 🔹 `/api/v1/hotels/{hotel_id}/rooms/**`, `/api/v1/hotels/{hotel_id}/room-types/**` ➔ `http://room-service:8002` *(Định tuyến ưu tiên)*
- 🔹 `/api/v1/bookings/**` ➔ `http://booking-service:8003`
- 🔹 `/api/v1/payments/**` ➔ `http://payment-service:8004`
- 🔹 `/api/v1/notifications/**` ➔ `http://notification-service:8005`
- 🔹 Gateway Health Check tổng quan: `GET http://localhost:8080/health`

> **Lợi ích kiến trúc Gateway**:
> - Khách hàng và Dashboard không cần biết địa chỉ IP/Port nội bộ của từng microservice.
> - Gateway tự động bảo lưu và chuyển tiếp Header `Authorization: Bearer <token>` cùng `X-Correlation-ID` qua tất cả microservice để phục vụ **Distributed Tracing**.
> - Chặn các yêu cầu truy cập trái phép trực tiếp vào các cổng dịch vụ nội bộ.

---

## 🔒 TỔNG KẾT CƠ CHẾ BẢO MẬT & TOÀN VẸN NGHIỆP VỤ (SECURITY & DATA TRUST)

Hệ thống được thiết kế theo tiêu chuẩn bảo mật doanh nghiệp nhiều lớp (Defense-in-depth):

### 1. Mã hóa mật khẩu Bcrypt & Kiểm soát trạng thái tài khoản
- Toàn bộ mật khẩu người dùng được băm an toàn bằng giải thuật **Bcrypt** thông qua thư viện `passlib.context.CryptContext(schemes=["bcrypt"])`. Mật khẩu dạng plain text tuyệt đối không xuất hiện trong cơ sở dữ liệu.
- Quá trình đăng nhập luôn kiểm tra trạng thái hoạt động `is_active`. Các tài khoản bị Admin vô hiệu hóa/khóa tạm thời sẽ bị từ chối đăng nhập với thông báo lỗi rõ ràng.

### 2. Xác thực giao dịch OTP & Băm bảo mật SHA-256
- **Ẩn mã OTP thô khỏi Response**: Mã OTP 6 chữ số sinh ngẫu nhiên chỉ được chuyển phát qua kênh gửi thông báo (Email / SMS) và **tuyệt đối không trả về trong JSON Response** của API.
- **Băm SHA-256 trong CSDL**: Trong bảng `thanh_toan`, cột `otp_hash` chỉ lưu chuỗi băm 64 ký tự hex `hashlib.sha256(otp.encode()).hexdigest()`. Kẻ tấn công đọc được database cũng không thể khôi phục mã OTP.
- **Giới hạn thời gian (TTL) & Số lần thử**: Mã OTP chỉ có hiệu lực trong vòng **3 phút**. Nếu nhập sai quá **3 lần**, phiên xác thực OTP sẽ bị hủy bỏ ngay lập tức.
- **Che giấu dữ liệu nhạy cảm (Data Masking)**: Khi lưu trữ vết thông báo trong CSDL (`noi_dung_thong_bao`) hoặc xuất ra màn hình console, mã OTP được tự động che theo định dạng `84****` để phòng ngừa rò rỉ dữ liệu qua nhật ký vận hành.

### 3. API Gateway Routing tập trung & Kiểm soát CORS
- **Chặn truy cập trực tiếp**: Các ứng dụng frontend kết nối qua Reverse Proxy `:8080`, tránh lộ mạng lưới dịch vụ phía sau.
- **CORS Thắt chặt**: Thay vì mở `*` (wildcard) với `allow_credentials=True`, cấu hình CORS trên Gateway và 6 microservice được giới hạn nghiêm ngặt chỉ chấp nhận các domain chỉ định (`localhost:3000`, `localhost:3001`).
- **Giao tiếp nội bộ an toàn (Server-to-Server Secret)**: Các endpoint nội bộ (như REST Fallback `/api/v1/notifications/internal-send`) được bảo vệ bằng header `X-Internal-Secret`, ngăn ngừa người dùng bên ngoài kích hoạt trái phép.

### 4. Bảo vệ dữ liệu tin cậy (Data Trust Protection) & Đối soát tài chính
- **Chống thao túng giá phòng (Room Price Trust)**: Khi tạo đơn đặt phòng, `booking-service` không dựa vào giá tiền do client gửi lên mà tự động truy vấn giá niêm yết gốc từ `room-service`. Nếu phát hiện giá bị làm sai lệch, giao dịch sẽ bị từ chối ngay lập tức.
- **Đối soát số tiền thanh toán (Payment Amount Reconciliation)**: `payment-service` đối chiếu số tiền thanh toán với đơn đặt phòng thực tế (bao gồm 10% thuế VAT được đồng bộ chuẩn giữa Frontend và Backend) trước khi mở cổng thanh toán.
- **Chống Overbooking & Khóa giữ chỗ**: Áp dụng khóa phân tán / `sp_getapplock` trong SQL Server cùng thời gian giữ chỗ 15 phút, tự động giải phóng phòng nếu khách không hoàn tất thanh toán.
- **Chống thanh toán trùng lặp (Idempotency Key)**: Ngăn chặn lỗi double payment khi người dùng nhấn nút thanh toán nhiều lần hoặc mạng chập chờn.

---

## 🧪 CHẠY BỘ KIỂM THỬ TỰ ĐỘNG TOÀN DIỆN (AUTOMATED TEST SUITE)

Dự án cung cấp script PowerShell tự động kiểm tra hạ tầng và thực thi tuần tự **6 bài test chuyên sâu** bao quát toàn bộ các luồng nghiệp vụ cốt lõi và tiêu chuẩn an toàn bảo mật:

```powershell
.\run-tests.ps1
```

### 📋 Danh sách 6 bài kiểm thử được thực thi tự động:

| STT | File kịch bản kiểm thử | Tên bài test & Mục tiêu kiểm tra | Thời gian TB |
| :---: | :--- | :--- | :---: |
| **1** | `test/test_booking_concurrency.py` | **Chống Overbooking & Khóa Concurrency**: Giả lập nhiều luồng tranh chấp cùng 1 phòng, đảm bảo chỉ 1 giao dịch thành công. | ~18s |
| **2** | `test/test_payment_idempotency.py` | **Idempotency Key & Chống Thanh Toán Trùng Lặp**: Kiểm tra việc gọi liên tiếp cùng một yêu cầu thanh toán không tạo ra nhiều bản ghi trừ tiền. | ~18s |
| **3** | `test/test_payment_otp.py` | **Xác Thực Thanh Toán OTP & Băm SHA-256**: Kiểm tra kiểm tra băm SHA-256, hạn 3 phút, khóa sau 3 lần sai. | ~18s |
| **4** | `test/test_notification_otp.py` | **Email Template OTP, Che Mã CSDL & Chống XSS**: Kiểm tra render template HTML, che mã `84****` trong CSDL, an toàn trước mã độc HTML. | ~18s |
| **5** | `test/test_correlation_tracing.py` | **Distributed Tracing với Header `X-Correlation-ID`**: Kiểm tra việc truyền vết request ID xuyên suốt các microservice. | ~23s |
| **6** | `test/test_gateway_flow.py` | **Định Tuyến Động & Toàn Diện Luồng Nghiệp Vụ Gateway**: Kiểm tra trọn vẹn luồng từ User ➔ Booking ➔ Payment qua API Gateway `:8080`. | ~28s |

> **Tính năng của `run-tests.ps1`**:
> - Tự động ping và kiểm tra trạng thái **API Gateway (:8080)**, **RabbitMQ (:5672)** và **SQL Server Database**.
> - Nếu một số service chưa bật, script tự động chuyển sang cơ chế kiểm thử giả lập (`TestClient` / In-Memory Mock) để bảo đảm việc kiểm thử luôn hoàn tất 100%.
> - Xuất bảng tổng hợp trực quan với trạng thái `PASS` và đo lường thời gian thực thi của từng bài test.

---

## 📧 CẤU HÌNH GỬI EMAIL SMTP THỰC TẾ (REAL SMTP SETUP)

Mặc định, `notification-service` chạy ở chế độ mô phỏng (`USE_MOCK_EMAIL=True`), nội dung email sẽ được ghi trực tiếp ra console terminal để phục vụ việc phát triển và kiểm thử mà không cần tài khoản email thật.

Để kích hoạt tính năng **gửi email HTML thật** (kèm mã QR check-in trực tuyến và hóa đơn điện tử) qua máy chủ SMTP (Gmail, Outlook, Amazon SES, SendGrid,...):

### 1. Cấu hình biến môi trường trong `services/notification-service/.env`

Chỉnh sửa hoặc tạo mới file `.env` tại thư mục `services/notification-service/`:

```env
# Chuyển đổi sang gửi email thật qua SMTP
USE_MOCK_EMAIL=False
MOCK_EMAIL_SEND=False

# Cấu hình SMTP Server (Ví dụ với Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_TLS=True
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_FROM_NAME="LuxeStay Booking Service"

# Cổng SSL thay thế (Nếu dùng cổng 465)
# SMTP_PORT=465
# SMTP_TLS=False
```

### 2. Hướng dẫn lấy Mật khẩu ứng dụng (App Password) cho Gmail:
1. Đăng nhập vào tài khoản Google của bạn và bật **Xác minh 2 bước (2-Step Verification)**.
2. Truy cập [Google Account Security ➔ App Passwords](https://myaccount.google.com/apppasswords).
3. Đặt tên ứng dụng (ví dụ: `HotelBooking`) và nhấn **Tạo (Create)**.
4. Copy chuỗi 16 ký tự vừa được cấp và dán vào biến `SMTP_PASSWORD` trong file `.env`.

### 3. Cơ chế chịu lỗi (Fault-Tolerant Email Delivery):
- **Ưu tiên RabbitMQ Message Broker**: Các dịch vụ gửi sự kiện vào hàng đợi `notification.booking.confirmed`, consumer của `notification-service` xử lý bất đồng bộ.
- **Tự động chuyển đổi REST Fallback**: Khi RabbitMQ gặp sự cố mạng hoặc bị tắt, `booking-service` và `payment-service` tự động fallback gọi trực tiếp HTTP endpoint nội bộ:
  `POST http://localhost:8005/api/v1/notifications/internal-send` kèm header `X-Internal-Secret`, đảm bảo **không bao giờ bị mất email xác nhận** của khách hàng.

---

## 💻 HƯỚNG DẪN CHẠY DỰ ÁN TRÊN MÁY MỚI (SETUP FROM SCRATCH)

Dành cho thành viên nhóm hoặc bất kỳ ai vừa clone dự án về máy tính mới.

### 1. Yêu cầu môi trường (Prerequisites)
Cần cài đặt sẵn các công cụ sau trên máy:
1. **Python**: Phiên bản 3.10 trở lên ([Tải tại python.org](https://www.python.org/downloads/)).
2. **Node.js**: Phiên bản 18 trở lên ([Tải tại nodejs.org](https://nodejs.org/)).
3. **pnpm**: Trình quản lý gói cho Monorepo (`npm install -g pnpm`).
4. **Microsoft SQL Server**: Phiên bản 2019/2022 (Developer hoặc Express) kèm `ODBC Driver 17 for SQL Server` hoặc `ODBC Driver 18 for SQL Server`. (Hoặc dùng Docker MSSQL).
5. **Git**: Dùng để clone mã nguồn.

---

### 2. Các bước cài đặt từ A đến Z

#### Bước 1: Clone mã nguồn
```bash
git clone https://github.com/nguyenvantai-imfine/System-Booking-service.git
cd System-Booking-service
```

#### Bước 2: Cài đặt thư viện dependencies (Tự động 1 lệnh)
Trên Windows PowerShell, chạy script:
```powershell
.\setup-environment.ps1
```
> **Script này sẽ tự động**:
> - Kiểm tra phiên bản Python và Node.js.
> - Tự động cài đặt `pnpm` nếu máy chưa có.
> - Cài đặt toàn bộ dependencies Python từ `requirements.txt` vào máy.
> - Cài đặt toàn bộ dependencies Front-end Monorepo (`pnpm install`).
> - Tự động copy `.env.example` thành `.env`.

*(Nếu muốn cài đặt thủ công từng phần)*:
```bash
# Cài đặt Python packages:
pip install -r requirements.txt

# Cài đặt Front-end packages:
cd front-end
pnpm install
cd ..
```

#### Bước 3: Khởi tạo Cơ sở dữ liệu (Database Setup)
Khởi tạo tự động 6 database trên SQL Server cục bộ bằng lệnh:
```powershell
# Chạy với Windows Authentication (mặc định):
.\init-databases-local.ps1

# Hoặc nếu dùng tài khoản SQL Server Auth:
.\init-databases-local.ps1 -Server "localhost" -Username "sa" -Password "Password123!"
```

*(Hoặc mở SQL Server Management Studio (SSMS) / Azure Data Studio và chạy lần lượt 6 script SQL)*:
1. `services/hotel-service/database_update.sql` ➔ Tạo CSDL `hotel_service`
2. `services/user-service/database_init.sql` ➔ Tạo CSDL `user_service`
3. `services/room-service/database_init.sql` ➔ Tạo CSDL `room_service`
4. `services/booking-service/database_init.sql` ➔ Tạo CSDL `booking_service`
5. `services/payment-service/database_init.sql` ➔ Tạo CSDL `payment_service`
6. `services/notification-service/database_init.sql` ➔ Tạo CSDL `notification_service`

---

### 🚀 CÁCH 1: Khởi Chạy Toàn Bộ Hệ Thống Bằng 1 Lệnh (Khuyên Dùng)

Mở PowerShell tại thư mục gốc dự án và thực thi:

```powershell
.\start-services-local.ps1
```

> **Tính năng nổi bật của script**:
> - Tự động giải phóng các cổng bị chiếm dụng trước khi bật.
> - Khởi chạy ngầm toàn bộ **9 dịch vụ** ngay trong terminal (**không bị bung cửa sổ popup ra ngoài màn hình**).
> - Ghi lại log chi tiết vào thư mục `logs/`.
> - Xuất bảng tổng hợp trực quan kèm link truy cập từng dịch vụ.

#### 🛠️ Các lệnh tiện ích khi vận hành:
- **Kiểm tra trạng thái các dịch vụ**:
  ```powershell
  .\status-services-local.ps1
  ```
- **Dừng toàn bộ hệ thống & giải phóng port**:
  ```powershell
  .\stop-services-local.ps1
  ```
- **Xem log thời gian thực của một dịch vụ**:
  ```powershell
  Get-Content logs\gateway.log -Wait
  Get-Content logs\booking-service.log -Wait
  Get-Content logs\customer-web.log -Wait
  ```

---

### 🐳 CÁCH 2: Khởi Chạy Bằng Docker Compose (Dành Cho Máy Có Docker)

Nếu máy bạn đã cài Docker Desktop:
```bash
docker compose up -d --build
```
Hệ thống sẽ tự động build và chạy toàn bộ container:
- SQL Server (`1433`) + Tự động chạy script tạo 6 CSDL
- RabbitMQ (`5672` & Dashboard `15672`)
- 6 Backend Microservices (`8000` - `8005`)
- API Gateway (`8080`)

---

### 💻 CÁCH 3: Khởi Chạy Thủ Công Từng Dịch Vụ (Manual Startup)

Nếu bạn muốn debug từng microservice độc lập, hãy mở các terminal riêng biệt:

| Dịch vụ | Lệnh thực thi trong Terminal | Đường dẫn Swagger / Giao diện |
| :--- | :--- | :--- |
| **Hotel Service** | `cd services/hotel-service` <br> `python -m uvicorn src.main:app --reload --port 8000` | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **User Service** | `cd services/user-service` <br> `python -m uvicorn src.main:app --reload --port 8001` | [http://localhost:8001/docs](http://localhost:8001/docs) |
| **Room Service** | `cd services/room-service` <br> `python -m uvicorn src.main:app --reload --port 8002` | [http://localhost:8002/docs](http://localhost:8002/docs) |
| **Booking Service** | `cd services/booking-service` <br> `python -m uvicorn src.main:app --reload --port 8003` | [http://localhost:8003/docs](http://localhost:8003/docs) |
| **Payment Service** | `cd services/payment-service` <br> `python -m uvicorn src.main:app --reload --port 8004` | [http://localhost:8004/docs](http://localhost:8004/docs) |
| **Notification Service** | `cd services/notification-service` <br> `python -m uvicorn src.main:app --reload --port 8005` | [http://localhost:8005/docs](http://localhost:8005/docs) |
| **API Gateway** | `cd gateway` <br> `python -m uvicorn src.main:app --reload --port 8080` | [http://localhost:8080](http://localhost:8080) / [health](http://localhost:8080/health) |
| **Admin Dashboard** | `cd front-end` <br> `pnpm --filter admin-dashboard dev` | [http://localhost:3000](http://localhost:3000) |
| **Customer Web App** | `cd front-end` <br> `pnpm --filter customer-web dev` | [http://localhost:3001](http://localhost:3001) |

---

## 🔑 TÀI KHOẢN MẪU ĐĂNG NHẬP HỆ THỐNG

| Nhóm vai trò | Email tài khoản | Mật khẩu | Quyền hạn & Chức năng |
| :--- | :--- | :---: | :--- |
| **Quản trị viên (Admin)** | `admin@hotel.com` | `123456` | Toàn quyền quản trị hệ thống, duyệt khách sạn, quản lý người dùng, xem doanh thu thực tế |
| **Đối tác (Partner)** | `partner@hotel.com` | `123456` | Quản lý khách sạn sở hữu, thêm hạng phòng, cập nhật phòng trống |
| **Khách hàng (Customer)** | `customer@hotel.com` | `123456` | Tìm kiếm phòng, đặt phòng trực tuyến, thanh toán OTP, quản lý vé điện tử |

---

## 🌟 ĐƯỜNG DẪN TRUY CẬP CÁC PHÂN HỆ GIAO DIỆN

### 1. Ứng dụng Khách hàng (Customer Web App - Port 3001):
- 🏠 **Trang chủ & Tìm kiếm thông minh**: [http://localhost:3001](http://localhost:3001)
- 🔍 **Trang Kết quả tìm kiếm & Bộ lọc**: [http://localhost:3001/search](http://localhost:3001/search)
- 🏨 **Chi tiết khách sạn & Chọn phòng**: [http://localhost:3001/hotels/5](http://localhost:3001/hotels/5)
- 💳 **Trang Checkout / Đặt phòng & Thanh toán**: [http://localhost:3001/booking/checkout](http://localhost:3001/booking/checkout)
- 📋 **Quản lý đơn đặt phòng của tôi (E-Ticket & Tra cứu QR)**: [http://localhost:3001/my-bookings](http://localhost:3001/my-bookings)

### 2. Trang Quản trị (Admin Dashboard - Port 3000):
- 📊 **Trang Tổng quan & Doanh thu thực tế**: [http://localhost:3000](http://localhost:3000)
- 🏨 **Quản lý Khách sạn**: [http://localhost:3000/Hotels](http://localhost:3000/Hotels)
- 🛏️ **Quản lý Hạng phòng & Phòng vật lý (Hỗ trợ Sắp xếp đa cột)**: [http://localhost:3000/Rooms](http://localhost:3000/Rooms)
- 👥 **Quản lý Người dùng & Khóa tài khoản**: [http://localhost:3000/Users](http://localhost:3000/Users)
- 📅 **Quản lý Đơn đặt phòng**: [http://localhost:3000/Bookings](http://localhost:3000/Bookings)
- 💳 **Lịch sử Giao dịch & Dòng tiền**: [http://localhost:3000/Payments](http://localhost:3000/Payments)

---

## 📬 LUỒNG NOTIFICATION & MESSAGE QUEUE

1. **Khách đặt phòng & Thanh toán**:
   - Khi thanh toán thành công, `payment-service` hoặc `booking-service` phát tín hiệu vào RabbitMQ queue:
     - `notification.booking.confirmed`: Xác nhận đơn đặt phòng thành công.
     - `notification.payment.success`: Xác nhận thanh toán thành công.
     - `notification.booking.cancelled`: Thông báo hủy đơn và nhả phòng.
2. **Notification Service tiêu thụ và gửi Email**:
   - Background consumer lắng nghe các queue, giải mã payload và render template HTML email cao cấp.
   - Template tích hợp sẵn mã QR check-in trực tuyến, mã booking, tên và địa chỉ khách sạn, ngày nhận/trả phòng, chi tiết giá và quy định lưu trú.
   - Lưu trữ vết lịch sử thông báo vào bảng `thong_bao` và `noi_dung_thong_bao` trong SQL Server (đã được che dữ liệu nhạy cảm).
