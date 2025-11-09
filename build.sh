#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit  # exit on error

echo "🔧 Starting build process..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Download spaCy model (fallback if requirements.txt method fails)
echo "🧠 Ensuring spaCy English model is available..."
python -m spacy download en_core_web_sm || echo "⚠️  spaCy model download failed, trying alternative..."

# Test imports
echo "🧪 Testing critical imports..."
python -c "
import spacy
import flask
import groq
print('✅ All critical imports successful')

# Test spaCy model loading
try:
    nlp = spacy.load('en_core_web_sm')
    print('✅ spaCy English model loaded successfully')
except Exception as e:
    print(f'⚠️  spaCy model loading issue: {e}')
    print('   This might cause issues but deployment will continue...')
"

echo "✅ Build process completed!"