# COMP3005 Assignment 3 – Part 1
## PostgreSQL Student Records CRUD Application

A small Python command-line application for creating, reading, updating, and
deleting records in the `students` table. PostgreSQL stores the records persistently;
the application does not maintain a separate in-memory database.

## Contents

```text
app/
  database.py          Connection configuration and password prompt
  students.py          Four CRUD functions and input validation
  main.py              Interactive menu and error messages
sql/
  00_create_database.sql
  01_schema.sql
  02_seed.sql
  03_verify.sql
tests/test_students.py PostgreSQL integration tests
tests/test_unit.py     Validation, query-binding, and menu tests
docs/DEMO_CHECKLIST.md  Five-minute demonstration outline
docs/TEST_RESULTS.md    What was actually tested
config.example.json    Connection settings template (no password)
requirements.txt       Python dependency
```

## Prerequisites

- Windows with Python 3.10 or newer (Python 3.12 is suitable).
- PostgreSQL server and pgAdmin 4.
- VS Code, or another editor and a terminal.

Official installers:
- Python: https://www.python.org/downloads/windows/
- PostgreSQL with pgAdmin: https://www.postgresql.org/download/windows/

When installing PostgreSQL, keep track of the password you choose for the
`postgres` account and the port (normally `5432`). The application needs the
database-server password, not a separate pgAdmin master password.

## 1. Create and populate the database in pgAdmin

1. Open pgAdmin and connect to your PostgreSQL server.
2. Select the existing `postgres` database and open its Query Tool.
3. Open `sql/00_create_database.sql` in the Query Tool and execute it with
   auto-commit enabled. Run this script alone, outside a transaction block.
4. Refresh the Databases tree. Select `students_db` and open a **new Query Tool**
   for that database. Running CREATE DATABASE does not switch the old connection.
5. Execute `sql/01_schema.sql`, then `sql/02_seed.sql` in `students_db`.
6. Execute `sql/03_verify.sql`. Confirm John Doe, Jane Smith, and Jim Beam appear.

Alternatively, create `students_db` using pgAdmin's Create Database dialog,
then proceed at step 4. Do not also run `00_create_database.sql` in that case.

The table has exactly the five requested columns:

| Column | Definition |
|---|---|
| student_id | INTEGER, generated automatically, PRIMARY KEY |
| first_name | TEXT NOT NULL |
| last_name | TEXT NOT NULL |
| email | TEXT NOT NULL UNIQUE |
| enrollment_date | DATE; NULL is permitted |

Run setup scripts **once**. A second table-creation run reports that the table
exists; a repeated seed run reports duplicate emails. Neither script silently
overwrites existing records. Do not reset your database simply to rerun the app.

## 2. Prepare Python on Windows

Extract the folder and open it in VS Code with **File > Open Folder**. The root
folder is the one containing this README and `requirements.txt`.
Open **Terminal > New Terminal** and use PowerShell:

```powershell
py --version
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item config.example.json config.json
```

If `py` is unavailable but `python --version` works, replace `py` with `python`
in the first two commands. These commands use the virtual environment directly;
there is no need to activate it or change PowerShell execution policy.

Open `config.json`. Match `host`, `port`, `dbname`, and `user` to your PostgreSQL
server. The example assumes localhost, port 5432, database students_db, and
user postgres. Keep the port as a number, not a quoted string. Do not add a password
field. The application asks for the password once per run, with input hidden.

No compilation step is required: Python executes the source files directly.

## 3. Run the application

From the project root:

```powershell
.\.venv\Scripts\python.exe -m app.main
```

Choose an operation from the menu:

| Choice | Function | Behavior |
|---|---|---|
| 1 | `getAllStudents()` | Displays every record in ascending ID order. |
| 2 | `addStudent(first_name, last_name, email, enrollment_date)` | Inserts a record and displays its automatically generated ID. |
| 3 | `updateStudentEmail(student_id, new_email)` | Changes the email for that ID only. |
| 4 | `deleteStudent(student_id)` | Deletes that ID after confirmation in the menu. |
| 0 | Exit | Closes the menu. |

Use the actual ID shown after insertion. Sequence values can have gaps after
deletions or rejected inserts; do not assume the next ID is always 4.
Enter dates as `YYYY-MM-DD`, or leave the date blank for NULL.

Functions return the affected record; update/delete return `None` if the ID
does not exist. `getAllStudents()` displays and returns a list. Validation and
database errors propagate to the menu, which shows a readable message.

