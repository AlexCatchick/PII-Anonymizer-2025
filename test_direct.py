"""
Direct test of the anonymizer module to verify the pseudonymization format.
This bypasses the Flask API to test the core functionality.
"""

import sys
import os

# Add current directory to path to import anonymizer
sys.path.append(os.getcwd())

from anonymizer import PIIAnonymizer

def test_direct_anonymizer():
    """Test the anonymizer directly to verify the new format."""
    
    print("🔬 Direct Anonymizer Test")
    print("=" * 40)
    
    # Initialize anonymizer
    anonymizer = PIIAnonymizer()
    
    # Test text from user's example
    test_text = """Write a formal email to a company's HR department requesting an update on my job application status. Include the following details in the email:

Name: John Doe

Phone Number: +1 234 567 8901

Address: 123 Maple Street, Springfield, IL 62704

Account Number: 9876543210

Employee ID: EMP10234

Application Number: APP56789"""

    print("📝 Input text:")
    print(test_text[:200] + "..." if len(test_text) > 200 else test_text)
    
    print("\n🔄 Testing pseudonymization:")
    anonymized, mappings = anonymizer.pseudonymize(test_text)
    
    print("\n📤 Anonymized result:")
    print(anonymized)
    
    print(f"\n🔑 Mappings ({len(mappings)} total):")
    for key, value in list(mappings.items())[:8]:  # Show first 8
        print(f"   {key} → {value}")
    if len(mappings) > 8:
        print(f"   ... and {len(mappings) - 8} more")
    
    # Check format
    print("\n🎯 Format Analysis:")
    if any(key.startswith(('name_', 'mobNo_', 'email_', 'physical_address_', 'location_')) for key in mappings.keys()):
        print("   ✅ SUCCESS: Using new LLM-friendly format!")
        print("   🏷️  Found semantic labels like 'name_X', 'mobNo_X', etc.")
    elif any(key.startswith('PII_') for key in mappings.keys()):
        print("   ❌ ISSUE: Still using old 'PII_' format")
    else:
        print("   ⚠️  UNCLEAR: No clear pattern detected")
    
    # Show specific examples
    semantic_labels = [k for k in mappings.keys() if '_' in k and not k.startswith('PII_')]
    if semantic_labels:
        print(f"\n✨ Semantic labels found: {semantic_labels[:5]}")

if __name__ == "__main__":
    test_direct_anonymizer()