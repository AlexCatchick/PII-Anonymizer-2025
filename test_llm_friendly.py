"""
Test LLM-friendly pseudonymization with semantic labels.
Demonstrates the new readable format for better LLM understanding.
"""

from anonymizer import PIIAnonymizer

def test_llm_friendly_anonymization():
    """Test the new LLM-friendly pseudonymization format."""
    
    anonymizer = PIIAnonymizer()
    
    # Test the exact example from the user
    test_input = """
Write a formal email to a company's HR department requesting an update on my job application status. Include the following details in the email:

Name: John Doe

Phone Number: +1 234 567 8901

Address: 123 Maple Street, Springfield, IL 62704

Account Number: 9876543210

Employee ID: EMP10234

Application Number: APP56789

The email should be polite, concise, and clearly formatted. It should include a greeting, purpose of the email, the applicant's details, and a courteous closing.
"""
    
    print("=== LLM-Friendly Anonymization Test ===\n")
    print("Original Input:")
    print(test_input)
    print("\n" + "="*60 + "\n")
    
    # Apply pseudonymization
    anonymized, mappings = anonymizer.pseudonymize(test_input)
    
    print("Anonymized Output with LLM-Friendly Labels:")
    print(anonymized)
    print("\n" + "-"*40 + "\n")
    
    print("Mapping Dictionary:")
    for placeholder, original in sorted(mappings.items()):
        print(f"   {placeholder} → {original}")
    
    print("\n" + "-"*40 + "\n")
    
    # Test deanonymization
    restored = anonymizer.deanonymize(anonymized, mappings)
    print("Deanonymization Test:")
    print("✅ Perfect match" if restored.strip() == test_input.strip() else "❌ Mismatch detected")
    
    print("\n" + "-"*40 + "\n")
    
    # Show detection statistics
    stats = anonymizer.get_detection_stats(test_input)
    print("Detection Statistics:")
    for entity_type, count in stats.items():
        print(f"   {entity_type}: {count}")
    
    print("\n=== Additional Test Cases ===\n")
    
    # Test additional complex examples
    complex_examples = [
        "Dr. Jane Smith called from jane.smith@hospital.com regarding patient ID MED123456.",
        "Transfer $1,500.00 to account 4532-1234-5678-9012 before March 15, 2024.",
        "Contact Emergency Services at 911 or visit https://emergency.gov for help.",
        "SSN 123-45-6789 belongs to address 456 Oak Street, Apartment 2B, Chicago, IL."
    ]
    
    for i, example in enumerate(complex_examples, 1):
        print(f"Example {i}:")
        print(f"Original: {example}")
        
        anonymized_ex, mappings_ex = anonymizer.pseudonymize(example)
        print(f"Anonymized: {anonymized_ex}")
        print()

if __name__ == "__main__":
    test_llm_friendly_anonymization()