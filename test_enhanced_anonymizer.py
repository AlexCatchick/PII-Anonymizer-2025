"""
Test script to demonstrate enhanced PII detection and anonymization capabilities.
Shows how the improved anonymizer handles complex entities with internal tokens.
"""

from anonymizer import PIIAnonymizer

def test_enhanced_detection():
    """Test enhanced PII detection with complex entities."""
    
    # Initialize the enhanced anonymizer
    anonymizer = PIIAnonymizer()
    
    # Test text with complex PII entities
    test_text = """
    Patient Information:
    Dr. John Smith visited the clinic at 123 Main Street, Apt 4B, New York.
    Contact: john.smith@hospital.com, (555) 123-4567
    Medical ID: MRN-123456789
    SSN: 123-45-6789
    Credit Card: 4532 1234 5678 9012
    
    Organization: Memorial Hospital Inc.
    Website: https://hospital.com/patient-portal
    Meeting Date: March 15, 2024
    Amount Due: $1,250.00
    
    Emergency Contact: Ms. Jane Doe at 456 Oak Avenue, Suite 102
    Phone: +1-555-987-6543
    Email: jane.doe@email.com
    """
    
    print("=== Enhanced PII Detection Test ===\n")
    print("Original Text:")
    print(test_text)
    print("\n" + "="*60 + "\n")
    
    # Preview detection without anonymizing
    print("1. Detection Preview:")
    preview = anonymizer.preview_detection(test_text)
    for entity_type, examples in preview.items():
        print(f"   {entity_type}: {examples}")
    
    print("\n" + "-"*40 + "\n")
    
    # Get detection statistics
    print("2. Detection Statistics:")
    stats = anonymizer.get_detection_stats(test_text)
    for entity_type, count in stats.items():
        print(f"   {entity_type}: {count} found")
    
    print("\n" + "-"*40 + "\n")
    
    # Test enhanced pseudonymization
    print("3. Enhanced Pseudonymization:")
    pseudonymized, pseudo_mappings = anonymizer.pseudonymize(test_text)
    print(pseudonymized)
    print("\nMappings:")
    for placeholder, original in pseudo_mappings.items():
        print(f"   {placeholder} -> {original}")
    
    print("\n" + "-"*40 + "\n")
    
    # Test enhanced masking
    print("4. Enhanced Masking:")
    anonymizer_mask = PIIAnonymizer()  # Fresh instance
    masked, mask_mappings = anonymizer_mask.mask(test_text)
    print(masked)
    
    print("\n" + "-"*40 + "\n")
    
    # Test enhanced replacement
    print("5. Enhanced Replacement:")
    anonymizer_replace = PIIAnonymizer()  # Fresh instance
    replaced, replace_mappings = anonymizer_replace.replace(test_text)
    print(replaced)
    
    print("\n" + "-"*40 + "\n")
    
    # Test deanonymization
    print("6. Deanonymization Test:")
    restored = anonymizer.deanonymize(pseudonymized, pseudo_mappings)
    print("Restored text matches original:", restored.strip() == test_text.strip())
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_enhanced_detection()