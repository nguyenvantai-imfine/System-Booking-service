-- ==============================================================================
-- HOTEL SERVICE DATABASE INITIALIZATION & MIGRATION SCRIPT (SQL SERVER / T-SQL)
-- Hệ thống Microservices System-Booking-service
-- Tự động chạy khi khởi tạo container SQL Server
-- ==============================================================================

-- 1. TẠO CƠ SỞ DỮ LIỆU NẾU CHƯA TỒN TẠI
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'hotel_service')
BEGIN
    PRINT N'>>> Chưa có CSDL [hotel_service]. Đang tiến hành tạo mới CSDL...';
    CREATE DATABASE [hotel_service];
    PRINT N'-- Đã tạo thành công database [hotel_service]';
END
ELSE
BEGIN
    PRINT N'>>> Database [hotel_service] đã tồn tại.';
END
GO

USE [hotel_service];
GO

PRINT N'>>> Đang tiến hành kiểm tra và khởi tạo/cập nhật bảng dữ liệu...';
GO

-- ==============================================================================
-- 2. TẠO HOẶC CẬP NHẬT BẢNG `khach_san`
-- ==============================================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND type in (N'U'))
BEGIN
    PRINT N'>>> Bảng [khach_san] chưa tồn tại. Đang tạo mới...';
    CREATE TABLE [dbo].[khach_san] (
        [id_khach_san] INT IDENTITY(1,1) NOT NULL,
        [id_tai_khoan] INT NOT NULL,
        [ten_khach_san] NVARCHAR(255) NOT NULL,
        [email_khach_san] VARCHAR(100) NULL,
        [sdt_khach_san] VARCHAR(20) NULL,
        [trang_thai] VARCHAR(50) NOT NULL DEFAULT 'HOAT_DONG',
        
        [dia_chi] NVARCHAR(255) NULL,
        [phuong_xa] NVARCHAR(100) NULL,
        [quan_huyen] NVARCHAR(100) NULL,
        [thanh_pho] NVARCHAR(100) NULL,
        [tinh] NVARCHAR(100) NULL,
        [quoc_gia] NVARCHAR(100) NULL DEFAULT N'Việt Nam',
        [kinh_do] FLOAT NULL,
        [vi_do] FLOAT NULL,
        [ma_buu_chinh] VARCHAR(20) NULL,
        
        [ten_nguoi_lien_he] NVARCHAR(100) NULL,
        [sdt_nguoi_lien_he] VARCHAR(20) NULL,
        
        [ngay_tao] DATETIME NOT NULL DEFAULT GETDATE(),
        [ngay_cap_nhat] DATETIME NOT NULL DEFAULT GETDATE(),
        
        [is_deleted] BIT NOT NULL DEFAULT 0,
        [deleted_at] DATETIME NULL,

        CONSTRAINT [PK_khach_san] PRIMARY KEY CLUSTERED ([id_khach_san] ASC),
        CONSTRAINT [CK_khach_san_trang_thai] CHECK ([trang_thai] IN ('HOAT_DONG', 'TAM_DUNG', 'CHO_DUYET', 'DA_XOA'))
    );
    PRINT N'-- Đã tạo mới thành công bảng [khach_san]';
