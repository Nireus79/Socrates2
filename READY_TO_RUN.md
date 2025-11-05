# Socrates2 - Ready to Run

**Status:** All dependencies installed and verified ✅
**Next Step:** Configure environment and create databases

---

## Step 1: Run Environment Setup (Windows PowerShell)

```powershell
# Navigate to backend directory
cd C:\Users\themi\PycharmProjects\Socrates2\backend

# Activate virtual environment (if not already active)
.\venv\Scripts\Activate.ps1

# Run the automated setup script
python scripts\setup_env.py
```

**What this script will do:**
- ✅ Auto-generate a secure SECRET_KEY
- ✅ Auto-detect your existing ANTHROPIC_API_KEY from environment
- ❓ Ask for your PostgreSQL password (the one you set during PostgreSQL installation)
- ✅ Create a complete `.env` file

**Expected interaction:**
```
======================================================================
Socrates2 - Environment Setup
======================================================================

I'll help you create the .env file.
Press Enter to use default values shown in [brackets]

✅ Generated SECRET_KEY: [random string]

PostgreSQL Setup:
----------------------------------------------------------------------
PostgreSQL username [postgres]: <press Enter>
PostgreSQL password (the one you set during installation): <type your password>
PostgreSQL host [localhost]: <press Enter>
PostgreSQL port [5432]: <press Enter>

Claude API Setup:
----------------------------------------------------------------------
✅ Found existing ANTHROPIC_API_KEY in environment
Use existing key? (Y/n): <press Enter>

Application Settings:
----------------------------------------------------------------------
Enable debug mode? [True]: <press Enter>
Environment [development]: <press Enter>
Log level [DEBUG]: <press Enter>

✅ .env file created successfully!
```

---

## Step 2: Verify PostgreSQL Installation

Check if PostgreSQL is installed:

```powershell
# Check if psql command exists
psql --version
```

**Expected output:** `psql (PostgreSQL) 15.x` or higher

**If PostgreSQL is NOT installed:**
1. Download from: https://www.postgresql.org/download/windows/
2. Run installer
3. Remember the password you set for the `postgres` user
4. Add to PATH: `C:\Program Files\PostgreSQL\15\bin`

---

## Step 3: Create Databases

```powershell
# Connect to PostgreSQL and create databases
psql -U postgres -c "CREATE DATABASE socrates_auth;"
psql -U postgres -c "CREATE DATABASE socrates_specs;"

# Verify databases created
psql -U postgres -l
```

**You should see:**
```
                                  List of databases
      Name       |  Owner   | Encoding |   Collate   |    Ctype    |
-----------------+----------+----------+-------------+-------------+
 socrates_auth   | postgres | UTF8     | English_... | English_... |
 socrates_specs  | postgres | UTF8     | English_... | English_... |
```

---

## Step 4: Verify Configuration

Test that .env file works:

```powershell
cd C:\Users\themi\PycharmProjects\Socrates2\backend
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('✅ DATABASE_URL_AUTH:', os.getenv('DATABASE_URL_AUTH')[:30] + '...'); print('✅ ANTHROPIC_API_KEY:', 'sk-ant-' in os.getenv('ANTHROPIC_API_KEY', '')); print('✅ SECRET_KEY:', len(os.getenv('SECRET_KEY', '')) > 20)"
```

**Expected output:**
```
✅ DATABASE_URL_AUTH: postgresql://postgres:***@loc...
✅ ANTHROPIC_API_KEY: True
✅ SECRET_KEY: True
```

---

## Step 5: Initialize Database Schema (Phase 1)

Once .env and databases are ready:

```powershell
# Run Alembic migrations to create tables
cd C:\Users\themi\PycharmProjects\Socrates2\backend
alembic upgrade head
```

**This will create:**
- `users` table in socrates_auth
- `projects`, `sessions`, `specifications` tables in socrates_specs
- All indexes and constraints

---

## Troubleshooting

### Issue: "psql is not recognized"
**Fix:** Add PostgreSQL to PATH:
```powershell
$env:Path += ";C:\Program Files\PostgreSQL\15\bin"
```

### Issue: "FATAL: password authentication failed"
**Fix:** Use the password you set during PostgreSQL installation. Reset if needed:
```powershell
# Connect as postgres user, then:
ALTER USER postgres PASSWORD 'your-new-password';
```

### Issue: "database already exists"
**Fix:** Drop and recreate:
```powershell
psql -U postgres -c "DROP DATABASE socrates_auth;"
psql -U postgres -c "DROP DATABASE socrates_specs;"
# Then run CREATE DATABASE commands again
```

---

## Current Status Checklist

- [x] Python 3.12.3 installed
- [x] Virtual environment created
- [x] All 40 dependencies installed
- [x] Dependencies verified (all green checkmarks)
- [x] setup_env.py script created
- [ ] .env file created (run setup_env.py)
- [ ] PostgreSQL installed
- [ ] socrates_auth database created
- [ ] socrates_specs database created
- [ ] Alembic migrations run

---

## What Happens After This?

Once all checkboxes above are complete, you'll be ready to:

1. **Start the FastAPI server:** `uvicorn app.main:app --reload`
2. **Test API endpoints:** Open http://localhost:8000/docs
3. **Create first user:** POST to /api/v1/auth/register
4. **Begin Phase 1 implementation:** Follow PHASE_1.md

---

**Ready to proceed? Run the commands in order starting with Step 1.**
