-- ==============================================================================
-- HOTEL SERVICE DATABASE SCRIPT (SQL SERVER / T-SQL)
-- Dành cho hệ thống Booking Service - Microservice Hotel
-- ==============================================================================
-- File này bao gồm 2 phần:
--   PHẦN 1: MIGRATION SCRIPT (Dành cho Database ĐÃ CÓ - thêm bảng, thêm cột an toàn)
--   PHẦN 2: TẠO MỚI TỪ ĐẦU (Dành cho Database MỚI TINH)
-- ==============================================================================

USE hotel_service;
GO

-- ==============================================================================
-- PHẦN 1: MIGRATION - CẬP NHẬT BỔ SUNG VÀO DATABASE ĐANG HOẠT ĐỘNG
-- (Chạy phần này nếu bạn đã có sẵn các bảng khach_san cũ và không muốn mất dữ liệu)
-- ==============================================================================

PRINT N'>>> Đang tiến hành kiểm tra và cập nhật cấu trúc database hotel_service...';

-- 1.1 Bổ sung các cột địa chỉ chi tiết, tọa độ và người liên hệ vào bảng `khach_san`
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'phuong_xa')
BEGIN
    ALTER TABLE [dbo].[khach_san] ADD [phuong_xa] NVARCHAR(100) NULL;
    PRINT N'-- Đã thêm cột [phuong_xa] vào bảng [khach_san]';
END
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'quan_huyen')
BEGIN
    ALTER TABLE [dbo].[khach_san] ADD [quan_huyen] NVARCHAR(100) NULL;
    PRINT N'-- Đã thêm cột [quan_huyen] vào bảng [khach_san]';
END
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'quoc_gia')
BEGIN
    ALTER TABLE [dbo].[khach_san] ADD [quoc_gia] NVARCHAR(100) NULL DEFAULT N'Việt Nam';
    PRINT N'-- Đã thêm cột [quoc_gia] vào bảng [khach_san]';
END
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'kinh_do')
BEGIN
    ALTER TABLE [dbo].[khach_san] ADD [kinh_do] FLOAT NULL;
    PRINT N'-- Đã thêm cột [kinh_do] vào bảng [khach_san]';
END
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'vi_do')
BEGIN
    ALTER TABLE [dbo].[khach_san] ADD [vi_do] FLOAT NULL;
    PRINT N'-- Đã thêm cột [vi_do] vào bảng [khach_san]';
END
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'ma_buu_chinh')
BEGIN
    ALTER TABLE [dbo].[khach_san] ADD [ma_buu_chinh] VARCHAR(20) NULL;
    PRINT N'-- Đã thêm cột [ma_buu_chinh] vào bảng [khach_san]';
END
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'ten_nguoi_lien_he')
BEGIN
    ALTER TABLE [dbo].[khach_san] ADD [ten_nguoi_lien_he] NVARCHAR(100) NULL;
    PRINT N'-- Đã thêm cột [ten_nguoi_lien_he] vào bảng [khach_san]';
END
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'sdt_nguoi_lien_he')
BEGIN
    ALTER TABLE [dbo].[khach_san] ADD [sdt_nguoi_lien_he] VARCHAR(20) NULL;
    PRINT N'-- Đã thêm cột [sdt_nguoi_lien_he] vào bảng [khach_san]';
END
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'ngay_tao')
BEGIN
    ALTER TABLE [dbo].[khach_san] ADD [ngay_tao] DATETIME NOT NULL DEFAULT GETDATE();
    PRINT N'-- Đã thêm cột [ngay_tao] vào bảng [khach_san]';
END
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'ngay_cap_nhat')
BEGIN
    ALTER TABLE [dbo].[khach_san] ADD [ngay_cap_nhat] DATETIME NOT NULL DEFAULT GETDATE();
    PRINT N'-- Đã thêm cột [ngay_cap_nhat] vào bảng [khach_san]';
END
GO

-- 1.2 Soft Delete Pattern: Bổ sung `is_deleted` và `deleted_at`
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'is_deleted')
BEGIN
    ALTER TABLE [dbo].[khach_san] ADD [is_deleted] BIT NOT NULL DEFAULT 0;
    PRINT N'-- Đã thêm cột [is_deleted] vào bảng [khach_san] (Soft Delete)';
END
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'deleted_at')
BEGIN
    ALTER TABLE [dbo].[khach_san] ADD [deleted_at] DATETIME NULL;
    PRINT N'-- Đã thêm cột [deleted_at] vào bảng [khach_san] (Soft Delete Timestamp)';
END
GO

