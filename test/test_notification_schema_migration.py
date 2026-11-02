import os
import re
import unittest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MIGRATION_PATH = os.path.join(
    PROJECT_ROOT,
    "services",
    "notification-service",
    "migrations",
    "20261102_add_event_key_idempotency.sql",
)


class TestNotificationSchemaMigration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(MIGRATION_PATH, encoding="utf-8") as migration_file:
            cls.sql = migration_file.read()
        cls.normalized_sql = re.sub(r"\s+", " ", cls.sql).lower()

    def test_adds_nullable_event_key_and_filtered_unique_index(self):
        self.assertIn(
            "alter table dbo.thong_bao add event_key nvarchar(64) null",
            self.normalized_sql,
        )
        self.assertIn(
            "create unique index uq_thong_bao_event_key",
            self.normalized_sql,
        )
        self.assertIn(
            "where event_key is not null",
            self.normalized_sql,
        )
        self.assertIn(
            "exec sys.sp_executesql n' create unique index uq_thong_bao_event_key",
            self.normalized_sql,
        )

    def test_prechecks_duplicates_before_unique_indexes(self):
        self.assertIn("having count_big(*) > 1", self.normalized_sql)
        self.assertIn("duplicate non-null event_key values", self.normalized_sql)
        self.assertIn("duplicate notification content rows", self.normalized_sql)
        self.assertLess(
            self.normalized_sql.index("duplicate notification content rows"),
            self.normalized_sql.index(
                "create unique index uq_noi_dung_thong_bao_id"
            ),
        )

    def test_migration_is_idempotent_and_preserves_existing_rows(self):
        self.assertIn("if col_length(n'dbo.thong_bao', n'event_key') is null", self.normalized_sql)
        self.assertIn("if not exists ( select 1 from sys.indexes", self.normalized_sql)
        self.assertIn("begin transaction", self.normalized_sql)
        self.assertIn("rollback transaction", self.normalized_sql)
        self.assertIn("count_big(*)", self.normalized_sql)
        self.assertIn("notification migration changed existing row counts", self.normalized_sql)
        self.assertIn("set quoted_identifier on", self.normalized_sql)
        self.assertIn("set ansi_nulls on", self.normalized_sql)
        self.assertIn("set ansi_warnings on", self.normalized_sql)
        self.assertIn("set arithabort on", self.normalized_sql)
        self.assertIn("set numeric_roundabort off", self.normalized_sql)
        self.assertNotRegex(
            self.normalized_sql,
            r"\b(drop\s+table|truncate\s+table|delete\s+from)\b",
        )

    def test_migration_requires_an_explicit_allowlisted_database_connection(self):
        guard = self.normalized_sql.index("if db_name() not in")
        transaction = self.normalized_sql.index("begin transaction")
        first_schema_change = self.normalized_sql.index(
            "alter table dbo.thong_bao add event_key"
        )
        self.assertLess(guard, transaction)
        self.assertLess(transaction, first_schema_change)
        self.assertIn("n'notification_service_test'", self.normalized_sql)
        self.assertIn("db_id() <= 4", self.normalized_sql)
        self.assertNotRegex(self.normalized_sql, r"\buse\s+\w+")

    def test_existing_indexes_must_be_enabled_and_match_required_filtering(self):
        self.assertGreaterEqual(
            self.normalized_sql.count("i.is_disabled = 0"),
            6,
        )
        self.assertGreaterEqual(
            self.normalized_sql.count("i.is_hypothetical = 0"),
            6,
        )
        self.assertGreaterEqual(
            self.normalized_sql.count("i.has_filter = 0"),
            3,
        )
        self.assertGreaterEqual(
            self.normalized_sql.count("= n'event_keyisnotnull'"),
            3,
        )

    def test_new_database_initialization_matches_the_orm_contract(self):
        init_path = os.path.join(
            PROJECT_ROOT,
            "services",
            "notification-service",
            "database_init.sql",
        )
        with open(init_path, encoding="utf-8") as init_file:
            init_sql = re.sub(r"\s+", " ", init_file.read()).lower()
        self.assertIn("event_key nvarchar(64) null", init_sql)
        self.assertIn("uq_thong_bao_event_key", init_sql)
        self.assertIn("uq_noi_dung_thong_bao_id unique (id_thong_bao)", init_sql)

    def test_rehearsal_fixture_is_limited_to_an_empty_test_database(self):
        fixture_path = os.path.join(
            PROJECT_ROOT,
            "services",
            "notification-service",
            "migrations",
            "rehearsal_notification_legacy_schema.sql",
        )
        with open(fixture_path, encoding="utf-8") as fixture_file:
            fixture = re.sub(r"\s+", " ", fixture_file.read()).lower()
        self.assertIn("if db_name() <> n'notification_service_test'", fixture)
        self.assertIn("if db_id() is null or db_id() <= 4", fixture)
        self.assertIn("must be empty", fixture)
        self.assertIn("begin transaction", fixture)
        self.assertIn("rollback transaction", fixture)
        self.assertNotIn("create database", fixture)
        self.assertNotRegex(fixture, r"\b(drop\s+table|truncate\s+table|delete\s+from)\b")
        self.assertNotIn("event_key nvarchar", fixture)


if __name__ == "__main__":
    unittest.main()
