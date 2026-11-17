-- Explicit, additive migration. Back up before applying to an existing database.
SET XACT_ABORT ON;
BEGIN TRANSACTION;
IF COL_LENGTH('dbo.tai_khoan', 'ngay_cap_nhat') IS NULL
    ALTER TABLE dbo.tai_khoan ADD ngay_cap_nhat DATETIME NOT NULL
        CONSTRAINT df_tai_khoan_updated DEFAULT GETDATE() WITH VALUES;
IF COL_LENGTH('dbo.nguoi_dung', 'ngay_cap_nhat') IS NULL
    ALTER TABLE dbo.nguoi_dung ADD ngay_cap_nhat DATETIME NOT NULL
        CONSTRAINT df_nguoi_dung_updated DEFAULT GETDATE() WITH VALUES;
COMMIT;
