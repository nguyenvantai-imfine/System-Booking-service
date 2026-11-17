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
        ngay_cap_nhat DATETIME NOT NULL DEFAULT GETDATE(),
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
        ngay_cap_nhat DATETIME NOT NULL DEFAULT GETDATE(),
        CONSTRAINT fk_nguoi_dung_tai_khoan FOREIGN KEY (id_tai_khoan) 
            REFERENCES tai_khoan(id_tai_khoan) ON DELETE CASCADE
    );

    CREATE INDEX idx_nguoi_dung_tai_khoan ON nguoi_dung(id_tai_khoan);
END
GO
