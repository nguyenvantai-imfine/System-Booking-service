-- ==============================================================================
-- DATABASE INIT SCRIPT FOR BOOKING-SERVICE (SQL SERVER)
-- ==============================================================================
USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'booking_service')
BEGIN
    CREATE DATABASE booking_service;
END
GO

USE booking_service;
GO

-- 1. BẢNG ĐẶT PHÒNG (dat_phong)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'dat_phong')
BEGIN
    CREATE TABLE dat_phong (
        id_dat_phong INT IDENTITY(1,1) PRIMARY KEY,
        ma_booking NVARCHAR(50) NOT NULL UNIQUE,
        id_tai_khoan INT NOT NULL,
        id_khach_san INT NOT NULL,
        ngay_nhan_phong DATE NOT NULL,
        ngay_tra_phong DATE NOT NULL,
        tong_tien DECIMAL(18, 2) NOT NULL,
        trang_thai NVARCHAR(20) NOT NULL DEFAULT 'PENDING_PAYMENT',
        han_giu_cho DATETIME NOT NULL,
        ngay_tao DATETIME NOT NULL DEFAULT GETDATE(),
        ngay_cap_nhat DATETIME NOT NULL DEFAULT GETDATE(),
        CONSTRAINT chk_trang_thai_booking CHECK (trang_thai IN ('PENDING_PAYMENT', 'CONFIRMED', 'CANCELLED', 'COMPLETED', 'REFUNDED'))
    );

    CREATE INDEX idx_dat_phong_ma_booking ON dat_phong(ma_booking);
    CREATE INDEX idx_dat_phong_tai_khoan ON dat_phong(id_tai_khoan);
    CREATE INDEX idx_dat_phong_khach_san ON dat_phong(id_khach_san);
    CREATE INDEX idx_dat_phong_ngay ON dat_phong(ngay_nhan_phong, ngay_tra_phong);
    CREATE INDEX idx_dat_phong_trang_thai ON dat_phong(trang_thai);
END
GO

-- 2. BẢNG CHI TIẾT ĐẶT PHÒNG (chi_tiet_dat_phong)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'chi_tiet_dat_phong')
BEGIN
    CREATE TABLE chi_tiet_dat_phong (
        id_chi_tiet INT IDENTITY(1,1) PRIMARY KEY,
        id_dat_phong INT NOT NULL,
        id_phong INT NOT NULL,
        id_loai_phong INT NOT NULL,
        so_phong NVARCHAR(50) NULL,
        ten_loai_phong NVARCHAR(100) NULL,
        gia_tai_thoi_diem_dat DECIMAL(18, 2) NOT NULL,
        CONSTRAINT fk_chi_tiet_dat_phong FOREIGN KEY (id_dat_phong)
            REFERENCES dat_phong(id_dat_phong) ON DELETE CASCADE
    );

    CREATE INDEX idx_chi_tiet_phong ON chi_tiet_dat_phong(id_phong);
    CREATE INDEX idx_chi_tiet_dat_phong ON chi_tiet_dat_phong(id_dat_phong);
END
GO

-- 3. BẢNG THÔNG TIN KHÁCH Ở (thong_tin_khach_o)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'thong_tin_khach_o')
BEGIN
    CREATE TABLE thong_tin_khach_o (
        id_khach_o INT IDENTITY(1,1) PRIMARY KEY,
        id_dat_phong INT NOT NULL UNIQUE,
        ho_ten NVARCHAR(100) NOT NULL,
        email NVARCHAR(150) NOT NULL,
        sdt NVARCHAR(20) NOT NULL,
        ghi_chu_dac_biet NVARCHAR(MAX) NULL,
        CONSTRAINT fk_khach_o_dat_phong FOREIGN KEY (id_dat_phong)
            REFERENCES dat_phong(id_dat_phong) ON DELETE CASCADE
    );

    CREATE INDEX idx_khach_o_dat_phong ON thong_tin_khach_o(id_dat_phong);
END
GO

-- 4. BẢNG NHẬT KÝ TRẠNG THÁI (nhat_ky_trang_thai_booking)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'nhat_ky_trang_thai_booking')
BEGIN
    CREATE TABLE nhat_ky_trang_thai_booking (
        id_nhat_ky INT IDENTITY(1,1) PRIMARY KEY,
        id_dat_phong INT NOT NULL,
        trang_thai_cu NVARCHAR(50) NULL,
        trang_thai_moi NVARCHAR(50) NOT NULL,
        ly_do NVARCHAR(255) NULL,
        thoi_gian DATETIME NOT NULL DEFAULT GETDATE(),
        CONSTRAINT fk_nhat_ky_dat_phong FOREIGN KEY (id_dat_phong)
            REFERENCES dat_phong(id_dat_phong) ON DELETE CASCADE
    );

    CREATE INDEX idx_nhat_ky_dat_phong ON nhat_ky_trang_thai_booking(id_dat_phong);
END
GO
