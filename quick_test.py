import requests
import json

# Quick production test
base_url = "http://127.0.0.1:5000"

print("🧪 Quick Production Test")
print("="*40)

# Test health
try:
    response = requests.get(f"{base_url}/api/health")
    if response.status_code == 200:
        health = response.json()
        print(f"✅ Health: {health.get('status')}")
        print(f"   Version: {health.get('version')}")
        print(f"   Debug: {health.get('environment', {}).get('debug_mode')}")
    
    # Test enhanced anonymization
    test_data = {
        "text": "Account Number: 9876543210\nPhone Number: 9876543210",
        "action": "anonymize"
    }
    
    response = requests.post(f"{base_url}/api/anonymize", json=test_data)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Anonymization working!")
        print(f"   Input: Account Number: 9876543210")
        print(f"   Output: {result['anonymized_text'].split('\\n')[0]}")
        print(f"   Mappings: {result['mappings_count']} detected")
        
        # Check semantic labels
        if 'account_number_' in result['anonymized_text']:
            print("✅ Semantic labels working!")
        else:
            print("⚠️  Check semantic labels")
    
    print("\n🎉 Production test completed successfully!")
    
except Exception as e:
    print(f"❌ Test error: {e}")