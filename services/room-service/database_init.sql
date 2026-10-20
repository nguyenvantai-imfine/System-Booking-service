-- ==============================================================================
-- DATABASE INIT SCRIPT FOR ROOM-SERVICE (SQL SERVER)
-- ==============================================================================
USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'room_service')
BEGIN
    CREATE DATABASE room_service;
END
GO

USE room_service;
GO

-- 1. BẢNG LOẠI PHÒNG (loai_phong)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'loai_phong')
BEGIN
    CREATE TABLE loai_phong (
        id_loai_phong INT IDENTITY(1,1) PRIMARY KEY,
        id_khach_san INT NOT NULL,
        ten_loai_phong NVARCHAR(100) NOT NULL,
        mo_ta NVARCHAR(MAX) NULL,
        suc_chua_nguoi_lon INT NOT NULL DEFAULT 2,
        suc_chua_tre_em INT NOT NULL DEFAULT 1,
        gia_co_ban_mot_dem DECIMAL(18, 2) NOT NULL,
        dien_tich_m2 FLOAT NULL,
        so_luong_phong INT NOT NULL DEFAULT 0,
        ngay_tao DATETIME NOT NULL DEFAULT GETDATE(),
        ngay_cap_nhat DATETIME NOT NULL DEFAULT GETDATE()
    );

    CREATE INDEX idx_loai_phong_khach_san ON loai_phong(id_khach_san);
END
GO

-- 2. BẢNG PHÒNG VẬT LÝ (phong)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'phong')
BEGIN
    CREATE TABLE phong (
        id_phong INT IDENTITY(1,1) PRIMARY KEY,
        id_loai_phong INT NOT NULL,
        id_khach_san INT NOT NULL,
        so_phong NVARCHAR(50) NOT NULL,
        tang INT NULL DEFAULT 1,
        trang_thai NVARCHAR(20) NOT NULL DEFAULT 'AVAILABLE',
        ghi_chu NVARCHAR(255) NULL,
        ngay_tao DATETIME NOT NULL DEFAULT GETDATE(),
        ngay_cap_nhat DATETIME NOT NULL DEFAULT GETDATE(),
        CONSTRAINT fk_phong_loai_phong FOREIGN KEY (id_loai_phong)
            REFERENCES loai_phong(id_loai_phong) ON DELETE CASCADE,
        CONSTRAINT uq_phong_khach_san_so_phong UNIQUE (id_khach_san, so_phong),
        CONSTRAINT chk_trang_thai_phong CHECK (trang_thai IN ('AVAILABLE', 'OCCUPIED', 'MAINTENANCE', 'INACTIVE'))
    );

    CREATE INDEX idx_phong_khach_san ON phong(id_khach_san);
    CREATE INDEX idx_phong_loai_phong ON phong(id_loai_phong);
    CREATE INDEX idx_phong_trang_thai ON phong(trang_thai);
END
GO

-- 3. BẢNG TIỆN ÍCH PHÒNG (tien_ich_phong)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'tien_ich_phong')
BEGIN
    CREATE TABLE tien_ich_phong (
        id_tien_ich INT IDENTITY(1,1) PRIMARY KEY,
        id_loai_phong INT NOT NULL,
        ten_tien_ich NVARCHAR(100) NOT NULL,
        bieu_tuong NVARCHAR(100) NULL,
        CONSTRAINT fk_tien_ich_loai_phong FOREIGN KEY (id_loai_phong)
            REFERENCES loai_phong(id_loai_phong) ON DELETE CASCADE
    );

    CREATE INDEX idx_tien_ich_loai_phong ON tien_ich_phong(id_loai_phong);
END
GO

-- 4. BẢNG QUY TẮC PHÒNG (quy_tac_phong)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'quy_tac_phong')
BEGIN
    CREATE TABLE quy_tac_phong (
        id_quy_tac INT IDENTITY(1,1) PRIMARY KEY,
        id_loai_phong INT NOT NULL,
        tieu_de NVARCHAR(150) NOT NULL,
        cho_phep BIT NOT NULL DEFAULT 0,
        ghi_chu NVARCHAR(255) NULL,
        CONSTRAINT fk_quy_tac_loai_phong FOREIGN KEY (id_loai_phong)
            REFERENCES loai_phong(id_loai_phong) ON DELETE CASCADE
    );

    CREATE INDEX idx_quy_tac_loai_phong ON quy_tac_phong(id_loai_phong);
END
GO

-- 5. BẢNG KHUYẾN MÃI PHÒNG (khuyen_mai_phong)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'khuyen_mai_phong')
BEGIN
    CREATE TABLE khuyen_mai_phong (
        id_khuyen_mai INT IDENTITY(1,1) PRIMARY KEY,
        id_loai_phong INT NOT NULL,
        ma_khuyen_mai NVARCHAR(50) NOT NULL,
        ngay_bat_dau DATE NOT NULL,
        ngay_ket_thuc DATE NOT NULL,
        phan_tram_giam FLOAT NOT NULL,
        mo_ta NVARCHAR(255) NULL,
        CONSTRAINT fk_khuyen_mai_loai_phong FOREIGN KEY (id_loai_phong)
            REFERENCES loai_phong(id_loai_phong) ON DELETE CASCADE
    );

    CREATE INDEX idx_khuyen_mai_loai_phong ON khuyen_mai_phong(id_loai_phong);
END
GO
