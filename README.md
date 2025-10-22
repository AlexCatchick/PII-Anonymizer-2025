# PII-Anonymizer Web-CLI

A complete, modular Python-Flask application that detects and anonymizes Personally Identifiable Information (PII) in text, supports multiple anonymization methods, stores encrypted reversible mappings, and enables deanonymization of LLM responses.

## Features

- **PII Detection**: Uses spaCy NER and regex patterns to detect various PII types
- **Multiple Anonymization Modes**:
  - **Pseudonymize**: Replace with reversible tokens (PII_1, PII_2...)
  - **Mask**: Partial masking with asterisks (J*** S***...)
  - **Replace**: Replace with entity type labels ([PERSON], [EMAIL]...)
- **Encrypted Storage**: Secure Fernet encryption for reversible mappings
- **LLM Integration**: Optional Gemini API integration with mock fallback
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

### 6. Access the Application

Open your browser and navigate to: **http://localhost:5000**

## Project Structure

```
PII-Anonymizer-Web-CLI/
├── app.py              # Flask application entry point
├── anonymizer.py       # PII detection and anonymization logic
├── storage.py          # Encrypted mapping file management
├── crypto_util.py      # Fernet encryption/decryption utilities
├── llm_client.py       # Gemini LLM client (with mock support)
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── .env                # Actual environment variables (create this)
├── mappings.enc        # Encrypted mappings file (auto-generated)
├── README.md           # This file
└── templates/
    └── index.html      # Web CLI interface
```

## Configuration

### Environment Variables (.env)

```env
# REQUIRED: Encryption key (generated using crypto_util.py)
ENCRYPTION_KEY=your_generated_key_here

# OPTIONAL: Gemini API configuration
GEMINI_API_URL=https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent
GEMINI_API_KEY=your_gemini_api_key_here

# OPTIONAL: Flask configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

## PII Detection Rules

### spaCy Entity Types

- **PERSON**: People's names
- **GPE**: Countries, cities, states
- **ORG**: Organizations, companies
- **DATE**: Dates, time periods
- **MONEY**: Monetary values
- **FAC**: Buildings, airports, highways
- **NORP**: Nationalities, religious/political groups

### Custom Regex Patterns

- **EMAIL**: Standard email format detection
- **PHONE**: US and international phone number formats
- **CREDIT_CARD**: Major credit card number patterns
- **SSN**: Social Security Numbers

## Usage Examples

### Sample Input

```
Hello, my name is John Smith. I live in New York and my email is john.smith@email.com.
You can call me at (555) 123-4567. My credit card is 4111-1111-1111-1111.
```

### Pseudonymize Output

```
Hello, my name is PII_1. I live in PII_2 and my email is PII_3.
You can call me at PII_4. My credit card is PII_5.
```

### Mask Output

```
Hello, my name is J*** S****. I live in N** Y*** and my email is j***@email.com.
You can call me at (555) -. My credit card is 4111---***.
```

### Replace Output

```
Hello, my name is [PERSON]. I live in [GPE] and my email is [EMAIL].
You can call me at [PHONE]. My credit card is [CREDIT_CARD].
```

## Security Features

- **XOR Encryption with SHA-256**: Secure encryption using Python's built-in libraries
- **Local Storage**: All data stored locally, no external transmission
- **Secure Key Management**: Environment-based key configuration
- **Reversible Anonymization**: Safely restore original data when needed

## LLM Integration

### With Gemini API

Configure `GEMINI_API_URL` and `GEMINI_API_KEY` in `.env` for real LLM integration.

### Mock Mode (Default)

If no API credentials are provided, the application runs in mock mode with simulated responses.

## 🛠️ Development

### Running Tests

```bash
# Test individual components
python crypto_util.py  # Generate encryption key
python anonymizer.py   # Test anonymization (if __main__ block added)
```

### Debugging

Enable Flask debug mode in `.env`:

```env
FLASK_DEBUG=True
```

## API Endpoints

### POST /api/anonymize

Anonymize input text with optional LLM call.

**Request:**
```json
{
  "text": "Input text with PII",
  "mode": "pseudonymize|mask|replace",
  "call_llm": true|false
}
```

**Response:**
```json
{
  "anonymized_text": "...",
  "llm_response_anonymized": "...",
  "deanonymized_output": "...",
  "mappings_count": 5
}
```

### POST /api/clear-mappings

Clear all stored encrypted mappings.

### GET /api/health

Health check endpoint.

## Troubleshooting

### spaCy Model Not Found

```bash
python -m spacy download en_core_web_sm
```

### Missing ENCRYPTION_KEY

Run `python crypto_util.py` to generate a new key, then add it to `.env`.

### Port Already in Use

Change the port in `app.py`:

```python
app.run(port=5001)  # Use different port
```

## License

This project is provided as-is for educational and demonstration purposes.

## Contributing

Feel free to fork, modify, and enhance this project for your needs!

## Support

For issues or questions, please refer to the documentation or create an issue in the repository.

---

## 🚀 Deployment Guide

This project is ready for deployment with the frontend on **GitHub Pages** and the backend on **Render** (or similar platforms).

### Frontend Deployment (GitHub Pages)

1. **Prepare the frontend files:**
   ```powershell
   # Create a docs folder for GitHub Pages
   mkdir docs
   Copy-Item templates\index.html docs\
   Copy-Item config.js docs\
   ```

2. **Configure the backend URL:**
   Edit `docs/config.js` and set your deployed backend URL:
   ```javascript
   window.BACKEND_URL = 'https://your-backend-name.onrender.com';
   ```

3. **Enable GitHub Pages:**
   - Push your repository to GitHub
   - Go to repository **Settings** → **Pages**
   - Set **Source** to deploy from the `docs/` folder on your main branch
   - Save and wait for deployment (usually takes 1-2 minutes)
   - Your frontend will be available at: `https://yourusername.github.io/your-repo-name/`

