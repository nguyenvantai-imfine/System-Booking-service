-- ==============================================================================
-- DATABASE INIT SCRIPT FOR PAYMENT-SERVICE (SQL SERVER)
-- ==============================================================================
USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'payment_service')
BEGIN
    CREATE DATABASE payment_service;
END
GO

USE payment_service;
GO

-- 1. BẢNG THANH TOÁN (thanh_toan)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'thanh_toan')
BEGIN
    CREATE TABLE thanh_toan (
        id_thanh_toan INT IDENTITY(1,1) PRIMARY KEY,
        id_dat_phong INT NOT NULL,
        ma_booking NVARCHAR(50) NOT NULL,
        so_tien DECIMAL(18, 2) NOT NULL,
        phuong_thuc NVARCHAR(20) NOT NULL DEFAULT 'VNPAY',
        trang_thai NVARCHAR(20) NOT NULL DEFAULT 'PENDING',
        ma_giao_dich_gateway NVARCHAR(100) NOT NULL UNIQUE,
        payment_url NVARCHAR(500) NULL,
        ngay_tao DATETIME NOT NULL DEFAULT GETDATE(),
        ngay_thanh_toan DATETIME NULL,
        ghi_chu NVARCHAR(255) NULL,
        CONSTRAINT chk_phuong_thuc CHECK (phuong_thuc IN ('VNPAY', 'MOMO', 'CREDIT_CARD', 'CASH')),
        CONSTRAINT chk_trang_thai_tt CHECK (trang_thai IN ('PENDING', 'SUCCESS', 'FAILED', 'REFUNDED'))
    );

    CREATE INDEX idx_thanh_toan_booking ON thanh_toan(id_dat_phong, ma_booking);
    CREATE INDEX idx_thanh_toan_gateway ON thanh_toan(ma_giao_dich_gateway);
    CREATE INDEX idx_thanh_toan_trang_thai ON thanh_toan(trang_thai);
END
GO

-- 2. BẢNG HOÀN TIỀN (hoan_tien)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'hoan_tien')
BEGIN
    CREATE TABLE hoan_tien (
        id_hoan_tien INT IDENTITY(1,1) PRIMARY KEY,
        id_thanh_toan INT NOT NULL,
        so_tien_hoan DECIMAL(18, 2) NOT NULL,
        ly_do NVARCHAR(255) NULL,
        ngay_hoan DATETIME NOT NULL DEFAULT GETDATE(),
        CONSTRAINT fk_hoan_tien_thanh_toan FOREIGN KEY (id_thanh_toan)
            REFERENCES thanh_toan(id_thanh_toan) ON DELETE CASCADE
    );

    CREATE INDEX idx_hoan_tien_thanh_toan ON hoan_tien(id_thanh_toan);
END
GO
