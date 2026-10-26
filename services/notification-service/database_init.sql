-- ==============================================================================
-- DATABASE INITIALIZATION SCRIPT CHO NOTIFICATION SERVICE (SQL SERVER)
-- ==============================================================================

IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'notification_service')
BEGIN
    CREATE DATABASE notification_service;
END
GO

USE notification_service;
GO

-- 1. BẢNG THÔNG BÁO (thong_bao)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'thong_bao')
BEGIN
    CREATE TABLE thong_bao (
        id_thong_bao INT IDENTITY(1,1) PRIMARY KEY,
        id_tai_khoan INT NULL,
        loai_thong_bao NVARCHAR(50) NOT NULL, -- BOOKING_CONFIRMED, PAYMENT_SUCCESS, BOOKING_CANCELLED, SYSTEM
        kenh_gui NVARCHAR(20) NOT NULL DEFAULT 'EMAIL', -- EMAIL, IN_APP
        nguoi_nhan NVARCHAR(150) NOT NULL, -- Email address
        trang_thai NVARCHAR(30) NOT NULL DEFAULT 'PENDING', -- SENT, FAILED, PENDING
        ma_booking NVARCHAR(50) NULL,
        ngay_tao DATETIME NOT NULL DEFAULT GETDATE(),
        ngay_gui DATETIME NULL,
        ghi_chu_loi NVARCHAR(MAX) NULL
    );

    CREATE INDEX idx_thong_bao_nguoi_nhan ON thong_bao(nguoi_nhan);
    CREATE INDEX idx_thong_bao_loai ON thong_bao(loai_thong_bao);
    CREATE INDEX idx_thong_bao_trang_thai ON thong_bao(trang_thai);
    CREATE INDEX idx_thong_bao_ma_booking ON thong_bao(ma_booking);
END
GO

IF COL_LENGTH('dbo.thong_bao', 'is_read') IS NULL
BEGIN
    ALTER TABLE dbo.thong_bao
        ADD is_read BIT NOT NULL
            CONSTRAINT df_thong_bao_is_read DEFAULT 0;
END
GO

-- 2. BẢNG NỘI DUNG THÔNG BÁO (noi_dung_thong_bao)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'noi_dung_thong_bao')
BEGIN
    CREATE TABLE noi_dung_thong_bao (
        id_noi_dung INT IDENTITY(1,1) PRIMARY KEY,
        id_thong_bao INT NOT NULL,
        tieu_de NVARCHAR(255) NOT NULL,
        noi_dung_html NVARCHAR(MAX) NOT NULL,
        noi_dung_text NVARCHAR(MAX) NULL,
        du_lieu_dinh_kem NVARCHAR(MAX) NULL, -- Lưu JSON raw data
        CONSTRAINT fk_noi_dung_thong_bao FOREIGN KEY (id_thong_bao)
            REFERENCES thong_bao(id_thong_bao) ON DELETE CASCADE
    );

    CREATE INDEX idx_noi_dung_thong_bao_id ON noi_dung_thong_bao(id_thong_bao);
END
GO
