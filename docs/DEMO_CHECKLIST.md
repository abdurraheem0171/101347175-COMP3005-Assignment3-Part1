# Demonstration checklist (maximum 5 minutes)

Record your screen with the application and pgAdmin readable. Use a disposable
demo database if you want to show setup from scratch; never drop a database
containing work you need. Hide passwords and unrelated windows.

| Time | Show |
|---|---|
| 0:00-1:00 | The database name, CREATE TABLE script, its five column definitions/constraints, seed INSERT, and the three initial rows in pgAdmin. Execute setup once in a fresh demo database, or clearly demonstrate the already-created setup. |
| 1:00-1:30 | Start the program. Choose list; show all initial records (`getAllStudents`). |
| 1:30-2:20 | Add a new student (`addStudent`). Show the returned ID. Re-run SELECT in pgAdmin and point to the new row. |
| 2:20-3:05 | Update that student's email (`updateStudentEmail`). Re-run SELECT in pgAdmin and point to the changed email. |
| 3:05-3:45 | Delete that student (`deleteStudent`), confirming with yes. Re-run SELECT in pgAdmin and show the row is absent. |
| 3:45-4:25 | Briefly demonstrate duplicate-email rejection or a missing ID. Verify no unintended row change. |
| 4:25-4:55 | Show source organization, comments, README run instructions, and the four function definitions. |

Use the ID actually returned by the insertion. Keep the recording under five
minutes; error-case testing is useful evidence but should not crowd out the
required setup and four operations. Narration is optional; demonstrate the behavior clearly on screen.

After recording, upload the video, check link access without signing in, and add
the actual URL to the README. A checklist is not a substitute for the video.
