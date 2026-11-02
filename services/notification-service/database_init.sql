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
        event_key NVARCHAR(64) NULL,
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

IF COL_LENGTH('dbo.thong_bao', 'event_key') IS NULL
BEGIN
    ALTER TABLE dbo.thong_bao ADD event_key NVARCHAR(64) NULL;
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'uq_thong_bao_event_key'
      AND object_id = OBJECT_ID('dbo.thong_bao')
)
BEGIN
    CREATE UNIQUE INDEX uq_thong_bao_event_key
        ON dbo.thong_bao(event_key)
        WHERE event_key IS NOT NULL;
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
            REFERENCES thong_bao(id_thong_bao) ON DELETE CASCADE,
        CONSTRAINT uq_noi_dung_thong_bao_id UNIQUE (id_thong_bao)
    );

END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'uq_noi_dung_thong_bao_id'
      AND object_id = OBJECT_ID('dbo.noi_dung_thong_bao')
)
BEGIN
    IF EXISTS (
        SELECT id_thong_bao
        FROM dbo.noi_dung_thong_bao
        GROUP BY id_thong_bao
        HAVING COUNT(*) > 1
    )
    BEGIN
        THROW 51000, 'Duplicate notification content rows must be reviewed before applying the unique constraint.', 1;
    END

    CREATE UNIQUE INDEX uq_noi_dung_thong_bao_id
        ON dbo.noi_dung_thong_bao(id_thong_bao);
END
GO
