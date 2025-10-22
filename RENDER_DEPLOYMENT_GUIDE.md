# 🚀 Render Deployment Guide - Step by Step

Complete guide to deploy your PII-Anonymizer backend on Render.

---

## Prerequisites

✅ GitHub account with your code pushed to a repository  
✅ Render account (free tier available at https://render.com)  
✅ Your Groq API key ready  
✅ Encryption key generated (run `python crypto_util.py` locally to get one)

---

## Step 1: Push Your Code to GitHub

If you haven't already:

```powershell
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - PII Anonymizer ready for deployment"

# Add your GitHub remote (replace with your repo URL)
git remote add origin https://github.com/yourusername/your-repo-name.git

# Push to GitHub
git push -u origin main
```

**Important:** Make sure your `.env` file is in `.gitignore` (never commit secrets!)

---

## Step 2: Sign Up / Log In to Render

1. Go to **https://render.com**
2. Click **"Get Started"** or **"Sign In"**
3. Sign up with GitHub (recommended - makes repo connection easy)
4. Verify your email if required

---

## Step 3: Create a New Web Service

### 3.1 Start New Service

1. From Render Dashboard, click **"New +"** button (top right)
2. Select **"Web Service"**

![Click New + and select Web Service]

### 3.2 Connect Your Repository

**Option A - If you signed in with GitHub:**
1. Click **"Connect account"** if needed
2. You'll see a list of your repositories
3. Find your PII-Anonymizer repo
4. Click **"Connect"**

**Option B - If using a public repo:**
1. Paste your GitHub repository URL in the "Public Git repository" field
2. Click **"Continue"**

---

## Step 4: Configure Your Web Service

Fill in the following settings exactly as shown:

### Basic Settings

| Field | Value |
|-------|-------|
| **Name** | `pii-anonymizer-backend` (or your choice - this becomes your URL) |
| **Region** | Choose closest to you (e.g., `Oregon (US West)`, `Frankfurt (EU)`) |
| **Branch** | `main` (or `master` if that's your default branch) |
| **Root Directory** | Leave blank (or `.` if your code is in a subfolder) |
| **Runtime** | **Python 3** (auto-detected) |

### Build & Deploy Settings

| Field | Value | Notes |
|-------|-------|-------|
| **Build Command** | `pip install -r requirements.txt` | Installs all dependencies |
| **Start Command** | `gunicorn -w 4 -b 0.0.0.0:$PORT app:app` | Starts your Flask app with Gunicorn |

### Instance Type

| Option | Details |
|--------|---------|
| **Free** | ✅ Choose this for testing (0.1 CPU, 512 MB RAM) |
| **Starter** | $7/month (0.5 CPU, 512 MB RAM) - better performance |
| **Standard** | For production with high traffic |

**For this project, FREE tier works fine for testing!**

---

## Step 5: Add Environment Variables

This is **critical** - your app won't work without these!

Scroll down to the **"Environment Variables"** section and click **"Add Environment Variable"**

Add these **one by one**:

### Required Environment Variables

| Key | Value | How to Get It |
|-----|-------|---------------|
| `GROQ_API_KEY` | `gsk_your_actual_key_here` | Your Groq API key (the one you have in your local `.env`) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | The LLM model to use |
| `ENCRYPTION_KEY` | `your_encryption_key_here` | Run `python crypto_util.py` locally and copy the key |
| `FLASK_DEBUG` | `False` | Disable debug mode in production |

### Optional but Recommended

| Key | Value | Purpose |
|-----|-------|---------|
| `ALLOWED_ORIGINS` | `https://yourusername.github.io` | Restrict CORS to your GitHub Pages frontend only (for security) |

**Example of adding environment variables:**

1. Key: `GROQ_API_KEY`  
   Value: `gsk_NCbgdfLNA3QhcQvF...` (paste your actual key)

2. Key: `GROQ_MODEL`  
   Value: `llama-3.3-70b-versatile`

3. Key: `ENCRYPTION_KEY`  
   Value: (paste the key you got from running `python crypto_util.py`)

4. Key: `FLASK_DEBUG`  
   Value: `False`

5. (Optional) Key: `ALLOWED_ORIGINS`  
   Value: `https://yourusername.github.io` (your GitHub Pages URL)

---

## Step 6: Deploy!

1. Click **"Create Web Service"** at the bottom
2. Render will start building your app (this takes 2-5 minutes)
3. You'll see a build log showing:
   - Installing Python dependencies
   - Installing spaCy
   - Installing Flask, Groq, etc.
4. When it says **"Your service is live 🎉"** - you're done!

---

## Step 7: Get Your Backend URL

After deployment succeeds:

1. Your service URL will be shown at the top:  
   `https://pii-anonymizer-backend.onrender.com` (or whatever name you chose)

2. Copy this URL - you'll need it for your frontend!

---

## Step 8: Test Your Backend

### Test 1: Health Check

Open your browser or use curl:

```powershell
curl https://pii-anonymizer-backend.onrender.com/api/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "llm_mode": "api",
  "mappings_file_exists": false
}
```

✅ If you see this, your backend is working!

### Test 2: Anonymize Text (optional)

```powershell
curl -X POST https://pii-anonymizer-backend.onrender.com/api/anonymize `
  -H "Content-Type: application/json" `
  -d '{\"text\": \"My name is John Smith and my email is john@example.com\", \"mode\": \"pseudonymize\", \"call_llm\": false}'
```

You should get back anonymized text!

---

## Step 9: Update Your Frontend Config

Now update your frontend to point to this backend:

1. Edit `docs/config.js` (or `config.js` if you haven't created `docs/` yet):

```javascript
// Replace with your actual Render URL
window.BACKEND_URL = 'https://pii-anonymizer-backend.onrender.com';
```

2. Commit and push to GitHub:

```powershell
git add docs/config.js
git commit -m "Update backend URL for Render deployment"
git push
```

3. If you've set up GitHub Pages, it will automatically redeploy with the new backend URL!

---

## 🎉 You're Done!

Your backend is now live on Render at:  
`https://your-service-name.onrender.com`

---

## 🔧 Troubleshooting

### Issue: Build fails with "No module named 'flask_cors'"

**Solution:** Make sure `Flask-Cors==4.0.0` is in your `requirements.txt`

### Issue: "Application failed to respond"

**Solutions:**
1. Check build logs in Render dashboard for errors
2. Verify environment variables are set correctly
3. Make sure `Start Command` is: `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`

### Issue: Health check returns "mock mode" instead of "api"

**Solution:** Verify `GROQ_API_KEY` environment variable is set in Render

### Issue: CORS errors in browser

**Solutions:**
1. Add `ALLOWED_ORIGINS` environment variable with your GitHub Pages URL
2. Or temporarily set it to `*` for testing (not recommended for production)

### Issue: Service is slow to wake up

**Note:** Free tier services on Render "sleep" after 15 minutes of inactivity. First request after sleep takes 30-60 seconds. This is normal! Consider upgrading to Starter plan ($7/month) to keep it always awake.

---

## 📊 Monitoring Your Service

### View Logs

1. Go to your service in Render dashboard
2. Click **"Logs"** tab
3. You'll see real-time logs of requests and any errors

### View Metrics

1. Click **"Metrics"** tab
2. See CPU, memory usage, and request counts

### Restart Service

If something goes wrong:
1. Click **"Manual Deploy"** → **"Clear build cache & deploy"**
2. Or go to **Settings** → **"Restart Service"**

---

## 🔐 Security Best Practices

✅ **Never commit `.env` file** - add it to `.gitignore`  
✅ **Use environment variables** for all secrets in Render  
✅ **Set ALLOWED_ORIGINS** to your specific GitHub Pages domain  
✅ **Use HTTPS** (Render provides this automatically)  
✅ **Rotate API keys** regularly  
✅ **Monitor logs** for suspicious activity  
✅ **Use Starter plan** for production (better reliability)

---

## 💰 Costs

| Plan | Cost | Best For |
|------|------|----------|
| **Free** | $0/month | Testing, personal projects, low traffic |
| **Starter** | $7/month | Production apps, always-on, faster response |
| **Standard** | $25+/month | High traffic, multiple workers |

**Free tier limitations:**
- 750 hours/month (enough for one service always-on)
- Service sleeps after 15 min inactivity
- Slower cold starts

---

## 🚀 Next Steps

1. ✅ Backend deployed on Render
2. 📝 Deploy frontend to GitHub Pages (see main README)
3. 🔗 Update `docs/config.js` with backend URL
4. 🧪 Test end-to-end from your GitHub Pages site
5. 📊 Monitor logs and metrics in Render dashboard

---

## 📞 Need Help?

- **Render Docs:** https://render.com/docs
- **Render Community:** https://community.render.com
- **This Project Issues:** Create an issue in your GitHub repo

---

**Happy Deploying! 🎉**
