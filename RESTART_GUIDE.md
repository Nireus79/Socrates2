# When You Come Back - Simple PostgreSQL Setup

**Status:** PostgreSQL 17 installed, pg_hba.conf changed to trust mode
**What's Left:** Restart service, create databases, run migrations

---

## Just Do These Steps (Fresh Start)

### Step 1: Restart PostgreSQL

```powershell
# Open PowerShell as Administrator (right-click PowerShell → Run as Administrator)

# Find your PostgreSQL service
Get-Service postgresql*

# You'll see something like: postgresql-x64-17
# Restart it (use the actual name you see):
Restart-Service postgresql-x64-17
```

---

### Step 2: Add PostgreSQL to PATH

```powershell
# Add to PATH
$env:Path += ";C:\Program Files\PostgreSQL\17\bin"

# Test it works
psql --version
```

---

### Step 3: Create Databases

```powershell
# Connect (should NOT ask for password now)
psql -U postgres

# At postgres=# prompt, type these 3 commands:
CREATE DATABASE socrates_auth;
CREATE DATABASE socrates_specs;
\q
```

---

### Step 4: Run Migrations

```powershell
# Navigate to backend
cd C:\Users\themi\PycharmProjects\Socrates2\backend

# Activate virtual environment
..\venv\Scripts\Activate.ps1

# Run migrations (should work now!)
.\scripts\run_migrations.ps1
```

---

## What You've Already Done ✅

- Installed Python 3.12.3
- Created virtual environment
- Installed all 40 dependencies
- Installed PostgreSQL 17
- Changed pg_hba.conf to trust mode (no password needed)
- Created .env file

**You're 90% done!** Just need to restart PostgreSQL service and create the databases.

---

## If You Get Stuck

The issue was: PostgreSQL password kept failing.

**Solution:** Set PostgreSQL to "trust" mode (no password for localhost).

**You already edited:** `C:\Program Files\PostgreSQL\17\data\pg_hba.conf`

**Just need to:** Restart the service to apply the changes.

---

## Expected Success Output

When migrations work, you'll see:

```
======================================================================
ALL MIGRATIONS COMPLETED SUCCESSFULLY!
======================================================================

Database: socrates_auth
  Tables: users, refresh_tokens, alembic_version

Database: socrates_specs
  Tables: projects, sessions, alembic_version
```

---

**Take a break. Come back fresh. You've got this.** 💪
