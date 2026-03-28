# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python 3 SDK for integrating with the Polish KSeF 2.0 (Krajowy System e-Faktur) platform. Supports token-based and XAdES certificate-based authentication, interactive and batch invoice submission, invoice retrieval, and UPO (Urzędowe Potwierdzenie Odbioru) handling.

## Development Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run all tests
python -m unittest discover tests

# Run a specific test file
python -m unittest tests.testsuite.test1

# Lint (critical errors only)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Lint (full, max-line-length=140)
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=140 --statistics

# Build distribution
python -m build
```

The `PYTHONPATH` must include the workspace root — `.vscode/settings.json` sets this automatically for VSCode terminal.

## Architecture

```
ksef/
  __init__.py          # Exports KSEFSDK
  sdk/
    ksefsdk.py         # Main public API class (inherits HOOKHTTP)
    authksef.py        # AUTHTOKEN / AUTHCERT authentication implementations
    httphook.py        # HTTP wrapper (requests); handles auth tokens, retries
    encrypt.py         # AES-256-CBC + RSA/OAEP encryption, SHA-256 hashing
    xades_sign.py      # XAdES enveloped XML signatures for cert-based auth
  pattern/
    request.xml        # XML template for authentication requests
```

### Key Design Points

**Authentication flow:**
1. Fetch challenge from KSeF `/auth/challenge`
2. Fetch KSeF public certificate for key encryption
3. Authenticate via token (AUTHTOKEN) or XAdES signature (AUTHCERT)
4. Redeem challenge response for session access token

**Two session modes:**
- *Interactive*: `start_session()` → `send_invoice()` → `close_session()`
- *Batch*: `send_batch_session_bytes()` handles full lifecycle internally

**Class hierarchy:** `KSEFSDK` → `HOOKHTTP` → uses `AUTHTOKEN`/`AUTHCERT` for auth strategy

**Rate limiting:** Polling methods use decorators with configurable delays (`_SESSIONRATELIMITER`, `_INVOICERATELIMITER`, etc.). HTTP 429 triggers exponential backoff.

### Environment Constants

```python
KSEFSDK.DEVKSEF  = 0  # Development: web2te-ksef.mf.gov.pl
KSEFSDK.PREKSEF  = 1  # Pre-production: ksef2te.mf.gov.pl
KSEFSDK.PRODKSEF = 2  # Production: ksef2.mf.gov.pl
```

### Subject Type Constants

```python
SUBJECT1 = 'Subject1'           # Seller
SUBJECT2 = 'Subject2'           # Buyer
SUBJECT3 = 'Subject3'           # Entity 3
SUBJECTAUTHORIZED = 'SubjectAuthorized'
```

## Publishing

Pushing a tag matching `v*` triggers the GitHub Actions workflow (`.github/workflows/publish.yml`) to build and publish to PyPI automatically.
