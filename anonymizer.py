"""
Enhanced PII Detection and Anonymization Module.
Handles complex entities with internal tokens using advanced spaCy NER,
custom patterns, and improved regex for multi-token PII detection.
"""
import re
import spacy
from spacy.matcher import Matcher
from spacy.lang.en import English
from typing import Dict, List, Tuple, Set


class PIIAnonymizer:
    
    # Enhanced spaCy entity mapping with human-friendly labels
    SPACY_PII_ENTITIES = {
        'PERSON': 'PERSON_NAME',
        'GPE': 'LOCATION', 
        'ORG': 'ORGANIZATION',
        'DATE': 'DATE_TIME',
        'MONEY': 'FINANCIAL_AMOUNT',
        'FAC': 'FACILITY_NAME',
        'NORP': 'NATIONALITY_GROUP',
        'EVENT': 'EVENT_NAME',
        'LAW': 'LEGAL_DOCUMENT',
        'LANGUAGE': 'LANGUAGE_NAME',
        'WORK_OF_ART': 'ARTWORK_TITLE'
    }
    
    # Enhanced regex patterns for complex multi-token PII with context awareness
    REGEX_PATTERNS = {
        'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'PHONE': r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}(?:\s?(?:ext|extension|x)\.?\s?\d{1,5})?\b',
        'CREDIT_CARD': r'\b(?:4\d{3}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}|5[1-5]\d{2}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}|3[47]\d{2}[\s-]?\d{6}[\s-]?\d{5}|3[0568]\d{2}[\s-]?\d{6}[\s-]?\d{4}|6(?:011|5\d{2})[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4})\b',
        'SSN': r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b',
        'PASSPORT': r'\b[A-Z]{1,2}\d{6,9}\b',
        'DRIVER_LICENSE': r'\b[A-Z]{1,2}[-.\s]?\d{6,8}\b',
        'IP_ADDRESS': r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
        'URL': r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?',
        'MEDICAL_ID': r'\b(?:MRN|MR|PATIENT)[\s#:-]*\d{6,12}\b',
        'ADDRESS': r'\b\d+\s+(?:[A-Z][a-z]+\s+)*(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Place|Pl|Way|Circle|Cir|Parkway|Pkwy)\.?\b'
    }
    
    # Human-friendly entity labels for better user experience
    HUMAN_LABELS = {
        'PERSON_NAME': 'Person Name',
        'LOCATION': 'Location',
        'ORGANIZATION': 'Organization',
        'DATE_TIME': 'Date/Time',
        'FINANCIAL_AMOUNT': 'Financial Amount',
        'FACILITY_NAME': 'Facility',
        'NATIONALITY_GROUP': 'Nationality/Group',
        'EVENT_NAME': 'Event',
        'LEGAL_DOCUMENT': 'Legal Document',
        'LANGUAGE_NAME': 'Language',
        'ARTWORK_TITLE': 'Artwork Title',
        'EMAIL': 'Email Address',
        'PHONE': 'Phone Number',
        'CREDIT_CARD': 'Credit Card',
        'SSN': 'Social Security Number',
        'PASSPORT': 'Passport Number',
        'DRIVER_LICENSE': 'Driver License',
        'ACCOUNT_NUMBER': 'Account Number',
        'EMPLOYEE_ID': 'Employee ID',
        'APPLICATION_NUMBER': 'Application Number',
        'BANK_ACCOUNT': 'Bank Account',
        'IP_ADDRESS': 'IP Address',
        'URL': 'Website URL',
        'MEDICAL_ID': 'Medical ID',
        'ADDRESS': 'Physical Address'
    }
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize enhanced PII anonymizer with spaCy model and custom patterns.
        Sets up advanced entity recognition for complex multi-token PII.
        """
        try:
            self.nlp = spacy.load(model_name)
            self.setup_custom_patterns()
        except OSError:
            print(f"spaCy model '{model_name}' not found. Downloading...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", model_name])
            self.nlp = spacy.load(model_name)
            self.setup_custom_patterns()
        
        self.counter = 0
        self.mappings: Dict[str, str] = {}
    
    def setup_custom_patterns(self):
        """
        Set up custom spaCy patterns for better detection of complex PII entities
        with internal tokens, spaces, punctuation, and line breaks.
        """
        self.matcher = Matcher(self.nlp.vocab)
        
        # Pattern for multi-word names with titles (Dr. John Smith, Ms. Jane Doe, etc.)
        name_patterns = [
            [{"LOWER": {"IN": ["dr", "mr", "mrs", "ms", "prof", "professor", "captain", "sir", "madam"]}}, 
             {"IS_ALPHA": True}, 
             {"IS_ALPHA": True, "OP": "?"}],
            [{"IS_ALPHA": True, "IS_TITLE": True}, 
             {"IS_ALPHA": True, "IS_TITLE": True}, 
             {"IS_ALPHA": True, "IS_TITLE": True, "OP": "?"}]
        ]
        self.matcher.add("ENHANCED_PERSON", name_patterns)
        
        # Pattern for complex addresses with multiple components
        address_patterns = [
            [{"LIKE_NUM": True}, 
             {"IS_ALPHA": True, "OP": "+"}, 
             {"LOWER": {"IN": ["street", "st", "avenue", "ave", "road", "rd", "boulevard", "blvd", "drive", "dr", "lane", "ln"]}}],
            [{"LIKE_NUM": True}, 
             {"IS_ALPHA": True}, 
             {"IS_ALPHA": True, "OP": "?"}, 
             {"LOWER": {"IN": ["apt", "apartment", "suite", "unit", "floor", "fl"]}, "OP": "?"}, 
             {"LIKE_NUM": True, "OP": "?"}]
        ]
        self.matcher.add("ENHANCED_ADDRESS", address_patterns)
        
        # Pattern for organization names with legal suffixes
        org_patterns = [
            [{"IS_ALPHA": True, "OP": "+"}, 
             {"LOWER": {"IN": ["inc", "corp", "llc", "ltd", "co", "company", "corporation", "incorporated", "limited"]}}],
            [{"IS_TITLE": True, "OP": "+"}, 
             {"LOWER": {"IN": ["bank", "hospital", "university", "college", "school", "clinic", "medical", "center"]}}]
        ]
        self.matcher.add("ENHANCED_ORGANIZATION", org_patterns)
        
        # Pattern for complex dates and times
        datetime_patterns = [
            [{"LIKE_NUM": True}, 
             {"TEXT": {"IN": ["/", "-", "."]}}, 
             {"LIKE_NUM": True}, 
             {"TEXT": {"IN": ["/", "-", "."]}}, 
             {"LIKE_NUM": True}],
            [{"IS_ALPHA": True, "LENGTH": {">=": 3}}, 
             {"LIKE_NUM": True}, 
             {"TEXT": ","}, 
             {"LIKE_NUM": True}]
        ]
        self.matcher.add("ENHANCED_DATETIME", datetime_patterns)
    
    def detect_pii(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        Enhanced PII detection using spaCy NER, custom patterns, and regex.
        Handles complex entities with internal tokens, spaces, punctuation, and line breaks.
        Includes special handling for key-value pairs to avoid misclassification.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of tuples: (entity_text, entity_type, start_pos, end_pos)
        """
        entities = []
        seen_spans = set()
        
        # Process text with spaCy
        doc = self.nlp(text)
        
        # SPECIAL HANDLING: Detect key-value pairs first
        self._detect_key_value_pairs(text, entities, seen_spans)
        
        # FIRST: Process regex patterns (higher priority for structured data)
        for entity_type, pattern in self.REGEX_PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                span = (match.start(), match.end())
                entity_text = match.group()
                
                # Skip if already covered by key-value detection
                if self._overlaps_with_existing(span, seen_spans):
                    continue
                
                # Additional validation for specific entity types
                if self._validate_entity(entity_text, entity_type):
                    entities.append((entity_text, entity_type, match.start(), match.end()))
                    seen_spans.add(span)
        
        # SECOND: Process spaCy NER entities (but avoid overlaps with regex)
        for ent in doc.ents:
            if ent.label_ in self.SPACY_PII_ENTITIES:
                span = (ent.start_char, ent.end_char)
                
                # Skip if already covered by regex patterns or key-value pairs
                if self._overlaps_with_existing(span, seen_spans):
                    continue
                
                # Filter out very short entities that are likely false positives
                if len(ent.text.strip()) < 2:
                    continue
                
                # Enhanced validation for spaCy entities
                entity_label = self.SPACY_PII_ENTITIES.get(ent.label_, ent.label_)
                if self._validate_entity(ent.text, entity_label):
                    entities.append((ent.text, entity_label, ent.start_char, ent.end_char))
                    seen_spans.add(span)
        
        # THIRD: Custom pattern matching for complex entities (lowest priority)
        matches = self.matcher(doc)
        for match_id, start, end in matches:
            span_doc = doc[start:end]
            entity_text = span_doc.text
            match_label = self.nlp.vocab.strings[match_id]
            
            # Skip if already covered
            span = (span_doc.start_char, span_doc.end_char)
            if self._overlaps_with_existing(span, seen_spans):
                continue
            
            # Additional validation for custom patterns
            if len(entity_text.strip()) < 3:
                continue
            
            # Map custom patterns to entity types
            if match_label == "ENHANCED_PERSON":
                entity_type = "PERSON_NAME"
            elif match_label == "ENHANCED_ADDRESS":
                entity_type = "ADDRESS"
            elif match_label == "ENHANCED_ORGANIZATION":
                entity_type = "ORGANIZATION"
            elif match_label == "ENHANCED_DATETIME":
                entity_type = "DATE_TIME"
            else:
                entity_type = match_label
            
            if self._validate_entity(entity_text, entity_type):
                entities.append((entity_text, entity_type, span_doc.start_char, span_doc.end_char))
                seen_spans.add(span)
        
        # Sort by start position (important for replacement)
        entities.sort(key=lambda x: x[2])
        
        return entities
    
    def _detect_key_value_pairs(self, text: str, entities: List, seen_spans: Set):
        """
        Special detection for key-value pairs to avoid misclassification.
        Handles patterns like "Name: John Doe", "Phone Number: +1 234 567 8901", etc.
        """
        # Pattern for key-value pairs
        kv_patterns = [
            (r'Account\s+Number:\s*(\d{8,17})', 'ACCOUNT_NUMBER'),
            (r'Employee\s+ID:\s*(\w{3,15})', 'EMPLOYEE_ID'),
            (r'Application\s+Number:\s*(\w{3,15})', 'APPLICATION_NUMBER'),
            (r'Phone\s+Number:\s*(\+?[0-9\s\(\)\-\.]{10,20})', 'PHONE'),
            (r'Name:\s*([A-Z][a-zA-Z\s]{2,30})', 'PERSON_NAME'),
        ]
        
        for pattern, entity_type in kv_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                value = match.group(1).strip()
                value_start = match.start(1)
                value_end = match.end(1)
                
                # Validate the extracted value
                if self._validate_entity(value, entity_type):
                    entities.append((value, entity_type, value_start, value_end))
                    seen_spans.add((value_start, value_end))
    
    def _validate_entity(self, entity_text: str, entity_type: str) -> bool:
        """
        Enhanced validation to reduce false positives and improve context recognition.
        
        Args:
            entity_text: The detected entity text
            entity_type: The type of entity
            
        Returns:
            True if the entity is valid
        """
        text = entity_text.strip()
        
        # Common field labels that should not be treated as person names
        field_labels = {
            'phone number', 'email', 'address', 'account number', 'employee id', 
            'application number', 'name', 'contact', 'information', 'details',
            'verification', 'request', 'department', 'status', 'update', 'date',
            'salary', 'position', 'title', 'id', 'number', 'code', 'reference',
            'date of birth', 'first name', 'last name', 'document number', 
            'social security number', 'passport number', 'driver license', 
            'license number', 'credit card number', 'phone', 'mobile', 'cell'
        }
        
        # Common organizational terms that shouldn't be person names
        org_terms = {
            'hr', 'human resources', 'department', 'team', 'company', 'corporation',
            'inc', 'llc', 'ltd', 'co', 'organization', 'office', 'division'
        }
        
        # Skip field labels for ANY entity type to prevent misclassification
        text_lower = text.lower().strip()
        if text_lower in field_labels or any(label in text_lower for label in field_labels):
            return False
        
        # If detected as PERSON_NAME, validate it's actually a person name
        if entity_type == 'PERSON_NAME':
            text_lower = text.lower()
            
            # Reject common field labels
            if text_lower in field_labels:
                return False
                
            # Reject organizational terms
            if text_lower in org_terms:
                return False
                
            # Reject if it contains common field patterns
            if any(pattern in text_lower for pattern in ['number', 'id', 'code', 'account', 'employee']):
                return False
                
            # Reject single words that are likely not names (unless common first names)
            common_first_names = {'john', 'jane', 'michael', 'sarah', 'david', 'mary', 'james', 'jennifer'}
            if len(text.split()) == 1 and text_lower not in common_first_names:
                if not text[0].isupper():  # Names should start with capital
                    return False
        
        # Enhanced phone number validation
        elif entity_type == 'PHONE':
            # Should contain enough digits and proper format
            digits = re.findall(r'\d', text)
            if len(digits) < 10:
                return False
            
            # Reject if it looks like an account number or ID (too long or no separators)
            if len(digits) > 15:  # Too long for phone
                return False
                
            # Should have phone-like separators or be exactly 10-11 digits
            if len(digits) > 11 and not re.search(r'[\(\)\-\.\s]', text):
                return False
                
            # Reject if it's clearly an account number pattern
            if len(digits) > 12 and not any(sep in text for sep in ['(', ')', '-', '.', ' ']):
                return False
        
        # Enhanced account number validation
        elif entity_type == 'ACCOUNT_NUMBER':
            digits = re.findall(r'\d', text)
            # Account numbers are typically 8-17 digits
            return 8 <= len(digits) <= 17
            
        elif entity_type == 'EMPLOYEE_ID':
            # Should have letters and/or numbers, reasonable length
            return len(text) >= 3 and len(text) <= 15
            
        elif entity_type == 'APPLICATION_NUMBER':
            # Should have letters and/or numbers, reasonable length
            return len(text) >= 3 and len(text) <= 15
        
        elif entity_type == 'EMAIL':
            # Basic email validation
            return '@' in text and '.' in text.split('@')[-1]
        
        elif entity_type == 'CREDIT_CARD':
            # Should have enough digits but not be confused with account numbers
            digits = re.findall(r'\d', text)
            return 13 <= len(digits) <= 19
        
        elif entity_type == 'SSN':
            # Should have exactly 9 digits
            digits = re.findall(r'\d', text)
            return len(digits) == 9
        
        elif entity_type == 'IP_ADDRESS':
            # Basic IP validation
            parts = text.split('.')
            if len(parts) != 4:
                return False
            try:
                return all(0 <= int(part) <= 255 for part in parts)
            except ValueError:
                return False
        
        elif entity_type == 'URL':
            # Should contain protocol or domain-like structure
            return any(protocol in text.lower() for protocol in ['http', 'www', '.com', '.org', '.net'])
        
        # For organizations, validate they're not field labels
        elif entity_type == 'ORGANIZATION':
            text_lower = text.lower()
            if text_lower in field_labels:
                return False
        
        return True
    
    def _overlaps_with_existing(self, span: Tuple[int, int], seen_spans: Set[Tuple[int, int]]) -> bool:
        """
        Check if a span overlaps with any existing spans to prevent duplicates.
        Uses a more sophisticated overlap detection to handle partial overlaps.
        
        Args:
            span: Tuple of (start, end) positions
            seen_spans: Set of already detected spans
            
        Returns:
            True if span overlaps with any existing span
        """
        start, end = span
        for seen_start, seen_end in seen_spans:
            # Check for any overlap with tolerance for entity boundaries
            overlap_start = max(start, seen_start)
            overlap_end = min(end, seen_end)
            
            # Consider overlapping if they share more than 20% of the smaller entity
            if overlap_start < overlap_end:
                overlap_length = overlap_end - overlap_start
                smaller_entity_length = min(end - start, seen_end - seen_start)
                
                # If overlap is more than 20% of smaller entity, consider it a duplicate
                if overlap_length / smaller_entity_length > 0.2:
                    return True
        return False
    
    def pseudonymize(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Enhanced pseudonymization with human-friendly labels for complex PII entities.
        Replace PII with descriptive, reversible pseudonyms using industry standards.
        
        Args:
            text: Input text containing PII
            
        Returns:
            Tuple of (anonymized_text, entity_mapping)
        """
        entities = self.detect_pii(text)
        self.counter = 0
        self.mappings = {}
        
        # Initialize entity counters for type-specific numbering
        entity_counters = {}
        
        # Process entities in correct order for position tracking
        result = text
        offset = 0
        
        for entity_text, entity_type, start, end in entities:
            # Generate human-friendly pseudonym with industry standard naming
            human_label = self.HUMAN_LABELS.get(entity_type, entity_type.replace('_', ' ').title())
            
            # Create context-aware pseudonyms with type-specific counters
            if entity_type in entity_counters:
                entity_counters[entity_type] += 1
            else:
                entity_counters[entity_type] = 1
            
            count = entity_counters[entity_type]
            
            # LLM-friendly pseudonym generation with semantic labels
            if entity_type == "PERSON_NAME":
                placeholder = f"name_{count}"
            elif entity_type == "ORGANIZATION":
                placeholder = f"company_{count}"
            elif entity_type == "LOCATION":
                placeholder = f"location_{count}"
            elif entity_type == "EMAIL":
                placeholder = f"email_{count}"
            elif entity_type == "PHONE":
                placeholder = f"mobNo_{count}"
            elif entity_type == "ADDRESS":
                placeholder = f"physical_address_{count}"
            elif entity_type == "DATE_TIME":
                placeholder = f"date_{count}"
            elif entity_type == "CREDIT_CARD":
                placeholder = f"credit_card_{count}"
            elif entity_type == "SSN":
                placeholder = f"ssn_{count}"
            elif entity_type == "MEDICAL_ID":
                placeholder = f"medical_id_{count}"
            elif entity_type == "FINANCIAL_AMOUNT":
                placeholder = f"amount_{count}"
            elif entity_type == "IP_ADDRESS":
                placeholder = f"ip_address_{count}"
            elif entity_type == "URL":
                placeholder = f"url_{count}"
            elif entity_type == "PASSPORT":
                placeholder = f"passport_{count}"
            elif entity_type == "DRIVER_LICENSE":
                placeholder = f"driver_license_{count}"
            elif entity_type == "ACCOUNT_NUMBER":
                placeholder = f"account_number_{count}"
            elif entity_type == "EMPLOYEE_ID":
                placeholder = f"employee_id_{count}"
            elif entity_type == "APPLICATION_NUMBER":
                placeholder = f"application_number_{count}"
            elif entity_type == "BANK_ACCOUNT":
                placeholder = f"bank_account_{count}"
            elif entity_type == "FACILITY_NAME":
                placeholder = f"facility_{count}"
            elif entity_type == "EVENT_NAME":
                placeholder = f"event_{count}"
            elif entity_type == "LEGAL_DOCUMENT":
                placeholder = f"document_{count}"
            elif entity_type == "NATIONALITY_GROUP":
                placeholder = f"group_{count}"
            elif entity_type == "LANGUAGE_NAME":
                placeholder = f"language_{count}"
            elif entity_type == "ARTWORK_TITLE":
                placeholder = f"artwork_{count}"
            else:
                # Generic pseudonym for other entity types with clean naming
                clean_type = entity_type.lower().replace('_', '_').replace(' ', '_')
                placeholder = f"{clean_type}_{count}"
            
            # Store mapping for reversibility
            self.mappings[placeholder] = entity_text
            
            # Replace in text with offset adjustment
            result = result[:start + offset] + placeholder + result[end + offset:]
            offset += len(placeholder) - (end - start)
        
        return result, self.mappings
    
    def mask(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Enhanced masking for complex PII entities with intelligent partial reveal.
        Partially mask PII while preserving structure and readability.
        
        Args:
            text: Input text containing PII
            
        Returns:
            Tuple of (anonymized_text, mappings_dict)
        """
        entities = self.detect_pii(text)
        self.mappings = {}
        
        result = text
        offset = 0
        
        for entity_text, entity_type, start, end in entities:
            # Create intelligently masked version based on entity type
            if entity_type == 'EMAIL':
                # Show first char of username and full domain
                parts = entity_text.split('@')
                if len(parts) == 2:
                    username_len = len(parts[0])
                    if username_len > 3:
                        masked = f"{parts[0][:2]}{'*' * (username_len - 2)}@{parts[1]}"
                    else:
                        masked = f"{parts[0][0]}{'*' * (username_len - 1)}@{parts[1]}"
                else:
                    masked = entity_text[0] + '*' * (len(entity_text) - 1)
            
            elif entity_type == 'CREDIT_CARD':
                # Show first 4 and last 4 digits, mask middle
                clean_number = re.sub(r'[-\s]', '', entity_text)
                if len(clean_number) >= 8:
                    masked = clean_number[:4] + '-XXXX-XXXX-' + clean_number[-4:]
                else:
                    masked = clean_number[:2] + '*' * (len(clean_number) - 2)
            
            elif entity_type == 'PHONE':
                # Preserve area code format, mask number
                if re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', entity_text):
                    masked = re.sub(r'(?<=\d{3}[-.\s()])\d(?=.*\d{3})', 'X', entity_text)
                else:
                    masked = entity_text[:3] + 'X' * (len(entity_text) - 3)
            
            elif entity_type == 'SSN':
                # Show first 3 digits, mask rest
                if '-' in entity_text:
                    parts = entity_text.split('-')
                    masked = f"{parts[0]}-XX-XXXX"
                else:
                    masked = entity_text[:3] + 'X' * (len(entity_text) - 3)
            
            elif entity_type in ['PERSON_NAME', 'ORGANIZATION']:
                # Show first letter of each word, mask rest
                words = entity_text.split()
                masked_words = []
                for word in words:
                    if len(word) > 2:
                        masked_words.append(word[0] + '*' * (len(word) - 1))
                    elif len(word) == 2:
                        masked_words.append(word[0] + '*')
                    else:
                        masked_words.append('*')
                masked = ' '.join(masked_words)
            
            elif entity_type == 'ADDRESS':
                # Show street number and first letter of street name
                address_parts = entity_text.split()
                if len(address_parts) > 1 and address_parts[0].isdigit():
                    masked_parts = [address_parts[0]]  # Keep street number
                    for part in address_parts[1:]:
                        if len(part) > 1:
                            masked_parts.append(part[0] + '*' * (len(part) - 1))
                        else:
                            masked_parts.append('*')
                    masked = ' '.join(masked_parts)
                else:
                    # Fallback to first letter masking
                    words = entity_text.split()
                    masked_words = [w[0] + '*' * (len(w) - 1) if len(w) > 1 else '*' for w in words]
                    masked = ' '.join(masked_words)
            
            elif entity_type == 'IP_ADDRESS':
                # Show first octet, mask rest
                octets = entity_text.split('.')
                if len(octets) == 4:
                    masked = f"{octets[0]}.XXX.XXX.XXX"
                else:
                    masked = entity_text[:3] + '*' * (len(entity_text) - 3)
            
            elif entity_type == 'URL':
                # Show domain, mask path
                if '://' in entity_text:
                    protocol, rest = entity_text.split('://', 1)
                    if '/' in rest:
                        domain, path = rest.split('/', 1)
                        masked = f"{protocol}://{domain}/***"
                    else:
                        masked = entity_text
                else:
                    masked = entity_text[:5] + '*' * max(0, len(entity_text) - 5)
            
            else:
                # Generic masking: show first character of each word
                words = entity_text.split()
                if len(words) > 1:
                    masked_words = [w[0] + '*' * (len(w) - 1) if len(w) > 1 else '*' for w in words]
                    masked = ' '.join(masked_words)
                else:
                    # Single word: show first and last char if long enough
                    if len(entity_text) > 3:
                        masked = entity_text[0] + '*' * (len(entity_text) - 2) + entity_text[-1]
                    elif len(entity_text) > 1:
                        masked = entity_text[0] + '*' * (len(entity_text) - 1)
                    else:
                        masked = '*'
            
            # Store mapping for potential reversal
            placeholder = f"MASKED_{start}_{end}"
            self.mappings[placeholder] = entity_text
            
            # Replace in text
            result = result[:start + offset] + masked + result[end + offset:]
            offset += len(masked) - (end - start)
        
        return result, self.mappings
    
    def replace(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Enhanced replacement with human-friendly entity type labels.
        Replace PII with descriptive entity labels using industry standards.
        
        Args:
            text: Input text containing PII
            
        Returns:
            Tuple of (anonymized_text, mappings_dict)
        """
        entities = self.detect_pii(text)
        self.counter = 0
        self.mappings = {}
        
        result = text
        offset = 0
        
        for entity_text, entity_type, start, end in entities:
            self.counter += 1
            
            # Use human-friendly labels from our mapping
            human_label = self.HUMAN_LABELS.get(entity_type, entity_type.replace('_', ' ').title())
            placeholder = f"[{human_label}]"
            
            # Store mapping with unique identifier for potential reversal
            unique_key = f"{placeholder}_{self.counter}"
            self.mappings[unique_key] = entity_text
            
            # Replace in text
            result = result[:start + offset] + placeholder + result[end + offset:]
            offset += len(placeholder) - (end - start)
        
        return result, self.mappings
    
    def get_detection_stats(self, text: str) -> Dict[str, int]:
        """
        Get statistics about PII entities detected in the text.
        Useful for understanding what types of sensitive data are present.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with entity counts by type
        """
        entities = self.detect_pii(text)
        stats = {}
        
        for _, entity_type, _, _ in entities:
            human_label = self.HUMAN_LABELS.get(entity_type, entity_type)
            stats[human_label] = stats.get(human_label, 0) + 1
        
        return stats
    
    def preview_detection(self, text: str, max_examples: int = 3) -> Dict[str, List[str]]:
        """
        Preview what entities would be detected without anonymizing.
        Useful for validation before applying anonymization.
        
        Args:
            text: Input text to analyze
            max_examples: Maximum number of examples to show per entity type
            
        Returns:
            Dictionary mapping entity types to example detected entities
        """
        entities = self.detect_pii(text)
        preview = {}
        
        for entity_text, entity_type, _, _ in entities:
            human_label = self.HUMAN_LABELS.get(entity_type, entity_type)
            
            if human_label not in preview:
                preview[human_label] = []
            
            # Add unique examples up to max_examples
            if entity_text not in preview[human_label] and len(preview[human_label]) < max_examples:
                preview[human_label].append(entity_text)
        
        return preview
    
    def anonymize(self, text: str, mode: str = 'pseudonymize') -> Tuple[str, Dict[str, str]]:
        """
        Anonymize text using specified mode.
        
        Args:
            text: Input text containing PII
            mode: Anonymization mode ('pseudonymize', 'mask', 'replace')
            
        Returns:
            Tuple of (anonymized_text, mappings_dict)
        """
        if mode == 'pseudonymize':
            return self.pseudonymize(text)
        elif mode == 'mask':
            return self.mask(text)
        elif mode == 'replace':
            return self.replace(text)
        else:
            raise ValueError(f"Unknown anonymization mode: {mode}")
    
    def deanonymize(self, text: str, mappings: Dict[str, str]) -> str:
        """
        Restore original PII using stored mappings.
        
        Args:
            text: Anonymized text
            mappings: Dictionary of placeholder -> original value
            
        Returns:
            Deanonymized text with original PII restored
        """
        result = text
        
        # Sort mappings by key length (longest first) to avoid partial replacements
        sorted_mappings = sorted(mappings.items(), key=lambda x: len(x[0]), reverse=True)
        
        for placeholder, original in sorted_mappings:
            result = result.replace(placeholder, original)
        
        return result
