"""
Flask application for PII-Anonymizer Web-CLI.
Main entry point for the web application.
"""
import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS
from anonymizer import PIIAnonymizer
from storage import MappingStorage
from llm_client import GroqClient

load_dotenv()

app = Flask(__name__)

# Use environment variable for secret key, or generate one if not provided
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    SECRET_KEY = os.urandom(24)
    # In production, you should set this as an environment variable
app.config['SECRET_KEY'] = SECRET_KEY

# If ALLOWED_ORIGINS is set in .env, use it as a comma-separated list. Otherwise default to allow all origins (useful for GitHub Pages during testing).
allowed_origins_env = os.getenv('ALLOWED_ORIGINS', '')
if allowed_origins_env:
    allowed = [o.strip() for o in allowed_origins_env.split(',') if o.strip()]
    CORS(app, origins=allowed)
else:
    # Default: allow all origins (change in production to restrict)
    CORS(app)

ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', '').encode()
if not ENCRYPTION_KEY or ENCRYPTION_KEY == b'your_encryption_key_here':
    print("WARNING: No valid ENCRYPTION_KEY found in environment variables!")
    # In production, generate a temporary key but warn about it
    from crypto_util import generate_key
    ENCRYPTION_KEY = generate_key()
    print(f"⚠️  Using temporary key for this session. For production, set ENCRYPTION_KEY environment variable!")
    print(f"Generated key: {ENCRYPTION_KEY.decode()}")

MAPPINGS_FILE = os.getenv('MAPPINGS_FILE', 'mappings.enc')

# Initialize components
print("🔧 Initializing PII Anonymizer...")
anonymizer = PIIAnonymizer()
print("✅ PII Anonymizer initialized")

print("🔧 Initializing storage...")
storage = MappingStorage(MAPPINGS_FILE, ENCRYPTION_KEY)
print("✅ Storage initialized")

# Initialize LLM client
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')

if GROQ_API_KEY:
    print(f"Running in API mode with Groq")
    print(f"   Model: {GROQ_MODEL}")
    print(f"   API Key: {GROQ_API_KEY[:20]}...{GROQ_API_KEY[-4:]}")
    llm_client = GroqClient(GROQ_API_KEY, GROQ_MODEL)
