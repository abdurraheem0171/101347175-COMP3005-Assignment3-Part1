"""The four required CRUD operations, independent of the interactive menu."""

from datetime import date, datetime

from psycopg.rows import dict_row

from app.database import get_connection


def _required_text(value, label):
    """Reject missing/blank input and remove surrounding whitespace."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} cannot be blank.")
    return value.strip()


def _email(value):
    """Check basic address structure; the database enforces uniqueness."""
    value = _required_text(value, "Email")
    if value.count("@") != 1 or any(char.isspace() for char in value):
        raise ValueError("Email needs one @ and no whitespace.")
    local, domain = value.split("@")
    if not local or not domain:
        raise ValueError("Email needs text before and after @.")
    return value


def _student_id(value):
    """Validate the positive integer range used by generated student IDs."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("Student ID must be an integer.")
    if not 1 <= value <= 2147483647:
        raise ValueError("Student ID must be between 1 and 2147483647.")
    return value


def _enrollment_date(value):
    """Accept an optional date; blank input becomes SQL NULL."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, str):
        value = value.strip()
        try:
            parsed = date.fromisoformat(value)
            if parsed.isoformat() == value:
                return parsed
        except ValueError:
            pass
    raise ValueError("Enrollment date must be a real date in YYYY-MM-DD format, or blank.")


def display_students(rows):
    """Print all five fields in a readable table, including optional dates."""
    if not rows:
        print("No students found.")
        return
    fields = ("student_id", "first_name", "last_name", "email", "enrollment_date")
    values = [["NULL" if row[key] is None else str(row[key]) for key in fields] for row in rows]
    widths = [max(len(key), *(len(row[i]) for row in values)) for i, key in enumerate(fields)]
    print(" | ".join(key.ljust(widths[i]) for i, key in enumerate(fields)))
    print("-+-".join("-" * width for width in widths))
    for row in values:
        print(" | ".join(value.ljust(widths[i]) for i, value in enumerate(row)))
    print(f"{len(rows)} student(s).")


def getAllStudents():
    """Retrieve and display every student, ordered by ID; also return the rows."""
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                SELECT student_id, first_name, last_name, email, enrollment_date
                FROM students ORDER BY student_id
            """)
            rows = cursor.fetchall()
    display_students(rows)
    return rows


def addStudent(first_name, last_name, email, enrollment_date):
    """Insert a student and return the saved record, including its generated ID."""
    first_name = _required_text(first_name, "First name")
    last_name = _required_text(last_name, "Last name")
    email = _email(email)
    enrollment_date = _enrollment_date(enrollment_date)
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            # Values are bound separately, never interpolated into SQL text.
            cursor.execute("""
                INSERT INTO students (first_name, last_name, email, enrollment_date)
                VALUES (%s, %s, %s, %s)
                RETURNING student_id, first_name, last_name, email, enrollment_date
            """, (first_name, last_name, email, enrollment_date))
            row = cursor.fetchone()
    # Reaching here means the context manager committed successfully.
    return row


def updateStudentEmail(student_id, new_email):
    """Update only the selected student's email; return None if ID is absent."""
    student_id = _student_id(student_id)
    new_email = _email(new_email)
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                UPDATE students SET email = %s WHERE student_id = %s
                RETURNING student_id, first_name, last_name, email, enrollment_date
            """, (new_email, student_id))
            row = cursor.fetchone()
    return row


def deleteStudent(student_id):
    """Delete only the selected student; return the removed row or None."""
    student_id = _student_id(student_id)
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                DELETE FROM students WHERE student_id = %s
                RETURNING student_id, first_name, last_name, email, enrollment_date
            """, (student_id,))
            row = cursor.fetchone()
    return row
