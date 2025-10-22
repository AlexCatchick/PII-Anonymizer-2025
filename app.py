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

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Configure CORS
# If ALLOWED_ORIGINS is set in .env, use it as a comma-separated list. Otherwise default to allow all origins (useful for GitHub Pages during testing).
allowed_origins_env = os.getenv('ALLOWED_ORIGINS', '')
if allowed_origins_env:
    allowed = [o.strip() for o in allowed_origins_env.split(',') if o.strip()]
    CORS(app, origins=allowed)
else:
    # Default: allow all origins (change in production to restrict)
    CORS(app)

# Initialize components
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', '').encode()
if not ENCRYPTION_KEY or ENCRYPTION_KEY == b'your_encryption_key_here':
    print("WARNING: No valid ENCRYPTION_KEY found in .env file!")
    print("Run 'python crypto_util.py' to generate a key, then add it to .env")
    # Generate a temporary key for testing
    from crypto_util import generate_key
    ENCRYPTION_KEY = generate_key()
    print(f"Using temporary key for this session: {ENCRYPTION_KEY.decode()}")

MAPPINGS_FILE = 'mappings.enc'

# Initialize anonymizer and storage
anonymizer = PIIAnonymizer()
storage = MappingStorage(MAPPINGS_FILE, ENCRYPTION_KEY)

# Initialize LLM client
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
llm_client = GroqClient(GROQ_API_KEY, GROQ_MODEL)


@app.route('/')
def index():
    """Render main web interface."""
    return render_template('index.html')


@app.route('/api/anonymize', methods=['POST'])
def anonymize_text():
    """
    Anonymize input text using specified mode.
    
    Request JSON:
        {
            "text": "Input text with PII",
            "mode": "pseudonymize|mask|replace",
            "call_llm": true|false
        }
    
    Response JSON:
        {
            "anonymized_text": "...",
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
        
        text = data['text']
        mode = data.get('mode', 'pseudonymize')
        call_llm = data.get('call_llm', False)
        
        # Anonymize the input text
        anonymized_text, mappings = anonymizer.anonymize(text, mode)
        
        # Store mappings
        storage.add_mappings(mappings)
        
        response_data = {
            'anonymized_text': anonymized_text,
            'mappings_count': len(mappings)
        }
        
        # If LLM call requested
        if call_llm:
            # Call LLM with anonymized text
            llm_prompt = f"Please respond to the following message:\n\n{anonymized_text}"
            llm_response = llm_client.generate_response(llm_prompt)
            
            # Deanonymize the LLM response
            deanonymized_output = anonymizer.deanonymize(llm_response, mappings)
            
            response_data.update({
                'llm_response_anonymized': llm_response,
                'deanonymized_output': deanonymized_output
            })
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'llm_mode': 'mock' if llm_client.mock_mode else 'api',
        'mappings_file_exists': os.path.exists(MAPPINGS_FILE)
    })


if __name__ == '__main__':
    print("=" * 60)
    print("Starting PII-Anonymizer Web-CLI")
    print("=" * 60)
    print(f"Mappings file: {MAPPINGS_FILE}")
    print(f"LLM mode: {'MOCK' if llm_client.mock_mode else 'API'}")
    print(f"Encryption: {'Enabled' if ENCRYPTION_KEY else 'Disabled'}")
    print("=" * 60)
    print("Access the application at: http://localhost:5000")
    print("=" * 60)
    
    # Run Flask app
    app.run(
        debug=os.getenv('FLASK_DEBUG', 'True') == 'True',
        host='0.0.0.0',
        port=5000
    )
