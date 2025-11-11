# WINDOWS SETUP GUIDE - Python 3.12 Installation

**Date:** November 5, 2025
**Platform:** Windows with PowerShell
**Target:** Python 3.12 for Socrates

---

## ✅ Step 1: Check Current Python Version

```powershell
# Check if Python is installed
python --version

# Or try
py --version

# Or check all installed versions
py -0
```

**Expected Output:** `Python 3.12.x` (any 3.12 version is fine)

---

## 🔴 If Python 3.12 Is NOT Installed

### Option A: Install via Microsoft Store (EASIEST)

1. Open **Microsoft Store**
2. Search for "**Python 3.12**"
3. Click **Get** / **Install**
4. Wait for installation to complete
5. Verify: `python --version` in PowerShell

### Option B: Install from Python.org

1. Go to https://www.python.org/downloads/
2. Download **Python 3.12.x** installer (latest 3.12 version)
3. Run installer
4. ⚠️ **IMPORTANT:** Check "**Add Python to PATH**"
5. Click "Install Now"
6. Verify: `python --version` in PowerShell

---

## ✅ Step 2: Verify Python 3.12 Installation

```powershell
# Check version
python --version
# Should show: Python 3.12.x

# Check detailed version
python -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
# Should show: Python 3.12.x

# Check where Python is installed
where python
# Should show path like: C:\Users\YourName\AppData\Local\Programs\Python\Python312\python.exe
```

---

## 📦 Step 3: Set Up Virtual Environment (Windows)

```powershell
# Navigate to project backend directory
cd C:\Users\themi\PycharmProjects\Socrates\backend

# Create virtual environment with Python 3.12
python -m venv venv

# Activate virtual environment (PowerShell)
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run this first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try activating again:
.\venv\Scripts\Activate.ps1

# Your prompt should now show (venv) at the beginning
```

---

## 🚨 If Activation Fails - Execution Policy Error

**Error:**
```
.\venv\Scripts\Activate.ps1 : File cannot be loaded because running scripts is disabled on this system
```

**Fix:**
```powershell
# Allow scripts to run (one-time setup)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Confirm by typing 'Y' when prompted

# Now activate:
.\venv\Scripts\Activate.ps1

# Your prompt should show (venv)
```

---

## ✅ Step 4: Verify Virtual Environment

```powershell
# Check Python version in virtual environment
python --version
# Should show: Python 3.12.x

# Check pip version
pip --version
# Should show: pip 24.x.x from ...\venv\Lib\site-packages\pip (python 3.12)

# Upgrade pip
python -m pip install --upgrade pip
```

---

## 📦 Step 5: Install Dependencies

```powershell
# Make sure you're in backend directory with (venv) active
cd C:\Users\themi\PycharmProjects\Socrates\backend

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (includes testing tools)
pip install -r requirements-dev.txt

# Verify installation
python scripts\verify_dependencies.py
```

---

## 🔧 Alternative: Use Command Prompt Instead of PowerShell

If PowerShell keeps giving issues, use **Command Prompt (cmd.exe)**:

```cmd
# Open Command Prompt
# Press Win+R, type 'cmd', press Enter

# Navigate to project
cd C:\Users\themi\PycharmProjects\Socrates\backend

# Create virtual environment
python -m venv venv

# Activate (Command Prompt - different from PowerShell!)
venv\Scripts\activate.bat

# Your prompt should show (venv)

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## 📋 Quick Commands Summary (PowerShell)

```powershell
# 1. Check Python 3.12 installed
python --version

# 2. Navigate to backend
cd C:\Users\themi\PycharmProjects\Socrates\backend

# 3. Create virtual environment
python -m venv venv

# 4. Allow script execution (if needed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 5. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 6. Verify Python version
python --version

# 7. Upgrade pip
python -m pip install --upgrade pip

# 8. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 9. Verify installation
python scripts\verify_dependencies.py
```

---

## 🎯 Current Status Check

Based on your prompt showing `(.venv)`, it looks like you already have a virtual environment activated!

Try this:
```powershell
# Check what Python version is in your current .venv
python --version

# If it shows Python 3.12.x - YOU'RE GOOD!
# If it shows Python 3.11 or other - need to recreate venv
```

---

## ❓ If Virtual Environment Has Wrong Python Version

If `python --version` inside (.venv) shows **Python 3.11** instead of **3.12**:

```powershell
# Deactivate current virtual environment
deactivate

# Delete old virtual environment
Remove-Item -Recurse -Force .venv

# Create new one with Python 3.12
python -m venv venv

# Activate new one
.\venv\Scripts\Activate.ps1

# Verify it's now 3.12
python --version
```

---

## 🆘 Troubleshooting

### Issue 1: "python: command not found"

**Solution:** Python not in PATH. Reinstall Python and check "Add to PATH" during installation.

### Issue 2: "python3.12: command not found"

**Windows doesn't use python3.12 command.** Use `python` or `py` instead.

### Issue 3: Virtual environment activation fails

**PowerShell:** Use `.\venv\Scripts\Activate.ps1`
**Command Prompt:** Use `venv\Scripts\activate.bat`

### Issue 4: Multiple Python versions

```powershell
# List all Python versions
py -0

# Use specific version to create venv
py -3.12 -m venv venv
```

---

**Next:** After verifying Python 3.12 and activating venv, install dependencies!

