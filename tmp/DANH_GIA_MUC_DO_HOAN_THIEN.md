# Đánh Giá Mức Độ Hoàn Thiện Dự Án (System-Booking-service)

> **Kết luận nhanh:** **CHƯA CÓ PHẦN NÀO ĐẠT MỨC HOÀN THIỆN 100% CHUẨN SẢN PHẨM.**  
> Mặc dù khung sườn kiến trúc Microservices, giao diện và các API cốt lõi đã được dựng xong về mặt mã nguồn (Code-level), nhưng tất cả các module hiện tại đều đang dính các lỗ hổng logic, rủi ro bảo mật nghiêm trọng hoặc lỗi tích hợp giữa các service.

---

## 📊 Bảng Tổng Hợp Mức Độ Hoàn Thiện

| STT | Thành phần / Module | Đánh giá | Tình trạng cốt lõi |
|:---:|---|:---:|---|
| 1 | **User Service** | ⚠️ RẤT KÉM | Rủi ro bảo mật cao (Plaintext password, hổng IDOR, sót trạng thái) |
| 2 | **Room Service** | 🟡 TRUNG BÌNH | Lỗi logic tìm phòng trống (không kiểm tra trùng ngày đặt phòng) |
| 3 | **Booking Service** | 🟠 KHÁ | Logic khóa tốt (`sp_getapplock`), nhưng hổng Auth & thiếu xác thực giá phòng |
| 4 | **Payment Service** | 🟡 TRUNG BÌNH | Sandbox giả lập, mã OTP lưu plaintext, thiếu Auth & đối soát tiền |
| 5 | **Notification Service** | 🟡 TRUNG BÌNH | Mặc định chạy Mock, lỗi 401 khi gọi REST fallback, nguy cơ XSS |
| 6 | **Hotel Service** | 🟡 TRUNG BÌNH | Đầy đủ CRUD, dùng auth giả / demo role, chưa check quyền sở hữu |
| 7 | **Frontend (Customer & Admin)** | 🟠 KHÁ (Giao diện) | UI đẹp & mượt nhưng logic lệch tiền, lạm dụng dữ liệu giả (fallback), menu thừa |
| 8 | **Hạ tầng, Gateway & Testing** | 🔴 KÉM | Frontend bypass Gateway, script test chưa từng chạy thật trên runtime |

---

## 🔍 Đánh Giá Chi Tiết Từng Phần

### 1. User Service (Xác thực & Người dùng)
* **Đánh giá:** ⚠️ **RẤT KÉM (Rủi ro bảo mật cao)**
* **Đã làm được:**
  * Đầy đủ các endpoint: Đăng ký (`/register`), Đăng nhập (`/login`), Refresh Token (`/refresh`).
  * Lấy và cập nhật thông tin cá nhân (`/users/me`), chức năng quản trị tài khoản cho Admin.
* **Chưa OK / Lỗi nặng:**
  * **Lưu mật khẩu dạng thô (Plaintext):** Hàm `hash_password` đang trả về nguyên văn mật khẩu người dùng nhập vào mà không hề mã hóa hay băm (hash).
  * **Lỗi phân quyền (IDOR):** API lấy hồ sơ cá nhân (`/users/{user_id}`) lấy ID trực tiếp từ URL mà không kiểm tra ID đó có trùng khớp với User ID trong JWT Token của người đang đăng nhập hay không.
  * **Chưa chặn đúng trạng thái:** Tài khoản ở trạng thái `INACTIVE` vẫn đăng nhập bình thường do hệ thống chỉ mới kiểm tra cờ `LOCKED`.

---

### 2. Room Service (Quản lý Phòng)
* **Đánh giá:** 🟡 **TRUNG BÌNH**
* **Đã làm được:**
  * Tạo / Sửa / Xóa loại phòng (`room-types`), tạo phòng vật lý, tạo phòng hàng loạt (`batch`), lọc danh sách phòng.
* **Chưa OK:**
  * **Lỗi logic tìm phòng trống:** API `/rooms/available` có nhận tham số ngày check-in / check-out từ client nhưng code lại không hề đối chiếu với lịch đặt chỗ bên `booking-service` để loại trừ các phòng đã có người đặt trong khoảng thời gian đó.

---

