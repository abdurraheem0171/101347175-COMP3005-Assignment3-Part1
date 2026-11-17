# Test results

The project contains 11 unit tests and 12 PostgreSQL integration tests.

| Check | Result |
|---|---|
| Python source syntax | Passed |
| Unit tests | 11 passed, 0 failed |
| PostgreSQL integration tests | 12 skipped because no separate test database was configured for this test run |

These checks were performed on November 16, 2026. The unit tests check validation, parameter binding, menu behavior, and error handling using mocks. They do not replace testing the application against a real PostgreSQL database.

To run the unit tests from the project root after installing requirements:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_unit.py -v
```

See section 6 of the README for instructions on running the integration tests with a dedicated PostgreSQL test database. Skipped tests should not be represented as passed.
