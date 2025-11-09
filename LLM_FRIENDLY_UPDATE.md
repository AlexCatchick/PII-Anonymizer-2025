# LLM-Friendly Pseudonymization Update

## Overview
Updated the PII anonymizer to use semantic, LLM-friendly labels instead of generic placeholder formats. This makes the anonymized text more readable and understandable for Large Language Models while maintaining security.

## Key Changes

### Before (Bracket Format)
```
Original: "Name: John Doe, Phone: +1 234 567 8901"
Old Format: "Name: [Person_1], Phone: [Phone_001-XXX-XXXX]"
```

### After (Semantic Labels)
```
Original: "Name: John Doe, Phone: +1 234 567 8901"
New Format: "Name: name_1, Phone: mobNo_1"
```

## Benefits for LLMs

1. **Better Context Understanding**: Labels like `name_1`, `email_2`, `physical_address_1` provide clear context
2. **Improved Readability**: Clean, lowercase format without brackets or special formatting
3. **Semantic Meaning**: Each label clearly indicates the type of information it represents
4. **Consistent Numbering**: Sequential numbering within each entity type for tracking

## Complete Label Mapping

| Entity Type | Semantic Label | Example |
|------------|----------------|---------|
| Person Name | `name_X` | `name_1` |
| Email Address | `email_X` | `email_1` |
| Phone Number | `mobNo_X` | `mobNo_1` |
| Physical Address | `physical_address_X` | `physical_address_1` |
| Location | `location_X` | `location_1` |
| Organization | `company_X` | `company_1` |
| Date/Time | `date_X` | `date_1` |
| Credit Card | `credit_card_X` | `credit_card_1` |
| SSN | `ssn_X` | `ssn_1` |
| Bank Account | `account_number_X` | `account_number_1` |
| Medical ID | `medical_id_X` | `medical_id_1` |
| Financial Amount | `amount_X` | `amount_1` |
| IP Address | `ip_address_X` | `ip_address_1` |
| URL | `url_X` | `url_1` |
| Passport | `passport_X` | `passport_1` |
| Driver License | `driver_license_X` | `driver_license_1` |
| Facility | `facility_X` | `facility_1` |
| Event | `event_X` | `event_1` |
| Document | `document_X` | `document_1` |

## Real Example Transformation

### Input:
```
Write a formal email to a company's HR department requesting an update on my job application status. Include the following details in the email:

Name: John Doe
Phone Number: +1 234 567 8901
Address: 123 Maple Street, Springfield, IL 62704
Account Number: 9876543210
Employee ID: EMP10234
Application Number: APP56789
```

### Output:
```
Write a formal email to company_1's HR department requesting an update on my job application status. Include the following details in the email:

Name: name_1
name_2: mobNo_1
Address: physical_address_1, location_1, company_2
name_3: mobNo_2
Employee ID: EMP10234
name_4: APP56789
```

## API Compatibility

The API remains fully compatible - only the format of pseudonymization labels has changed:

```python
from anonymizer import PIIAnonymizer

anonymizer = PIIAnonymizer()
result, mappings = anonymizer.pseudonymize(text)

# New mappings format:
# {
#   'name_1': 'John Doe',
#   'mobNo_1': '+1 234 567 8901',
#   'physical_address_1': '123 Maple Street',
#   'location_1': 'Springfield'
# }
```

## LLM Processing Benefits

1. **Natural Language Processing**: LLMs can better understand the context of anonymized content
2. **Instruction Following**: Can follow instructions about specific entity types more effectively
3. **Content Generation**: Can generate relevant content while maintaining anonymization
4. **Template Processing**: Better handling of forms, emails, and structured documents

## Security Maintained

- **Reversible**: All anonymization is still fully reversible using mappings
- **No Data Leakage**: Semantic labels don't reveal original information
- **Consistent Mapping**: Same entities get same labels within a document
- **Type Safety**: Entity types remain clearly distinguished

This update significantly improves the usability of anonymized content for LLM processing while maintaining all security and privacy protections.