END
ELSE
BEGIN
    PRINT N'>>> Bảng [khach_san] đã có sẵn. Đang kiểm tra bổ sung cột...';
    
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'phuong_xa')
        ALTER TABLE [dbo].[khach_san] ADD [phuong_xa] NVARCHAR(100) NULL;

    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'quan_huyen')
        ALTER TABLE [dbo].[khach_san] ADD [quan_huyen] NVARCHAR(100) NULL;

    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'quoc_gia')
        ALTER TABLE [dbo].[khach_san] ADD [quoc_gia] NVARCHAR(100) NULL DEFAULT N'Việt Nam';

    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'kinh_do')
        ALTER TABLE [dbo].[khach_san] ADD [kinh_do] FLOAT NULL;

    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'vi_do')
        ALTER TABLE [dbo].[khach_san] ADD [vi_do] FLOAT NULL;

    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'ma_buu_chinh')
        ALTER TABLE [dbo].[khach_san] ADD [ma_buu_chinh] VARCHAR(20) NULL;

    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'ten_nguoi_lien_he')
        ALTER TABLE [dbo].[khach_san] ADD [ten_nguoi_lien_he] NVARCHAR(100) NULL;

    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'sdt_nguoi_lien_he')
        ALTER TABLE [dbo].[khach_san] ADD [sdt_nguoi_lien_he] VARCHAR(20) NULL;

    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'ngay_tao')
        ALTER TABLE [dbo].[khach_san] ADD [ngay_tao] DATETIME NOT NULL DEFAULT GETDATE();

    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'ngay_cap_nhat')
        ALTER TABLE [dbo].[khach_san] ADD [ngay_cap_nhat] DATETIME NOT NULL DEFAULT GETDATE();

    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'is_deleted')
        ALTER TABLE [dbo].[khach_san] ADD [is_deleted] BIT NOT NULL DEFAULT 0;

    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[khach_san]') AND name = 'deleted_at')
        ALTER TABLE [dbo].[khach_san] ADD [deleted_at] DATETIME NULL;

    -- Chuẩn hóa dữ liệu trạng thái
    UPDATE [dbo].[khach_san] SET [trang_thai] = 'HOAT_DONG' WHERE [trang_thai] = N'Hoạt động' OR [trang_thai] IS NULL;
    UPDATE [dbo].[khach_san] SET [trang_thai] = 'TAM_DUNG' WHERE [trang_thai] = N'Ngừng hoạt động' OR [trang_thai] = N'Tạm dừng';
    UPDATE [dbo].[khach_san] SET [trang_thai] = 'CHO_DUYET' WHERE [trang_thai] = N'Chờ duyệt';
    UPDATE [dbo].[khach_san] SET [trang_thai] = 'DA_XOA' WHERE [trang_thai] = N'Đã xóa' OR [is_deleted] = 1;

    IF EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_khach_san_trang_thai')
        ALTER TABLE [dbo].[khach_san] DROP CONSTRAINT [CK_khach_san_trang_thai];

    ALTER TABLE [dbo].[khach_san]
    ADD CONSTRAINT [CK_khach_san_trang_thai] CHECK ([trang_thai] IN ('HOAT_DONG', 'TAM_DUNG', 'CHO_DUYET', 'DA_XOA'));
END
GO

