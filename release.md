### Wersja 1.1.2 Date: 2026/05/16
- Replace flake8/unittest with ruff/pytest across CI, VSCode settings, and docs
- Add KSEFSDK.UNITTEST=3 env constant that disables 429 retry sleep during tests
- Improve HTTP 429 handling: exponential backoff, configurable max retries
- Consolidate duplicate TestTokenOnLine/TestCertfOnLine into one parametrized TestOnLine
- Move pytest and ruff config into pyproject.toml; remove requirements.txt
### Wersja 1.1.1 Data: 2026/05/01
* Refactoring po Claude review
* Poprawiona obsługa temporary files
* Timeout do http requests
### Wersja 1.1.0r1  Data: 2026/04/27
* Poprawienie logowania w wypadku wykrycia błędu, np. zduplikowana faktura
### Wersja 1.1.0  Data: 2026/03/13
* Dodanie exportu paczki faktury /invoices/exports
