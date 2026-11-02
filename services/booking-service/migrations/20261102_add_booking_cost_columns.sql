SET XACT_ABORT ON;

IF DB_NAME() NOT IN (N'booking_service', N'booking_service_test')
BEGIN
    THROW 51000, 'Migration chỉ được chạy trên booking_service hoặc booking_service_test.', 1;
END;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(N'dbo.dat_phong', N'U') IS NULL
    BEGIN
        THROW 51001, 'Không tìm thấy bảng dbo.dat_phong.', 1;
    END;

    IF COL_LENGTH(N'dbo.dat_phong', N'tien_phong') IS NULL
    BEGIN
        ALTER TABLE dbo.dat_phong
            ADD tien_phong DECIMAL(18, 2) NULL;
    END
    ELSE IF NOT EXISTS (
        SELECT 1
        FROM sys.columns AS c
        JOIN sys.types AS t ON t.user_type_id = c.user_type_id
        WHERE c.object_id = OBJECT_ID(N'dbo.dat_phong')
          AND c.name = N'tien_phong'
          AND t.name IN (N'decimal', N'numeric')
          AND c.precision = 18
          AND c.scale = 2
          AND c.is_nullable = 1
    )
    BEGIN
        THROW 51002, 'dbo.dat_phong.tien_phong không khớp DECIMAL(18,2) NULL.', 1;
    END;

    IF COL_LENGTH(N'dbo.dat_phong', N'thue_phi') IS NULL
    BEGIN
        IF OBJECT_ID(N'dbo.DF_dat_phong_thue_phi', N'D') IS NOT NULL
        BEGIN
            THROW 51003, 'Tên constraint DF_dat_phong_thue_phi đã được sử dụng.', 1;
        END;

        ALTER TABLE dbo.dat_phong
            ADD thue_phi DECIMAL(18, 2) NOT NULL
                CONSTRAINT DF_dat_phong_thue_phi DEFAULT (0) WITH VALUES;
    END
    ELSE IF NOT EXISTS (
        SELECT 1
        FROM sys.columns AS c
        JOIN sys.types AS t ON t.user_type_id = c.user_type_id
        WHERE c.object_id = OBJECT_ID(N'dbo.dat_phong')
          AND c.name = N'thue_phi'
          AND t.name IN (N'decimal', N'numeric')
          AND c.precision = 18
          AND c.scale = 2
          AND c.is_nullable = 0
    )
    BEGIN
        THROW 51004, 'dbo.dat_phong.thue_phi không khớp DECIMAL(18,2) NOT NULL.', 1;
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.default_constraints AS dc
        JOIN sys.columns AS c
          ON c.object_id = dc.parent_object_id
         AND c.column_id = dc.parent_column_id
        WHERE dc.parent_object_id = OBJECT_ID(N'dbo.dat_phong')
          AND c.name = N'thue_phi'
          AND TRY_CONVERT(
                DECIMAL(18, 2),
                REPLACE(REPLACE(REPLACE(dc.definition, N'(', N''), N')', N''), N' ', N'')
              ) = 0
    )
    BEGIN
        IF EXISTS (
            SELECT 1
            FROM sys.default_constraints AS dc
            JOIN sys.columns AS c
              ON c.object_id = dc.parent_object_id
             AND c.column_id = dc.parent_column_id
            WHERE dc.parent_object_id = OBJECT_ID(N'dbo.dat_phong')
              AND c.name = N'thue_phi'
        )
        BEGIN
            THROW 51005, 'Default của dbo.dat_phong.thue_phi không bằng 0.', 1;
        END;

        IF OBJECT_ID(N'dbo.DF_dat_phong_thue_phi', N'D') IS NOT NULL
        BEGIN
            THROW 51006, 'Tên constraint DF_dat_phong_thue_phi đã được sử dụng.', 1;
        END;

        ALTER TABLE dbo.dat_phong
            ADD CONSTRAINT DF_dat_phong_thue_phi DEFAULT (0) FOR thue_phi;
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.columns AS c
        JOIN sys.types AS t ON t.user_type_id = c.user_type_id
        WHERE c.object_id = OBJECT_ID(N'dbo.dat_phong')
          AND c.name = N'tien_phong'
          AND t.name IN (N'decimal', N'numeric')
          AND c.precision = 18
          AND c.scale = 2
          AND c.is_nullable = 1
    )
    OR NOT EXISTS (
        SELECT 1
        FROM sys.columns AS c
        JOIN sys.types AS t ON t.user_type_id = c.user_type_id
        WHERE c.object_id = OBJECT_ID(N'dbo.dat_phong')
          AND c.name = N'thue_phi'
          AND t.name IN (N'decimal', N'numeric')
          AND c.precision = 18
          AND c.scale = 2
          AND c.is_nullable = 0
    )
    BEGIN
        THROW 51007, 'Kiểm tra schema sau migration thất bại.', 1;
    END;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
    BEGIN
        ROLLBACK TRANSACTION;
    END;

    THROW;
END CATCH;
