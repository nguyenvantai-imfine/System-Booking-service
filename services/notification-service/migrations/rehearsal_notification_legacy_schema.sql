-- Rehearsal fixture only. First create an empty notification_service_test
-- database on an isolated SQL Server instance, then connect to it explicitly.
IF DB_NAME() <> N'notification_service_test'
    THROW 51100, 'This rehearsal fixture may run only in notification_service_test.', 1;

IF DB_ID() IS NULL OR DB_ID() <= 4
    THROW 51101, 'System databases cannot be used for the rehearsal fixture.', 1;

IF OBJECT_ID(N'dbo.thong_bao', N'U') IS NOT NULL
   OR OBJECT_ID(N'dbo.noi_dung_thong_bao', N'U') IS NOT NULL
    THROW 51102, 'The rehearsal database must be empty; do not overwrite existing tables.', 1;

SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    CREATE TABLE dbo.thong_bao (
        id_thong_bao INT IDENTITY(1,1) NOT NULL
            CONSTRAINT pk_rehearsal_thong_bao PRIMARY KEY,
        id_tai_khoan INT NULL,
        loai_thong_bao NVARCHAR(50) NOT NULL,
        kenh_gui NVARCHAR(20) NOT NULL
            CONSTRAINT df_rehearsal_thong_bao_kenh_gui DEFAULT N'EMAIL',
        nguoi_nhan NVARCHAR(150) NOT NULL,
        trang_thai NVARCHAR(30) NOT NULL
            CONSTRAINT df_rehearsal_thong_bao_trang_thai DEFAULT N'PENDING',
        ma_booking NVARCHAR(50) NULL,
        ngay_tao DATETIME NOT NULL
            CONSTRAINT df_rehearsal_thong_bao_ngay_tao DEFAULT GETDATE(),
        ngay_gui DATETIME NULL,
        ghi_chu_loi NVARCHAR(MAX) NULL,
        is_read BIT NOT NULL
            CONSTRAINT df_rehearsal_thong_bao_is_read DEFAULT 0
    );

    CREATE INDEX idx_thong_bao_nguoi_nhan
        ON dbo.thong_bao(nguoi_nhan);
    CREATE INDEX idx_thong_bao_loai
        ON dbo.thong_bao(loai_thong_bao);
    CREATE INDEX idx_thong_bao_trang_thai
        ON dbo.thong_bao(trang_thai);
    CREATE INDEX idx_thong_bao_ma_booking
        ON dbo.thong_bao(ma_booking);

    CREATE TABLE dbo.noi_dung_thong_bao (
        id_noi_dung INT IDENTITY(1,1) NOT NULL
            CONSTRAINT pk_rehearsal_noi_dung_thong_bao PRIMARY KEY,
        id_thong_bao INT NOT NULL,
        tieu_de NVARCHAR(255) NOT NULL,
        noi_dung_html NVARCHAR(MAX) NOT NULL,
        noi_dung_text NVARCHAR(MAX) NULL,
        du_lieu_dinh_kem NVARCHAR(MAX) NULL,
        CONSTRAINT fk_rehearsal_noi_dung_thong_bao
            FOREIGN KEY (id_thong_bao)
            REFERENCES dbo.thong_bao(id_thong_bao)
            ON DELETE CASCADE
    );

    CREATE INDEX idx_noi_dung_thong_bao_id
        ON dbo.noi_dung_thong_bao(id_thong_bao);

    DECLARE @notification_id INT;

    INSERT INTO dbo.thong_bao (
        id_tai_khoan,
        loai_thong_bao,
        kenh_gui,
        nguoi_nhan,
        trang_thai,
        ma_booking
    )
    VALUES (
        NULL,
        N'SYSTEM',
        N'EMAIL',
        N'rehearsal@example.invalid',
        N'SENT',
        N'REHEARSAL-ONLY'
    );

    SET @notification_id = CONVERT(INT, SCOPE_IDENTITY());

    INSERT INTO dbo.noi_dung_thong_bao (
        id_thong_bao,
        tieu_de,
        noi_dung_html,
        noi_dung_text
    )
    VALUES (
        @notification_id,
        N'Rehearsal fixture',
        N'<p>Local migration rehearsal only; no email is sent.</p>',
        N'Local migration rehearsal only; no email is sent.'
    );

    COMMIT TRANSACTION;
    PRINT 'Legacy Notification rehearsal schema and one fixture row created.';
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
