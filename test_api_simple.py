"""
Simple curl-equivalent test for the API endpoint using urllib.
"""

import urllib.request
import urllib.parse
import json

def test_api_simple():
    """Test API with urllib to avoid dependency issues."""
    
    url = "http://127.0.0.1:5000/api/anonymize"
    
    data = {
        "text": "Name: John Doe, Phone: +1 234 567 8901, Email: john@example.com",
        "mode": "pseudonymize",
        "call_llm": False
    }
    
    # Convert to JSON
    json_data = json.dumps(data).encode('utf-8')
    
    # Create request
    req = urllib.request.Request(url, data=json_data, 
                                headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            print("API Test Results:")
            print("================")
            print(f"Status: {response.getcode()}")
            print(f"Mappings count: {result.get('mappings_count', 0)}")
            print("\nAnonymized text:")
            print(result.get('anonymized_text', 'No text'))
            
            # Check format
            text = result.get('anonymized_text', '')
            if 'name_' in text or 'mobNo_' in text:
                print("\n✅ SUCCESS: API is using new LLM-friendly format!")
            elif 'PII_' in text:
                print("\n❌ ISSUE: API still using old format")
            else:
                print("\n❓ UNCLEAR: Check the output above")
                
    except Exception as e:
        print(f"Error testing API: {e}")

if __name__ == "__main__":
    test_api_simple()