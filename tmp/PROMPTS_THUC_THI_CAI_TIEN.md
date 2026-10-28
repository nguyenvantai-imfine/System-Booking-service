# BỘ PROMPT THỰC THI CẢI TIẾN HỆ THỐNG THEO THỨ TỰ ƯU TIÊN (P0 ➔ P3)

Tài liệu này được biên soạn để thực thi tuần tự các đầu việc cải tiến theo đúng lộ trình đã đề ra tại [KE_HOACH_CAI_TIEN_HE_THONG.md](file:///c:/Users/VanVi/.gemini/antigravity/brain/8eec6926-1957-404f-914c-e5aedba4e3d2/KE_HOACH_CAI_TIEN_HE_THONG.md).

Mỗi prompt được thiết kế **độc lập, đầy đủ ngữ cảnh, chỉ rõ file cần sửa, giải pháp chi tiết và tiêu chí nghiệm thu**, cho phép copy và thực thi trực tiếp từng bước mà không lo sót dữ liệu.

---

## 📑 MỤC LỤC BỘ PROMPT

- [GIAI ĐOẠN 1: P0 - BẢO MẬT NGHIÊM TRỌNG](#giai-đoan-1-p0---bảo-mật-nghiêm-trọng)
  - [Prompt 1 (P0.1): Bật lại mã hóa mật khẩu Bcrypt trong User Service](#prompt-1-p01-bật-lại-mã-hóa-mật-khẩu-bcrypt-trong-user-service)
  - [Prompt 2 (P0.2 & P0.3): Chặn lỗ hổng IDOR và Tài khoản INACTIVE trong User Service](#prompt-2-p02--p03-chặn-lỗ-hổng-idor-và-tài-khoản-inactive-trong-user-service)
  - [Prompt 3 (P0.4): Băm và bảo vệ mã OTP trong Payment Service](#prompt-3-p04-băm-và-bảo-vệ-mã-otp-trong-payment-service)
  - [Prompt 4 (P0.5): Che OTP trong thông báo & Chống XSS trong Email Template](#prompt-4-p05-che-otp-trong-thông-báo--chống-xss-trong-email-template)
  - [Prompt 5 (P0.6): Bổ sung Auth & Ownership Check cho Booking, Payment, Hotel](#prompt-5-p06-bổ-sung-auth--ownership-check-cho-booking-payment-hotel)
  - [Prompt 6 (P0.7): Siết chặt cấu hình CORS tại Gateway và tất cả Service](#prompt-6-p07-siết-chặt-cấu-hình-cors-tại-gateway-và-tất-cả-service)
- [GIAI ĐOẠN 2: P1 - LOGIC NGHIỆP VỤ & TÍNH ĐÚNG ĐẮN DỮ LIỆU](#giai-đoan-2-p1---logic-nghiệp-vụ--tính-đúng-đắn-dữ-liệu)
  - [Prompt 7 (P1.1): Lọc phòng trống theo khoảng ngày đối chiếu với Booking Service](#prompt-7-p11-lọc-phòng-trống-theo-khoảng-ngày-đối-chiếu-với-booking-service)
  - [Prompt 8 (P1.2): Xác thực giá phòng & dữ liệu phòng từ Room Service khi tạo Booking](#prompt-8-p12-xác-thực-giá-phòng--dữ-liệu-phòng-từ-room-service-khi-tạo-booking)
  - [Prompt 9 (P1.3 & P1.4): Đối soát số tiền thanh toán & Xử lý trạng thái khi xác nhận Booking lỗi](#prompt-9-p13--p14-đối-soát-số-tiền-thanh-toán--xử-lý-trạng-thái-khi-xác-nhận-booking-lỗi)
- [GIAI ĐOẠN 3: P2 - TÍCH HỢP GATEWAY & EVENT-DRIVEN BROKER](#giai-đoan-3-p2---tích-hợp-gateway--event-driven-broker)
  - [Prompt 10 (P2.1 & P2.2): Định tuyến Frontend qua Gateway và sửa lỗi route `room-types`](#prompt-10-p21--p22-định-tuyến-frontend-qua-gateway-và-sửa-lỗi-route-room-types)
  - [Prompt 11 (P2.3): Bổ sung thư viện `pika` cho Booking và Payment Service](#prompt-11-p23-bổ-sung-thư-viện-pika-cho-booking-và-payment-service)
  - [Prompt 12 (P2.4 & P2.5): Sửa lỗi 401 REST Fallback và hoàn thiện cấu hình gửi email SMTP](#prompt-12-p24--p25-sửa-lỗi-401-rest-fallback-và-hoàn-thiện-cấu-hình-gửi-email-smtp)
- [GIAI ĐOẠN 4: P3 - FRONTEND & CLEAN CODE](#giai-đoan-4-p3---frontend--clean-code)
  - [Prompt 13 (P3.1 & P3.2): Đồng bộ thuế/phí 10% và chuẩn hóa Enum phương thức thanh toán](#prompt-13-p31--p32-đồng-bộ-thuếphí-10-và-chuẩn-hóa-enum-phương-thức-thanh-toán)
  - [Prompt 14 (P3.3): Bỏ dữ liệu Mock ngầm, hiển thị lỗi thật và hoàn thiện luồng người dùng](#prompt-14-p33-bỏ-dữ-liệu-mock-ngầm-hiển-thị-lỗi-thật-và-hoàn-thiện-luồng-người-dùng)
  - [Prompt 15 (P3.4): Tinh chỉnh Admin Dashboard (Navbar, Sort phòng, Doanh thu thực)](#prompt-15-p34-tinh-chỉnh-admin-dashboard-navbar-sort-phòng-doanh-thu-thực)
  - [Prompt 16 (P3.5): Dọn dẹp Clean Code và tạo Script chạy tự động bộ 6 bài Test](#prompt-16-p35-dọn-dẹp-clean-code-và-tạo-script-chạy-tự-động-bộ-6-bài-test)

---

## GIAI ĐOẠN 1: P0 - BẢO MẬT NGHIÊM TRỌNG

### Prompt 1 (P0.1): Bật lại mã hóa mật khẩu Bcrypt trong User Service

```markdown
Bạn hãy thực hiện Task P0.1: Kích hoạt lại mã hóa mật khẩu bằng Bcrypt cho User Service.

### Ngữ cảnh & Vấn đề:
Hiện tại trong `services/user-service/src/core/security.py`, hàm `hash_password` đang comment đoạn code mã hóa và trả về plain text thô:
```python
def hash_password(password: str) -> str:
    # return bcrypt.hashpw(...)
    return password
```
Điều này khiến mật khẩu người dùng bị lưu trực tiếp dạng plaintext trong SQL Server (`tai_khoan.mat_khau_hash`).

### File cần sửa:
1. `services/user-service/src/core/security.py`
2. `services/user-service/src/services/auth_service.py`
3. `services/user-service/requirements.txt`

### Yêu cầu cụ thể:
1. Trong `requirements.txt`: Đảm bảo có `bcrypt>=4.0.0` và `passlib>=1.7.4`.
2. Trong `security.py`:
   - Mở lại logic băm mật khẩu `hash_password(password: str) -> str` sử dụng `bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')`.
   - Trong `verify_password(plain_password: str, hashed_password: str) -> bool`:
     - Kiểm tra nếu `hashed_password` bắt đầu bằng `$2` thì dùng `bcrypt.checkpw(...)`.
     - Giữ cơ chế fallback so sánh trực tiếp `plain_password == hashed_password` chỉ để tương thích với các tài khoản seed cũ chưa được cập nhật hash bcrypt.
3. Trong `auth_service.py`:
   - Xác nhận hàm `register` gọi `hash_password(req.mat_khau)` trước khi lưu vào CSDL.
   - Thêm cơ chế tự động nâng cấp hash: Khi người dùng đăng nhập thành công bằng mật khẩu plaintext cũ, tự động băm lại mật khẩu và cập nhật `mat_khau_hash` vào CSDL.

### Tiêu chí nghiệm thu:
- Tạo tài khoản mới qua `POST /api/v1/auth/register`, chuỗi trong DB bắt đầu bằng `$2b$12$...`.
- Đăng nhập tài khoản mới tạo và tài khoản seed cũ đều thành công.
```

---

### Prompt 2 (P0.2 & P0.3): Chặn lỗ hổng IDOR và Tài khoản INACTIVE trong User Service

```markdown
Bạn hãy thực hiện Task P0.2 và P0.3: Khắc phục lỗ hổng IDOR và chặn tài khoản INACTIVE trong User Service.

### Ngữ cảnh & Vấn đề:
1. **Lỗ hổng IDOR:** Trong `services/user-service/src/api/v1/endpoints/users.py`, API `GET /api/v1/users/{user_id}` nhận `user_id` từ URL và trả về thông tin profile qua `UserService.get_me(db, user_id)` mà không kiểm tra người gọi có quyền xem hay không.
2. **Bỏ sót trạng thái INACTIVE:** Trong `services/user-service/src/services/auth_service.py` và `src/api/dependencies.py`, hệ thống chỉ kiểm tra `tai_khoan.trang_thai == TrangThaiTaiKhoanEnum.LOCKED`, bỏ qua `INACTIVE`. Tài khoản chưa kích hoạt hoặc bị tạm ngưng vẫn đăng nhập được.

### File cần sửa:
1. `services/user-service/src/api/v1/endpoints/users.py`
2. `services/user-service/src/services/auth_service.py`
3. `services/user-service/src/api/dependencies.py`

### Yêu cầu cụ thể:
1. Trong `users.py` (`get_user_by_id`):
   - Kiểm tra: Nếu `current_user.id_tai_khoan != user_id` và `current_user.vai_tro != VaiTroEnum.ADMIN`:
     - Bắn `HTTPException(status_code=403, detail="Bạn không có quyền truy cập thông tin của tài khoản khác.")`.
2. Trong `auth_service.py` (`login`):
   - Thêm điều kiện:
     ```python
     if tai_khoan.trang_thai == TrangThaiTaiKhoanEnum.INACTIVE:
         raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN,
             detail="Tài khoản chưa được kích hoạt hoặc đã ngừng hoạt động.",
         )
     ```
3. Trong `api/dependencies.py` (`get_current_user`):
   - Thêm kiểm tra tương tự: Nếu `user.trang_thai == TrangThaiTaiKhoanEnum.INACTIVE`, bắn HTTP 403 Forbidden.

### Tiêu chí nghiệm thu:
- Dùng token của User A gọi `GET /api/v1/users/{User_B_id}` trả về 403 Forbidden.
- Dùng token của ADMIN gọi `GET /api/v1/users/{User_B_id}` trả về 200 OK.
- Tài khoản có `trang_thai = 'INACTIVE'` khi đăng nhập hoặc gọi API có JWT bị từ chối với mã 403 Forbidden.
```

---

### Prompt 3 (P0.4): Băm và bảo vệ mã OTP trong Payment Service

```markdown
Bạn hãy thực hiện Task P0.4: Mã hóa mã OTP lưu trong CSDL của Payment Service.

### Ngữ cảnh & Vấn đề:
Trong `services/payment-service/src/models/giao_dich_otp.py` và `database_init.sql`, cột `otp_code` là `NVARCHAR(6)` lưu nguyên văn 6 số OTP. Nếu CSDL bị trích xuất hoặc log bị lộ, toàn bộ OTP đang chờ xác thực đều có thể bị đọc.

### File cần sửa:
1. `services/payment-service/src/models/giao_dich_otp.py`
2. `services/payment-service/src/services/payment_service.py`
3. `services/payment-service/database_init.sql`

### Yêu cầu cụ thể:
1. Trong `models/giao_dich_otp.py`:
   - Đổi `otp_code = Column(String(64), nullable=False)`.
2. Trong `database_init.sql`:
   - Đổi `otp_code NVARCHAR(64) NOT NULL`.
3. Trong `payment_service.py`:
   - Viết hàm trợ giúp băm OTP:
     ```python
     import hashlib

     def hash_otp(raw_otp: str) -> str:
         return hashlib.sha256(raw_otp.encode('utf-8')).hexdigest()
     ```
   - Trong `generate_otp`:
     - Sinh mã OTP 6 số ngẫu nhiên `raw_otp` để gửi email/mock cho người dùng.
     - Lưu `otp_code = hash_otp(raw_otp)` vào `GiaoDichOtpModel`.
   - Trong `verify_otp`:
     - Băm mã `req.otp_code` mà người dùng nhập vào: `hash_input = hash_otp(req.otp_code)`.
     - So khớp `otp_record.otp_code == hash_input`.

### Tiêu chí nghiệm thu:
- Trong CSDL bảng `giao_dich_otp`, cột `otp_code` là chuỗi băm 64 ký tự (SHA-256).
- Quy trình `generate-otp` -> `verify-otp` với mã 6 chữ số hợp lệ vẫn thành công 100%. Nhập sai mã OTP bị từ chối chính xác.
```

---

### Prompt 4 (P0.5): Che OTP trong thông báo & Chống XSS trong Email Template

```markdown
Bạn hãy thực hiện Task P0.5: Khắc phục rò rỉ OTP trong tiêu đề thông báo và ngăn chặn nguy cơ XSS trong Notification Service.

### Ngữ cảnh & Vấn đề:
1. Trong `services/notification-service/src/services/notification_service.py`, hàm đã mask OTP trong `saved_html` và `saved_text`, nhưng dòng `noi_dung = NoiDungThongBaoModel(..., tieu_de=subject)` vẫn lưu nguyên `subject` chứa raw OTP (`Mã OTP xác thực giao dịch thanh toán: 123456`).
2. Trong `services/notification-service/src/core/templates.py`, các template nối chuỗi f-string trực tiếp dữ liệu từ request/event vào HTML (`so_phong`, `ten_khach`, `dia_chi`,...), có nguy cơ Script/HTML Injection nếu client nhập tên chứa thẻ `<script>` hoặc HTML độc hại.

### File cần sửa:
1. `services/notification-service/src/services/notification_service.py`
2. `services/notification-service/src/core/templates.py`

### Yêu cầu cụ thể:
1. Trong `notification_service.py`:
   - Khi lưu vào bảng `NoiDungThongBaoModel`, nếu loại thông báo là OTP (`loai == "OTP"`):
     - Thay thế mã OTP thực tế trong `subject` bằng dạng che `**-***` hoặc `Mã OTP xác thực giao dịch thanh toán (Đã bảo mật)`.
     - Tuyệt đối không lưu raw OTP vào bất kỳ trường nào của CSDL `thong_bao` hoặc `noi_dung_thong_bao`.
2. Trong `templates.py`:
   - Import `html` và sử dụng `html.escape(str(val))` cho tất cả các biến động người dùng: `ten_khach`, `ten_khach_san`, `dia_chi`, `so_phong`, `ten_loai_phong`,... trước khi nhúng vào khung HTML email.

### Tiêu chí nghiệm thu:
- Tạo thông báo OTP và kiểm tra CSDL: Bảng `noi_dung_thong_bao` không còn xuất hiện 6 chữ số OTP ở cả `tieu_de`, `noi_dung_html`, `noi_dung_text` và `du_lieu_dinh_kem`.
- Gửi payload có `ten_khach: "<script>alert(1)</script>"`: HTML render ra chuỗi escaped `&lt;script&gt;alert(1)&lt;/script&gt;` an toàn.
```

---

### Prompt 5 (P0.6): Bổ sung Auth & Ownership Check cho Booking, Payment, Hotel

```markdown
Bạn hãy thực hiện Task P0.6: Bổ sung Authentication & Authorization cho Booking Service, Payment Service và Hotel Service.

### Ngữ cảnh & Vấn đề:
1. **Payment Service:** File `services/payment-service/src/api/v1/endpoints/payments.py` không có bất kỳ dependency bảo mật nào. Ai cũng có thể tạo thanh toán, verify OTP hoặc truy vấn danh sách giao dịch qua `GET /payments` và `/stats`.
2. **Booking Service:** Endpoint `POST /bookings` cho phép `payload.id_tai_khoan` từ body ghi đè token (`user_id = payload.id_tai_khoan or current_user_id or 1`). Các API xem, hủy, xác nhận booking đều public.
3. **Hotel Service:** Endpoint chỉnh sửa, xóa khách sạn/phòng chưa xác thực quyền sở hữu thực sự của đối tác đối với khách sạn (`id_chu_so_huu`).

### File cần sửa:
1. `services/payment-service/src/api/dependencies.py` *(hoàn thiện nếu chưa có)*
2. `services/payment-service/src/api/v1/endpoints/payments.py`
3. `services/booking-service/src/api/dependencies.py`
4. `services/booking-service/src/api/v1/endpoints/bookings.py`
5. `services/booking-service/src/services/booking_service.py`
6. `services/hotel-service/src/api/dependencies.py`
7. `services/room-service/src/api/v1/dependencies.py`

### Yêu cầu cụ thể:
1. **Payment Service:**
   - Tạo/Cập nhật `api/dependencies.py` để verify JWT token từ Header `Authorization: Bearer <token>`, trích xuất `user_id` và `role`.
   - Áp dụng dependency xác thực:
     - `create-payment`, `generate-otp`, `verify-otp`: Yêu cầu người dùng đăng nhập.
     - `GET /payments`, `GET /stats`: Yêu cầu quyền `ADMIN`.
     - Route `simulate-ipn`: Bảo vệ bằng IPN Secret Key hoặc chỉ cho phép sandbox testing.
2. **Booking Service:**
   - Trong `POST /bookings`: Bắt buộc người dùng phải đăng nhập (`user_id = current_user_id`). Bỏ việc tin tưởng `payload.id_tai_khoan` từ body trừ khi `current_user.role == 'ADMIN'`.
   - Trong `GET /bookings`: Lọc danh sách theo `current_user_id` nếu là khách thông thường; chỉ `ADMIN` mới được xem toàn bộ.
   - Trong `GET /bookings/{id_or_code}` và `PATCH .../cancel`: Kiểm tra đơn đặt phòng phải thuộc sở hữu của `current_user_id` hoặc caller là `ADMIN`.
3. **Hotel & Room Service:**
   - Trong hàm kiểm tra quyền cập nhật/xóa khách sạn, phòng: So khớp `hotel.id_chu_so_huu == current_user.id` hoặc `current_user.role == 'ADMIN'`. Không cho phép partner sửa khách sạn của partner khác.

### Tiêu chí nghiệm thu:
- Khách không truyền JWT token gọi `POST /bookings` hoặc `GET /payments` bị trả về 401 Unauthorized.
- User bình thường không thể hủy hoặc xem đơn đặt phòng của User khác (403 Forbidden).
- Partner không thể sửa phòng thuộc khách sạn của partner khác (403 Forbidden).
```

---

### Prompt 6 (P0.7): Siết chặt cấu hình CORS tại Gateway và tất cả Service

```markdown
Bạn hãy thực hiện Task P0.7: Siết chặt cấu hình CORS tại API Gateway và 6 Backend Services.

### Ngữ cảnh & Vấn đề:
Hiện tại `gateway/src/main.py` và các file `main.py` của 6 services đều cấu hình:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
Cấu hình `allow_origins=["*"]` kết hợp `allow_credentials=True` vi phạm đặc tả bảo mật CORS của trình duyệt hiện đại và mở rộng bề mặt tấn công Cross-Site.

### File cần sửa:
1. `gateway/src/main.py` và `gateway/src/core/config.py`
2. `services/user-service/src/main.py` và `src/core/config.py`
3. `services/hotel-service/src/main.py` và `src/core/config.py`
4. `services/room-service/src/main.py` và `src/core/config.py`
5. `services/booking-service/src/main.py` và `src/core/config.py`
6. `services/payment-service/src/main.py` và `src/core/config.py`
7. `services/notification-service/src/main.py` và `src/core/config.py`
8. `.env.example`

### Yêu cầu cụ thể:
1. Trong file cấu hình (`config.py`) của Gateway và các Services:
   - Thêm cấu hình:
     ```python
     CORS_ORIGINS: list[str] = [
         "http://localhost:3000",
         "http://localhost:3001",
         "http://127.0.0.1:3000",
         "http://127.0.0.1:3001",
     ]
     ```
   - Cho phép parse chuỗi từ biến môi trường dạng danh sách phân tách bằng dấu phẩy.
2. Trong `main.py` của từng service:
   - Cập nhật `allow_origins=settings.CORS_ORIGINS`, giữ `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`.
3. Bổ sung vào `.env.example`: `CORS_ORIGINS=http://localhost:3000,http://localhost:3001`.

### Tiêu chí nghiệm thu:
- Trình duyệt từ `http://localhost:3000` (Customer Web) và `http://localhost:3001` (Admin Dashboard) gọi API bình thường kèm Cookie/Authorization header.
- Các request từ origin lạ (ví dụ `http://evil-site.com`) bị trình duyệt chặn CORS response header.
```

---

## GIAI ĐOẠN 2: P1 - LOGIC NGHIỆP VỤ & TÍNH ĐÚNG ĐẮN DỮ LIỆU

### Prompt 7 (P1.1): Lọc phòng trống theo khoảng ngày đối chiếu với Booking Service

```markdown
Bạn hãy thực hiện Task P1.1: Sửa logic tìm kiếm phòng trống theo khoảng ngày trong Room Service.

### Ngữ cảnh & Vấn đề:
Trong `services/room-service/src/services/room_service.py` hàm `get_available_rooms`, code nhận vào `check_in` và `check_out` nhưng chỉ kiểm tra `PhongModel.trang_thai == AVAILABLE`. Code không đối chiếu xem phòng đó đã bị người khác đặt hoặc giữ chỗ bên `booking-service` trong khoảng ngày đó hay chưa, dẫn đến việc phòng đã có khách đặt vẫn hiển thị khả dụng.

### File cần sửa:
1. `services/booking-service/src/api/v1/endpoints/bookings.py`
2. `services/booking-service/src/services/booking_service.py`
3. `services/room-service/src/services/room_service.py`
4. `services/room-service/src/core/config.py`

### Yêu cầu cụ thể:
1. **Tại Booking Service:**
   - Tạo endpoint nội bộ: `GET /api/v1/bookings/booked-room-ids`
   - Nhận query params: `hotel_id: int`, `check_in: date`, `check_out: date`.
   - Viết method trong `BookingService`: Truy vấn tất cả `ChiTietDatPhongModel.id_phong` thuộc các đơn đặt phòng có điều kiện giao thoa ngày:
     `(ngay_nhan_phong < check_out) AND (ngay_tra_phong > check_in)`
     và trạng thái là `CONFIRMED`, `COMPLETED` hoặc `PENDING_PAYMENT` còn trong hạn giữ chỗ (`han_giu_cho > now_utc`).
   - Trả về danh sách `booked_room_ids: List[int]`.
2. **Tại Room Service:**
   - Thêm cấu hình `BOOKING_SERVICE_URL: str = "http://localhost:8003/api/v1"` vào `room-service/src/core/config.py`.
   - Trong `RoomService.get_available_rooms`:
     - Gọi HTTP GET sang endpoint `booked-room-ids` của Booking Service (với timeout ngắn 3-5 giây, có kèm `X-Correlation-ID`).
     - Lấy danh sách `booked_ids`.
     - Nếu `booked_ids` có phần tử, bổ sung điều kiện lọc vào query SQL:
       `query = query.filter(PhongModel.id_phong.notin_(booked_ids))`.
     - Nếu Booking Service không phản hồi (fallback), log warning nhưng không crash ứng dụng.

### Tiêu chí nghiệm thu:
- Tạo một đơn đặt phòng cho Phòng #101 từ ngày `2026-11-01` đến `2026-11-05` (ở trạng thái PENDING hoặc CONFIRMED).
- Gọi `GET /api/v1/rooms/available?hotel_id=...&check_in=2026-11-02&check_out=2026-11-04`: Phòng #101 không còn xuất hiện trong kết quả trả về.
- Gọi kiểm tra khoảng ngày không trùng (ví dụ `2026-11-06` đến `2026-11-10`): Phòng #101 xuất hiện bình thường.
```

---

### Prompt 8 (P1.2): Xác thực giá phòng & dữ liệu phòng từ Room Service khi tạo Booking

```markdown
Bạn hãy thực hiện Task P1.2: Xác thực giá phòng và thông tin phòng từ Room Service khi tạo Booking (Data Trust Protection).

### Ngữ cảnh & Vấn đề:
Trong `services/booking-service/src/services/booking_service.py` hàm `create_booking`:
```python
total_price_per_night = sum(float(r.gia) for r in payload.rooms)
tong_tien = total_price_per_night * nights
```
Dữ liệu `r.gia`, `r.ten_loai_phong`, `r.so_phong` được lấy trực tiếp từ client gửi lên mà không đối chiếu với nguồn dữ liệu gốc của Room Service. Kẻ xấu có thể can thiệp payload gửi giá 0đ hoặc 1.000đ để đặt phòng cao cấp.

### File cần sửa:
1. `services/booking-service/src/services/booking_service.py`
2. `services/booking-service/src/core/config.py`

### Yêu cầu cụ thể:
1. Trong `booking-service/src/core/config.py`:
   - Đảm bảo biến `ROOM_SERVICE_URL: str = "http://localhost:8002/api/v1"` đã sẵn sàng sử dụng.
2. Trong `booking_service.py` (`create_booking`):
   - Trước khi tính tiền và insert đơn đặt phòng:
     - Với từng `room` trong `payload.rooms`, gọi HTTP sang Room Service để kiểm tra:
       `GET {settings.ROOM_SERVICE_URL}/rooms/{room.id_phong}` hoặc `GET .../room-types/{room.id_loai_phong}`.
     - Kiểm tra phòng có tồn tại, thuộc đúng `id_khach_san` của đơn đặt không và trạng thái phòng có phải `AVAILABLE` không.
     - Lấy giá gốc niêm yết từ Room Service (`gia_co_ban_mot_dem`).
     - Gán giá niêm yết này vào `gia_tai_thoi_diem_dat` thay vì dùng giá client gửi lên.
   - Tính toán lại `tong_tien = sum(gia_niem_yet) * nights`.
   - Nếu client gửi giá lệch quá mức so với giá niêm yết của Room Service (chênh lệch > 0.01), có thể tự động áp dụng giá niêm yết gốc hoặc thông báo lỗi `400 BAD REQUEST` ("Giá phòng đã thay đổi, vui lòng tải lại trang").

### Tiêu chí nghiệm thu:
- Thử gửi request `POST /api/v1/bookings` với body cố tình sửa `gia: 1000` (trong khi giá thực tế là 1.500.000đ):
  - Đơn đặt phòng được tạo với đúng giá 1.500.000đ x số đêm, hoặc bị từ chối với lỗi rõ ràng.
  - Tổng tiền `tong_tien` trong DB luôn khớp chính xác với giá niêm yết từ Room Service.
```

---

### Prompt 9 (P1.3 & P1.4): Đối soát số tiền thanh toán & Xử lý trạng thái khi xác nhận Booking lỗi

```markdown
Bạn hãy thực hiện Task P1.3 và P1.4: Đối soát số tiền thanh toán với Booking Service và đảm bảo tính nhất quán trạng thái giao dịch.

### Ngữ cảnh & Vấn đề:
1. **Thiếu đối soát số tiền:** Trong `services/payment-service/src/services/payment_service.py` (`create_payment`), service chỉ kiểm tra đơn booking tồn tại và còn hạn giữ chỗ, nhưng không so sánh `payload.so_tien` với `booking.tong_tien`. Khách hàng có thể thanh toán số tiền nhỏ hơn giá trị thực tế của đơn hàng.
2. **Nguy cơ bất đồng bộ trạng thái:** Khi xác nhận thanh toán thành công (qua OTP hoặc IPN), `payment_service.py` cập nhật bản ghi thành `SUCCESS` trước, sau đó gọi PATCH sang Booking Service. Nếu cuộc gọi sang Booking Service thất bại (mạng lag/timeout), lỗi chỉ bị catch và in log, dẫn đến tiền đã trừ nhưng booking không được xác nhận và sẽ bị hủy tự động.

### File cần sửa:
1. `services/payment-service/src/services/payment_service.py`
2. `services/payment-service/src/models/thanh_toan.py`
3. `services/payment-service/src/schemas/payment_schema.py`

### Yêu cầu cụ thể:
1. **Đối soát số tiền (P1.3):**
   - Trong `PaymentService.create_payment`:
     - Sau khi lấy được `bk_data` từ Booking Service, lấy `booking_total = Decimal(str(bk_data.get("tong_tien", 0)))`.
     - So sánh với `req_amount = Decimal(str(payload.so_tien))`.
     - Nếu `req_amount != booking_total`:
       - Bắn `HTTPException(status_code=400, detail=f"Số tiền thanh toán ({req_amount:,.0f} đ) không khớp với giá trị đơn đặt phòng ({booking_total:,.0f} đ).")`.
2. **Xử lý nhất quán khi Booking confirmation thất bại (P1.4):**
   - Bổ sung giá trị enum vào `TrangThaiThanhToanEnum`: `SYNC_FAILED = "SYNC_FAILED"`.
   - Trong luồng OTP verify và IPN:
     - Tạo hàm gọi `confirm_booking_with_retry` thử gọi PATCH sang Booking Service với 3 lần retry (exponential backoff).
     - Nếu sau 3 lần vẫn không gọi được Booking Service:
       - Cập nhật trạng thái giao dịch thành `SYNC_FAILED` kèm ghi chú: `"Thanh toán thành công nhưng chưa thể cập nhật Booking Service. Chờ đối soát tự động."`
       - Bắn cảnh báo hoặc lưu vào danh sách chờ đồng bộ lại thay vì coi như đã hoàn tất suôn sẻ.
     - Khi gọi Booking Service thành công mới xác nhận trạng thái cuối cùng là `SUCCESS`.

### Tiêu chí nghiệm thu:
- Gọi `POST /payments/create-payment` với số tiền lệch so với booking: Bị chặn với lỗi 400.
- Nếu Booking Service bị tắt đột ngột khi khách verify OTP: Trạng thái không bị ghi nhận là SUCCESS hoàn hảo giả mạo, mà ghi nhận rõ lỗi đồng bộ để quản trị viên đối soát xử lý.
```

---

## GIAI ĐOẠN 3: P2 - TÍCH HỢP GATEWAY & EVENT-DRIVEN BROKER

### Prompt 10 (P2.1 & P2.2): Định tuyến Frontend qua Gateway và sửa lỗi route `room-types`

```markdown
Bạn hãy thực hiện Task P2.1 và P2.2: Hợp nhất luồng Frontend qua API Gateway (:8080) và khắc phục lỗi định tuyến của Gateway.

### Ngữ cảnh & Vấn đề:
1. **Bypass Gateway:** Cả hai ứng dụng `customer-web` và `admin-dashboard` đang trỏ trực tiếp vào port của từng backend service (8000-8005) trong `lib/api.ts` thay vì đi qua Gateway `:8080`.
2. **Lỗi định tuyến Gateway:** Trong `gateway/src/main.py` hàm `resolve_target_url`:
   - Chưa có nhánh xử lý cho `room-types` -> các request `/api/v1/room-types/...` bị trả về `None` (lỗi 404/502).
   - Các route như `/api/v1/hotels/{hotel_id}/rooms` hoặc `/api/v1/hotels/{hotel_id}/room-types` thuộc Room Service nhưng do bắt đầu bằng `hotels` nên Gateway forward nhầm sang Hotel Service.

### File cần sửa:
1. `gateway/src/main.py`
2. `front-end/packages/api-client/src/index.ts`
3. `front-end/apps/customer-web/src/lib/api.ts`
4. `front-end/apps/admin-dashboard/src/lib/api.ts`
5. `front-end/apps/customer-web/.env.example`
6. `front-end/apps/admin-dashboard/.env.example`

### Yêu cầu cụ thể:
1. **Tại Gateway (`gateway/src/main.py`):**
   - Viết lại hàm `resolve_target_url(full_path: str) -> str`:
     - Nếu path bắt đầu bằng `api/v1/room-types`: Trỏ về `settings.ROOM_SERVICE_URL`.
     - Nếu path khớp mẫu regex `^api/v1/hotels/\d+/(rooms|room-types)`: Trỏ về `settings.ROOM_SERVICE_URL`.
     - Các path `api/v1/hotels/...` còn lại: Trỏ về `settings.HOTEL_SERVICE_URL`.
     - Giữ nguyên các định tuyến đúng khác (`auth`, `users`, `admin`, `bookings`, `payments`, `notifications`).
2. **Tại Frontend:**
   - Trong `front-end/packages/api-client/src/index.ts`:
     - Nếu `gatewayUrl` được truyền vào, cho phép tất cả các request mặc định đi qua `gatewayUrl` thay vì bắt buộc chia nhỏ từng service URL.
   - Trong `front-end/apps/customer-web/src/lib/api.ts` và `admin-dashboard/src/lib/api.ts`:
     - Cập nhật mặc định API endpoint trỏ về Gateway:
       `export const GATEWAY_API_BASE_URL = process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8080/api/v1";`
     - Cấu hình `apiClient` sử dụng `GATEWAY_API_BASE_URL`.
   - Cập nhật file `.env.example` của cả hai app phản ánh cổng `8080`.

### Tiêu chí nghiệm thu:
- Khởi động Gateway `:8080` và các service.
- Gọi thử qua Gateway: `GET http://localhost:8080/api/v1/room-types` trả về dữ liệu đúng từ Room Service.
- Gọi thử qua Gateway: `GET http://localhost:8080/api/v1/hotels/1/rooms` trả về danh sách phòng từ Room Service (thay vì 404 từ Hotel Service).
- Mở Customer Web và Admin Dashboard, kiểm tra Network tab trên trình duyệt: 100% request HTTP gửi tới `localhost:8080`.
```

---

### Prompt 11 (P2.3): Bổ sung thư viện `pika` cho Booking và Payment Service

```markdown
Bạn hãy thực hiện Task P2.3: Bổ sung khai báo thư viện `pika` trong `requirements.txt` của Booking Service và Payment Service.

### Ngữ cảnh & Vấn đề:
Cả `services/booking-service/src/core/publisher.py` và `services/payment-service/src/core/publisher.py` đều thực thi `import pika` để kết nối và gửi sự kiện sang RabbitMQ. Tuy nhiên, file `requirements.txt` của cả hai service này đều thiếu khai báo `pika`. Khi build Docker container hoặc chạy độc lập từ requirements cục bộ của từng service, ứng dụng sẽ bị crash ngay khi khởi động (`ModuleNotFoundError: No module named 'pika'`).

### File cần sửa:
1. `services/booking-service/requirements.txt`
2. `services/payment-service/requirements.txt`

### Yêu cầu cụ thể:
1. Thêm `pika>=1.3.2` vào cuối file `services/booking-service/requirements.txt`.
2. Thêm `pika>=1.3.2` vào cuối file `services/payment-service/requirements.txt`.
3. Kiểm tra xem root `requirements.txt` đã có `pika` chưa, nếu chưa hãy bổ sung đồng bộ.

### Tiêu chí nghiệm thu:
- Cả hai file `requirements.txt` đều chứa khai báo `pika>=1.3.2`.
- Kiểm tra import `python -c "import pika"` trong môi trường ảo của service thành công không lỗi.
```

---

### Prompt 12 (P2.4 & P2.5): Sửa lỗi 401 REST Fallback và hoàn thiện cấu hình gửi email SMTP

```markdown
Bạn hãy thực hiện Task P2.4 và P2.5: Sửa lỗi 401 Unauthorized khi gọi REST Fallback sang Notification Service và cấu hình tùy chọn gửi email SMTP thật.

### Ngữ cảnh & Vấn đề:
1. **Lỗi 401 REST Fallback:** Trong `publisher.py` của Booking và Payment Service, khi RabbitMQ gặp sự cố, code fallback gọi `POST /api/v1/notifications/send`. Nhưng route này trong Notification Service yêu cầu JWT token của người dùng (`Depends(get_current_user_id)`). Cuộc gọi nội bộ từ server sang server không có Header Authorization nên luôn nhận về `401 Unauthorized`.
2. **Email chỉ chạy Mock:** Notification Service có cờ `USE_MOCK_EMAIL=True` mặc định, chỉ in log console mà không hỗ trợ gửi email thật qua SMTP khi cấu hình.

### File cần sửa:
1. `services/notification-service/src/api/v1/endpoints/notifications.py`
2. `services/notification-service/src/core/config.py`
3. `services/notification-service/src/core/email_sender.py`
4. `services/booking-service/src/core/publisher.py`
5. `services/payment-service/src/core/publisher.py`
6. `.env.example`

### Yêu cầu cụ thể:
1. **Tại Notification Service:**
   - Thêm biến cấu hình `INTERNAL_SERVICE_SECRET: str = "booking_internal_secret_key_2026"` vào `config.py`.
   - Tạo endpoint nội bộ riêng trong `notifications.py`:
     `POST /api/v1/notifications/internal-send`
     - Xác thực thông qua Header `X-Internal-Secret`. Nếu khớp với `settings.INTERNAL_SERVICE_SECRET` thì cho phép tạo thông báo mà không cần JWT user token.
   - Trong `email_sender.py`:
     - Kiểm tra nếu `USE_MOCK_EMAIL` là `False` và có thông tin cấu hình `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`: Sử dụng `aiosmtplib` hoặc `smtplib` để gửi email thật qua STARTTLS (port 587) hoặc SSL (port 465).
2. **Tại Booking và Payment Service (`publisher.py`):**
   - Sửa URL gọi REST Fallback trỏ về: `{settings.NOTIFICATION_SERVICE_URL}/notifications/internal-send`.
   - Bổ sung Header `X-Internal-Secret: <secret_key>` và `X-Correlation-ID: <cid>` trong request HTTP.
3. Cập nhật `.env.example` với các tham số SMTP mẫu (host, port, user, password, from_email) và `INTERNAL_SERVICE_SECRET`.

### Tiêu chí nghiệm thu:
- Tắt container RabbitMQ để ép hệ thống dùng REST Fallback: Booking Service và Payment Service gửi thông báo qua REST thành công (trả về status 200/201 thay vì 401).
- Khi cấu hình tài khoản SMTP hợp lệ trong `.env` và đặt `USE_MOCK_EMAIL=False`, email xác nhận đặt phòng và OTP được gửi tới hòm thư thật.
```

---

## GIAI ĐOẠN 4: P3 - FRONTEND & CLEAN CODE

### Prompt 13 (P3.1 & P3.2): Đồng bộ thuế/phí 10% và chuẩn hóa Enum phương thức thanh toán

```markdown
Bạn hãy thực hiện Task P3.1 và P3.2: Đồng bộ logic thuế phí (10%) giữa Frontend và Backend, đồng thời chuẩn hóa Enums phương thức thanh toán.

### Ngữ cảnh & Vấn đề:
1. **Lệch tiền do thuế/phí:** Tại `checkout/page.tsx`, Frontend tự tính 10% phí và cộng vào `finalTotal` khi gọi Payment Service (`so_tien: finalTotal`), nhưng khi gửi sang Booking Service lại chỉ gửi `roomTotal` không phí. Điều này khiến hai service ghi nhận hai tổng tiền khác nhau cho cùng một đơn đặt phòng.
2. **Lệch Enum phương thức thanh toán:** Frontend định nghĩa `"ATM_CARD" | "TIEN_MAT"` và ép kiểu bằng `paymentMethod as any`, trong khi Backend mong đợi `"VNPAY" | "MOMO" | "CREDIT_CARD" | "CASH"`.

### File cần sửa:
1. `front-end/packages/types/src/index.ts`
2. `front-end/apps/customer-web/src/app/booking/checkout/page.tsx`
3. `services/booking-service/src/schemas/booking_schema.py`
4. `services/booking-service/src/services/booking_service.py`

### Yêu cầu cụ thể:
1. **Đồng bộ thuế/phí:**
   - Trong `Booking Service`:
     - Bổ sung trường `thue_phi` và `tong_tien` trong schema và database/logic của `DatPhongModel`.
     - Khi tạo booking, tính:
       - `tien_phong = sum(gia_phong) * so_dem`
       - `thue_phi = round(tien_phong * 0.10)` (thuế VAT 10%)
       - `tong_tien = tien_phong + thue_phi`
     - Trả về chi tiết `tien_phong`, `thue_phi`, `tong_tien` cho client.
   - Tại `checkout/page.tsx`:
     - Hiển thị bảng kê chi tiết minh bạch: Giá phòng, Thuế VAT (10%), Tổng thanh toán cuối cùng.
     - Sử dụng chính xác con số `bookingRes.tong_tien` nhận được từ Booking Service để truyền sang `apiClient.createPayment`.
2. **Chuẩn hóa Enum thanh toán:**
   - Trong `@repo/types`: Khai báo enum chuẩn:
     ```typescript
     export enum PhuongThucThanhToan {
       VNPAY = "VNPAY",
       MOMO = "MOMO",
       CREDIT_CARD = "CREDIT_CARD",
       CASH = "CASH",
     }
     ```
   - Trong `checkout/page.tsx`:
     - Sử dụng `PhuongThucThanhToan` chuẩn từ `@repo/types`.
     - Xóa hoàn toàn việc ép kiểu `as any`.
     - Khớp các nhãn tiếng Việt trên UI: VNPAY, Ví MoMo, Thẻ tín dụng quốc tế (CREDIT_CARD), Tiền mặt tại khách sạn (CASH).

### Tiêu chí nghiệm thu:
- Đặt phòng trên giao diện và theo dõi giá trị lưu trong CSDL: Cả `booking_service` và `payment_service` đều ghi nhận chính xác cùng một con số `tong_tien`.
- Không còn bất kỳ cảnh báo TypeScript nào liên quan đến ép kiểu `as any` tại `checkout/page.tsx`.
```

---

### Prompt 14 (P3.3): Bỏ dữ liệu Mock ngầm, hiển thị lỗi thật và hoàn thiện luồng người dùng

```markdown
Bạn hãy thực hiện Task P3.3: Dọn dẹp Mock Data ngầm trên Customer Web, hiển thị giao diện báo lỗi trực quan và kết nối các trang còn thiếu.

### Ngữ cảnh & Vấn đề:
Khi API backend bị lỗi hoặc không có dữ liệu, các trang `page.tsx` (Trang chủ), `search/page.tsx`, `hotels/[id]/page.tsx`, `booking/success/[code]/page.tsx` tự động chuyển sang nạp các biến mock tĩnh (`mockHotels`, `mockRooms`,...). Người dùng tưởng hệ thống vẫn hoạt động nhưng thực tế API đã bị lỗi. Ngoài ra, nút "Đơn đặt của tôi" trên Navbar chỉ hiển thị popup alert và nút "Quên mật khẩu" trỏ vào liên kết rỗng `#`.

### File cần sửa:
1. `front-end/apps/customer-web/src/app/page.tsx`
2. `front-end/apps/customer-web/src/app/search/page.tsx`
3. `front-end/apps/customer-web/src/app/hotels/[id]/page.tsx`
4. `front-end/apps/customer-web/src/app/booking/success/[code]/page.tsx`
5. `front-end/apps/customer-web/src/components/Navbar.tsx`
6. `front-end/apps/customer-web/src/components/AuthModal.tsx`
7. Tạo trang mới: `front-end/apps/customer-web/src/app/my-bookings/page.tsx`

### Yêu cầu cụ thể:
1. **Loại bỏ Fallback Mock ngầm:**
   - Xóa bỏ việc nạp dữ liệu mock khi fetch API bị `catch(err)`.
   - Nếu API lỗi, hiển thị Error State trực quan với thông điệp: "Không thể kết nối đến máy chủ. Vui lòng thử lại sau." kèm nút bấm **"Thử lại"**.
   - Chỉ hiển thị Mock Data nếu có biến môi trường `NEXT_PUBLIC_DEMO_MODE=true` được bật tường minh.
2. **Tạo trang "Đơn đặt của tôi" (`my-bookings/page.tsx`):**
   - Viết trang danh sách các đơn đặt phòng của tài khoản đang đăng nhập bằng cách gọi `apiClient.getBookings()`.
   - Hiển thị mã đơn, tên khách sạn, ngày nhận/trả phòng, tổng tiền và badge trạng thái (`PENDING_PAYMENT`, `CONFIRMED`, `CANCELLED`).
   - Cập nhật liên kết trên Navbar trỏ tới `/my-bookings` thay vì bắn `alert()`.
3. **Cập nhật AuthModal:**
   - Xử lý link "Quên mật khẩu": Hiển thị tab/modal nhập email để nhận mã khôi phục hoặc hướng dẫn liên hệ hỗ trợ.

### Tiêu chí nghiệm thu:
- Tắt một service backend (ví dụ Hotel Service): Giao diện tìm kiếm hiển thị khung báo lỗi rõ ràng kèm nút thử lại, không còn tự ý hiển thị khách sạn giả lập.
- Người dùng sau khi đặt phòng xong có thể vào mục "Đơn đặt của tôi" và thấy danh sách đơn đặt phòng thực tế của chính mình.
```

---

### Prompt 15 (P3.4): Tinh chỉnh Admin Dashboard (Navbar, Sort phòng, Doanh thu thực)

```markdown
Bạn hãy thực hiện Task P3.4: Tinh chỉnh Admin Dashboard (Dọn dẹp menu thừa, sửa tính năng sắp xếp phòng, tính doanh thu thực tế).

### Ngữ cảnh & Vấn đề:
1. **Menu rác:** Navbar Admin có 6 liên kết dẫn đến trang 404: `/Revenue`, `/Reviews`, `/Promotions`, `/Reports`, `/Settings`, `/Profile`.
2. **Lỗi Sort phòng:** Trong `front-end/apps/admin-dashboard/src/app/Rooms/page.tsx`, hàm `handleSort` thay đổi state `sortField` và `sortOrder`, nhưng mảng render trong bảng `rooms.map(...)` lại giữ nguyên thứ tự API trả về mà không hề áp dụng sắp xếp.
3. **Thống kê doanh thu giả:** Tại `front-end/apps/admin-dashboard/src/app/page.tsx`, doanh thu hôm nay được tính bằng công thức nhân cứng: `todayRevenue = Math.round(totalRevenue * 0.35)`.

### File cần sửa:
1. `front-end/apps/admin-dashboard/src/components/Navbar.tsx`
2. `front-end/apps/admin-dashboard/src/app/Rooms/page.tsx`
3. `front-end/apps/admin-dashboard/src/app/page.tsx`
4. `services/payment-service/src/services/payment_service.py`

### Yêu cầu cụ thể:
1. **Dọn dẹp Navbar:**
   - Ẩn hoặc loại bỏ các menu chưa có trang thực tế khỏi danh sách `navItems` trong `Navbar.tsx` (chỉ giữ lại: `Người dùng`, `Khách Sạn`, `Phòng`, `Đặt Phòng`, `Thanh toán`, `Thông báo`).
   - Nếu muốn giữ lại để demo UI, gắn thêm badge nhỏ `Sắp ra mắt` và vô hiệu hóa thẻ `<Link>` để tránh lỗi 404 khi bấm vào.
2. **Sửa tính năng Sắp xếp tại `Rooms/page.tsx`:**
   - Tạo biến mảng đã sắp xếp:
     ```typescript
     const sortedRooms = useMemo(() => {
       return [...rooms].sort((a, b) => {
         let valA = a[sortField];
         let valB = b[sortField];
         if (sortField === "price") {
           valA = a.loai_phong?.gia_co_ban_mot_dem || 0;
           valB = b.loai_phong?.gia_co_ban_mot_dem || 0;
         }
         if (valA < valB) return sortOrder === "asc" ? -1 : 1;
         if (valA > valB) return sortOrder === "asc" ? 1 : -1;
         return 0;
       });
     }, [rooms, sortField, sortOrder]);
     ```
   - Thay thế `rooms.map(...)` bằng `sortedRooms.map(...)`.
   - Kết nối sự kiện `onClick={() => handleSort(...)}` cho các cột: Số phòng, Khách sạn, Giá tiền, Trạng thái.
3. **Thống kê doanh thu thực tế:**
   - Trong `PaymentService.get_stats`: Bổ sung truy vấn tính tổng tiền các giao dịch `SUCCESS` có `thoi_gian_tao` trong ngày hôm nay (`func.sum` lọc theo `cast(thoi_gian_tao as Date) == today`).
   - Trong `admin-dashboard/src/app/page.tsx`: Lấy `todayRevenue` trực tiếp từ API stats của backend thay vì nhân hệ số `0.35`.

### Tiêu chí nghiệm thu:
- Bấm vào header cột "Giá tiền" hoặc "Số phòng" trong trang quản lý Phòng: Danh sách phòng được đảo chiều sắp xếp tăng/giảm mượt mà ngay trên bảng.
- Navbar chỉ hiển thị các trang đang hoạt động tốt.
- Số liệu doanh thu hôm nay trên trang chủ Admin phản ánh đúng tổng các giao dịch thành công trong ngày.
```

---

### Prompt 16 (P3.5): Dọn dẹp Clean Code và tạo Script chạy tự động bộ 6 bài Test

```markdown
Bạn hãy thực hiện Task P3.5: Dọn dẹp Clean Code và tạo Script kiểm thử tự động toàn diện.

### Ngữ cảnh & Vấn đề:
1. File `services/room-service/package.json` là tàn dư cấu hình không dùng đến trong một Python service, chứa test script lỗi thời.
2. Thư mục `test/` có sẵn 6 file test Python rất chất lượng (test concurrency, test idempotency, test tracing, test OTP,...) nhưng chưa từng được chạy kiểm thử trên runtime và chưa có runner tự động một lệnh.

### File cần sửa / tạo mới:
1. `services/room-service/package.json` *(Xóa file này)*
2. `test/test_gateway_flow.py` *(Cập nhật token/auth tương ứng với các thay đổi bảo mật P0)*
3. `test/test_payment_otp.py` *(Cập nhật phù hợp với cơ chế băm OTP)*
4. Tạo mới script: `run-tests.ps1` ở thư mục gốc dự án.

### Yêu cầu cụ thể:
1. Xóa bỏ file `services/room-service/package.json`.
2. Soát lỗi và cập nhật 6 script test trong thư mục `test/`:
   - Đảm bảo các script có thể đăng nhập lấy token JWT hợp lệ trước khi gọi các endpoint đã được siết chặt bảo mật ở Giai đoạn P0.
3. Tạo file PowerShell `run-tests.ps1`:
   - Kiểm tra kết nối tới các dịch vụ (Gateway `:8080`, SQL Server, RabbitMQ).
   - Chạy tuần tự 6 bài test bằng `pytest -v` hoặc `python test/<test_file>.py`:
     1. `test/test_booking_concurrency.py`
     2. `test/test_payment_idempotency.py`
     3. `test/test_payment_otp.py`
     4. `test/test_notification_otp.py`
     5. `test/test_correlation_tracing.py`
     6. `test/test_gateway_flow.py`
   - In bảng tổng kết kết quả: Bài nào PASS (xanh lá), bài nào FAIL (đỏ) kèm thời gian thực thi.

### Tiêu chí nghiệm thu:
- Chạy lệnh `.\run-tests.ps1`: Toàn bộ 6 kịch bản kiểm thử chạy tự động và báo cáo kết quả chi tiết mà không bị treo.
- Cấu trúc thư mục sạch sẽ, không còn file thừa không đúng mục đích.
```
