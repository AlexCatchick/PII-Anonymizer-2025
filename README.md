# PII-Anonymizer Web-CLI

A complete, modular Python-Flask application that detects and anonymizes Personally Identifiable Information (PII) in text, supports multiple anonymization methods, stores encrypted reversible mappings, and enables deanonymization of LLM responses.

## Features

- **PII Detection**: Uses spaCy NER and regex patterns to detect various PII types
- **Multiple Anonymization Modes**:
  - **Pseudonymize**: Replace with reversible tokens (PII_1, PII_2...)
  - **Mask**: Partial masking with asterisks (J*** S***...)
  - **Replace**: Replace with entity type labels ([PERSON], [EMAIL]...)
- **Encrypted Storage**: Secure Fernet encryption for reversible mappings
- **LLM Integration**: LLM API integration with mock fallback
- **Deanonymization**: Restore original PII from LLM responses
- **Web Interface**: Clean, responsive web CLI interface

## Requirements

- Python 3.8+
- pip (Python package manager)

**Note:** This project uses built-in Python libraries for encryption (no external cryptography library needed).

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Download spaCy Model

```bash
python -m spacy download en_core_web_sm
```

### 3. Generate Encryption Key

```bash
python crypto_util.py
```

Copy the generated key to your `.env` file.

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your `FERNET_KEY` (required) and optional Gemini API credentials.

### 5. Run the Application

```bash
python app.py
```
```

**Built with ❤️ by Alex, Adit, Yashas and Rahul**
