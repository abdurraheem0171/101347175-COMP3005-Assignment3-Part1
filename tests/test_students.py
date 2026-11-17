"""Integration tests against a real PostgreSQL server, in a temporary schema.

Set A3_TEST_DSN to a connection string for a TEST database, then use unittest.
No application table is changed: a unique schema is created and later dropped.
"""

from contextlib import redirect_stdout
from datetime import date
import io
import os
from pathlib import Path
import unittest
from unittest.mock import patch
import uuid

import psycopg
from psycopg import sql

from app import students

ROOT = Path(__file__).resolve().parent.parent


@unittest.skipUnless(os.environ.get("A3_TEST_DSN"), "Set A3_TEST_DSN to run PostgreSQL integration tests.")
class StudentIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dsn = os.environ["A3_TEST_DSN"]
        cls.schema = "a3_test_" + uuid.uuid4().hex
        with psycopg.connect(cls.dsn) as connection:
            connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(cls.schema)))
        cls.addClassCleanup(cls.drop_schema)
        with cls.connect() as connection:
            connection.execute((ROOT / "sql/01_schema.sql").read_text())

    @classmethod
    def connect(cls):
        return psycopg.connect(cls.dsn, options=f"-c search_path={cls.schema}")

    @classmethod
    def drop_schema(cls):
        with psycopg.connect(cls.dsn) as connection:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(cls.schema)))

    def setUp(self):
        with self.connect() as connection:
            connection.execute("TRUNCATE students RESTART IDENTITY")
            connection.execute((ROOT / "sql/02_seed.sql").read_text())
        self.patcher = patch("app.students.get_connection", self.connect)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def rows(self):
        with redirect_stdout(io.StringIO()):
            return students.getAllStudents()

    def test_initial_records_and_display(self):
        output = io.StringIO()
        with redirect_stdout(output):
            rows = students.getAllStudents()
        self.assertEqual([r["first_name"] for r in rows], ["John", "Jane", "Jim"])
        self.assertEqual([r["student_id"] for r in rows], [1, 2, 3])
        self.assertEqual(rows[0]["enrollment_date"], date(2023, 9, 1))
        self.assertIn("jim.beam@example.com", output.getvalue())

    def test_insert_commits_and_generates_id(self):
        row = students.addStudent("Alex", "Taylor", "alex.taylor@example.com", "2026-11-15")
        self.assertEqual(row["student_id"], 4)
        self.assertEqual(self.rows()[-1], row)

    def test_update_changes_only_target_email(self):
        before = self.rows()
        row = students.updateStudentEmail(2, "jane.new@example.com")
        self.assertEqual(row["email"], "jane.new@example.com")
        after = self.rows()
        self.assertEqual(before[0], after[0])
        self.assertEqual(before[2], after[2])
        self.assertEqual({k:v for k,v in before[1].items() if k != "email"},
                         {k:v for k,v in after[1].items() if k != "email"})

    def test_delete_changes_only_target(self):
        removed = students.deleteStudent(2)
        self.assertEqual(removed["first_name"], "Jane")
        self.assertEqual([r["student_id"] for r in self.rows()], [1, 3])

    def test_missing_ids_do_not_claim_success(self):
        self.assertIsNone(students.updateStudentEmail(99999, "missing@example.com"))
        self.assertIsNone(students.deleteStudent(99999))
        self.assertEqual(len(self.rows()), 3)

    def test_duplicate_insert_rolls_back_and_next_operation_works(self):
        with self.assertRaises(psycopg.errors.UniqueViolation):
            students.addStudent("Other", "Person", "john.doe@example.com", None)
        self.assertEqual(len(self.rows()), 3)
        row = students.addStudent("Other", "Person", "other@example.com", None)
        self.assertIsNotNone(row)
        self.assertEqual(len(self.rows()), 4)

    def test_duplicate_update_preserves_original_email(self):
        with self.assertRaises(psycopg.errors.UniqueViolation):
            students.updateStudentEmail(2, "john.doe@example.com")
        self.assertEqual(self.rows()[1]["email"], "jane.smith@example.com")

    def test_optional_date_and_unicode_names(self):
        row = students.addStudent("Zoë", "O'Connor", "zoe@example.com", "")
        self.assertIsNone(row["enrollment_date"])
        self.assertEqual(self.rows()[-1]["last_name"], "O'Connor")

    def test_sql_like_name_is_stored_as_data(self):
        name = "Robert'); DROP TABLE students; --"
        row = students.addStudent(name, "Test", "robert@example.com", None)
        self.assertEqual(row["first_name"], name)
        self.assertEqual(len(self.rows()), 4)

    def test_invalid_inputs_do_not_change_database(self):
        for args in [(" ", "Test", "x@example.com", None),
                     ("A", "Test", "invalid", None),
                     ("A", "Test", "x@example.com", "2026-02-30")]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                students.addStudent(*args)
        for invalid_id in [0, -1, True, "2", 2147483648]:
            with self.subTest(student_id=invalid_id), self.assertRaises(ValueError):
                students.deleteStudent(invalid_id)
        self.assertEqual(len(self.rows()), 3)

    def test_empty_table_has_clear_message(self):
        for row in self.rows():
            students.deleteStudent(row["student_id"])
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(students.getAllStudents(), [])
        self.assertIn("No students found", output.getvalue())

    def test_database_enforces_not_null_without_application(self):
        for column in ["first_name", "last_name", "email"]:
            with self.subTest(column=column), self.assertRaises(psycopg.errors.NotNullViolation):
                with self.connect() as connection:
                    connection.execute(sql.SQL("UPDATE students SET {} = NULL WHERE student_id = 1")
                                       .format(sql.Identifier(column)))
        self.assertEqual(len(self.rows()), 3)


if __name__ == "__main__":
    unittest.main()
