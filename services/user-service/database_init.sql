-- ==============================================================================
-- DATABASE INIT SCRIPT FOR USER-SERVICE (SQL SERVER)
-- ==============================================================================
USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'user_service')
BEGIN
    CREATE DATABASE user_service;
END
GO

USE user_service;
GO

-- 1. BẢNG TÀI KHOẢN (tai_khoan)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'tai_khoan')
BEGIN
    CREATE TABLE tai_khoan (
        id_tai_khoan INT IDENTITY(1,1) PRIMARY KEY,
        ten_dang_nhap NVARCHAR(50) NOT NULL UNIQUE,
        email NVARCHAR(150) NOT NULL UNIQUE,
        sdt NVARCHAR(20) NULL,
        mat_khau_hash NVARCHAR(255) NOT NULL,
        vai_tro NVARCHAR(20) NOT NULL DEFAULT 'CUSTOMER',
        trang_thai NVARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
        ngay_tao DATETIME NOT NULL DEFAULT GETDATE(),
        CONSTRAINT chk_vai_tro CHECK (vai_tro IN ('ADMIN', 'PARTNER', 'CUSTOMER')),
        CONSTRAINT chk_trang_thai CHECK (trang_thai IN ('ACTIVE', 'LOCKED', 'INACTIVE'))
    );

    CREATE INDEX idx_tai_khoan_email ON tai_khoan(email);
    CREATE INDEX idx_tai_khoan_ten_dang_nhap ON tai_khoan(ten_dang_nhap);
    CREATE INDEX idx_tai_khoan_vai_tro ON tai_khoan(vai_tro);
END
GO

-- 2. BẢNG NGƯỜI DÙNG (nguoi_dung - quan hệ 1:1 với tai_khoan)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'nguoi_dung')
BEGIN
    CREATE TABLE nguoi_dung (
        id_nguoi_dung INT IDENTITY(1,1) PRIMARY KEY,
        id_tai_khoan INT NOT NULL UNIQUE,
        ho NVARCHAR(50) NULL,
        ten NVARCHAR(50) NULL,
        ngay_sinh DATE NULL,
        gioi_tinh NVARCHAR(10) NULL,
        dia_chi NVARCHAR(255) NULL,
        avatar NVARCHAR(500) NULL,
        cccd NVARCHAR(20) NULL,
        CONSTRAINT fk_nguoi_dung_tai_khoan FOREIGN KEY (id_tai_khoan) 
            REFERENCES tai_khoan(id_tai_khoan) ON DELETE CASCADE
    );

    CREATE INDEX idx_nguoi_dung_tai_khoan ON nguoi_dung(id_tai_khoan);
END
GO

-- 3. TÀI KHOẢN MẪU (Password bcrypt hash của "123456")
-- Hash: $2b$12$e8yN8bVbIqG0WzN8mD6f4eR9r2b6m5N8yN8bVbIqG0WzN8mD6f4eR
IF NOT EXISTS (SELECT * FROM tai_khoan WHERE ten_dang_nhap = 'admin')
BEGIN
    INSERT INTO tai_khoan (ten_dang_nhap, email, sdt, mat_khau_hash, vai_tro, trang_thai)
    VALUES ('admin', 'admin@hotel.com', '0900000001', '$2b$12$Kqn2T4eXTRDp8BblqbANu.QelIG.Zhr6VHT6zNXfiSnhgeKJhLV6W', 'ADMIN', 'ACTIVE');

    DECLARE @admin_id INT = SCOPE_IDENTITY();
    INSERT INTO nguoi_dung (id_tai_khoan, ho, ten, dia_chi)
    VALUES (@admin_id, N'Quản Trị', N'Viên', N'Hà Nội, Việt Nam');
END
GO

IF NOT EXISTS (SELECT * FROM tai_khoan WHERE ten_dang_nhap = 'partner1')
BEGIN
    INSERT INTO tai_khoan (ten_dang_nhap, email, sdt, mat_khau_hash, vai_tro, trang_thai)
    VALUES ('partner1', 'partner@hotel.com', '0900000002', '$2b$12$Kqn2T4eXTRDp8BblqbANu.QelIG.Zhr6VHT6zNXfiSnhgeKJhLV6W', 'PARTNER', 'ACTIVE');

    DECLARE @partner_id INT = SCOPE_IDENTITY();
    INSERT INTO nguoi_dung (id_tai_khoan, ho, ten, dia_chi)
    VALUES (@partner_id, N'Chủ Khách Sạn', N'Đại Dương', N'Đà Nẵng, Việt Nam');
END
GO

IF NOT EXISTS (SELECT * FROM tai_khoan WHERE ten_dang_nhap = 'customer1')
BEGIN
    INSERT INTO tai_khoan (ten_dang_nhap, email, sdt, mat_khau_hash, vai_tro, trang_thai)
    VALUES ('customer1', 'customer@gmail.com', '0900000003', '$2b$12$Kqn2T4eXTRDp8BblqbANu.QelIG.Zhr6VHT6zNXfiSnhgeKJhLV6W', 'CUSTOMER', 'ACTIVE');

    DECLARE @cust_id INT = SCOPE_IDENTITY();
    INSERT INTO nguoi_dung (id_tai_khoan, ho, ten, dia_chi)
    VALUES (@cust_id, N'Nguyễn', N'Văn An', N'TP. Hồ Chí Minh, Việt Nam');
END
GO
