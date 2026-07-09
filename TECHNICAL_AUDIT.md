# TECHNICAL AUDIT

Version: 1.0

## Current State

The engine is stable production software with a legacy structure.

Active providers:

- Betfair
- Unibet
- Bet3000

Legacy providers remain in the repository but are not actively maintained.

## Main Technical Debt

1. Database access is spread across multiple files using direct pymysql calls.

2. Credentials are hardcoded or stored in plain config-style files.

3. Provider modules duplicate matching, insert and retry patterns.

4. arb_monitor.py is large and controls too many responsibilities.

5. Active and legacy code live side by side.

6. Logging is inconsistent.

7. Runtime-generated files are mixed with source files.

8. Backup files are stored in the repository.

9. There is no formal test suite.

10. Error handling is broad and often silent.

## Recommended Improvement Order

1. Do not refactor yet.

2. Keep documenting active production paths.

3. Add .gitignore improvements.

4. Separate generated files from source over time.

5. Introduce safer config handling.

6. Centralize database access only after behaviour is fully understood.

7. Improve logging gradually.

8. Add narrow tests for Betfair, Unibet and Bet3000.

9. Only then consider refactoring arb_monitor.py.

## Rule

Every improvement must be small, reversible and production-safe.
