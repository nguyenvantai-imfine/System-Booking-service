# System-Booking-service (Hệ thống Quản lý Đặt phòng Khách sạn)

Hệ thống đặt phòng khách sạn trực tuyến áp dụng kiến trúc **Microservices / SOA** kết hợp **Monorepo** và **API Gateway**:

| Microservice / Ứng dụng | Công nghệ | Cổng (Port) | Chức năng chính |
| :--- | :--- | :---: | :--- |
| **API Gateway** | FastAPI / Nginx Reverse Proxy | `8080` | Điểm truy cập duy nhất định tuyến động, gom cụm CORS, bảo vệ backend |
| **Hotel Service** | FastAPI + SQLAlchemy 2 + SQL Server | `8000` | Quản lý thông tin khách sạn, tiện nghi, quy tắc, hình ảnh |
| **User Service** | FastAPI + SQLAlchemy 2 + SQL Server | `8001` | Xác thực JWT 3 vai trò (Admin, Partner, Customer), phân quyền, hồ sơ người dùng |
| **Room Service** | FastAPI + SQLAlchemy 2 + SQL Server | `8002` | Quản lý hạng phòng, kho phòng vật lý, trạng thái phòng trống khả dụng |
| **Booking Service** | FastAPI + SQLAlchemy 2 + SQL Server | `8003` | Quy trình đặt phòng, khóa giữ chỗ 15 phút, chống Overbooking đồng thời |
| **Payment Service** | FastAPI + SQLAlchemy 2 + SQL Server | `8004` | Cổng thanh toán giả lập Sandbox, Webhook IPN Callback xác nhận thanh toán |
| **Notification Service** | FastAPI + RabbitMQ + SMTP | `8005` | Tiêu thụ message queue, gửi email HTML xác nhận kèm mã QR check-in |
| **Message Broker** | RabbitMQ + Management UI | `5672` / `15672` | Hàng đợi tin nhắn bất đồng bộ (`notification.*`) |
| **Admin Dashboard** | Next.js 16 + React 19 + TailwindCSS | `3000` | Giao diện quản trị toàn diện: Khách sạn, Phòng, Người dùng, Đơn đặt, Dòng tiền |

---

## 🌐 ĐỊNH TUYẾN TẬP TRUNG QUA API GATEWAY (`http://localhost:8080`)

Client (Web, Mobile, Admin Dashboard) chỉ cần gọi vào một cổng duy nhất **`http://localhost:8080/api/v1/...`**:

- 🔹 `/api/v1/auth/**`, `/api/v1/users/**`, `/api/v1/admin/**` ➔ `http://user-service:8001`
- 🔹 `/api/v1/hotels/**` ➔ `http://hotel-service:8000`
- 🔹 `/api/v1/rooms/**` ➔ `http://room-service:8002`
- 🔹 `/api/v1/bookings/**` ➔ `http://booking-service:8003`
- 🔹 `/api/v1/payments/**` ➔ `http://payment-service:8004`
- 🔹 `/api/v1/notifications/**` ➔ `http://notification-service:8005`
- 🔹 Gateway Health Check tổng quan: `GET http://localhost:8080/health`

---

## 💻 HƯỚNG DẪN KHỞI CHẠY TRÊN CỤC BỘ (LOCAL ENVIRONMENT)

Chạy trực tiếp trên máy tính phát triển (Windows / macOS / Linux) mà không bắt buộc dùng Docker.

### 1. Yêu cầu môi trường (Prerequisites)
- **Python**: Phiên bản 3.10 trở lên (`pip install -r requirements.txt`).
- **Node.js**: Phiên bản 18+ và công cụ `pnpm` (`npm install -g pnpm`).
- **Microsoft SQL Server**: Bản cài cục bộ (SQL Server Developer, Express, hoặc container MSSQL) đang mở cổng `1433` kèm driver `ODBC Driver 17 for SQL Server` hoặc `ODBC Driver 18 for SQL Server`.
- **RabbitMQ** (Tùy chọn): Mặc định hệ thống đã có cơ chế tự động chuyển sang REST fallback nếu chưa bật broker RabbitMQ cục bộ.

### 2. Khởi tạo Cơ sở dữ liệu (Database Setup)
Trước khi chạy lần đầu, hãy thực thi 6 script SQL sau trong SQL Server:
1. `services/hotel-service/database_update.sql` ➔ Tạo CSDL `hotel_service`
2. `services/user-service/database_init.sql` ➔ Tạo CSDL `user_service`
3. `services/room-service/database_init.sql` ➔ Tạo CSDL `room_service`
4. `services/booking-service/database_init.sql` ➔ Tạo CSDL `booking_service`
5. `services/payment-service/database_init.sql` ➔ Tạo CSDL `payment_service`
6. `services/notification-service/database_init.sql` ➔ Tạo CSDL `notification_service`

---

### 🚀 CÁCH 1: Chạy Tự Động Toàn Bộ Bằng 1 Lệnh (Khuyên Dùng Trên Windows)

Mở **PowerShell** tại thư mục gốc của dự án (`d:\System-Booking-service`) và chạy lệnh:

```powershell
.\start-services-local.ps1
```

> **Ghi chú**: Script sẽ tự động chạy ngầm toàn bộ 8 dịch vụ ngay bên trong terminal Antigravity (**không nhảy cửa sổ bên ngoài**), ghi log vào thư mục `logs/` và hiển thị bảng trạng thái:
> - **Kiểm tra trạng thái**: `.\status-services-local.ps1`
> - **Xem log trực tiếp**: `Get-Content logs\gateway.log -Wait` (hoặc tên service bất kỳ)
> - **Dừng toàn bộ dịch vụ**: `.\stop-services-local.ps1`

