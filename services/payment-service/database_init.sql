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

-- Đảm bảo cột ma_giao_dich_gateway của thanh_toan đồng nhất kiểu NVARCHAR(100) nếu DB cũ được tạo từ trước
IF EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'thanh_toan' 
      AND column_name = 'ma_giao_dich_gateway' 
      AND data_type = 'varchar'
)
BEGIN
    IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'ix_thanh_toan_ma_giao_dich_gateway' AND object_id = OBJECT_ID('thanh_toan'))
        DROP INDEX ix_thanh_toan_ma_giao_dich_gateway ON thanh_toan;

    IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_thanh_toan_gateway' AND object_id = OBJECT_ID('thanh_toan'))
        DROP INDEX idx_thanh_toan_gateway ON thanh_toan;

    ALTER TABLE thanh_toan ALTER COLUMN ma_giao_dich_gateway NVARCHAR(100) NOT NULL;

    CREATE UNIQUE INDEX ix_thanh_toan_ma_giao_dich_gateway ON thanh_toan(ma_giao_dich_gateway);
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

-- 3. BẢNG GIAO DỊCH OTP (giao_dich_otp)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'giao_dich_otp')
BEGIN
    CREATE TABLE giao_dich_otp (
        id_otp INT IDENTITY(1,1) PRIMARY KEY,
        ma_giao_dich_gateway NVARCHAR(100) NOT NULL,
        email NVARCHAR(150) NOT NULL,
        otp_code NVARCHAR(6) NOT NULL,
        thoi_gian_tao DATETIME NOT NULL DEFAULT GETDATE(),
        thoi_gian_het_han DATETIME NOT NULL,
        da_su_dung BIT NOT NULL DEFAULT 0,
        so_lan_thu INT NOT NULL DEFAULT 0,
        CONSTRAINT fk_otp_thanh_toan FOREIGN KEY (ma_giao_dich_gateway)
            REFERENCES thanh_toan(ma_giao_dich_gateway) ON DELETE CASCADE
    );

    CREATE INDEX idx_otp_txn ON giao_dich_otp(ma_giao_dich_gateway);
END
GO

IF EXISTS (SELECT * FROM sys.tables WHERE name = 'giao_dich_otp')
   AND NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_otp_txn' AND object_id = OBJECT_ID('giao_dich_otp'))
BEGIN
    CREATE INDEX idx_otp_txn ON giao_dich_otp(ma_giao_dich_gateway);
END
GO

