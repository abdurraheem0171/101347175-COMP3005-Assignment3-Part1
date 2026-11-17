-- Run once in students_db. Existing tables are not dropped or overwritten.
-- IDENTITY generates student IDs automatically; PRIMARY KEY enforces uniqueness.
CREATE TABLE students (
    student_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    enrollment_date DATE
);
