-- Re-run in pgAdmin after each application operation; an old result grid is static.
SELECT student_id, first_name, last_name, email, enrollment_date
FROM students
ORDER BY student_id;