Each operation uses a separate connection and transaction. Successful operations
commit before success is displayed. Exceptions roll back the transaction and
close the connection. SQL parameters are bound with `%s` placeholders rather
than concatenated into SQL, so quotes and SQL-like input remain data.

### Alternative for an existing virtual environment

If `.venv` was created one directory above the
project root, run:

```powershell
..\.venv\Scripts\python.exe -m app.main
```

The normal setup instructions above create `.venv`
inside the project folder.


## 4. Check the effects in pgAdmin

Keep a Query Tool connected to **the same students_db** open. After each add,
update, or delete, re-execute `sql/03_verify.sql`. Previously displayed results
do not automatically refresh when the application changes the database.

For a simple comparison run:
1. List the three initial students.
2. Add Alex Taylor, alex.taylor@example.com, 2026-11-15. Note the returned ID.
3. Re-run the SELECT in pgAdmin and confirm the new record.
4. Update that ID's email to alex.updated@example.com; verify in pgAdmin.
5. Delete that ID, confirm with `yes`, and verify the record is gone in pgAdmin.

## 5. Error handling and deliberate choices

- Duplicate emails are rejected by PostgreSQL for both inserts and updates.
- A nonexistent ID reports that nothing was updated/deleted.
- Names cannot be blank in the application. Basic email structure and dates
  are checked before a query is sent. Email validation is not a complete RFC validator.
- Email case is preserved. The table uses the requested ordinary TEXT UNIQUE
  constraint; it does not add a case-insensitive uniqueness rule.
- An optional date becomes NULL; the other required fields cannot be NULL.
- The menu continues after normal input/database errors. Ctrl+C or end of input exits.
- `deleteStudent()` itself deletes immediately; confirmation belongs to the menu.
- The application does not create tables or insert seed data at startup.

## 6. Tests

Run the local unit tests without a database:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_unit.py -v
```

The **integration tests** need a separate PostgreSQL test database; the unit
tests above do not. Integration tests create a randomly named schema,
populate it, test actual SQL behavior, and drop only that schema afterwards.
They do not modify `public.students`. The database account needs schema-creation
permission. Use a dedicated test database, such as `students_test`.

Set connection details in the current PowerShell session, using your local values:

```powershell
$env:A3_TEST_DSN = "host=localhost port=5432 dbname=students_test user=postgres"
$securePassword = Read-Host "PostgreSQL password" -AsSecureString
$env:PGPASSWORD = [System.Net.NetworkCredential]::new("", $securePassword).Password
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Remove-Item Env:PGPASSWORD
Remove-Item Env:A3_TEST_DSN
```

If A3_TEST_DSN is absent, the integration tests are explicitly **skipped**, not
reported as passed. See `docs/TEST_RESULTS.md` for the results from this copy.

## 7. Repository and video requirements

The assignment calls for a new **public GitHub repository** containing the source,
SQL scripts, and README, with a video link in the README. It asks for the repository
URL on Brightspace. Keep `.gitignore` in the repository so local credentials and
the virtual environment are excluded. Do not upload `config.json` or passwords.

### Demonstration video

[Watch the PostgreSQL CRUD demonstration on YouTube](https://youtu.be/aKOxvWDeFTQ)
## Troubleshooting

| Problem | What to check |
|---|---|
| Python command opens the Microsoft Store | Install Python and reopen the terminal; try the `py` launcher. |
| `No module named psycopg` | Install requirements using the same `.venv` Python used to run the app. |
| `No module named app` | Open a terminal in the project root and use `-m app.main`. |
| Connection fails | Start the PostgreSQL Windows service; verify host, port, database name, and user. |
| Wrong password | Exit and restart the app to enter the server password again. |
| students table missing | Check the selected database and execute 01_schema.sql, then 02_seed.sql. |
| Record seems unchanged in pgAdmin | Re-execute SELECT in the same database; check for an old transaction if auto-commit is off. |
| Email already exists | Use a different email; the rejected operation leaves stored records unchanged. |

## Technical references

- PostgreSQL identity columns: https://www.postgresql.org/docs/current/ddl-identity-columns.html
- Psycopg connection/cursor usage: https://www.psycopg.org/psycopg3/docs/basic/usage.html
- Psycopg query parameters: https://www.psycopg.org/psycopg3/docs/basic/params.html
