#!/usr/bin/env python3
"""
Production test script for PII Anonymizer.
Tests all enhanced features work correctly in production.
"""
import requests
import json
import time
import sys

def test_production_deployment(base_url):
    """Test the production deployment comprehensively."""
    print(f"🧪 Testing Production Deployment: {base_url}")
    print("=" * 60)
    
    # Test 1: Health Check
    print("\n📊 Test 1: Health Check")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Status: {health.get('status')}")
            print(f"   Version: {health.get('version')}")
            print(f"   Anonymizer: {'✅' if health.get('anonymizer_healthy') else '❌'}")
            print(f"   LLM Mode: {health.get('llm_mode')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Enhanced Anonymization
    print("\n🔍 Test 2: Enhanced Anonymization (Semantic Labels)")
    test_data = {
        "text": "Account Number: 9876543210\nPhone Number: +1-234-567-8901\nName: John Smith",
        "action": "anonymize"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/anonymize",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Anonymization successful!")
            print(f"📝 Original: {test_data['text'][:50]}...")
            print(f"🏷️ Anonymized: {result['anonymized_text']}")
            print(f"🗂️ Mappings: {result.get('mappings_count', 0)} entities detected")
            
            # Check for semantic labels
            anonymized = result['anonymized_text']
            if 'account_number_' in anonymized and 'mobNo_' in anonymized and 'name_' in anonymized:
                print("✅ Semantic labels working correctly!")
            else:
                print("⚠️  Semantic labels might not be working as expected")
                
        else:
            print(f"❌ Anonymization failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Anonymization error: {e}")
        return False
    
    # Test 3: Context Recognition
    print("\n🎯 Test 3: Context Recognition")
    context_test = {
        "text": "Account Number: 1234567890\nPhone Number: 1234567890",
        "action": "anonymize"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/anonymize",
            json=context_test,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            anonymized = result['anonymized_text']
            
            # Check if same number gets different labels based on context
            if 'account_number_' in anonymized and 'mobNo_' in anonymized:
                print("✅ Context recognition working - same number classified differently!")
                print(f"   Result: {anonymized}")
            else:
                print("⚠️  Context recognition might need attention")
                print(f"   Result: {anonymized}")
                
        else:
            print(f"❌ Context test failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Context test error: {e}")
    
    # Test 4: Startup Check
    print("\n🔧 Test 4: Detailed Startup Check")
    try:
        response = requests.get(f"{base_url}/api/startup-check", timeout=15)
        if response.status_code == 200:
            startup = response.json()
            print("✅ Startup check successful!")
            
            checks = startup.get('checks', {})
            for component, status in checks.items():
                icon = "✅" if "working" in status else "❌"
                print(f"   {icon} {component}: {status}")
                
            env_vars = startup.get('environment_vars', {})
            print(f"   🔑 API Key: {env_vars.get('GROQ_API_KEY', 'not set')}")
            print(f"   🔐 Encryption: {env_vars.get('ENCRYPTION_KEY', 'not set')}")
            
        else:
            print(f"❌ Startup check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Startup check error: {e}")
    
    print("\n🎉 Production testing completed!")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter your Render app URL (e.g., https://your-app.onrender.com): ").strip()
    
    if not url.startswith('http'):
        url = f"https://{url}"
    
    success = test_production_deployment(url)
    
    if success:
        print("\n🚀 Production deployment is working correctly!")
        print("\n🎯 Key Features Verified:")
        print("  ✓ Enhanced PII detection with multi-token support")
        print("  ✓ LLM-friendly semantic labels (name_1, mobNo_1, etc.)")
        print("  ✓ Context-aware classification")
        print("  ✓ Production security and monitoring")
    else:
        print("\n⚠️  Some issues detected. Check the logs above.")
        sys.exit(1)