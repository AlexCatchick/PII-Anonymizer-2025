"""
Test the improved context recognition and entity detection.
"""

from anonymizer import PIIAnonymizer

def test_improved_context():
    """Test improved context recognition for key-value pairs."""
    
    print("🔍 Testing Improved Context Recognition")
    print("=" * 50)
    
    # Test the exact user input
    test_text = """Write a formal email to a company's HR department requesting an update on my job application status. Include the following details in the email:

Name: John Doe

Phone Number: +1 234 567 8901

Address: 123 Maple Street, Springfield, IL 62704

Account Number: 9876543210

Employee ID: 10234

Application Number: 56789

The email should be polite, concise, and clearly formatted. It should include a greeting, purpose of the email, the applicant's details, and a courteous closing."""

    anonymizer = PIIAnonymizer()
    
    print("📝 Original Text:")
    print(test_text)
    
    print("\n🔍 Entity Detection Analysis:")
    entities = anonymizer.detect_pii(test_text)
    for entity_text, entity_type, start, end in entities:
        print(f"   {entity_type:20} → {entity_text}")
    
    print(f"\n📊 Detection Statistics:")
    stats = anonymizer.get_detection_stats(test_text)
    for entity_type, count in stats.items():
        print(f"   {entity_type:20}: {count}")
    
    print(f"\n🏷️ Pseudonymization Result:")
    anonymized, mappings = anonymizer.pseudonymize(test_text)
    print(anonymized)
    
    print(f"\n🔑 Mappings ({len(mappings)} total):")
    for placeholder, original in mappings.items():
        print(f"   {placeholder:20} → {original}")
    
    print(f"\n✅ Expected vs Actual:")
    expected_patterns = [
        ("John Doe", "name_1"),
        ("+1 234 567 8901", "mobNo_1"), 
        ("9876543210", "account_number_1"),
        ("10234", "employee_id_1"),
        ("56789", "application_number_1")
    ]
    
    for original, expected_label in expected_patterns:
        found_label = None
        for placeholder, mapped_original in mappings.items():
            if mapped_original == original:
                found_label = placeholder
                break
        
        status = "✅" if found_label and expected_label.split('_')[0] in found_label else "❌"
        print(f"   {status} {original:20} → {found_label or 'NOT FOUND'}")
    
    # Test key issues
    print(f"\n🎯 Key Issue Analysis:")
    issues = []
    
    # Check if field labels are being detected as names
    field_labels_as_names = [item for item in mappings.items() 
                           if 'name_' in item[0] and item[1].lower() in ['phone number', 'account number', 'application number']]
    if field_labels_as_names:
        issues.append("❌ Field labels detected as person names")
        for placeholder, original in field_labels_as_names:
            print(f"      {placeholder} → {original}")
    else:
        print("   ✅ No field labels incorrectly detected as names")
    
    # Check if account numbers are being detected as phone numbers
    account_as_phone = [item for item in mappings.items() 
                       if 'mobNo_' in item[0] and len(re.findall(r'\d', item[1])) > 10 and '@' not in item[1]]
    if account_as_phone:
        issues.append("❌ Account numbers detected as phone numbers")
        for placeholder, original in account_as_phone:
            print(f"      {placeholder} → {original}")
    else:
        print("   ✅ No account numbers incorrectly detected as phone numbers")
    
    print(f"\n🏆 Overall Result:")
    if not issues:
        print("   🎉 EXCELLENT! All context recognition issues resolved!")
    else:
        print(f"   ⚠️  Found {len(issues)} issues that need attention")

if __name__ == "__main__":
    import re
    test_improved_context()