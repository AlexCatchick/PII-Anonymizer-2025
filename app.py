"""
Flask application for PII-Anonymizer Web-CLI.
Main entry point for the web application.
Uses Hybrid Smart Extraction (Option B) for optimal performance on Render free tier.
"""
import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS
from anonymizer import PIIAnonymizer
from storage import MappingStorage
from llm_client import GroqClient
from hybrid_ocr_extractor import HybridOCRExtractor
from ocr_extractor import ContextAwarePIIExtractor

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
    print(f"Using temporary key for this session. For production, set ENCRYPTION_KEY environment variable!")
    print(f"Generated key: {ENCRYPTION_KEY.decode()}")

MAPPINGS_FILE = os.getenv('MAPPINGS_FILE', 'mappings.enc')
MAPPING_TTL = int(os.getenv('MAPPING_TTL', '1800'))  # Default: 30 min

# Initialize components
print("Initializing PII Anonymizer...")
anonymizer = PIIAnonymizer()
print("PII Anonymizer initialized")

print("Initializing storage...")
storage = MappingStorage(MAPPINGS_FILE, ENCRYPTION_KEY, ttl_seconds=MAPPING_TTL)
print(f"Storage initialized (TTL: {storage._format_ttl(MAPPING_TTL)}, auto-cleanup: active)")

# Initialize LLM client
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')

if GROQ_API_KEY:
    print(f"Running in API mode with Groq")
    print(f"   Model: {GROQ_MODEL}")
    print(f"   API Key: {GROQ_API_KEY[:20]}...{GROQ_API_KEY[-4:]}")
    llm_client = GroqClient(GROQ_API_KEY, GROQ_MODEL)
else:
    print("No GROQ_API_KEY found - running in mock mode")
    print("   Set GROQ_API_KEY environment variable to enable LLM features")
    llm_client = GroqClient(None, GROQ_MODEL)  # Will use mock mode

# Initialize Hybrid OCR Extractor (Option B: Smart Extraction)
print("\nInitializing Hybrid OCR Extractor (Option B - Optimized for Render)...")
print("   Strategy: Pattern-based extraction + OpenCV detection + EasyOCR fallback")
print("   Memory footprint: ~150-200MB (fits Render 512MB free tier)")
print("   EasyOCR will be lazy-loaded only when needed")

ocr_extractor = HybridOCRExtractor(languages=['en'])
print(f"   Capabilities: {ocr_extractor.get_capabilities()}")