-- 1.3 Chuẩn hóa dữ liệu cũ & Thêm CHECK CONSTRAINT cho `trang_thai` (Enum: HOAT_DONG, TAM_DUNG, CHO_DUYET, DA_XOA)
UPDATE [dbo].[khach_san] SET [trang_thai] = 'HOAT_DONG' WHERE [trang_thai] = N'Hoạt động' OR [trang_thai] IS NULL;
UPDATE [dbo].[khach_san] SET [trang_thai] = 'TAM_DUNG' WHERE [trang_thai] = N'Ngừng hoạt động' OR [trang_thai] = N'Tạm dừng';
UPDATE [dbo].[khach_san] SET [trang_thai] = 'CHO_DUYET' WHERE [trang_thai] = N'Chờ duyệt';
UPDATE [dbo].[khach_san] SET [trang_thai] = 'DA_XOA' WHERE [trang_thai] = N'Đã xóa' OR [is_deleted] = 1;
GO

-- Xóa constraint cũ nếu đã tồn tại để cập nhật giá trị mới 'DA_XOA'
IF EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_khach_san_trang_thai')
BEGIN
    ALTER TABLE [dbo].[khach_san] DROP CONSTRAINT CK_khach_san_trang_thai;
END
GO

ALTER TABLE [dbo].[khach_san]
ADD CONSTRAINT CK_khach_san_trang_thai CHECK ([trang_thai] IN ('HOAT_DONG', 'TAM_DUNG', 'CHO_DUYET', 'DA_XOA'));
PRINT N'-- Đã thêm CHECK CONSTRAINT [CK_khach_san_trang_thai] cho [trang_thai] (bao gồm DA_XOA)';
GO

-- 1.4 Bổ sung cột phân loại chính sách `loai_chinh_sach` vào bảng `quy_tac_khach_san`
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[quy_tac_khach_san]') AND name = 'loai_chinh_sach')
BEGIN
    ALTER TABLE [dbo].[quy_tac_khach_san] ADD [loai_chinh_sach] NVARCHAR(50) NOT NULL DEFAULT N'QUY_DINH_CHUNG';
    PRINT N'-- Đã thêm cột [loai_chinh_sach] vào bảng [quy_tac_khach_san]';
END
GO

IF NOT EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_quy_tac_loai_chinh_sach')
BEGIN
    ALTER TABLE [dbo].[quy_tac_khach_san]
    ADD CONSTRAINT CK_quy_tac_loai_chinh_sach CHECK ([loai_chinh_sach] IN ('CHECK_IN_OUT', 'HUY_PHONG', 'TRE_EM', 'DAT_COC', 'QUY_DINH_CHUNG'));
    PRINT N'-- Đã thêm CHECK CONSTRAINT [CK_quy_tac_loai_chinh_sach]';
END
GO

-- 1.5 Tạo bảng MỚI: `hinh_anh_khach_san` (Quản lý hình ảnh khách sạn)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[hinh_anh_khach_san]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[hinh_anh_khach_san] (
        [id_hinh_anh] INT IDENTITY(1,1) NOT NULL,
        [id_khach_san] INT NOT NULL,
        [duong_dan_anh] NVARCHAR(500) NOT NULL,
        [loai_anh] NVARCHAR(50) NULL DEFAULT N'chung', -- ngoai_canh, sanh, phong_ngu, tien_ich, khac
        [la_anh_chinh] BIT NOT NULL DEFAULT 0,          -- 1: Ảnh đại diện hiển thị ở danh sách
        [thu_tu] INT NOT NULL DEFAULT 0,                -- Thứ tự ưu tiên hiển thị
        [ngay_tao] DATETIME NOT NULL DEFAULT GETDATE(),

        CONSTRAINT [PK_hinh_anh_khach_san] PRIMARY KEY CLUSTERED ([id_hinh_anh] ASC),
        CONSTRAINT [FK_hinh_anh_khach_san] FOREIGN KEY ([id_khach_san])
            REFERENCES [dbo].[khach_san] ([id_khach_san])
            ON DELETE CASCADE
            ON UPDATE CASCADE
    );
    PRINT N'-- Đã tạo mới thành công bảng [hinh_anh_khach_san]';
END
GO

-- 1.6 Đánh Index tối ưu hóa truy vấn tìm kiếm
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_khach_san_dia_ly' AND object_id = OBJECT_ID(N'[dbo].[khach_san]'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_khach_san_dia_ly]
    ON [dbo].[khach_san] ([thanh_pho], [tinh], [quan_huyen], [trang_thai], [is_deleted]);
    PRINT N'-- Đã tạo Index [IX_khach_san_dia_ly]';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_khach_san_active' AND object_id = OBJECT_ID(N'[dbo].[khach_san]'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_khach_san_active]
    ON [dbo].[khach_san] ([is_deleted], [trang_thai]);
    PRINT N'-- Đã tạo Index [IX_khach_san_active] (Hỗ trợ lọc khách sạn khả dụng)';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_khach_san_partner' AND object_id = OBJECT_ID(N'[dbo].[khach_san]'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_khach_san_partner]
    ON [dbo].[khach_san] ([id_tai_khoan], [is_deleted]);
    PRINT N'-- Đã tạo Index [IX_khach_san_partner]';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_hinh_anh_khach_san' AND object_id = OBJECT_ID(N'[dbo].[hinh_anh_khach_san]'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_hinh_anh_khach_san]
    ON [dbo].[hinh_anh_khach_san] ([id_khach_san], [la_anh_chinh], [thu_tu]);
    PRINT N'-- Đã tạo Index [IX_hinh_anh_khach_san]';