-- ==============================================================================
-- 3. TẠO BẢNG `hinh_anh_khach_san`
-- ==============================================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[hinh_anh_khach_san]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[hinh_anh_khach_san] (
        [id_hinh_anh] INT IDENTITY(1,1) NOT NULL,
        [id_khach_san] INT NOT NULL,
        [duong_dan_anh] NVARCHAR(500) NOT NULL,
        [loai_anh] NVARCHAR(50) NULL DEFAULT N'chung',
        [la_anh_chinh] BIT NOT NULL DEFAULT 0,
        [thu_tu] INT NOT NULL DEFAULT 0,
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

-- ==============================================================================
-- 4. TẠO BẢNG `thong_tin_khach_san`
-- ==============================================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[thong_tin_khach_san]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[thong_tin_khach_san] (
        [id_thong_tin] INT IDENTITY(1,1) NOT NULL,
        [id_khach_san] INT NOT NULL,
        [loai_thong_tin] NVARCHAR(255) NOT NULL,
        [noi_dung] NVARCHAR(MAX) NULL,

        CONSTRAINT [PK_thong_tin_khach_san] PRIMARY KEY CLUSTERED ([id_thong_tin] ASC),
        CONSTRAINT [FK_thong_tin_khach_san] FOREIGN KEY ([id_khach_san])
            REFERENCES [dbo].[khach_san] ([id_khach_san])
            ON DELETE CASCADE
            ON UPDATE CASCADE
    );
    PRINT N'-- Đã tạo mới thành công bảng [thong_tin_khach_san]';
END
GO

-- ==============================================================================
-- 5. TẠO HOẶC CẬP NHẬT BẢNG `quy_tac_khach_san`
-- ==============================================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[quy_tac_khach_san]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[quy_tac_khach_san] (
        [id_quy_tac] INT IDENTITY(1,1) NOT NULL,
        [id_khach_san] INT NOT NULL,
        [loai_chinh_sach] NVARCHAR(50) NOT NULL DEFAULT N'QUY_DINH_CHUNG',
        [ten] NVARCHAR(255) NOT NULL,
        [gia_tri_chon] NVARCHAR(255) NULL,
        [mo_ta] NVARCHAR(MAX) NULL,

        CONSTRAINT [PK_quy_tac_khach_san] PRIMARY KEY CLUSTERED ([id_quy_tac] ASC),
        CONSTRAINT [FK_quy_tac_khach_san] FOREIGN KEY ([id_khach_san])
            REFERENCES [dbo].[khach_san] ([id_khach_san])
            ON DELETE CASCADE
            ON UPDATE CASCADE,
        CONSTRAINT [CK_quy_tac_loai_chinh_sach] CHECK ([loai_chinh_sach] IN ('CHECK_IN_OUT', 'HUY_PHONG', 'TRE_EM', 'DAT_COC', 'QUY_DINH_CHUNG'))
    );
    PRINT N'-- Đã tạo mới thành công bảng [quy_tac_khach_san]';
END
ELSE
BEGIN
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[quy_tac_khach_san]') AND name = 'loai_chinh_sach')
    BEGIN
        ALTER TABLE [dbo].[quy_tac_khach_san] ADD [loai_chinh_sach] NVARCHAR(50) NOT NULL DEFAULT N'QUY_DINH_CHUNG';
        PRINT N'-- Đã thêm cột [loai_chinh_sach] vào bảng [quy_tac_khach_san]';
    END

    IF NOT EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_quy_tac_loai_chinh_sach')
    BEGIN
        ALTER TABLE [dbo].[quy_tac_khach_san]
        ADD CONSTRAINT [CK_quy_tac_loai_chinh_sach] CHECK ([loai_chinh_sach] IN ('CHECK_IN_OUT', 'HUY_PHONG', 'TRE_EM', 'DAT_COC', 'QUY_DINH_CHUNG'));
    END
END
GO

-- ==============================================================================
-- 6. TẠO BẢNG `danh_muc_tien_ich`
-- ==============================================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[danh_muc_tien_ich]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[danh_muc_tien_ich] (
        [id_danh_muc] INT IDENTITY(1,1) NOT NULL,
        [id_khach_san] INT NOT NULL,
        [ten_danh_muc] NVARCHAR(255) NOT NULL,
        [icon_danh_muc] NVARCHAR(255) NULL,

        CONSTRAINT [PK_danh_muc_tien_ich] PRIMARY KEY CLUSTERED ([id_danh_muc] ASC),
        CONSTRAINT [FK_danh_muc_khach_san] FOREIGN KEY ([id_khach_san])
            REFERENCES [dbo].[khach_san] ([id_khach_san])
            ON DELETE CASCADE
            ON UPDATE CASCADE
    );
    PRINT N'-- Đã tạo mới thành công bảng [danh_muc_tien_ich]';
END
GO

-- ==============================================================================
-- 7. TẠO BẢNG `chi_tiet_tien_nghi`
-- ==============================================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[chi_tiet_tien_nghi]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[chi_tiet_tien_nghi] (
        [id_tien_nghi] INT IDENTITY(1,1) NOT NULL,
        [id_danh_muc] INT NOT NULL,
        [ten_tien_ich] NVARCHAR(255) NOT NULL,

        CONSTRAINT [PK_chi_tiet_tien_nghi] PRIMARY KEY CLUSTERED ([id_tien_nghi] ASC),
        CONSTRAINT [FK_chi_tiet_danh_muc] FOREIGN KEY ([id_danh_muc])
            REFERENCES [dbo].[danh_muc_tien_ich] ([id_danh_muc])
            ON DELETE CASCADE
            ON UPDATE CASCADE
    );
    PRINT N'-- Đã tạo mới thành công bảng [chi_tiet_tien_nghi]';
END
GO

-- ==============================================================================
-- 8. TẠO BẢNG ALEMBIC VERSION (Đồng bộ với Alembic Migrations)
-- ==============================================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[alembic_version]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[alembic_version] (
        [version_num] VARCHAR(32) NOT NULL,
        CONSTRAINT [alembic_version_pkc] PRIMARY KEY ([version_num])
    );
    INSERT INTO [dbo].[alembic_version] ([version_num]) VALUES ('1adff95a44fc');
    PRINT N'-- Đã tạo bảng [alembic_version] với revision head (1adff95a44fc)';
END
GO

-- ==============================================================================
-- 9. TẠO INDEXES TỐI ƯU HÓA HIỆU NĂNG TRUY VẤN
-- ==============================================================================
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'ix_khach_san_id_khach_san' AND object_id = OBJECT_ID(N'[dbo].[khach_san]'))
    CREATE NONCLUSTERED INDEX [ix_khach_san_id_khach_san] ON [dbo].[khach_san] ([id_khach_san]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'ix_khach_san_id_tai_khoan' AND object_id = OBJECT_ID(N'[dbo].[khach_san]'))
    CREATE NONCLUSTERED INDEX [ix_khach_san_id_tai_khoan] ON [dbo].[khach_san] ([id_tai_khoan]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'ix_khach_san_ten_khach_san' AND object_id = OBJECT_ID(N'[dbo].[khach_san]'))
    CREATE NONCLUSTERED INDEX [ix_khach_san_ten_khach_san] ON [dbo].[khach_san] ([ten_khach_san]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'ix_khach_san_thanh_pho' AND object_id = OBJECT_ID(N'[dbo].[khach_san]'))
    CREATE NONCLUSTERED INDEX [ix_khach_san_thanh_pho] ON [dbo].[khach_san] ([thanh_pho]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'ix_khach_san_tinh' AND object_id = OBJECT_ID(N'[dbo].[khach_san]'))
    CREATE NONCLUSTERED INDEX [ix_khach_san_tinh] ON [dbo].[khach_san] ([tinh]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'ix_khach_san_quan_huyen' AND object_id = OBJECT_ID(N'[dbo].[khach_san]'))
    CREATE NONCLUSTERED INDEX [ix_khach_san_quan_huyen] ON [dbo].[khach_san] ([quan_huyen]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'ix_khach_san_trang_thai' AND object_id = OBJECT_ID(N'[dbo].[khach_san]'))
    CREATE NONCLUSTERED INDEX [ix_khach_san_trang_thai] ON [dbo].[khach_san] ([trang_thai]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'ix_khach_san_is_deleted' AND object_id = OBJECT_ID(N'[dbo].[khach_san]'))
    CREATE NONCLUSTERED INDEX [ix_khach_san_is_deleted] ON [dbo].[khach_san] ([is_deleted]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_khach_san_dia_ly' AND object_id = OBJECT_ID(N'[dbo].[khach_san]'))
    CREATE NONCLUSTERED INDEX [IX_khach_san_dia_ly] ON [dbo].[khach_san] ([thanh_pho], [tinh], [quan_huyen], [trang_thai], [is_deleted]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_khach_san_active' AND object_id = OBJECT_ID(N'[dbo].[khach_san]'))
    CREATE NONCLUSTERED INDEX [IX_khach_san_active] ON [dbo].[khach_san] ([is_deleted], [trang_thai]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_khach_san_partner' AND object_id = OBJECT_ID(N'[dbo].[khach_san]'))
    CREATE NONCLUSTERED INDEX [IX_khach_san_partner] ON [dbo].[khach_san] ([id_tai_khoan], [is_deleted]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_hinh_anh_khach_san' AND object_id = OBJECT_ID(N'[dbo].[hinh_anh_khach_san]'))
    CREATE NONCLUSTERED INDEX [IX_hinh_anh_khach_san] ON [dbo].[hinh_anh_khach_san] ([id_khach_san], [la_anh_chinh], [thu_tu]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'ix_thong_tin_khach_san_id_thong_tin' AND object_id = OBJECT_ID(N'[dbo].[thong_tin_khach_san]'))
    CREATE NONCLUSTERED INDEX [ix_thong_tin_khach_san_id_thong_tin] ON [dbo].[thong_tin_khach_san] ([id_thong_tin]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'ix_quy_tac_khach_san_id_quy_tac' AND object_id = OBJECT_ID(N'[dbo].[quy_tac_khach_san]'))
    CREATE NONCLUSTERED INDEX [ix_quy_tac_khach_san_id_quy_tac] ON [dbo].[quy_tac_khach_san] ([id_quy_tac]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'ix_danh_muc_tien_ich_id_danh_muc' AND object_id = OBJECT_ID(N'[dbo].[danh_muc_tien_ich]'))
    CREATE NONCLUSTERED INDEX [ix_danh_muc_tien_ich_id_danh_muc] ON [dbo].[danh_muc_tien_ich] ([id_danh_muc]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'ix_chi_tiet_tien_nghi_id_tien_nghi' AND object_id = OBJECT_ID(N'[dbo].[chi_tiet_tien_nghi]'))
    CREATE NONCLUSTERED INDEX [ix_chi_tiet_tien_nghi_id_tien_nghi] ON [dbo].[chi_tiet_tien_nghi] ([id_tien_nghi]);
GO

PRINT N'>>> [database_update.sql] Cấu trúc CSDL hotel_service đã sẵn sàng và cập nhật thành công!';
GO