### 3. Booking Service (Đặt phòng)
* **Đánh giá:** 🟠 **KHÁ (Logic khóa tốt nhưng hổng Auth)**
* **Đã làm được:**
  * Tạo đơn đặt phòng, cơ chế giữ chỗ tạm thời trong 15 phút, hủy / xác nhận đơn.
  * Xử lý tranh chấp phòng đồng thời (Concurrency) hiệu quả bằng `sp_getapplock` và Transaction SQL Server.
* **Chưa OK:**
  * **Lập trình thiếu kiểm tra (Data Trust):** Khi tạo booking, service tin tưởng tuyệt đối giá phòng và ID phòng do Frontend gửi lên trong Body mà không gọi sang `room-service` để xác minh lại.
  * **Thiếu Auth:** Lấy ID tài khoản người đặt từ Body request thay vì trích xuất từ JWT Token; các API đọc/hủy đơn chưa bắt buộc Token xác thực.

---

### 4. Payment Service (Thanh toán)
* **Đánh giá:** 🟡 **TRUNG BÌNH (Chỉ là Sandbox)**
* **Đã làm được:**
  * Tạo giao dịch, Idempotency (chống trùng thanh toán), sinh/xác thực OTP 6 số, giả lập callback IPN.
* **Chưa OK:**
  * **Chưa có cổng thanh toán thật:** Mới dừng ở mức sandbox / giả lập IPN.
  * **Rủi ro dữ liệu:** Mã OTP lưu dưới dạng văn bản thô (Plaintext) trực tiếp trong SQL Server.
  * **Thiếu đồng bộ:** Không đối chiếu số tiền nhận được với bản ghi gốc bên `booking-service`; các endpoint thiếu phân quyền Auth.

---

### 5. Notification Service (Thông báo)
* **Đánh giá:** 🟡 **TRUNG BÌNH**
* **Đã làm được:**
  * Lắng nghe event RabbitMQ từ Booking/Payment, lưu lịch sử thông báo, render mẫu HTML email.
* **Chưa OK:**
  * **Mặc định chạy MOCK:** Hệ thống báo "đã gửi" nhưng thực tế không kết nối server SMTP để gửi email thật.
  * **Lỗi tích hợp REST:** Khi Booking/Payment gọi REST fallback sang Notification bị lỗi `401 Unauthorized` do thiếu Authorization Header.
  * **Nguy cơ XSS:** Template email chèn trực tiếp dữ liệu động vào HTML mà không escape/mã hóa.

---

### 6. Hotel Service (Quản lý Khách sạn)
* **Đánh giá:** 🟡 **TRUNG BÌNH**
* **Đã làm được:**
  * CRUD khách sạn, quản lý danh sách hình ảnh, tiện nghi, chính sách khách sạn.
* **Chưa OK:**
  * Đang dùng auth giả / demo role; chưa kiểm tra quyền sở hữu thực sự của chủ khách sạn đối với tài nguyên thao tác.

---

### 7. Frontend (Customer Web & Admin Dashboard)
* **Đánh giá:** 🟠 **KHÁ VỀ GIAO DIỆN (Lỗi logic dữ liệu)**
* **Customer Web:**
  * *Đã làm:* Hoàn thiện luồng Tìm kiếm $\rightarrow$ Chi tiết $\rightarrow$ Checkout $\rightarrow$ OTP $\rightarrow$ Thành công.
  * *Chưa OK:* Tự động cộng 10% phí ở UI gây lệch tổng tiền với Backend; lạm dụng dữ liệu giả (fallback) khi API lỗi khiến người dùng khó nhận biết lỗi thật; chưa có trang Quên mật khẩu và Lịch sử đơn thật.
* **Admin Dashboard:**
  * *Đã làm:* Giao diện quản lý Phòng, Khách sạn, User, Booking, Payment, Notification.
  * *Chưa OK:* Thừa menu không có trang thật (Doanh thu, Đánh giá, Khuyến mãi, Báo cáo, Cài đặt trên Navbar); nút Sắp xếp (Sort) ở trang Rooms không có tác dụng; số liệu Thống kê ở trang chủ là số fix cứng chứ không query CSDL.

---

### 8. Hạ tầng, API Gateway & Testing
* **Đánh giá:** 🔴 **KÉM**
* **API Gateway:** Đã viết code proxy nhưng Frontend mặc định lại gọi trực tiếp vào port của từng Backend Service (8000–8005) thay vì đi qua Gateway (:8080).
* **Testing:** Có sẵn 6 file script test Python nhưng tất cả mới chỉ nằm trên file, chưa từng được chạy thử nghiệm thực tế trên môi trường runtime.