END
GO

PRINT N'>>> Migration hoàn tất thành công!';
GO

-- ==============================================================================
-- PHẦN 2: DDL ĐẦY ĐỦ CHO TRƯỜNG HỢP SETUP DATABASE TỪ CON SỐ 0 (THAM KHẢO)
-- ==============================================================================
/*
CREATE DATABASE hotel_service;
GO
USE hotel_service;
GO

-- 1. BẢNG KHÁCH SẠN
CREATE TABLE khach_san (
    id_khach_san INT IDENTITY(1,1) PRIMARY KEY,
    id_tai_khoan INT NOT NULL,
    ten_khach_san NVARCHAR(255) NOT NULL,
    email_khach_san VARCHAR(100) NULL,
    sdt_khach_san VARCHAR(20) NULL,
    trang_thai VARCHAR(50) NOT NULL DEFAULT 'HOAT_DONG',
    
    dia_chi NVARCHAR(255) NULL,
    phuong_xa NVARCHAR(100) NULL,
    quan_huyen NVARCHAR(100) NULL,
    thanh_pho NVARCHAR(100) NULL,
    tinh NVARCHAR(100) NULL,
    quoc_gia NVARCHAR(100) DEFAULT N'Việt Nam',
    kinh_do FLOAT NULL,
    vi_do FLOAT NULL,
    ma_buu_chinh VARCHAR(20) NULL,
    
    ten_nguoi_lien_he NVARCHAR(100) NULL,
    sdt_nguoi_lien_he VARCHAR(20) NULL,
    
    ngay_tao DATETIME DEFAULT GETDATE(),
    ngay_cap_nhat DATETIME DEFAULT GETDATE(),
    
    is_deleted BIT NOT NULL DEFAULT 0,
    deleted_at DATETIME NULL,

    CONSTRAINT CK_khach_san_trang_thai CHECK (trang_thai IN ('HOAT_DONG', 'TAM_DUNG', 'CHO_DUYET'))
);

-- 2. BẢNG HÌNH ẢNH
CREATE TABLE hinh_anh_khach_san (
    id_hinh_anh INT IDENTITY(1,1) PRIMARY KEY,
    id_khach_san INT NOT NULL,
    duong_dan_anh NVARCHAR(500) NOT NULL,
    loai_anh NVARCHAR(50) DEFAULT N'chung',
    la_anh_chinh BIT DEFAULT 0,
    thu_tu INT DEFAULT 0,
    ngay_tao DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_hinh_anh_khach_san FOREIGN KEY (id_khach_san) 
        REFERENCES khach_san(id_khach_san) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 3. BẢNG THÔNG TIN KHÁCH SẠN
CREATE TABLE thong_tin_khach_san (
    id_thong_tin INT IDENTITY(1,1) PRIMARY KEY,
    id_khach_san INT NOT NULL,
    loai_thong_tin NVARCHAR(255) NOT NULL,
    noi_dung NVARCHAR(MAX) NULL,
    CONSTRAINT FK_thong_tin_khach_san FOREIGN KEY (id_khach_san) 
        REFERENCES khach_san(id_khach_san) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 4. BẢNG QUY TẮC & CHÍNH SÁCH KHÁCH SẠN
CREATE TABLE quy_tac_khach_san (
    id_quy_tac INT IDENTITY(1,1) PRIMARY KEY,
    id_khach_san INT NOT NULL,
    loai_chinh_sach NVARCHAR(50) DEFAULT N'QUY_DINH_CHUNG',
    ten NVARCHAR(255) NOT NULL,
    gia_tri_chon NVARCHAR(255) NULL,
    mo_ta NVARCHAR(MAX) NULL,
    CONSTRAINT FK_quy_tac_khach_san FOREIGN KEY (id_khach_san) 
        REFERENCES khach_san(id_khach_san) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 5. BẢNG DANH MỤC TIỆN ÍCH
CREATE TABLE danh_muc_tien_ich (
    id_danh_muc INT IDENTITY(1,1) PRIMARY KEY,
    id_khach_san INT NOT NULL,
    ten_danh_muc NVARCHAR(255) NOT NULL,
    icon_danh_muc NVARCHAR(255) NULL,
    CONSTRAINT FK_danh_muc_khach_san FOREIGN KEY (id_khach_san) 
        REFERENCES khach_san(id_khach_san) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 6. BẢNG CHI TIẾT TIỆN NGHI
CREATE TABLE chi_tiet_tien_nghi (
    id_tien_nghi INT IDENTITY(1,1) PRIMARY KEY,
    id_danh_muc INT NOT NULL,
    ten_tien_ich NVARCHAR(255) NOT NULL,
    CONSTRAINT FK_chi_tiet_danh_muc FOREIGN KEY (id_danh_muc) 
        REFERENCES danh_muc_tien_ich(id_danh_muc) ON DELETE CASCADE ON UPDATE CASCADE
);
*/
