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
- 🔹 `/api/v1/rooms/**` ➔ `http://room-service:8002`
- 🔹 `/api/v1/bookings/**` ➔ `http://booking-service:8003`
- 🔹 `/api/v1/payments/**` ➔ `http://payment-service:8004`
- 🔹 `/api/v1/notifications/**` ➔ `http://notification-service:8005`
- 🔹 Gateway Health Check tổng quan: `GET http://localhost:8080/health`

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
| **Quản trị viên (Admin)** | `admin@hotel.com` | `123456` | Toàn quyền quản trị hệ thống, duyệt khách sạn, quản lý người dùng, xem doanh thu |
| **Đối tác (Partner)** | `partner@hotel.com` | `123456` | Quản lý khách sạn sở hữu, thêm hạng phòng, cập nhật phòng trống |
| **Khách hàng (Customer)** | `customer@hotel.com` | `123456` | Tìm kiếm phòng, đặt phòng trực tuyến, thanh toán, xem vé điện tử |

---

## 🌟 ĐƯỜNG DẪN TRUY CẬP CÁC PHÂN HỆ GIAO DIỆN

### 1. Ứng dụng Khách hàng (Customer Web App - Port 3001):
- 🏠 **Trang chủ & Tìm kiếm thông minh**: [http://localhost:3001](http://localhost:3001)
- 🔍 **Trang Kết quả tìm kiếm & Bộ lọc**: [http://localhost:3001/search](http://localhost:3001/search)
- 🏨 **Chi tiết khách sạn & Chọn phòng**: [http://localhost:3001/hotels/5](http://localhost:3001/hotels/5)
- 💳 **Trang Checkout / Đặt phòng**: [http://localhost:3001/booking/checkout](http://localhost:3001/booking/checkout)

### 2. Trang Quản trị (Admin Dashboard - Port 3000):
- 🏨 **Quản lý Khách sạn**: [http://localhost:3000/Hotels](http://localhost:3000/Hotels)
- 🛏️ **Quản lý Hạng phòng & Phòng vật lý**: [http://localhost:3000/Rooms](http://localhost:3000/Rooms)
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
   - Lưu trữ vết lịch sử thông báo vào bảng `thong_bao` và `noi_dung_thong_bao` trong SQL Server.
