from anonymizer import PIIAnonymizer

# Simple test for exact user scenario
anonymizer = PIIAnonymizer()

test_text = """
Account Number: 9876543210
Phone Number: 9876543210
"""

print("🔍 Testing Simple Key-Value Detection")
print("="*50)
print(f"📝 Original Text:\n{test_text}")

# Detect entities
detected = anonymizer.detect_pii(test_text)
print("\n🔍 Entity Detection Results:")
for entity_text, entity_type, start, end in detected:
    print(f"   {entity_type:<20} → {entity_text}")

# Pseudonymize
result, mappings = anonymizer.pseudonymize(test_text)
print(f"\n🏷️ Pseudonymization Result:\n{result}")

print(f"\n🔑 Mappings ({len(mappings)} total):")
for label, original in mappings.items():
    print(f"   {label:<20} → {original}")