### Backend Deployment (Render)

1. **Push your code to GitHub** (if not already done)

2. **Create a new Web Service on Render:**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click **New** → **Web Service**
   - Connect your GitHub repository
   - Configure the service:
     - **Name**: Choose a name (e.g., `pii-anonymizer-backend`)
     - **Region**: Choose closest to your users
     - **Branch**: `main` (or your default branch)
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`

3. **Add Environment Variables** in Render:
   - `GROQ_API_KEY`: Your Groq API key
   - `GROQ_MODEL`: `llama-3.3-70b-versatile` (or your preferred model)
   - `ENCRYPTION_KEY`: Generate using `python crypto_util.py` locally and paste the key
   - `ALLOWED_ORIGINS` (optional): Your GitHub Pages URL (e.g., `https://yourusername.github.io`)
   - `FLASK_DEBUG`: `False` (for production)

4. **Deploy:**
   - Click **Create Web Service**
   - Wait for the build and deployment (usually 2-5 minutes)
   - Your backend will be available at: `https://your-backend-name.onrender.com`

5. **Update frontend config:**
   - Go back to your `docs/config.js` file
   - Update `window.BACKEND_URL` with your Render backend URL
   - Commit and push the changes
   - GitHub Pages will automatically redeploy

### Verify Deployment

1. **Test backend health:**
   ```powershell
   curl https://your-backend-name.onrender.com/api/health
   ```
   Should return: `{"status":"healthy","llm_mode":"api","mappings_file_exists":...}`

2. **Test frontend:**
   - Visit your GitHub Pages URL
   - Open browser DevTools (F12) → Console
   - You should see a successful health check API call
   - Try anonymizing sample text to verify end-to-end functionality

### Security Best Practices

- ✅ Never commit `.env` file or expose API keys
- ✅ Set `ALLOWED_ORIGINS` to restrict CORS to your GitHub Pages domain only
- ✅ Use Render's environment variables for secrets (not hardcoded in code)
- ✅ Enable HTTPS (Render provides this automatically)
- ✅ Consider rate limiting for production use
- ✅ Regularly rotate your `ENCRYPTION_KEY` and `GROQ_API_KEY`

### Alternative Deployment Options

**Backend alternatives:**
- **Heroku**: Similar process, use the included `Procfile`
- **Railway**: Auto-detects Procfile and requirements.txt
- **Azure App Service**: Supports Python web apps
- **AWS Elastic Beanstalk**: For scalable deployments

**Frontend alternatives:**
- **Netlify**: Drag-and-drop deployment
- **Vercel**: Git-based deployments
- **Cloudflare Pages**: Fast global CDN

### Troubleshooting

**Issue: Frontend can't reach backend**
- Verify `BACKEND_URL` in `config.js` is correct
- Check browser console for CORS errors
- Ensure `ALLOWED_ORIGINS` includes your GitHub Pages URL

**Issue: Backend returns 500 errors**
- Check Render logs for Python errors
- Verify all environment variables are set
- Ensure spaCy model is installed (check build logs)

**Issue: LLM responses are mocked**
- Verify `GROQ_API_KEY` is set correctly in Render
- Check Render logs for API errors
- Verify Groq API quota/billing status

---

**Built with ❤️ by Alex, Adit, Yashas and Rahul**
