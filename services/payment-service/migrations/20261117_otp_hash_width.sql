-- Run explicitly against payment_service after backup. Never truncates data.
SET XACT_ABORT ON;
BEGIN TRANSACTION;
IF EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID(N'dbo.giao_dich_otp')
      AND name = N'otp_code' AND max_length > 0 AND max_length < 128
)
BEGIN
    ALTER TABLE dbo.giao_dich_otp ALTER COLUMN otp_code NVARCHAR(64) NOT NULL;
END;
COMMIT;
