import requests
import json

# Test the web interface with the exact user scenario
test_data = {
    "text": "Account Number: 9876543210\nPhone Number: 9876543210",
    "action": "anonymize"
}

try:
    response = requests.post("http://127.0.0.1:5000/api/anonymize", 
                           json=test_data,
                           headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        result = response.json()
        print("🎉 Web API Test Results:")
        print("="*40)
        print(f"📝 Original: {test_data['text']}")
        print(f"🏷️ Anonymized: {result['anonymized_text']}")
        print(f"🔑 Mappings: {result['entity_mappings']}")
        print(f"✅ Status: Success!")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"❌ Connection Error: {e}")
    print("Make sure Flask server is running on http://127.0.0.1:5000")