else:
    print("⚠️  No GROQ_API_KEY found - running in mock mode")
    print("   Set GROQ_API_KEY environment variable to enable LLM features")
    llm_client = GroqClient(None, GROQ_MODEL)  # Will use mock mode


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/anonymize', methods=['POST'])
def anonymize_text():
    """
    Enhanced anonymize endpoint with three anonymization modes.
    
    Request JSON:
        {
            "text": "Input text with PII",
            "mode": "pseudonymize|mask|replace",
            "call_llm": true|false
        }
    
    Anonymization Modes:
        - pseudonymize: Creates semantic placeholders (name_1, email_1, mobNo_1, etc.)
        - mask: Intelligent partial masking preserving structure (P*** M***, +1 (555) 123-X567)
        - replace: Human-friendly labels ([Person Name], [Email Address], [Phone Number])
    
    Response JSON:
        {
            "anonymized_text": "...",
            "entity_mappings": {...},
            "llm_response": "...",  (if call_llm=true)
            "llm_response_anonymized": "...",  (if call_llm=true)
            "deanonymized_output": "...",  (if call_llm=true)
            "mappings_count": 5
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({'error': 'Empty text provided'}), 400
        
        # Support both 'action' and 'mode' for backward compatibility
        mode = data.get('mode', data.get('action', 'pseudonymize'))
        if mode == 'anonymize':  # Map old 'anonymize' to 'pseudonymize'
            mode = 'pseudonymize'
        
        call_llm = data.get('call_llm', False)
        
        print(f"🔍 Processing text (length: {len(text)}, mode: {mode})")
        
        # Use the appropriate anonymization method based on mode
        if mode == 'mask':
            anonymized_text, mappings = anonymizer.mask(text)
        elif mode == 'replace':
            anonymized_text, mappings = anonymizer.replace(text)
        else:  # Default to pseudonymize
            anonymized_text, mappings = anonymizer.pseudonymize(text)
        
        # Store mappings for later deanonymization
        if mappings:
            storage.add_mappings(mappings)
            print(f"💾 Stored {len(mappings)} entity mappings")
        
        response_data = {
            'anonymized_text': anonymized_text,
            'entity_mappings': mappings,  # Include mappings in response
            'mappings_count': len(mappings)
        }
        
        if call_llm and llm_client:
            print("🤖 Calling LLM with anonymized text...")
            # Call LLM with anonymized text
            llm_prompt = f"Please respond to the following message:\n\n{anonymized_text}"
            llm_response = llm_client.generate_response(llm_prompt)
            print(f"✅ LLM response received (length: {len(llm_response)})")
            
            # Deanonymize the LLM response
            deanonymized_output = anonymizer.deanonymize(llm_response, mappings)
            
            response_data.update({
                'llm_response': llm_response,  # Keep original name for compatibility
                'llm_response_anonymized': llm_response,
                'deanonymized_output': deanonymized_output
            })
        
        return jsonify(response_data)
    
    except Exception as e:
        print(f"❌ Error in anonymize_text: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/deanonymize', methods=['POST'])
def deanonymize_text():
    """
    Deanonymize text using stored mappings.
    
    Request JSON:
        {
            "text": "Anonymized text"
        }
    
    Response JSON:
        {
            "deanonymized_text": "..."
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
        
        text = data['text']
        
        # Load stored mappings
        mappings = storage.load_mappings()
        
        # Deanonymize
        deanonymized_text = anonymizer.deanonymize(text, mappings)
        
        return jsonify({
            'deanonymized_text': deanonymized_text,
            'mappings_used': len(mappings)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/clear-mappings', methods=['POST'])
def clear_mappings():
    """Clear all stored mappings."""
    try:
        storage.clear_mappings()
        return jsonify({'message': 'Mappings cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint for production monitoring."""
    try:
        # Test anonymizer functionality
        test_result = anonymizer.detect_pii("Test John Doe")
        anonymizer_healthy = len(test_result) > 0
        
        return jsonify({
            'status': 'healthy',
            'timestamp': os.environ.get('TIMESTAMP', 'unknown'),
            'version': '2.0.0',  # Update version
            'anonymizer_healthy': anonymizer_healthy,
            'llm_mode': 'mock' if (not llm_client or llm_client.mock_mode) else 'api',
            'llm_available': GROQ_API_KEY is not None,
            'mappings_file_exists': os.path.exists(MAPPINGS_FILE),
            'environment': {
                'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                'has_groq_api_key': bool(GROQ_API_KEY),
                'has_encryption_key': bool(ENCRYPTION_KEY),
                'debug_mode': os.getenv('FLASK_DEBUG', 'False') == 'True'
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': os.environ.get('TIMESTAMP', 'unknown')
        }), 500


# Add a startup endpoint to verify all components
@app.route('/api/startup-check', methods=['GET'])
def startup_check():
    """Comprehensive startup check for debugging deployment issues."""
    checks = {}
    
    try:
        # Check spaCy model
        import spacy
        nlp = spacy.load('en_core_web_sm')
        checks['spacy_model'] = 'loaded'
    except Exception as e:
        checks['spacy_model'] = f'error: {str(e)}'
    
    try:
        # Check anonymizer
        test_entities = anonymizer.detect_pii("John Doe works at ACME Corp")
        checks['anonymizer'] = f'working - detected {len(test_entities)} entities'
    except Exception as e:
        checks['anonymizer'] = f'error: {str(e)}'
    
    try:
        # Check storage
        test_mappings = {'test_1': 'test_value'}
        storage.add_mappings(test_mappings)
        loaded = storage.load_mappings()
        checks['storage'] = f'working - {len(loaded)} mappings stored'
    except Exception as e:
        checks['storage'] = f'error: {str(e)}'
    
    return jsonify({
        'checks': checks,
        'environment_vars': {
            'GROQ_API_KEY': 'set' if GROQ_API_KEY else 'not set',
            'ENCRYPTION_KEY': 'set' if ENCRYPTION_KEY else 'not set',
            'MAPPINGS_FILE': MAPPINGS_FILE,
            'PORT': os.getenv('PORT', 'not set'),
            'FLASK_DEBUG': os.getenv('FLASK_DEBUG', 'not set')
        }
    })


if __name__ == '__main__':
    # Development server configuration
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    
    print(f"🚀 Starting Flask application...")
    print(f"   Debug mode: {debug_mode}")
    print(f"   Port: {port}")
    print(f"   Host: 0.0.0.0")
    
    app.run(
        debug=debug_mode,
        host='0.0.0.0',
        port=port
    )
