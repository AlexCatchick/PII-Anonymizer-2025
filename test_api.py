"""
Test the Flask API directly to verify the new LLM-friendly format is working.
"""

import requests
import json

def test_api():
    """Test the Flask API with the updated anonymizer."""
    
    url = "http://127.0.0.1:5000/api/anonymize"
    
    # Test data from the user's example
    test_data = {
        "text": """Write a formal email to a company's HR department requesting an update on my job application status. Include the following details in the email:

Name: John Doe

Phone Number: +1 234 567 8901

Address: 123 Maple Street, Springfield, IL 62704

Account Number: 9876543210

Employee ID: EMP10234

Application Number: APP56789

The email should be polite, concise, and clearly formatted. It should include a greeting, purpose of the email, the applicant's details, and a courteous closing.""",
        "mode": "pseudonymize",
        "call_llm": False
    }
    
    try:
        print("🧪 Testing Flask API with Enhanced Anonymizer")
        print("=" * 50)
        
        response = requests.post(url, json=test_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API Response successful!")
            print(f"📊 Mappings count: {result.get('mappings_count', 0)}")
            print("\n🔄 Anonymized text:")
            print(result.get('anonymized_text', 'No text returned'))
            
            # Check if it's using the new format
            anonymized = result.get('anonymized_text', '')
            if 'name_' in anonymized or 'mobNo_' in anonymized or 'email_' in anonymized:
                print("\n✅ SUCCESS: Using new LLM-friendly format!")
            elif 'PII_' in anonymized:
                print("\n❌ ISSUE: Still using old PII_ format")
            else:
                print("\n⚠️ UNCLEAR: Format unclear, check manually")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Is the Flask server running?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api()