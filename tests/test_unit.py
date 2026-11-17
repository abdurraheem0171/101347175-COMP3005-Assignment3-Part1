"""Local validation and query-binding checks; no database server required."""

from contextlib import redirect_stdout
from datetime import date, datetime
import io
import unittest
from unittest.mock import MagicMock, patch

import psycopg

from app import students
from app.main import main


class ValidationTests(unittest.TestCase):
    def test_required_names(self):
        self.assertEqual(students._required_text("  Zoë  ", "Name"), "Zoë")
        for invalid in [None, "", "  ", 123]:
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                students._required_text(invalid, "Name")

    def test_email_format_and_case(self):
        self.assertEqual(students._email(" A@Example.com "), "A@Example.com")
        for invalid in [None, "", "x", "x@@y", "@y", "x@", "x y@z"]:
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                students._email(invalid)

    def test_optional_and_real_dates(self):
        for value in [None, "", "  "]:
            self.assertIsNone(students._enrollment_date(value))
        self.assertEqual(students._enrollment_date("2024-02-29"), date(2024, 2, 29))
        self.assertEqual(students._enrollment_date(date(2026, 11, 15)), date(2026, 11, 15))
        for invalid in ["2026-02-29", "2026-11-31", "20261115", "15/11/2026", datetime.now(), 123]:
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                students._enrollment_date(invalid)

    def test_ids(self):
        self.assertEqual(students._student_id(1), 1)
        for invalid in [True, False, 0, -1, "1", None, 1.5, 2147483648]:
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                students._student_id(invalid)


class QueryBindingTests(unittest.TestCase):
    def setUp(self):
        self.connection = MagicMock()
        self.connection.__enter__.return_value = self.connection
        self.cursor = self.connection.cursor.return_value.__enter__.return_value
        patcher = patch("app.students.get_connection", return_value=self.connection)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_insert_binds_quote_containing_values(self):
        name = "Robert'); DROP TABLE students; --"
        expected = {"student_id": 4}
        self.cursor.fetchone.return_value = expected
        result = students.addStudent(name, "O'Connor", "x@example.com", "2026-11-15")
        query, values = self.cursor.execute.call_args.args
        self.assertNotIn(name, query)
        self.assertEqual(values, (name, "O'Connor", "x@example.com", date(2026, 11, 15)))
        self.assertEqual(query.count("%s"), 4)
        self.assertIs(result, expected)
        self.connection.__exit__.assert_called_once_with(None, None, None)

    def test_update_and_delete_return_none_for_missing_id(self):
        self.cursor.fetchone.return_value = None
        self.assertIsNone(students.updateStudentEmail(99, "new@example.com"))
        query, values = self.cursor.execute.call_args.args
        self.assertIn("WHERE student_id = %s", query)
        self.assertEqual(values, ("new@example.com", 99))
        self.assertIsNone(students.deleteStudent(99))
        query, values = self.cursor.execute.call_args.args
        self.assertIn("WHERE student_id = %s", query)
        self.assertEqual(values, (99,))

    def test_database_error_reaches_transaction_context(self):
        error = psycopg.errors.UniqueViolation("duplicate")
        self.cursor.execute.side_effect = error
        with self.assertRaises(psycopg.errors.UniqueViolation):
            students.addStudent("A", "B", "a@example.com", None)
        self.assertIs(self.connection.__exit__.call_args.args[0], psycopg.errors.UniqueViolation)

    def test_read_displays_and_returns_rows(self):
        rows = [{"student_id":1,"first_name":"A","last_name":"B",
                 "email":"a@example.com","enrollment_date":None}]
        self.cursor.fetchall.return_value = rows
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(students.getAllStudents(), rows)
        self.assertIn("a@example.com", output.getvalue())
        self.assertIn("NULL", output.getvalue())
        self.assertIn("ORDER BY student_id", self.cursor.execute.call_args.args[0])


class MenuTests(unittest.TestCase):
    def test_menu_recovers_from_bad_choice_and_bad_id(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["bad", "3", "abc", "0"]), redirect_stdout(output):
            main()
        self.assertIn("Choose 0, 1, 2, 3, or 4", output.getvalue())
        self.assertIn("numeric student ID", output.getvalue())
        self.assertIn("Goodbye", output.getvalue())

    def test_cancel_does_not_call_delete(self):
        with patch("builtins.input", side_effect=["4", "1", "no", "0"]), \
             patch("app.main.deleteStudent") as delete, redirect_stdout(io.StringIO()):
            main()
        delete.assert_not_called()

    def test_duplicate_email_message_and_continue(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["3", "1", "duplicate@example.com", "0"]), \
             patch("app.main.updateStudentEmail", side_effect=psycopg.errors.UniqueViolation()), \
             redirect_stdout(output):
            main()
        self.assertIn("already in use", output.getvalue())
        self.assertIn("Goodbye", output.getvalue())


if __name__ == "__main__":
    unittest.main()
