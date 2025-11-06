# RUN SOCRATES2 - DO THIS NOW

## 1. Pull the Code

```bash
cd C:\path\to\Socrates2
git pull origin master
```

## 2. Install Dependencies

```bash
cd backend
pip install -e ".[dev]"
```

**This installs the package so imports work everywhere.**

## 3. Configure Database

```bash
# Copy example
copy .env.example .env

# Edit .env - set these:
DATABASE_URL_AUTH=postgresql://postgres@localhost:5432/socrates_auth
DATABASE_URL_SPECS=postgresql://postgres@localhost:5432/socrates_specs
SECRET_KEY=your-secret-key-here-change-this
ANTHROPIC_API_KEY=your-api-key-here
```

## 4. RUN the Critical Tests

```bash
pytest tests/test_data_persistence.py -v
```

**All 4 tests MUST pass.** This verifies the archive killer bug is fixed.

## 5. RUN the Server

```bash
python -m uvicorn app.main:app --reload
```

## 6. USE IT

Open browser: **http://localhost:8000/docs**

Test the endpoints:
- POST /api/v1/auth/register - Create user
- POST /api/v1/auth/login - Get JWT token
- GET /api/v1/admin/health - Check databases

---

## If Step 2 Fails

Dependencies not installed. Run:

```bash
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Then try step 4.

---

## If Step 4 Fails

Database not set up. Run:

```bash
createdb socrates_auth
createdb socrates_specs
alembic upgrade head
```

Then try step 4 again.

---

## That's It

The code is ready. Just pull, install, and run.
