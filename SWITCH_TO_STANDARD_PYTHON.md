# Switch from MSYS2 to Standard Windows Python

## Problem
Your current Python (MSYS2/MinGW) cannot compile spaCy's dependencies (numpy, etc.) because it lacks proper Python development headers.

## Solution: Use Standard Windows Python

### Step 1: Install Standard Python for Windows

1. **Download Python 3.10 or 3.11:**
   - Go to: https://www.python.org/downloads/windows/
   - Download: "Windows installer (64-bit)" for Python 3.10.x or 3.11.x
   - **Important:** During installation, CHECK ✓ "Add Python to PATH"

2. **Verify Installation:**
   Open a **NEW** PowerShell window (not MSYS2 terminal):
   ```powershell
   python --version
   # Should show: Python 3.10.x or 3.11.x
   
   where python
   # Should show: C:\Users\...\AppData\Local\Programs\Python\Python310\python.exe
   # NOT: C:\msys64\...
   ```

### Step 2: Install All Dependencies

In the **NEW PowerShell** window:

```powershell
# Navigate to project
cd C:\Users\ASUS\Desktop\fyp_01

# Upgrade pip
python -m pip install --upgrade pip

# Install all dependencies (this will work now!)
pip install Flask==2.3.3
pip install requests==2.31.0
pip install python-dotenv==1.0.0
pip install spacy==3.7.2

# Download spaCy language model
python -m spacy download en_core_web_sm
```

### Step 3: Run the Application

```powershell
# Generate encryption key (if not done already)
python crypto_util.py

# Run the app
python app.py
```

### Step 4: Access the Application
Open browser: http://localhost:5000

---

## Why Standard Python Works Better

| Feature | MSYS2 Python | Standard Windows Python |
|---------|--------------|------------------------|
| Package compatibility | ❌ Poor | ✅ Excellent |
| Precompiled wheels | ❌ Limited | ✅ Available for most packages |
| Compilation requirements | ❌ Needs GCC, dev headers | ✅ No compilation needed |
| spaCy installation | ❌ Fails | ✅ Works perfectly |
| Use case | Unix-like development | Windows Python development |

---

## Alternative: If You Must Use MSYS2

If you absolutely need to keep MSYS2, you need to install development packages:

```bash
# Open MSYS2 UCRT64 terminal
pacman -S mingw-w64-ucrt-x86_64-python-pip
pacman -S mingw-w64-ucrt-x86_64-python-numpy
pacman -S mingw-w64-ucrt-x86_64-gcc
pacman -S mingw-w64-ucrt-x86_64-python-devel

# Then try installing spaCy
pip install spacy
```

**However, this is NOT recommended** - standard Windows Python is much easier.

---

## Quick Test After Installing Standard Python

Run this to verify everything works:

```powershell
python -c "import spacy; print('✅ spaCy installed successfully')"
python -c "import flask; print('✅ Flask installed successfully')"
python generate_key_and_setup.py
```

---

## Need Help?

If you encounter issues:
1. Make sure you're using a **NEW** PowerShell window (not MSYS2)
2. Verify Python path: `where python` should NOT show MSYS2
3. If MSYS2 Python still appears first, you may need to adjust PATH or uninstall MSYS2 Python

**The key is: Use standard Windows Python from python.org, NOT MSYS2 Python!**
