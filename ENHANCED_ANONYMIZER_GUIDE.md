# Enhanced PII Anonymizer Documentation

## Overview

The enhanced PII anonymizer has been significantly improved to handle complex entities with internal tokens, spaces, punctuation, and line breaks. It now provides industry-standard labeling and better detection capabilities for production-level applications.

## Key Improvements

### 1. Enhanced Entity Detection

#### Multi-Token Entity Support
- **Complex Names**: Handles titles and multi-part names (e.g., "Dr. John Smith", "Ms. Jane Doe")
- **Multi-Word Organizations**: Detects organization names with legal suffixes (e.g., "Memorial Hospital Inc.")
- **Complex Addresses**: Recognizes full address formats with apartment/suite numbers
- **Structured Dates**: Supports various date formats with punctuation and spacing

#### Advanced Pattern Matching
- **Custom spaCy Patterns**: Configured Matcher for complex entity recognition
- **Enhanced Regex**: Improved patterns for emails, phone numbers, credit cards, SSNs
- **New Entity Types**: Added support for passport numbers, driver licenses, bank accounts, IP addresses, URLs, medical IDs

#### Overlap Detection
- **Smart Deduplication**: Prevents duplicate detection of the same entity by multiple methods
- **Percentage-Based Overlap**: Uses sophisticated logic to handle partial overlaps
- **Entity Validation**: Filters out false positives with type-specific validation

### 2. Industry-Standard Labeling

#### Human-Friendly Labels
```python
HUMAN_LABELS = {
    'PERSON_NAME': 'Person Name',
    'LOCATION': 'Location',
    'ORGANIZATION': 'Organization',
    'DATE_TIME': 'Date/Time',
    'EMAIL': 'Email Address',
    'PHONE': 'Phone Number',
    'CREDIT_CARD': 'Credit Card',
    'SSN': 'Social Security Number',
    # ... and more
}
```

#### Entity Type Mapping
- Maps spaCy NER labels to descriptive, production-ready labels
- Provides consistent naming across different detection methods
- Follows industry standards for data privacy and compliance

### 3. Enhanced Anonymization Modes

#### Improved Pseudonymization
- **Context-Aware Labels**: Uses entity-specific numbering (e.g., `[Person_1]`, `[Email_1@example.com]`)
- **Type-Specific Formatting**: Different formats for different entity types
- **Reversible Mapping**: Maintains mapping for deanonymization

Examples:
```
Original: "Dr. John Smith, john.smith@hospital.com"
Pseudonymized: "Dr. [Person_1], [email_1@example.com]"
```

#### Enhanced Masking
- **Intelligent Partial Reveal**: Shows relevant parts while hiding sensitive information
- **Structure Preservation**: Maintains format for readability
- **Type-Specific Logic**: Different masking strategies per entity type

Examples:
```
Email: john.smith@hospital.com → jo********@hospital.com
Credit Card: 4532 1234 5678 9012 → 4532-XXXX-XXXX-9012
Phone: (555) 123-4567 → (555) 123-X567
SSN: 123-45-6789 → 123-XX-XXXX
```

#### Smart Replacement
- **Descriptive Labels**: Uses human-friendly entity type names
- **Consistent Formatting**: Standardized bracket notation
- **Unique Tracking**: Maintains mappings for reversal when needed

### 4. New Utility Methods

#### Detection Preview
```python
preview = anonymizer.preview_detection(text)
# Returns: {'Person Name': ['John Smith', 'Jane Doe'], ...}
```

#### Detection Statistics
```python
stats = anonymizer.get_detection_stats(text)
# Returns: {'Person Name': 2, 'Email Address': 1, ...}
```

#### Entity Validation
- Validates detected entities to reduce false positives
- Type-specific validation rules
- Filters out common misclassifications

## Supported Entity Types

### Personal Information
- **Person Names**: Including titles, first/last names
- **Email Addresses**: Various formats and domains
- **Phone Numbers**: Multiple formats with extensions
- **Social Security Numbers**: With or without dashes
- **Passport Numbers**: International formats
- **Driver License Numbers**: State-specific formats

### Financial Information
- **Credit Card Numbers**: All major card types with various separators
- **Bank Account Numbers**: Various lengths and formats
- **Financial Amounts**: Currency symbols and formatting

### Location Information
- **Addresses**: Street addresses with apartment/suite numbers
- **Locations**: Cities, states, countries
- **Facilities**: Buildings, hospitals, schools

### Organization Information
- **Company Names**: Including legal suffixes
- **Organization Types**: Various entity types

### Technical Information
- **IP Addresses**: IPv4 format validation
- **URLs**: Web addresses with protocols
- **Medical IDs**: Patient identifiers

### Temporal Information
- **Dates**: Multiple formats and separators
- **Times**: Various time representations

## Usage Examples

### Basic Anonymization
```python
from anonymizer import PIIAnonymizer

anonymizer = PIIAnonymizer()

# Pseudonymization with context-aware labels
result, mappings = anonymizer.pseudonymize(text)

# Enhanced masking with intelligent partial reveal
result, mappings = anonymizer.mask(text)

# Replacement with human-friendly labels
result, mappings = anonymizer.replace(text)
```

### Detection and Analysis
```python
# Preview detected entities
preview = anonymizer.preview_detection(text)
print(f"Found entities: {preview}")

# Get statistics
stats = anonymizer.get_detection_stats(text)
print(f"Entity counts: {stats}")

# Direct detection
entities = anonymizer.detect_pii(text)
for entity_text, entity_type, start, end in entities:
    print(f"{entity_type}: {entity_text}")
```

### Reversible Anonymization
```python
# Anonymize
anonymized_text, mappings = anonymizer.pseudonymize(original_text)

# Store mappings securely
encrypted_mappings = store_mappings_securely(mappings)

# Later, deanonymize
restored_text = anonymizer.deanonymize(anonymized_text, mappings)
```

## Configuration Options

### Custom Patterns
The anonymizer supports custom spaCy patterns for organization-specific entity types:

```python
# Add custom patterns to the matcher
anonymizer.matcher.add("CUSTOM_ID", [pattern_list])
```

### Validation Rules
Custom validation can be added for specific entity types:

```python
def custom_validate_entity(entity_text, entity_type):
    # Custom validation logic
    return True
```

## Performance Considerations

- **Efficient Overlap Detection**: Uses optimized algorithms to prevent duplicate processing
- **Pattern Caching**: spaCy patterns are compiled once during initialization
- **Minimal False Positives**: Validation reduces unnecessary processing
- **Memory Efficient**: Streaming processing for large texts

## Security Features

- **Reversible Encryption**: Mappings can be encrypted for secure storage
- **No Hardcoded Secrets**: All sensitive data handled through mappings
- **Configurable Sensitivity**: Different anonymization levels available
- **Audit Trail**: Detection statistics for compliance reporting

## Integration with Existing Project

The enhanced anonymizer is fully compatible with your existing Flask application:

```python
# In app.py
anonymizer = PIIAnonymizer()

@app.route('/api/anonymize', methods=['POST'])
def anonymize_text():
    data = request.json
    text = data['text']
    mode = data.get('mode', 'pseudonymize')
    
    # Use enhanced anonymization
    result, mappings = anonymizer.anonymize(text, mode)
    
    return jsonify({
        'anonymized_text': result,
        'entity_stats': anonymizer.get_detection_stats(text),
        'mappings': mappings
    })
```

This enhancement significantly improves the PII detection capabilities for complex entities while maintaining backward compatibility with your deployed application.