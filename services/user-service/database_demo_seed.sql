USE user_service;
GO
-- 3. Demo accounts: bcrypt hashes; isolated development only.
IF NOT EXISTS (SELECT * FROM tai_khoan WHERE ten_dang_nhap = 'admin')
BEGIN
    INSERT INTO tai_khoan (ten_dang_nhap, email, sdt, mat_khau_hash, vai_tro, trang_thai)
    VALUES ('admin', 'admin@hotel.com', '0900000001', '$2b$12$fN3QNDSIOcqEKg9VUNMG6.nJ01g/asNcFxggHN72BZF3gTZBcSJPO', 'ADMIN', 'ACTIVE');

    DECLARE @admin_id INT = SCOPE_IDENTITY();
    INSERT INTO nguoi_dung (id_tai_khoan, ho, ten, dia_chi)
    VALUES (@admin_id, N'Quản Trị', N'Viên', N'Hà Nội, Việt Nam');
END
GO

IF NOT EXISTS (SELECT * FROM tai_khoan WHERE ten_dang_nhap = 'partner1')
BEGIN
    INSERT INTO tai_khoan (ten_dang_nhap, email, sdt, mat_khau_hash, vai_tro, trang_thai)
    VALUES ('partner1', 'partner@hotel.com', '0900000002', '$2b$12$fN3QNDSIOcqEKg9VUNMG6.nJ01g/asNcFxggHN72BZF3gTZBcSJPO', 'PARTNER', 'ACTIVE');

    DECLARE @partner_id INT = SCOPE_IDENTITY();
    INSERT INTO nguoi_dung (id_tai_khoan, ho, ten, dia_chi)
    VALUES (@partner_id, N'Chủ Khách Sạn', N'Đại Dương', N'Đà Nẵng, Việt Nam');
END
GO

IF NOT EXISTS (SELECT * FROM tai_khoan WHERE ten_dang_nhap = 'customer1')
BEGIN
    INSERT INTO tai_khoan (ten_dang_nhap, email, sdt, mat_khau_hash, vai_tro, trang_thai)
    VALUES ('customer1', 'customer@gmail.com', '0900000003', '$2b$12$fN3QNDSIOcqEKg9VUNMG6.nJ01g/asNcFxggHN72BZF3gTZBcSJPO', 'CUSTOMER', 'ACTIVE');

    DECLARE @cust_id INT = SCOPE_IDENTITY();
    INSERT INTO nguoi_dung (id_tai_khoan, ho, ten, dia_chi)
    VALUES (@cust_id, N'Nguyễn', N'Văn An', N'TP. Hồ Chí Minh, Việt Nam');
END
GO
