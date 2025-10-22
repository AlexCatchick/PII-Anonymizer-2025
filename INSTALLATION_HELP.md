# PII-Anonymizer Web-CLI - Installation Guide

## ⚠️ Important: Installation Issues on MSYS2/MinGW

Your Python installation (MSYS2/MinGW) has compatibility issues with some packages that require Rust compilation.

## 🔧 Solution Options:

### Option 1: Use Standard Windows Python (RECOMMENDED)

1. **Install Standard Python for Windows:**
   - Download from: https://www.python.org/downloads/
   - Get Python 3.10 or 3.11
   - During installation, check "Add Python to PATH"
   
2. **Open a NEW PowerShell window** (not MSYS2)

3. **Navigate to project and install:**
   ```powershell
   cd c:\Users\ASUS\Desktop\fyp_01
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

### Option 2: Install via MSYS2 UCRT Terminal

If you must use MSYS2, open an MSYS2 UCRT64 terminal:

```bash
pacman -S mingw-w64-ucrt-x86_64-python-cryptography
pacman -S mingw-w64-ucrt-x86_64-python-flask
pip install python-dotenv requests
# For spaCy, you may need to install from source or use pip with --no-build-isolation
```

### Option 3: Run Without SpaCy (Limited Functionality)

I can create a simplified version that only uses regex patterns without spaCy NER.

**Run this now:**
```powershell
python generate_key_and_setup.py
```

This will:
1. Generate encryption key
2. Create .env file
3. Check what's missing

## 📦 Manual Package Installation

Try installing packages one by one:

```powershell
# Install Flask and dependencies (these should work)
pip install Flask==2.3.3
pip install requests==2.31.0
pip install python-dotenv==1.0.0

# Try spaCy (may fail on MSYS2, but worth a try)
pip install spacy --prefer-binary
python -m spacy download en_core_web_sm
```

**Note:** Cryptography package has been removed - we now use built-in Python encryption!

## 🚀 Quick Test Without Full Installation

I'll create a simplified demo version that works with minimal dependencies!

Run: `python app_simple.py` (creating next...)
