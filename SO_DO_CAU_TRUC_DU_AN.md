# 🗺️ BẢN ĐỒ CẤU TRÚC TOÀN DIỆN DỰ ÁN (PROJECT STRUCTURE MAP)
## Hệ Thống Quản Lý & Đặt Phòng Khách Sạn Trực Tuyến (`System-Booking-service`)
**Kiến trúc:** Microservices / SOA | Monorepo (Turborepo + pnpm) | API Gateway | Event-Driven (RabbitMQ) | Database-Per-Service (MS SQL Server)

---

## 📌 MỤC LỤC
1. [Tổng Quan Kiến Trúc Hệ Thống](#1-tổng-quan-kiến-trúc-hệ-thống)
2. [Sơ Đồ Kiến Trúc Tổng Thể (Mermaid Architecture Diagram)](#2-sơ-đồ-kiến-trúc-tổng-thể)
3. [Cây Thư Mục Toàn Dự Án (Comprehensive Directory Tree)](#3-cây-thư-mục-toàn-dự-án)
4. [Kiến Trúc Chi Tiết Từng Phân Hệ](#4-kiến-trúc-chi-tiết-từng-phân-hệ)
   - [4.1. API Gateway (Port 8080)](#41-api-gateway-port-8080)
   - [4.2. User Service (Port 8001)](#42-user-service-port-8001)
   - [4.3. Hotel Service (Port 8000)](#43-hotel-service-port-8000)
   - [4.4. Room Service (Port 8002)](#44-room-service-port-8002)
   - [4.5. Booking Service (Port 8003)](#45-booking-service-port-8003)
   - [4.6. Payment Service (Port 8004)](#46-payment-service-port-8004)
   - [4.7. Notification Service (Port 8005)](#47-notification-service-port-8005)
   - [4.8. Front-end Monorepo (Port 3000 & 3001)](#48-front-end-monorepo)
5. [Mô Hình Dữ Liệu & Ma Trận Cơ Sở Dữ Liệu (Database-per-Service)](#5-mô-hình-dữ-liệu--ma-trận-cơ-sở-dữ-liệu)
6. [Luồng Tương Tác Nghiệp Vụ Chính (Core Business Sequence Flow)](#6-luồng-tương-tác-nghiệp-vụ-chính)
7. [Hạ Tầng, Định Tuyến & Bảng Cổng (Port Mapping Matrix)](#7-hạ-tầng-định-tuyến--bảng-cổng)
8. [Hướng Dẫn Vận Hành & Khởi Chạy](#8-hướng-dẫn-vận-hành--khởi-chạy)

---

## 1. TỔNG QUAN KIẾN TRÚC HỆ THỐNG

Hệ thống được thiết kế theo các nguyên tắc chuẩn của **Kiến trúc Hướng dịch vụ (SOA) / Microservices**:
- **Single Entry Point (API Gateway Pattern):** Toàn bộ client chỉ kết nối qua cổng duy nhất `8080`. Gateway phụ trách Reverse Proxy, giải phóng CORS, xác thực và gom routing.
- **Database-per-Service:** Mỗi microservice sở hữu một database Microsoft SQL Server riêng biệt, không đọc/ghi chéo dữ liệu trực tiếp:
  - `user_service`, `hotel_service`, `room_service`, `booking_service`, `payment_service`, `notification_service`.
- **Event-Driven Architecture (Message Broker):** Sử dụng **RabbitMQ** để xử lý giao tiếp bất đồng bộ giữa Payment, Booking và Notification (gửi email hóa đơn, vé điện tử kèm QR Code check-in).
- **Concurrency Control & Room Locking:** Booking Service tích hợp cơ chế khóa giữ chỗ tạm thời (Hold Expire 15 phút) và kiểm tra giao thoa ngày (`overlap`) nhằm triệt tiêu hiện tượng Overbooking.
- **Frontend Monorepo (Turborepo + pnpm):** Quản lý tập trung 2 ứng dụng web (Next.js 16, React 19, TailwindCSS v4) và các thư viện dùng chung (types, api-client, ui components).

---

## 2. SƠ ĐỒ KIẾN TRÚC TỔNG THỂ

### 2.1. Sơ đồ các tầng kiến trúc (High-Level Architecture)

```mermaid
graph TD
    subgraph CLIENT_TIER["🖥️ Client Tier (Front-end Monorepo)"]
        CustomerWeb["Customer Web App\n(Next.js 16 - Port 3001)\n[Tìm kiếm, Xem phòng, Checkout, E-Ticket]"]
        AdminDashboard["Admin Dashboard\n(Next.js 16 - Port 3000)\n[Quản trị Khách sạn, Phòng, Users, Booking, Doanh thu]"]
    end

    subgraph GATEWAY_TIER["🚪 API Gateway Tier"]
        Gateway["API Gateway Proxy\n(FastAPI / Nginx - Port 8080)\n- Dynamic Reverse Routing\n- CORS Centralization\n- Health Monitoring"]
    end

    subgraph BACKEND_SERVICES["⚙️ Microservices Tier (FastAPI + SQLAlchemy 2)"]
        UserService["User Service\n(Port 8001)\nJWT IAM, Auth, Profile"]
        HotelService["Hotel Service\n(Port 8000)\nHotel Profile, Amenities, Policies"]
        RoomService["Room Service\n(Port 8002)\nRoom Types, Inventory, Availability"]
        BookingService["Booking Service\n(Port 8003)\nBooking Logic, 15m Hold Lock"]
        PaymentService["Payment Service\n(Port 8004)\nSandbox IPN, MoMo, VNPay"]
        NotificationService["Notification Service\n(Port 8005)\nRabbitMQ Consumer, Mailer + QR"]
    end

    subgraph EVENT_BROKER["📬 Message Broker Tier"]
        RabbitMQ[("RabbitMQ Broker (5672/15672)\nExchanges: booking-exchange, payment-exchange\nQueues: notification.*")]
    end

    subgraph DATA_TIER["🗄️ Database Tier (MS SQL Server 2022 - Port 1433)"]
        DB_User[("user_service DB")]
        DB_Hotel[("hotel_service DB")]
        DB_Room[("room_service DB")]
        DB_Booking[("booking_service DB")]
        DB_Payment[("payment_service DB")]
        DB_Notification[("notification_service DB")]
    end

    subgraph EXTERNAL_TIER["🌐 External Services Tier"]
        SMTPMail["SMTP Email Server\n(HTML Ticket + QR Code)"]
    end

    %% Client -> Gateway
    CustomerWeb -->|HTTP / REST| Gateway
    AdminDashboard -->|HTTP / REST| Gateway

    %% Gateway -> Services
    Gateway -->|/api/v1/auth, /users, /admin| UserService
    Gateway -->|/api/v1/hotels| HotelService
    Gateway -->|/api/v1/rooms| RoomService
    Gateway -->|/api/v1/bookings| BookingService
    Gateway -->|/api/v1/payments| PaymentService
    Gateway -->|/api/v1/notifications| NotificationService

    %% Inter-service Sync HTTP
    BookingService -.->|HTTP: Validate Room| RoomService
    PaymentService -.->|HTTP: Confirm Status| BookingService

    %% Async RabbitMQ
    BookingService -->|Publish Events| RabbitMQ
    PaymentService -->|Publish Events| RabbitMQ
    RabbitMQ -->|Consume Events| NotificationService

    %% Services -> DB
    UserService --> DB_User
    HotelService --> DB_Hotel
    RoomService --> DB_Room
    BookingService --> DB_Booking
    PaymentService --> DB_Payment
    NotificationService --> DB_Notification

    %% Notification -> External
    NotificationService --> SMTPMail
```

---

## 3. CÂY THƯ MỤC TOÀN DỰ ÁN

```text
D:\System-Booking-service/
│
├── .env                                  # File biến môi trường toàn cục (Local runtime)
├── .env.example                          # Template cấu hình mẫu cho môi trường
├── .gitignore                            # Quy tắc bỏ qua file của Git (node_modules, logs, venv...)
├── .pids.json                            # Lưu PID các tiến trình đang chạy ngầm trên máy local
├── docker-compose.yml                    # Cấu hình khởi chạy toàn bộ 9 container (MSSQL, RabbitMQ, 6 Services, Gateway)
├── requirements.txt                      # Thư viện Python cấp độ root dùng cho script kiểm tra
├── setup-environment.ps1                 # Script tự động cài đặt môi trường (Python, Node.js, pnpm, pip)
├── init-databases-local.ps1              # Script khởi tạo 6 CSDL trên SQL Server cục bộ tự động
├── start-services-local.ps1              # Script khởi chạy ngầm 9 dịch vụ bằng 1 lệnh duy nhất
├── status-services-local.ps1             # Script kiểm tra trạng thái hoạt động & port của từng service
├── stop-services-local.ps1               # Script dừng sạch toàn bộ hệ thống & giải phóng port
├── README.md                             # Tài liệu tổng quan dự án & hướng dẫn setup
├── SO_DO_CAU_TRUC_DU_AN.md               # [File hiện tại] Bản đồ & sơ đồ cấu trúc toàn diện của dự án
│
├── contracts/                            # Hợp đồng giao tiếp liên dịch vụ (Schema contracts / Protobuf / OpenApi)
│   └── .gitkeep
│
├── docs/                                 # Tài liệu đặc tả phân tích thiết kế, biểu đồ DFD, ERD, Rubric
│   ├── DFD_Booking_muc1.png              # Sơ đồ luồng dữ liệu Booking mức 1
│   ├── DFD_Booking_muc2.png              # Sơ đồ luồng dữ liệu Booking mức 2
│   ├── DFD_Hotel_muc1.drawio             # Thiết kế DFD Hotel Service mức 1
│   ├── DFD_hotel_muc2.drawio             # Thiết kế DFD Hotel Service mức 2
│   ├── DFD_Payment_muc1.png              # Sơ đồ luồng dữ liệu Payment mức 1
│   ├── DFD_Payment_muc2.png              # Sơ đồ luồng dữ liệu Payment mức 2
│   ├── DFD_room_muc1.drawio              # Thiết kế DFD Room Service mức 1
│   ├── DFD_room_muc2.drawio              # Thiết kế DFD Room Service mức 2
│   ├── ERD.drawio                        # Sơ đồ thực thể liên kết (Entity Relationship Diagram)
│   ├── notification-service-DFD-1.drawio # DFD Notification Service mức 1
│   ├── notification-service-DFD-2.drawio # DFD Notification Service mức 2
│   ├── user-server-DFD1.drawio           # DFD User Service mức 1
│   ├── user-service-DFD-2.drawio         # DFD User Service mức 2
│   ├── PLAN_DAT_DIEM_10_RUBRIC.md        # Kế hoạch hành động chi tiết đạt điểm tối đa môn KT Hướng Dịch Vụ
│   ├── Template_VN (1).dotx              # Template văn bản báo cáo theo định dạng trường
│   └── HoangQuan/                        # Các bản vẽ chi tiết phân hệ của thành viên Hoàng Quân
│
├── front-end/                            # Monorepo Giao diện Khách hàng & Quản trị viên (Turborepo + pnpm)
│   ├── package.json                      # Cấu hình root workspace npm/pnpm
│   ├── pnpm-workspace.yaml               # Định nghĩa các package con trong monorepo (apps/*, packages/*)
│   ├── pnpm-lock.yaml                    # Khóa phiên bản dependencies front-end chính xác
│   ├── turbo.json                        # Cấu hình pipeline build/lint/dev của Turborepo
│   │
│   ├── apps/                             # Các ứng dụng web đầu cuối (End-user Applications)
│   │   ├── admin-dashboard/              # Trang Quản trị Hệ thống (Next.js 16, App Router - Port 3000)
│   │   │   ├── package.json
│   │   │   ├── tsconfig.json
│   │   │   ├── postcss.config.mjs
│   │   │   ├── .env.local                # Biến môi trường kết nối API Gateway (http://localhost:8080)
│   │   │   └── src/
│   │   │       ├── app/                  # Các tuyến đường giao diện (Next.js App Router)
│   │   │       │   ├── layout.tsx        # Khung giao diện dùng chung (Admin layout)
│   │   │       │   ├── page.tsx          # Dashboard tổng quan & thống kê
│   │   │       │   ├── globals.css       # Style TailwindCSS
│   │   │       │   ├── login/            # Màn hình đăng nhập Quản trị viên
│   │   │       │   ├── Hotels/           # Quản lý khách sạn (Duyệt, Thêm, Sửa, Xóa)
│   │   │       │   ├── Rooms/            # Quản lý hạng phòng & kho phòng vật lý
│   │   │       │   ├── Users/            # Quản lý tài khoản, phân quyền, khóa người dùng
│   │   │       │   ├── Bookings/         # Quản lý đơn đặt phòng & theo dõi trạng thái
│   │   │       │   └── Payments/         # Lịch sử giao dịch, dòng tiền & trạng thái thanh toán
│   │   │       ├── components/
│   │   │       │   └── Navbar.tsx        # Thanh điều hướng quản trị
│   │   │       └── lib/
│   │   │           └── api.ts            # Client gọi API vào Gateway
│   │   │
│   │   └── customer-web/                 # Ứng dụng Web Khách hàng (Next.js 16, App Router - Port 3001)
│   │       ├── package.json
│   │       ├── tsconfig.json
│   │       ├── postcss.config.mjs
│   │       ├── .env.local                # Biến môi trường kết nối API Gateway (http://localhost:8080)
│   │       └── src/
│   │           ├── app/
│   │           │   ├── layout.tsx        # Root Layout, bọc AuthContext & Header/Footer
│   │           │   ├── page.tsx          # Trang chủ: Hero Banner, Search Bar, Danh sách khách sạn nổi bật
│   │           │   ├── globals.css       # Style TailwindCSS v4
│   │           │   ├── search/           # Trang kết quả tìm kiếm với bộ lọc địa điểm, ngày, giá
│   │           │   ├── hotels/[id]/      # Trang chi tiết khách sạn, hình ảnh, tiện nghi & bảng chọn phòng
│   │           │   └── booking/
│   │           │       ├── checkout/     # Màn hình thanh toán, nhập thông tin khách, chọn ví/thẻ
│   │           │       └── success/      # Trang hoàn tất đặt phòng & hiển thị E-Ticket kèm mã QR
│   │           ├── components/
│   │           │   ├── Navbar.tsx        # Header định vị, menu đăng nhập/đăng ký
│   │           │   ├── Footer.tsx        # Chân trang
│   │           │   ├── SearchBar.tsx     # Bộ tìm kiếm động (Địa điểm, Check-in, Check-out, Khách)
│   │           │   ├── HotelCard.tsx     # Card hiển thị thông tin tóm tắt khách sạn
│   │           │   ├── QRCode.tsx        # Component render mã QR Check-in động
│   │           │   └── AuthModal.tsx     # Popup đăng nhập / đăng ký tài khoản trực tuyến
│   │           ├── context/
│   │           │   └── AuthContext.tsx   # Quản lý trạng thái phiên đăng nhập của người dùng
│   │           └── lib/
│   │               ├── api.ts            # Axios / Fetch client tương tác qua API Gateway
│   │               └── utils.ts          # Các hàm format ngày tháng, tiền tệ VNĐ
│   │
│   └── packages/                         # Các gói thư viện tái sử dụng nội bộ (Shared Packages)
│       ├── api-client/                   # SDK wrapper gọi API tập trung chuẩn TypeScript
│       ├── types/                        # Khai báo kiểu dữ liệu chung (Hotel, Room, Booking, User, Payment)
│       ├── ui/                           # Thư viện linh kiện giao diện tái sử dụng (Button, Input, Modal, Badge)
│       ├── config-eslint/                # Cấu hình Lint chuẩn chung cho các ứng dụng
│       ├── config-tailwind/              # Cấu hình TailwindCSS và theme màu sắc hệ thống
│       └── config-typescript/            # Cấu hình `tsconfig.base.json` thống nhất
│
├── gateway/                              # API Gateway tập trung (Port 8080)
│   ├── Dockerfile                        # Dockerfile đóng gói container API Gateway
│   ├── requirements.txt                  # Dependencies: FastAPI, httpx, uvicorn, pydantic-settings
│   ├── nginx.conf                        # Cấu hình Reverse Proxy Nginx tùy chọn
│   ├── .env.example                      # Cấu hình mẫu URL các backend service
│   └── src/
│       └── main.py                       # Reverse proxy động phân giải tiền tố /api/v1/**, xử lý CORS, Health check
│
├── infrastructure/                       # Kịch bản triển khai & cấu hình hạ tầng
│   ├── sqlserver/
│   │   ├── entrypoint.sh                 # Entrypoint khởi động MSSQL trong Docker
│   │   └── init-db.sh                    # Tự động thực thi 6 script SQL tạo CSDL khi container khởi chạy
│   └── .gitkeep
│
├── logs/                                 # Lưu trữ log vận hành thời gian thực của các dịch vụ chạy ngầm
│   ├── gateway.log                       # Log API Gateway (Port 8080)
│   ├── hotel-service.log                 # Log Hotel Service (Port 8000)
│   ├── user-service.log                  # Log User Service (Port 8001)
│   ├── room-service.log                  # Log Room Service (Port 8002)
│   ├── booking-service.log               # Log Booking Service (Port 8003)
│   ├── payment-service.log               # Log Payment Service (Port 8004)
│   ├── notification-service.log          # Log Notification Service (Port 8005)
│   ├── customer-web.log                  # Log Customer Web (Port 3001)
│   └── admin-dashboard.log               # Log Admin Dashboard (Port 3000)
│
├── orchestration/                        # Kịch bản điều phối quy trình phân tán
│   └── .gitkeep
│
├── services/                             # Các Microservices nghiệp vụ Backend (FastAPI + SQLAlchemy)
│   │
│   ├── hotel-service/                    # 1. Khách sạn & Tiện ích (Port 8000)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── database_update.sql           # Script T-SQL khởi tạo CSDL `hotel_service`
│   │   ├── alembic/                      # Cấu hình Database Migration bằng Alembic
│   │   └── src/
│   │       ├── main.py                   # Khởi chạy FastAPI app, cấu hình CORS, Auto-seed DB
│   │       ├── api/
│   │       │   ├── dependencies.py       # Dependency get_db, kiểm tra quyền Partner/Admin
│   │       │   └── v1/
│   │       │       ├── router.py         # Router tổng hợp v1
│   │       │       └── endpoints/
│   │       │           ├── hotels.py     # CRUD khách sạn, tìm kiếm lọc theo tỉnh/thành, rating
│   │       │           ├── amenities.py  # Quản lý danh mục & chi tiết tiện nghi khách sạn
│   │       │           ├── policies.py   # Quy tắc, thời gian nhận/trả phòng, chính sách hủy
│   │       │           └── images.py     # Quản lý thư viện hình ảnh khách sạn
│   │       ├── core/
│   │       │   ├── config.py             # Cấu hình kết nối DB `hotel_service` & Port 8000
│   │       │   ├── database.py           # Thiết lập SQLAlchemy engine & session
│   │       │   └── security.py           # Tiện ích giải mã token JWT
│   │       ├── models/                   # SQLAlchemy ORM Entities
│   │       │   ├── khach_san.py          # Bảng `khach_san`
│   │       │   ├── thong_tin_khach_san.py# Bảng `thong_tin_khach_san`
│   │       │   ├── hinh_anh_khach_san.py # Bảng `hinh_anh_khach_san`
│   │       │   ├── quy_tac_khach_san.py  # Bảng `quy_tac_khach_san`
│   │       │   ├── danh_muc_tien_nghi.py # Bảng `danh_muc_tien_nghi`
│   │       │   └── chi_tiet_tien_nghi.py # Bảng `chi_tiet_tien_nghi`
│   │       ├── repositories/             # Tách tầng Repository thao tác truy vấn
│   │       │   └── hotel_repository.py
│   │       ├── schemas/                  # Pydantic Schemas (DTO)
│   │       │   └── hotel_schema.py
│   │       └── services/                 # Nghiệp vụ xử lý
│   │           └── hotel_service.py
│   │
│   ├── user-service/                     # 2. Định danh & Phân quyền IAM (Port 8001)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── database_init.sql             # Script T-SQL khởi tạo CSDL `user_service` & dữ liệu mẫu
│   │   ├── so_do_cau_truc_USER_SERVICE.md# Tài liệu kiến trúc chuyên biệt cho User Service
│   │   └── src/
│   │       ├── main.py                   # Khởi chạy FastAPI app, cấu hình CORS, Auto-seed DB
│   │       ├── api/
│   │       │   ├── dependencies.py       # Giải mã JWT Bearer Token, kiểm tra tài khoản bị khóa
│   │       │   └── v1/
│   │       │       ├── router.py         # Router tổng hợp v1
│   │       │       └── endpoints/
│   │       │           ├── auth.py       # Đăng ký (/register), Đăng nhập (/login), Refresh Token (/refresh)
│   │       │           ├── users.py      # Lấy & cập nhật hồ sơ cá nhân (/me, /{id})
│   │       │           └── admin.py      # Quản trị viên quản lý danh sách, Khóa/Mở khóa user
│   │       ├── core/
│   │       │   ├── config.py             # Cấu hình CSDL `user_service`, Secret Key, Expiration
│   │       │   ├── database.py           # Kết nối SQLAlchemy
│   │       │   └── security.py           # Tạo hash mật khẩu, kiểm tra password, sinh JWT
│   │       ├── models/
│   │       │   ├── tai_khoan.py          # Bảng `tai_khoan` (username, email, role ADMIN/PARTNER/CUSTOMER, status)
│   │       │   └── nguoi_dung.py         # Bảng `nguoi_dung` (họ tên, ngày sinh, cccd, avatar, địa chỉ)
│   │       ├── schemas/
│   │       │   ├── auth_schema.py        # DTO Đăng ký, Đăng nhập, Trả về Token
│   │       │   └── user_schema.py        # DTO Thông tin người dùng, Cập nhật hồ sơ, Phân trang
│   │       └── services/
│   │           ├── auth_service.py       # Logic xác thực, kiểm tra trùng lặp email/username
│   │           └── user_service.py       # Logic thao tác với hồ sơ người dùng
│   │
│   ├── room-service/                     # 3. Quản lý Hạng Phòng & Tồn Kho Phòng (Port 8002)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── database_init.sql             # Script T-SQL khởi tạo CSDL `room_service`
│   │   └── src/
│   │       ├── main.py                   # Khởi chạy FastAPI app, CORS, Auto-seed DB
│   │       ├── api/v1/
│   │       │   ├── dependencies.py       # Dependency get_db, require_partner_or_admin
│   │       │   ├── router.py             # Router tổng hợp
│   │       │   └── endpoints/
│   │       │       ├── room_types.py     # CRUD loại phòng, giá cơ bản, sức chứa khách
│   │       │       └── rooms.py          # CRUD phòng vật lý, Batch tạo số phòng, Tra cứu phòng trống
│   │       ├── core/
│   │       │   ├── config.py             # Kết nối CSDL `room_service`
│   │       │   ├── database.py
│   │       │   └── security.py
│   │       ├── models/
│   │       │   ├── loai_phong.py         # Bảng `loai_phong` (giá cơ bản, diện tích, sức chứa)
│   │       │   ├── phong.py              # Bảng `phong` (số phòng P.101, tầng, trạng thái HOAT_DONG/BAO_TRI)
│   │       │   ├── tien_ich_phong.py     # Bảng `tien_ich_phong`
│   │       │   ├── quy_tac_phong.py      # Bảng `quy_tac_phong`
│   │       │   └── khuyen_mai_phong.py   # Bảng `khuyen_mai_phong`
│   │       ├── schemas/
│   │       │   ├── room_type_schema.py   # DTO Hạng phòng
│   │       │   └── room_schema.py        # DTO Phòng vật lý & Batch create
│   │       └── services/
│   │           ├── room_type_service.py  # Xử lý nghiệp vụ loại phòng
│   │           └── room_service.py       # Xử lý kiểm tra tồn kho & phòng trống khả dụng
│   │
│   ├── booking-service/                  # 4. Quản lý Đơn Đặt Phòng & Chống Trùng (Port 8003)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── database_init.sql             # Script T-SQL khởi tạo CSDL `booking_service`
│   │   └── src/
│   │       ├── main.py                   # Khởi chạy FastAPI app, CORS, Auto-seed DB
│   │       ├── api/v1/
│   │       │   ├── dependencies.py       # Dependency get_db, trích xuất user token
│   │       │   ├── router.py
│   │       │   └── endpoints/
│   │       │       └── bookings.py       # API Tạo booking, Hủy booking, Tra cứu đơn
│   │       ├── core/
│   │       │   ├── config.py             # CSDL `booking_service`, RabbitMQ config, thời gian giữ chỗ (15 phút)
│   │       │   ├── database.py
│   │       │   ├── publisher.py          # RabbitMQ Publisher (Bắn event thông báo booking)
│   │       │   └── security.py
│   │       ├── models/
│   │       │   ├── dat_phong.py          # Bảng `dat_phong` (mã booking, checkin, checkout, tổng tiền, trạng thái)
│   │       │   ├── chi_tiet_dat_phong.py # Bảng `chi_tiet_dat_phong` (gắn kết số phòng vật lý)
│   │       │   ├── thong_tin_khach_o.py  # Bảng `thong_tin_khach_o` (họ tên, email, sdt khách lưu trú)
│   │       │   └── nhat_ky_booking.py    # Bảng `nhat_ky_booking` (Audit trail lịch sử đổi trạng thái)
│   │       ├── schemas/
│   │       │   └── booking_schema.py     # DTO Booking request/response
│   │       └── services/
│   │           └── booking_service.py    # Thuật toán chống Overbooking, Khóa giữ chỗ 15 phút
│   │
│   ├── payment-service/                  # 5. Thanh Toán Giả Lập & Xử Lý Giao Dịch (Port 8004)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── database_init.sql             # Script T-SQL khởi tạo CSDL `payment_service`
│   │   └── src/
│   │       ├── main.py                   # Khởi chạy FastAPI app, CORS, Auto-seed DB
│   │       ├── api/v1/
│   │       │   ├── dependencies.py
│   │       │   ├── router.py
│   │       │   └── endpoints/
│   │       │       └── payments.py       # API /create-payment, /simulate-ipn, Tra cứu & Thống kê doanh thu
│   │       ├── core/
│   │       │   ├── config.py             # CSDL `payment_service`, RabbitMQ config
│   │       │   ├── database.py
│   │       │   ├── publisher.py          # RabbitMQ Publisher (Bắn event payment.success)
│   │       │   └── security.py
│   │       ├── models/
│   │       │   ├── thanh_toan.py         # Bảng `thanh_toan` (mã giao dịch, số tiền, hình thức VNPAY/MOMO, trạng thái)
│   │       │   ├── hoan_tien.py          # Bảng `hoan_tien` (ghi nhận giao dịch refund)
│   │       │   └── giao_dich_otp.py      # Bảng `giao_dich_otp` (mã OTP xác thực thanh toán, thời gian hết hạn)
│   │       ├── schemas/
│   │       │   └── payment_schema.py     # DTO Thanh toán, IPN simulation, thống kê
│   │       └── services/
│   │           └── payment_service.py    # Kích hoạt cập nhật đơn đặt sang CONFIRMED và kích hoạt email
│   │
│   └── notification-service/             # 6. Gửi Email, Mã QR Check-in & Thông Báo (Port 8005)
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── database_init.sql             # Script T-SQL khởi tạo CSDL `notification_service`
│       └── src/
│           ├── main.py                   # Khởi chạy FastAPI app, khởi động background RabbitMQ consumer
│           ├── api/v1/
│           │   ├── router.py
│           │   └── endpoints/
│           │       └── notifications.py  # API gửi trực tiếp /send, xem thống kê /stats, tra cứu lịch sử
│           ├── core/
│           │   ├── config.py             # CSDL `notification_service`, RabbitMQ settings, SMTP config
│           │   ├── database.py
│           │   ├── rabbitmq_consumer.py  # Consumer lắng nghe queues: booking.confirmed, payment.success
│           │   ├── templates.py          # Render Template HTML Email sang trọng kèm mã QR check-in
│           │   └── email_sender.py       # Module gửi email SMTP (hỗ trợ Mock Mode hoặc SMTP thật)
│           ├── models/
│           │   ├── thong_bao.py          # Bảng `thong_bao` (kênh gửi, người nhận, loại thông báo, trạng thái)
│           │   └── noi_dung_thong_bao.py # Bảng `noi_dung_thong_bao` (tiêu đề, nội dung HTML chi tiết)
│           ├── schemas/
│           │   └── notification_schema.py# DTO Request/Response gửi & lịch sử thông báo
│           └── services/
│               └── notification_service.py# Nghiệp vụ xử lý tiêu thụ queue và ghi vết thông báo
│
└── test/                                 # Kịch bản kiểm thử tích hợp (End-to-End & Integration Testing)
    ├── .gitkeep
    └── test_gateway_flow.py              # Test script kiểm thử toàn chuỗi qua Gateway 8080: Booking -> Payment -> IPN
```

---

## 4. KIẾN TRÚC CHI TIẾT TỪNG PHÂN HỆ

### 4.1. API Gateway (Port `8080`)
- **Nhiệm vụ:** Là cửa ngõ duy nhất (Reverse Proxy) tiếp nhận toàn bộ lưu lượng HTTP từ Front-end và Client bên ngoài.
- **Tính năng nổi bật:**
  - Định tuyến ngược động dựa trên tiền tố đường dẫn:
    - `/api/v1/auth/**`, `/api/v1/users/**`, `/api/v1/admin/**` $\rightarrow$ `User Service (8001)`
    - `/api/v1/hotels/**` $\rightarrow$ `Hotel Service (8000)`
    - `/api/v1/rooms/**` $\rightarrow$ `Room Service (8002)`
    - `/api/v1/bookings/**` $\rightarrow$ `Booking Service (8003)`
    - `/api/v1/payments/**` $\rightarrow$ `Payment Service (8004)`
    - `/api/v1/notifications/**` $\rightarrow$ `Notification Service (8005)`
  - Tập trung xử lý **CORS (Cross-Origin Resource Sharing)**, loại bỏ lỗi CORS trên các trình duyệt.
  - Cung cấp endpoint giám sát sức khỏe phân tán: `GET /health` (tự động ping kiểm tra trạng thái sống của toàn bộ 6 service con).

### 4.2. User Service (Port `8001`)
- **Nhiệm vụ:** Quản lý danh tính, xác thực và kiểm soát quyền truy cập (IAM - Identity & Access Management).
- **Cơ sở dữ liệu:** `user_service` trên SQL Server.
- **Vai trò người dùng:**
  - `ADMIN`: Quản trị viên toàn hệ thống (Duyệt khách sạn, quản lý người dùng, xem toàn bộ giao dịch).
  - `PARTNER`: Đối tác chủ khách sạn (Đăng tải khách sạn, thêm loại phòng, thiết lập giá và phòng trống).
  - `CUSTOMER`: Khách hàng (Tìm kiếm, đặt phòng, thanh toán, xem vé điện tử).
- **Cơ chế xác thực:** JWT (JSON Web Token) ký bằng thuật toán HS256, hỗ trợ `access_token` (hạn 60 phút) và `refresh_token` (hạn 7 ngày).

### 4.3. Hotel Service (Port `8000`)
- **Nhiệm vụ:** Quản lý toàn bộ thông tin đối tác khách sạn, tiện ích, chính sách lưu trú và hình ảnh truyền thông.
- **Cơ sở dữ liệu:** `hotel_service`.
- **Thực thể quản lý:**
  - `khach_san`: Tên, địa chỉ, định vị GPS (kinh độ, vĩ độ), trạng thái duyệt (`HOAT_DONG`, `TAM_DUNG`, `CHO_DUYET`, `DA_XOA`).
  - `thong_tin_khach_san`: Mô tả chi tiết, sao xếp hạng (1-5 sao), chính sách nhận phòng (14:00), trả phòng (12:00).
  - `hinh_anh_khach_san`: Danh mục URL hình ảnh thực tế của khách sạn.
  - `quy_tac_khach_san`: Chính sách thú cưng, hút thuốc, hủy phòng.
  - `danh_muc_tien_nghi` & `chi_tiet_tien_nghi`: Bể bơi vô cực, Spa, Wifi miễn phí, Buffet sáng...

### 4.4. Room Service (Port `8002`)
- **Nhiệm vụ:** Quản lý các hạng phòng (Room Types) và kho phòng vật lý (Physical Rooms), kiểm tra tình trạng phòng trống.
- **Cơ sở dữ liệu:** `room_service`.
- **Thực thể quản lý:**
  - `loai_phong`: Hạng phòng (Deluxe Ocean View, Superior King, Family Suite...), giá cơ bản một đêm, diện tích, sức chứa tối đa.
  - `phong`: Số phòng cụ thể (P.101, P.102, P.201...), trạng thái hiện tại (`HOAT_DONG`, `BAO_TRI`, `TAM_KHOA`).
  - `tien_ich_phong`, `quy_tac_phong`, `khuyen_mai_phong`.
- **Điểm đặc biệt:** Hỗ trợ API `batch create` tạo hàng loạt danh sách số phòng tự động cho khách sạn. Cung cấp API `/rooms/available` kiểm tra phòng trống theo khoảng ngày nhận/trả.

### 4.5. Booking Service (Port `8003`)
- **Nhiệm vụ:** Xử lý toàn bộ vòng đời của một đơn đặt phòng: Đặt chỗ $\rightarrow$ Giữ chỗ $\rightarrow$ Xác nhận $\rightarrow$ Hoàn tất / Hủy.
- **Cơ sở dữ liệu:** `booking_service`.
- **Cơ chế chống Overbooking (Tranh chấp phòng):**
  - Khi khách bấm đặt phòng, hệ thống gán trạng thái `PENDING_PAYMENT` và thiết lập mốc thời gian giữ chỗ (`han_giu_cho` = Thời điểm hiện tại + 15 phút).
  - Kiểm tra điều kiện giao thoa ngày giữa đơn mới và các đơn hiện hữu đang giữ chỗ hoặc đã xác nhận:
    $$\text{Đơn trùng lặp nếu: } (\text{CheckIn}_{\text{new}} < \text{CheckOut}_{\text{old}}) \land (\text{CheckOut}_{\text{new}} > \text{CheckIn}_{\text{old}})$$
  - Nếu trùng lịch, hệ thống lập tức từ chối với mã lỗi `409 Conflict`.
- **Tích hợp RabbitMQ:** Bắn event `notification.booking.cancelled` khi hết hạn giữ chỗ hoặc khách chủ động hủy đơn.

### 4.6. Payment Service (Port `8004`)
- **Nhiệm vụ:** Khởi tạo yêu cầu thanh toán, điều hướng tới cổng thanh toán giả lập Sandbox (VNPAY, MoMo, Thẻ tín dụng, Tiền mặt) và tiếp nhận IPN Callback.
- **Cơ sở dữ liệu:** `payment_service`.
- **Cơ chế kích hoạt tự động (Webhook / IPN):**
  - Khi nhận tín hiệu thanh toán thành công từ Webhook Sandbox, service chuyển trạng thái thanh toán sang `SUCCESS`.
  - Gọi HTTP nội bộ sang `booking-service` cập nhật trạng thái đơn sang `CONFIRMED`.
  - Publish message vào RabbitMQ queue `notification.payment.success` kèm thông tin booking để gửi email xác nhận.

### 4.7. Notification Service (Port `8005`)
- **Nhiệm vụ:** Tiêu thụ tin nhắn bất đồng bộ từ RabbitMQ, render nội dung HTML Email cao cấp kèm mã QR Code Check-in và gửi tới khách hàng.
- **Cơ sở dữ liệu:** `notification_service`.
- **Cơ chế hoạt động:**
  - Khởi chạy một Background Consumer Thread khi ứng dụng FastAPI start up.
  - Lắng nghe các sự kiện: `notification.booking.confirmed`, `notification.payment.success`, `notification.booking.cancelled`.
  - Sinh mã QR chứa nội dung JSON xác thực đặt phòng (`ma_booking`, `ten_khach`, `ngay_nhan_phong`).
  - Hỗ trợ chế độ `MOCK_EMAIL_SEND=True` (in log kiểm thử không tốn tài nguyên) hoặc SMTP thật (Gmail SMTP).
  - Lưu trữ toàn bộ vết lịch sử thông báo vào bảng `thong_bao` và `noi_dung_thong_bao`.

### 4.8. Front-end Monorepo
Quản lý trong thư mục `front-end/` thông qua **Turborepo** và **pnpm workspace**:
1. **Customer Web App (`apps/customer-web` - Port 3001):**
   - Ứng dụng web phục vụ khách hàng với giao diện hiện đại, chuẩn Responsive.
   - Luồng người dùng: Trang chủ $\rightarrow$ Tìm kiếm theo địa phương & ngày $\rightarrow$ Chi tiết khách sạn & chọn phòng $\rightarrow$ Checkout thanh toán $\rightarrow$ Nhận vé điện tử E-Ticket kèm mã QR.
2. **Admin Dashboard (`apps/admin-dashboard` - Port 3000):**
   - Trung tâm quản trị cho Admin và Partner.
   - Quản lý danh mục Khách sạn, Hạng phòng & Phòng, Người dùng, Danh sách Đơn đặt, và Báo cáo Doanh thu giao dịch.
3. **Thư viện nội bộ dùng chung (`packages/*`):**
   - `packages/types`: Khai báo TypeScript Interface chuẩn hóa toàn bộ entity của 6 backend services.
   - `packages/api-client`: SDK đóng gói các hàm gọi API thông qua Gateway.
   - `packages/ui`: Các UI Component tái sử dụng như Button, Card, Dialog, Badge...

---

## 5. MÔ HÌNH DỮ LIỆU & MA TRẬN CƠ SỞ DỮ LIỆU

Dự án áp dụng mô hình **Database-per-Service** với 6 CSDL độc lập chạy trên Microsoft SQL Server 2022:

| Cơ sở dữ liệu | Bảng chính (Tables) | Khóa chính / Khóa ngoại | Trách nhiệm lưu trữ dữ liệu |
| :--- | :--- | :--- | :--- |
| **`user_service`** | `tai_khoan`<br>`nguoi_dung` | `id_tai_khoan` (PK)<br>`id_nguoi_dung` (PK), `id_tai_khoan` (FK) | Tài khoản, mật khẩu băm, phân quyền vai trò (Admin, Partner, Customer), hồ sơ cá nhân. |
| **`hotel_service`** | `khach_san`<br>`thong_tin_khach_san`<br>`hinh_anh_khach_san`<br>`quy_tac_khach_san`<br>`danh_muc_tien_nghi`<br>`chi_tiet_tien_nghi` | `id_khach_san` (PK)<br>`id_tai_khoan` (Logic FK)<br>`id_thong_tin` (PK)<br>`id_hinh_anh` (PK)<br>`id_tien_nghi` (PK) | Thông tin khách sạn, địa chỉ, vị trí GPS, xếp hạng sao, thư viện ảnh và tiện nghi khách sạn. |
| **`room_service`** | `loai_phong`<br>`phong`<br>`tien_ich_phong`<br>`quy_tac_phong`<br>`khuyen_mai_phong` | `id_loai_phong` (PK)<br>`id_khach_san` (Logic FK)<br>`id_phong` (PK), `id_loai_phong` (FK) | Danh mục hạng phòng, sức chứa, giá gốc mỗi đêm, danh sách số phòng vật lý và trạng thái phòng. |
| **`booking_service`** | `dat_phong`<br>`chi_tiet_dat_phong`<br>`thong_tin_khach_o`<br>`nhat_ky_booking` | `id_dat_phong` (PK), `ma_booking` (UK)<br>`id_tai_khoan` (Logic FK)<br>`id_khach_san` (Logic FK)<br>`id_chi_tiet` (PK), `id_phong` (Logic FK) | Đơn đặt phòng, khoảng thời gian lưu trú, thời hạn giữ chỗ 15 phút, danh sách phòng chọn và vết kiểm toán. |
| **`payment_service`** | `thanh_toan`<br>`hoan_tien`<br>`giao_dich_otp` | `id_thanh_toan` (PK)<br>`id_dat_phong` (Logic FK)<br>`ma_giao_dich_gateway` (UK)<br>`id_hoan_tien` (PK)<br>`id_otp` (PK) | Giao dịch thanh toán, cổng thanh toán (VNPAY, MoMo), trạng thái (PENDING, SUCCESS), giao dịch hoàn tiền, OTP xác thực thanh toán. |
| **`notification_service`** | `thong_bao`<br>`noi_dung_thong_bao` | `id_thong_bao` (PK)<br>`id_noi_dung` (PK), `id_thong_bao` (FK) | Lịch sử thông báo gửi đi, kênh gửi (EMAIL/SMS), trạng thái gửi và nội dung HTML email kèm mã QR. |

---

## 6. LUỒNG TƯƠNG TÁC NGHIỆP VỤ CHÍNH

### Quy trình Đặt phòng $\rightarrow$ Giữ chỗ $\rightarrow$ Thanh toán $\rightarrow$ Gửi vé điện tử

```mermaid
sequenceDiagram
    autonumber
    actor User as Khách hàng (Customer Web)
    participant Gateway as API Gateway (8080)
    participant BookingSvc as Booking Service (8003)
    participant PaymentSvc as Payment Service (8004)
    participant Broker as RabbitMQ Broker (5672)
    participant NotiSvc as Notification Service (8005)
    participant MailSvr as Mail Server (SMTP)

    User->>Gateway: POST /api/v1/bookings\n{ id_khach_san, ngay_nhan, ngay_tra, rooms, khach_o }
    Gateway->>BookingSvc: Proxy Request
    Note over BookingSvc: 1. Kiểm tra Overbooking trùng ngày\n2. Gán hạn giữ chỗ hiện tại + 15 phút\n3. Trạng thái: PENDING_PAYMENT
    BookingSvc-->>Gateway: 201 Created { id_dat_phong, ma_booking, tong_tien }
    Gateway-->>User: Hiển thị màn hình Checkout & Đồng hồ đếm ngược 15 phút

    User->>Gateway: POST /api/v1/payments/create-payment\n{ id_dat_phong, ma_booking, phuong_thuc: 'VNPAY' }
    Gateway->>PaymentSvc: Proxy Request
    PaymentSvc-->>Gateway: 201 Created { ma_giao_dich_gateway, payment_url }
    Gateway-->>User: Điều hướng khách tới Cổng thanh toán Sandbox

    Note over User,PaymentSvc: Khách xác nhận thanh toán trên giao diện Sandbox
    PaymentSvc->>PaymentSvc: Nhận IPN Webhook: Trạng thái -> SUCCESS
    PaymentSvc->>Gateway: PATCH /api/v1/bookings/{id}/status -> CONFIRMED
    Gateway->>BookingSvc: Cập nhật trạng thái đơn thành công
    
    PaymentSvc->>Broker: Publish Event 'notification.payment.success'\n{ ma_booking, email, ho_ten, tong_tien, qr_data }
    Broker-->>NotiSvc: Consumer nhận message từ queue
    Note over NotiSvc: 1. Tạo hình ảnh QR Code Check-in\n2. Render Template HTML Email xác nhận\n3. Ghi vết vào CSDL notification_service
    NotiSvc->>MailSvr: Gửi Email xác nhận đơn kèm E-Ticket & QR Code
    MailSvr-->>User: Hộp thư khách nhận Email vé điện tử
```

---

## 7. HẠ TẦNG, ĐỊNH TUYẾN & BẢNG CỔNG

### 7.1. Bảng phân bổ cổng (Port Mapping)

| Phân hệ / Dịch vụ | Cổng Local (Port) | Giao thức | URL Truy cập Trực tiếp | URL Qua API Gateway (Khuyên dùng) |
| :--- | :---: | :---: | :--- | :--- |
| **API Gateway** | `8080` | HTTP | `http://localhost:8080` | `http://localhost:8080/health` |
| **Hotel Service** | `8000` | HTTP | `http://localhost:8000/docs` | `http://localhost:8080/api/v1/hotels/...` |
| **User Service** | `8001` | HTTP | `http://localhost:8001/docs` | `http://localhost:8080/api/v1/auth/...` |
| **Room Service** | `8002` | HTTP | `http://localhost:8002/docs` | `http://localhost:8080/api/v1/rooms/...` |
| **Booking Service** | `8003` | HTTP | `http://localhost:8003/docs` | `http://localhost:8080/api/v1/bookings/...` |
| **Payment Service** | `8004` | HTTP | `http://localhost:8004/docs` | `http://localhost:8080/api/v1/payments/...` |
| **Notification Service** | `8005` | HTTP | `http://localhost:8005/docs` | `http://localhost:8080/api/v1/notifications/...` |
| **RabbitMQ Dashboard** | `15672` | HTTP | `http://localhost:15672` *(guest/guest)* | Không qua Gateway |
| **RabbitMQ AMQP** | `5672` | AMQP | `amqp://guest:guest@localhost:5672/` | Không qua Gateway |
| **SQL Server 2022** | `1433` | TDS | `localhost:1433` *(sa / Password123!)* | Không qua Gateway |
| **Admin Dashboard** | `3000` | HTTP | `http://localhost:3000` | - |
| **Customer Web App** | `3001` | HTTP | `http://localhost:3001` | - |

---

## 8. HƯỚNG DẪN VẬN HÀNH & KHỞI CHẠY

Dự án cung cấp 3 cách vận hành linh hoạt tùy theo nhu cầu phát triển:

### 🌟 Cách 1: Khởi chạy ngầm toàn bộ 9 dịch vụ bằng 1 lệnh (Khuyên dùng khi dev local)
Hệ thống script PowerShell tự động giải phóng port, khởi chạy ngầm toàn bộ backend và frontend, ghi log vào thư mục `logs/`:
```powershell
# 1. Cài đặt thư viện tự động lần đầu:
.\setup-environment.ps1

# 2. Khởi tạo 6 CSDL trên SQL Server:
.\init-databases-local.ps1

# 3. Khởi chạy 9 dịch vụ ngầm:
.\start-services-local.ps1

# 4. Kiểm tra trạng thái các port và PID:
.\status-services-local.ps1

# 5. Dừng hệ thống khi không sử dụng:
.\stop-services-local.ps1
```

### 🐳 Cách 2: Khởi chạy bằng Docker Compose
Dành cho máy đã cài đặt Docker Desktop:
```bash
docker compose up -d --build
```
> Tự động dựng SQL Server (kèm script tự tạo 6 CSDL), RabbitMQ Broker, 6 Backend Microservices và API Gateway.

### 🧪 Cách 3: Chạy kịch bản kiểm thử tích hợp tự động (End-to-End Test)
Kiểm tra luồng đặt phòng, thanh toán và mô phỏng IPN qua API Gateway:
```powershell
python test/test_gateway_flow.py
```

---
*Tài liệu được khởi tạo và cập nhật tự động theo trạng thái mã nguồn thực tế của dự án.*