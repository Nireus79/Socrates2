# PyCharm Configuration for Socrates2

## Fix "Unresolved reference 'app'" Error

### Method 1: Mark Directory as Sources Root (Recommended)
1. In PyCharm Project view, right-click on `backend` folder
2. Select **"Mark Directory as"** → **"Sources Root"**
3. The `backend` folder should turn blue/purple
4. PyCharm will now resolve imports starting from `backend/`

### Method 2: Configure Python Interpreter
1. Go to **File** → **Settings** (Windows) or **PyCharm** → **Preferences** (Mac)
2. Navigate to **Project: Socrates2** → **Python Interpreter**
3. Ensure your virtual environment is selected
4. If no venv exists, create one:
   - Click gear icon → **Add...**
   - Select **Virtualenv Environment** → **New environment**
   - Location: `C:\path\to\Socrates2\backend\venv`
   - Base interpreter: Python 3.12
5. Click **OK** and wait for PyCharm to index

### Method 3: Invalidate Caches
If the above doesn't work:
1. Go to **File** → **Invalidate Caches**
2. Check **"Clear file system cache and Local History"**
3. Click **"Invalidate and Restart"**
4. Wait for PyCharm to re-index (bottom right progress bar)

### Method 4: Set Working Directory
For run configurations:
1. Click **Edit Configurations** (top right, near play button)
2. For Python or pytest configurations:
   - Set **Working directory** to: `C:\path\to\Socrates2\backend`
   - Check **"Add content roots to PYTHONPATH"**
   - Check **"Add source roots to PYTHONPATH"**
3. Click **Apply** and **OK**

## Verify It's Fixed

Open any file (e.g., `backend/tests/test_data_persistence.py`) and check:
- `from app.models.user import User` should NOT show red underline
- Ctrl+Click (Cmd+Click on Mac) on `app` should jump to `backend/app/__init__.py`
- No more "Unresolved reference" warnings

## Alternative: Use Relative Imports (Not Recommended)

If you still have issues, you can add this to the top of test files:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

But this is a workaround - proper solution is marking `backend` as Sources Root.

## For Running Tests from Terminal

Always run from the `backend` directory:
```bash
cd C:\path\to\Socrates2\backend
pytest tests/test_data_persistence.py -v
```

The `pytest.ini` file already configures `pythonpath = .` so imports will work.

## For Running FastAPI Server

From `backend` directory:
```bash
cd C:\path\to\Socrates2\backend
python -m uvicorn app.main:app --reload
```

Or create a PyCharm run configuration:
1. **Run** → **Edit Configurations** → **+** → **Python**
2. Name: "FastAPI Server"
3. Script path: Select `uvicorn` executable in your venv
4. Parameters: `app.main:app --reload`
5. Working directory: `C:\path\to\Socrates2\backend`
6. Python interpreter: Your venv
7. Click **OK**

Now you can run the server with the play button!