# Initialize Context-Aware PII Extractor (uses LLM for context filtering)
print("\nInitializing Context-Aware PII Extractor...")
context_extractor = ContextAwarePIIExtractor(llm_client)
print("   Context-Aware PII Extractor ready")


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
        context_prompt = data.get('context_prompt', '').strip()
        
        print(f"Processing text (length: {len(text)}, mode: {mode})")
        if context_prompt:
            print(f"Context prompt provided: {context_prompt[:100]}...")
        
        # Use the appropriate anonymization method based on mode
        if mode == 'mask':
            anonymized_text, mappings = anonymizer.mask(text)
            print(f"Using mask mode (irreversible)")
        elif mode == 'replace':
            anonymized_text, mappings = anonymizer.replace(text)
            print(f"Using replace mode (irreversible)")
        else:  # Default to pseudonymize
            anonymized_text, mappings = anonymizer.pseudonymize(text)
            print(f"Using pseudonymize mode (reversible)")
        
        # Store mappings for later deanonymization (only for pseudonymize mode)
        if mappings:
            storage.add_mappings(mappings)
            print(f"Stored {len(mappings)} entity mappings")
        else:
            print(f"No mappings stored - {mode} mode is irreversible")
        
        response_data = {
            'anonymized_text': anonymized_text,
            'entity_mappings': mappings,  # Include mappings in response
            'mappings_count': len(mappings),
            'mode': mode,
            'reversible': len(mappings) > 0
        }
        
        if call_llm and llm_client:
            print("Calling LLM with anonymized text...")
            # Build LLM prompt including context prompt if provided
            if context_prompt:
                llm_prompt = (f"User's request/context: {context_prompt}\n\n"
                              f"Below is the relevant information (with PII anonymized):\n\n{anonymized_text}\n\n"
                              f"Please respond to the user's request above using the anonymized information provided.")
            else:
                llm_prompt = f"Please respond to the following message:\n\n{anonymized_text}"
            llm_response = llm_client.generate_response(llm_prompt)
            print(f"LLM response received (length: {len(llm_response)})")
            
            # Deanonymize the LLM response (only works if mappings exist)
            if mappings:
                deanonymized_output = anonymizer.deanonymize(llm_response, mappings)
            else:
                deanonymized_output = llm_response  # Can't deanonymize mask/replace
                print(f"LLM response cannot be deanonymized ({mode} mode is irreversible)")
            
            response_data.update({
                'llm_response': llm_response,  # Keep original name for compatibility
                'llm_response_anonymized': llm_response,
                'deanonymized_output': deanonymized_output
            })
        
        return jsonify(response_data)
    
    except Exception as e:
        print(f"Error in anonymize_text: {str(e)}")
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
    """Clear all stored mappings immediately (secure wipe)."""
    try:
        storage.clear_mappings()
        return jsonify({'message': 'Mappings cleared and securely wiped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/storage-info', methods=['GET'])
def storage_info():
    """Return storage health and TTL information."""
    try:
        info = storage.get_storage_info()
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/set-ttl', methods=['POST'])
def set_mapping_ttl():
    """
    Update the mapping TTL (time-to-live).
    
    Request JSON:
        { "ttl_seconds": 900 }   // e.g. 15 minutes
    
    Accepted range: 60 – 86400 seconds (1 minute – 24 hours)
    """
    try:
        data = request.get_json()
        if not data or 'ttl_seconds' not in data:
            return jsonify({'error': 'Provide ttl_seconds (60-86400)'}), 400
        
        ttl = int(data['ttl_seconds'])
        storage.set_ttl_seconds(ttl)
        
        return jsonify({
            'message': f'TTL updated to {storage._format_ttl(storage.ttl_seconds)}',
            'ttl_seconds': storage.ttl_seconds
        })
    except (ValueError, TypeError):
        return jsonify({'error': 'ttl_seconds must be an integer'}), 400
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
            'version': '2.1.0',
            'anonymizer_healthy': anonymizer_healthy,
            'llm_mode': 'mock' if (not llm_client or llm_client.mock_mode) else 'api',
            'llm_available': GROQ_API_KEY is not None,
            'mappings_file_exists': os.path.exists(MAPPINGS_FILE),
            'storage': storage.get_storage_info(),
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


@app.route('/api/ocr/capabilities', methods=['GET'])
def get_ocr_capabilities():
    """Get available OCR and file processing capabilities."""
    return jsonify({
        'capabilities': ocr_extractor.get_capabilities(),
        'supported_formats': {
            'images': list(HybridOCRExtractor.SUPPORTED_IMAGE_FORMATS),
            'text': list(HybridOCRExtractor.SUPPORTED_TEXT_FORMATS),
            'pdf': list(HybridOCRExtractor.SUPPORTED_PDF_FORMATS)
        }
    })


@app.route('/api/ocr/extract', methods=['POST'])
def extract_text_from_file():
    """
    Extract text from uploaded file (image, PDF, or text file).
    
    Request: multipart/form-data with 'file' field
    OR JSON with 'base64_data' and 'filename' fields
    
    Response JSON:
        {
            "success": true/false,
            "text": "extracted text",
            "source_type": "image|pdf|text_file",
            "pages_processed": 1,
            "ocr_applied": true/false,
            "metadata": {...}
        }
    """
    try:
        # Handle file upload or base64 data
        if request.content_type and 'multipart/form-data' in request.content_type:
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            file_bytes = file.read()
            file_name = file.filename
            print(f"[OCR DEBUG] Received file: {file_name}, size: {len(file_bytes)} bytes")
        else:
            data = request.get_json()
            if not data or 'base64_data' not in data:
                return jsonify({'error': 'No file data provided'}), 400
            
            import base64
            file_bytes = base64.b64decode(data['base64_data'])
            file_name = data.get('filename', 'unknown')
            print(f"[OCR DEBUG] Received base64 file: {file_name}, size: {len(file_bytes)} bytes")
        
        print(f"[OCR DEBUG] Calling extract_text...")
        # Extract text
        result = ocr_extractor.extract_text(
            file_bytes=file_bytes,
            file_name=file_name
        )
        print(f"[OCR DEBUG] Result success: {result.get('success')}, text length: {len(result.get('text', ''))}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in extract_text_from_file: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Extraction failed: {str(e)}'}), 500


@app.route('/api/ocr/process', methods=['POST'])
def process_file_with_context():
    """
    Full pipeline: Extract text from file and identify context-relevant PII.
    
    Request: multipart/form-data with:
        - 'file': The file to process
        - 'context_prompt': User's context/query for PII extraction
        - 'pii_categories' (optional): Comma-separated PII categories to focus on
        - 'skip_filtering' (optional): 'true' to skip context filtering
    
    OR JSON with:
        - 'base64_data': Base64 encoded file
        - 'filename': Original filename
        - 'context_prompt': User's context/query
        - 'pii_categories' (optional): Array of PII categories
        - 'skip_filtering' (optional): boolean
    
    Response JSON:
        {
            "success": true/false,
            "extraction": {...},
            "pii_analysis": {
                "relevant_pii": [...],
                "excluded_pii": [...],
                "summary": "..."
            },
            "text_for_pseudonymization": "..."
        }
    """
    try:
        # Parse request
        if request.content_type and 'multipart/form-data' in request.content_type:
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            file_bytes = file.read()
            file_name = file.filename
            
            context_prompt = request.form.get('context_prompt', '')
            pii_categories = request.form.get('pii_categories', '')
            pii_categories = [c.strip() for c in pii_categories.split(',')] if pii_categories else None
            skip_filtering = request.form.get('skip_filtering', 'false').lower() == 'true'
        else:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            import base64
            if 'base64_data' in data:
                file_bytes = base64.b64decode(data['base64_data'])
                file_name = data.get('filename', 'unknown')
            else:
                return jsonify({'error': 'No file data provided'}), 400
            
            context_prompt = data.get('context_prompt', '')
            pii_categories = data.get('pii_categories')
            skip_filtering = data.get('skip_filtering', False)
        
        if not context_prompt and not skip_filtering:
            return jsonify({'error': 'context_prompt is required unless skip_filtering is true'}), 400
        
        # Step 1: Extract text from file
        extraction = ocr_extractor.extract_text(
            file_bytes=file_bytes,
            file_name=file_name
        )
        
        if not extraction.get('success', False):
            return jsonify({
                'success': False,
                'extraction': extraction,
                'error': extraction.get('error', 'Text extraction failed')
            })
        
        extracted_text = extraction.get('text', '')
        
        # Step 2: Context-aware PII analysis
        pii_analysis = None
        text_for_pseudonymization = extracted_text
        relevant_pii_list = None
        
        if context_prompt and not skip_filtering:
            print(f"[/api/ocr/process] Running hybrid context-aware PII extraction...")
            print(f"   Context prompt: {context_prompt[:100]}...")
            print(f"   Text length: {len(extracted_text)} chars")
            
            try:
                # Step 2a: Detect ALL PIIs using the thorough regex+spaCy anonymizer
                detected_piis = anonymizer.detect_pii(extracted_text)
                print(f"   Regex+spaCy detected: {len(detected_piis)} PII entities")
                
                # Step 2b: Use LLM to filter which PIIs are relevant to context
                pii_result = context_extractor.extract_contextual_pii(
                    text=extracted_text,
                    context_prompt=context_prompt,
                    pii_categories=pii_categories,
                    detected_piis=detected_piis
                )
                
                if pii_result.get('success', False):
                    relevant_pii_list = pii_result.get('relevant_pii', [])
                    pii_analysis = {
                        'relevant_pii': relevant_pii_list,
                        'excluded_pii': pii_result.get('excluded_pii', []),
                        'summary': pii_result.get('summary', '')
                    }
                    
                    # Generate selectively anonymized preview
                    if relevant_pii_list:
                        preview_text, _ = anonymizer.selective_pseudonymize(
                            extracted_text, relevant_pii_list, mode='pseudonymize'
                        )
                        text_for_pseudonymization = preview_text
                    
                    print(f"   PII analysis complete: {len(relevant_pii_list)} relevant, "
                          f"{len(pii_result.get('excluded_pii', []))} excluded")
                else:
                    error_msg = pii_result.get('error', 'Unknown error')
                    print(f"   PII extraction failed: {error_msg}")
                    pii_analysis = {
                        'relevant_pii': [],
                        'excluded_pii': [],
                        'summary': f"Context filtering failed: {error_msg}"
                    }
            except Exception as e:
                print(f"   Context extraction error: {str(e)}")
                pii_analysis = {
                    'relevant_pii': [],
                    'excluded_pii': [],
                    'summary': f"Context filtering error: {str(e)}"
                }
        else:
            if skip_filtering:
                print("[/api/ocr/process] Context filtering skipped by user")
                pii_analysis = {
                    'relevant_pii': [],
                    'excluded_pii': [],
                    'summary': 'Context filtering was skipped. All PII will be anonymized.'
                }
        
        result = {
            'success': True,
            'extraction': extraction,
            'extracted_text': extracted_text,
            'text_for_pseudonymization': text_for_pseudonymization,
            'context_prompt': context_prompt
        }
        
        if pii_analysis:
            result['pii_analysis'] = pii_analysis
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in process_file_with_context: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500


@app.route('/api/ocr/anonymize', methods=['POST'])
def ocr_and_anonymize():
    """
    Complete pipeline: Extract text, identify context-relevant PII, and pseudonymize.
    
    Request: multipart/form-data with:
        - 'file': The file to process
        - 'context_prompt': User's context/query for PII extraction
        - 'mode': 'pseudonymize' | 'mask' | 'replace' (default: pseudonymize)
        - 'call_llm': 'true' to get LLM response (default: false)
        - 'pii_categories' (optional): Comma-separated PII categories
        - 'skip_filtering' (optional): 'true' to skip context filtering
    
    Response JSON: Same as /api/anonymize endpoint plus extraction metadata
    """
    try:
        # Parse request
        if request.content_type and 'multipart/form-data' in request.content_type:
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            file_bytes = file.read()
            file_name = file.filename
            
            context_prompt = request.form.get('context_prompt', '')
            mode = request.form.get('mode', 'pseudonymize')
            call_llm = request.form.get('call_llm', 'false').lower() == 'true'
            pii_categories = request.form.get('pii_categories', '')
            pii_categories = [c.strip() for c in pii_categories.split(',')] if pii_categories else None
            skip_filtering = request.form.get('skip_filtering', 'false').lower() == 'true'
        else:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            import base64
            if 'base64_data' in data:
                file_bytes = base64.b64decode(data['base64_data'])
                file_name = data.get('filename', 'unknown')
            else:
                return jsonify({'error': 'No file data provided'}), 400
            
            context_prompt = data.get('context_prompt', '')
            mode = data.get('mode', 'pseudonymize')
            call_llm = data.get('call_llm', False)
            pii_categories = data.get('pii_categories')
            skip_filtering = data.get('skip_filtering', False)
        
        # Step 1: Extract text from file
        extraction_result = ocr_extractor.extract_text(
            file_bytes=file_bytes,
            file_name=file_name
        )
        
        if not extraction_result.get('success', False):
            return jsonify({
                'error': extraction_result.get('error', 'File extraction failed'),
                'extraction': extraction_result
            }), 400
        
        text_to_anonymize = extraction_result.get('text', '')
        
        # Step 2: Anonymize ALL PII in the extracted text (full anonymization always)
        # Context prompt is only for PII identification/extraction, not for filtering anonymization
        print(f"Anonymizing all PII in extracted text ({len(text_to_anonymize)} chars, mode: {mode})")
        if mode == 'mask':
            anonymized_text, mappings = anonymizer.mask(text_to_anonymize)
        elif mode == 'replace':
            anonymized_text, mappings = anonymizer.replace(text_to_anonymize)
        else:
            anonymized_text, mappings = anonymizer.pseudonymize(text_to_anonymize)
        
        # Store mappings for later deanonymization
        if mappings:
            storage.add_mappings(mappings)
        
        response_data = {
            'success': True,
            'original_text': text_to_anonymize,
            'anonymized_text': anonymized_text,
            'entity_mappings': mappings,
            'mappings_count': len(mappings),
            'mode': mode,
            'reversible': len(mappings) > 0,
            'extraction_metadata': {
                'source_type': extraction_result.get('source_type'),
                'pages_processed': extraction_result.get('pages_processed'),
                'ocr_applied': extraction_result.get('ocr_applied'),
                'file_metadata': extraction_result.get('metadata', {})
            }
        }
        
        # Step 3: Call LLM if requested
        if call_llm and llm_client:
            # Build LLM prompt including context prompt if provided
            if context_prompt:
                llm_prompt = (f"User's request/context: {context_prompt}\n\n"
                              f"Below is the relevant information (with PII anonymized):\n\n{anonymized_text}\n\n"
                              f"Please respond to the user's request above using the anonymized information provided.")
            else:
                llm_prompt = f"Please respond to the following message:\n\n{anonymized_text}"
            
            llm_response = llm_client.generate_response(llm_prompt)
            
            if mappings:
                deanonymized_output = anonymizer.deanonymize(llm_response, mappings)
            else:
                deanonymized_output = llm_response
            
            response_data.update({
                'llm_response': llm_response,
                'llm_response_anonymized': llm_response,
                'deanonymized_output': deanonymized_output
            })
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in ocr_and_anonymize: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'OCR and anonymization failed: {str(e)}'}), 500


if __name__ == '__main__':
    # Development server configuration
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    
    print(f"Starting Flask application...")
    print(f"   Debug mode: {debug_mode}")
    print(f"   Port: {port}")
    print(f"   Host: 0.0.0.0")
    
    app.run(
        debug=debug_mode,
        host='0.0.0.0',
        port=port
    )