---

### 🛠️ CÁCH 2: Khởi Chạy Thủ Công Từng Dịch Vụ (Manual Startup)

Mở các Terminal riêng biệt cho từng service:

#### 🔹 Terminal 1: Hotel Service (Cổng 8000)
```powershell
cd services/hotel-service
python -m uvicorn src.main:app --reload --port 8000
```
- Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

#### 🔹 Terminal 2: User Service (Cổng 8001)
```powershell
cd services/user-service
python -m uvicorn src.main:app --reload --port 8001
```
- Swagger Docs: [http://localhost:8001/docs](http://localhost:8001/docs)

#### 🔹 Terminal 3: Room Service (Cổng 8002)
```powershell
cd services/room-service
python -m uvicorn src.main:app --reload --port 8002
```
- Swagger Docs: [http://localhost:8002/docs](http://localhost:8002/docs)

#### 🔹 Terminal 4: Booking Service (Cổng 8003)
```powershell
cd services/booking-service
python -m uvicorn src.main:app --reload --port 8003
```
- Swagger Docs: [http://localhost:8003/docs](http://localhost:8003/docs)

#### 🔹 Terminal 5: Payment Service (Cổng 8004)
```powershell
cd services/payment-service
python -m uvicorn src.main:app --reload --port 8004
```
- Swagger Docs: [http://localhost:8004/docs](http://localhost:8004/docs)

#### 🔹 Terminal 6: Notification Service (Cổng 8005)
```powershell
cd services/notification-service
python -m uvicorn src.main:app --reload --port 8005
```
- Swagger Docs: [http://localhost:8005/docs](http://localhost:8005/docs)

#### 🔹 Terminal 7: API Gateway (Cổng 8080)
```powershell
cd gateway
python -m uvicorn src.main:app --reload --port 8080
```
- Gateway Status: [http://localhost:8080](http://localhost:8080) | Health: [http://localhost:8080/health](http://localhost:8080/health)

#### 🔹 Terminal 8: Front-end Admin Dashboard (Cổng 3000)
```powershell
cd front-end
pnpm install
pnpm dev
```
- Giao diện Admin: [http://localhost:3000](http://localhost:3000)

---

## 🐳 HƯỚNG DẪN KHỞI CHẠY BẰNG DOCKER COMPOSE

Dành cho môi trường có cài đặt Docker Desktop và Docker Compose:

### 1. Chuẩn bị file `.env`
Đảm bảo file `.env` tại thư mục gốc có đầy đủ cấu hình (tham khảo mẫu tại [.env.example](file:///d:/System-Booking-service/.env.example)).

### 2. Khởi chạy 1 lệnh bằng Docker Compose
```bash
docker compose up -d --build
```

Container SQL Server và RabbitMQ sẽ tự động khởi động và liên kết các container:
- `sqlserver` (Port 1433)
- `rabbitmq` (Port 5672 & Dashboard 15672: `guest`/`guest`)
- `hotel-service` (Port 8000)
- `user-service` (Port 8001)
- `room-service` (Port 8002)
- `booking-service` (Port 8003)
- `payment-service` (Port 8004)
- `notification-service` (Port 8005)
- `api-gateway` (Port 8080)

---

## 🔑 TÀI KHOẢN VÀ ĐƯỜNG DẪN TRUY CẬP HỆ THỐNG

### Tài khoản đăng nhập Dashboard:
- **Tài khoản Quản trị viên (Admin)**: `admin@hotel.com` | Mật khẩu: `123456`
- **Tài khoản Đối tác khách sạn (Partner)**: `partner@hotel.com` | Mật khẩu: `123456`
- **Tài khoản Khách hàng (Customer)**: `customer@hotel.com` | Mật khẩu: `123456`

### Các trang quản trị trên Admin Dashboard:
- 🏨 **Quản lý Khách sạn**: [http://localhost:3000/Hotels](http://localhost:3000/Hotels)
- 🛏️ **Quản lý Hạng phòng & Phòng vật lý**: [http://localhost:3000/Rooms](http://localhost:3000/Rooms)
- 👥 **Quản lý Người dùng & Khóa tài khoản**: [http://localhost:3000/Users](http://localhost:3000/Users)
- 📅 **Quản lý Đơn đặt phòng**: [http://localhost:3000/Bookings](http://localhost:3000/Bookings)
- 💳 **Lịch sử Giao dịch & Dòng tiền**: [http://localhost:3000/Payments](http://localhost:3000/Payments)

---

## 📬 LUỒNG XỬ LÝ NOTIFICATION & MESSAGE QUEUE

1. **Khách đặt phòng & Thanh toán**:
   - Khi thanh toán thành công, `payment-service` hoặc `booking-service` phát tín hiệu vào RabbitMQ queue:
     - `notification.booking.confirmed`: Xác nhận đơn đặt phòng thành công.
     - `notification.payment.success`: Xác nhận thanh toán thành công.
     - `notification.booking.cancelled`: Thông báo hủy đơn và nhả phòng.
2. **Notification Service tiêu thụ và gửi Email**:
   - Background consumer lắng nghe các queue, giải mã payload và render template HTML email cao cấp.
   - Template tích hợp sẵn mã QR/Barcode check-in trực tuyến, mã booking, tên và địa chỉ khách sạn, ngày nhận/trả phòng, chi tiết giá và quy định lưu trú.
   - Lưu trữ vết lịch sử thông báo vào bảng `thong_bao` và `noi_dung_thong_bao` trong SQL Server.
