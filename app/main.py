"""Interactive command-line menu. Run from the project root: python -m app.main."""

import psycopg

from app.students import (
    addStudent, deleteStudent, display_students, getAllStudents, updateStudentEmail,
)


def read_id():
    """Convert keyboard input into an integer before passing it to CRUD logic."""
    try:
        return int(input("Student ID: ").strip())
    except ValueError as error:
        raise ValueError("Enter a numeric student ID, for example 4.") from error


def main():
    """Dispatch menu actions and keep expected input/database errors recoverable."""
    print("Student Records - PostgreSQL")
    while True:
        try:
            print("\n1. List all students\n2. Add student\n3. Update student email\n4. Delete student\n0. Exit")
            choice = input("Choose an option: ").strip()
            if choice == "0":
                print("Goodbye.")
                return
            if choice == "1":
                getAllStudents()
            elif choice == "2":
                row = addStudent(
                    input("First name: "), input("Last name: "),
                    input("Email: "), input("Enrollment date (YYYY-MM-DD, blank for none): "),
                )
                print("Student added and committed.")
                display_students([row])
            elif choice == "3":
                row = updateStudentEmail(read_id(), input("New email: "))
                if row is None:
                    print("No student has that ID; nothing was updated.")
                else:
                    print("Email updated and committed.")
                    display_students([row])
            elif choice == "4":
                student_id = read_id()
                if input(f"Delete student {student_id}? Type yes to confirm: ").strip().lower() != "yes":
                    print("Deletion cancelled.")
                    continue
                row = deleteStudent(student_id)
                if row is None:
                    print("No student has that ID; nothing was deleted.")
                else:
                    print("Student deleted and committed.")
                    display_students([row])
            else:
                print("Choose 0, 1, 2, 3, or 4.")
        except ValueError as error:
            print(f"Input/configuration error: {error}")
        except psycopg.errors.UniqueViolation:
            print("That email is already in use. No changes were saved.")
        except psycopg.errors.UndefinedTable:
            print("The students table is missing. Check config.json and run sql/01_schema.sql first.")
        except psycopg.OperationalError:
            print("Cannot connect to PostgreSQL. Check the service, database, port, user, and password.")
            print("If the password was wrong, restart the application to enter it again.")
        except psycopg.Error as error:
            # Avoid showing connection credentials or a long traceback in the menu.
            print(f"Database operation failed (SQLSTATE {error.sqlstate or 'unavailable'}).")
            print("The transaction did not complete. Check the schema and server connection before retrying.")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return


if __name__ == "__main__":
    main()
