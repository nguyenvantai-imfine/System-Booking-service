-- Connect explicitly to notification_service or notification_service_test before
-- executing this script. Do not rely on the connection's default database.
IF DB_NAME() NOT IN (N'notification_service', N'notification_service_test')
    THROW 51000, 'Connect explicitly to notification_service or notification_service_test before running this migration.', 1;

IF DB_ID() IS NULL OR DB_ID() <= 4
    THROW 51010, 'System databases cannot be migrated.', 1;

SET ANSI_NULLS ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET ARITHABORT ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET QUOTED_IDENTIFIER ON;
SET NUMERIC_ROUNDABORT OFF;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @notification_rows_before BIGINT;
    DECLARE @content_rows_before BIGINT;

    IF OBJECT_ID(N'dbo.thong_bao', N'U') IS NULL
        THROW 51001, 'Required table dbo.thong_bao is missing; initialize the Notification database first.', 1;

    IF OBJECT_ID(N'dbo.noi_dung_thong_bao', N'U') IS NULL
        THROW 51002, 'Required table dbo.noi_dung_thong_bao is missing; initialize the Notification database first.', 1;

    SELECT @notification_rows_before = COUNT_BIG(*)
    FROM dbo.thong_bao;

    SELECT @content_rows_before = COUNT_BIG(*)
    FROM dbo.noi_dung_thong_bao;

    IF COL_LENGTH(N'dbo.thong_bao', N'event_key') IS NOT NULL
       AND NOT EXISTS (
            SELECT 1
            FROM sys.columns AS c
            JOIN sys.types AS t ON t.user_type_id = c.user_type_id
            WHERE c.object_id = OBJECT_ID(N'dbo.thong_bao')
              AND c.name = N'event_key'
              AND t.name IN (N'varchar', N'nvarchar')
              AND c.max_length IN (64, 128)
              AND c.is_nullable = 1
       )
        THROW 51003, 'dbo.thong_bao.event_key exists with an incompatible type, length, or nullability.', 1;

    IF COL_LENGTH(N'dbo.thong_bao', N'event_key') IS NOT NULL
    BEGIN
        EXEC sys.sp_executesql N'
            IF EXISTS (
                SELECT event_key
                FROM dbo.thong_bao
                WHERE event_key IS NOT NULL
                GROUP BY event_key
                HAVING COUNT_BIG(*) > 1
            )
                THROW 51004, ''Duplicate non-null event_key values must be reviewed before migration.'', 1;';
    END

    IF EXISTS (
        SELECT id_thong_bao
        FROM dbo.noi_dung_thong_bao
        GROUP BY id_thong_bao
        HAVING COUNT_BIG(*) > 1
    )
        THROW 51005, 'Duplicate notification content rows must be reviewed before migration.', 1;

    IF COL_LENGTH(N'dbo.thong_bao', N'event_key') IS NULL
        ALTER TABLE dbo.thong_bao ADD event_key NVARCHAR(64) NULL;

    IF EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE object_id = OBJECT_ID(N'dbo.thong_bao')
          AND name = N'uq_thong_bao_event_key'
    )
       AND NOT EXISTS (
            SELECT 1
            FROM sys.indexes AS i
            JOIN sys.index_columns AS ic
              ON ic.object_id = i.object_id
             AND ic.index_id = i.index_id
             AND ic.key_ordinal = 1
            JOIN sys.columns AS c
              ON c.object_id = ic.object_id
             AND c.column_id = ic.column_id
            WHERE i.object_id = OBJECT_ID(N'dbo.thong_bao')
              AND i.name = N'uq_thong_bao_event_key'
              AND i.is_unique = 1
              AND i.is_disabled = 0
              AND i.is_hypothetical = 0
              AND i.has_filter = 1
              AND c.name = N'event_key'
              AND REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                    UPPER(i.filter_definition),
                    N'[', N''), N']', N''), N'(', N''), N')', N''), N' ', N''
                  ) = N'EVENT_KEYISNOTNULL'
              AND NOT EXISTS (
                    SELECT 1
                    FROM sys.index_columns AS other_ic
                    WHERE other_ic.object_id = i.object_id
                      AND other_ic.index_id = i.index_id
                      AND other_ic.key_ordinal > 1
              )
       )
        THROW 51006, 'Index uq_thong_bao_event_key exists but does not match the required unique filtered event_key index.', 1;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes AS i
        JOIN sys.index_columns AS ic
          ON ic.object_id = i.object_id
         AND ic.index_id = i.index_id
         AND ic.key_ordinal = 1
        JOIN sys.columns AS c
          ON c.object_id = ic.object_id
         AND c.column_id = ic.column_id
        WHERE i.object_id = OBJECT_ID(N'dbo.thong_bao')
          AND i.is_unique = 1
          AND i.is_disabled = 0
          AND i.is_hypothetical = 0
          AND i.has_filter = 1
          AND c.name = N'event_key'
          AND REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                UPPER(i.filter_definition),
                N'[', N''), N']', N''), N'(', N''), N')', N''), N' ', N''
              ) = N'EVENT_KEYISNOTNULL'
          AND NOT EXISTS (
                SELECT 1
                FROM sys.index_columns AS other_ic
                WHERE other_ic.object_id = i.object_id
                  AND other_ic.index_id = i.index_id
                  AND other_ic.key_ordinal > 1
          )
    )
        EXEC sys.sp_executesql N'
            CREATE UNIQUE INDEX uq_thong_bao_event_key
                ON dbo.thong_bao(event_key)
                WHERE event_key IS NOT NULL;';

    IF EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE object_id = OBJECT_ID(N'dbo.noi_dung_thong_bao')
          AND name = N'uq_noi_dung_thong_bao_id'
    )
       AND NOT EXISTS (
            SELECT 1
            FROM sys.indexes AS i
            JOIN sys.index_columns AS ic
              ON ic.object_id = i.object_id
             AND ic.index_id = i.index_id
             AND ic.key_ordinal = 1
            JOIN sys.columns AS c
              ON c.object_id = ic.object_id
             AND c.column_id = ic.column_id
            WHERE i.object_id = OBJECT_ID(N'dbo.noi_dung_thong_bao')
              AND i.name = N'uq_noi_dung_thong_bao_id'
              AND i.is_unique = 1
              AND i.is_disabled = 0
              AND i.is_hypothetical = 0
              AND i.has_filter = 0
              AND c.name = N'id_thong_bao'
              AND NOT EXISTS (
                    SELECT 1
                    FROM sys.index_columns AS other_ic
                    WHERE other_ic.object_id = i.object_id
                      AND other_ic.index_id = i.index_id
                      AND other_ic.key_ordinal > 1
              )
       )
        THROW 51007, 'Index uq_noi_dung_thong_bao_id exists but is not a unique index on id_thong_bao.', 1;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes AS i
        JOIN sys.index_columns AS ic
          ON ic.object_id = i.object_id
         AND ic.index_id = i.index_id
         AND ic.key_ordinal = 1
        JOIN sys.columns AS c
          ON c.object_id = ic.object_id
         AND c.column_id = ic.column_id
        WHERE i.object_id = OBJECT_ID(N'dbo.noi_dung_thong_bao')
          AND i.is_unique = 1
          AND i.is_disabled = 0
          AND i.is_hypothetical = 0
          AND i.has_filter = 0
          AND c.name = N'id_thong_bao'
          AND NOT EXISTS (
                SELECT 1
                FROM sys.index_columns AS other_ic
                WHERE other_ic.object_id = i.object_id
                  AND other_ic.index_id = i.index_id
                  AND other_ic.key_ordinal > 1
          )
    )
        CREATE UNIQUE INDEX uq_noi_dung_thong_bao_id
            ON dbo.noi_dung_thong_bao(id_thong_bao);

    IF COL_LENGTH(N'dbo.thong_bao', N'event_key') IS NULL
       OR NOT EXISTS (
            SELECT 1
            FROM sys.indexes AS i
            JOIN sys.index_columns AS ic
              ON ic.object_id = i.object_id
             AND ic.index_id = i.index_id
             AND ic.key_ordinal = 1
            JOIN sys.columns AS c
              ON c.object_id = ic.object_id
             AND c.column_id = ic.column_id
            WHERE i.object_id = OBJECT_ID(N'dbo.thong_bao')
              AND i.is_unique = 1
              AND i.is_disabled = 0
              AND i.is_hypothetical = 0
              AND i.has_filter = 1
              AND c.name = N'event_key'
              AND REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                    UPPER(i.filter_definition),
                    N'[', N''), N']', N''), N'(', N''), N')', N''), N' ', N''
                  ) = N'EVENT_KEYISNOTNULL'
       )
       OR NOT EXISTS (
            SELECT 1
            FROM sys.indexes AS i
            JOIN sys.index_columns AS ic
              ON ic.object_id = i.object_id
             AND ic.index_id = i.index_id
             AND ic.key_ordinal = 1
            JOIN sys.columns AS c
              ON c.object_id = ic.object_id
             AND c.column_id = ic.column_id
            WHERE i.object_id = OBJECT_ID(N'dbo.noi_dung_thong_bao')
              AND i.is_unique = 1
              AND i.is_disabled = 0
              AND i.is_hypothetical = 0
              AND i.has_filter = 0
              AND c.name = N'id_thong_bao'
              AND NOT EXISTS (
                    SELECT 1
                    FROM sys.index_columns AS other_ic
                    WHERE other_ic.object_id = i.object_id
                      AND other_ic.index_id = i.index_id
                      AND other_ic.key_ordinal > 1
              )
       )
        THROW 51008, 'Notification idempotency schema postcheck failed.', 1;

    IF (SELECT COUNT_BIG(*) FROM dbo.thong_bao) <> @notification_rows_before
       OR (SELECT COUNT_BIG(*) FROM dbo.noi_dung_thong_bao) <> @content_rows_before
        THROW 51009, 'Notification migration changed existing row counts.', 1;

    COMMIT TRANSACTION;
    PRINT CONCAT(
        'Notification idempotency schema migration completed for ',
        DB_NAME(),
        '; thong_bao rows=',
        @notification_rows_before,
        '; noi_dung_thong_bao rows=',
        @content_rows_before,
        '.'
    );
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
