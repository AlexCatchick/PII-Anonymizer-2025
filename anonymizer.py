"""
PII Detection and Anonymization Module.
Handles detection using spaCy NER and regex patterns,
and supports multiple anonymization modes.
"""
import re
import spacy
from typing import Dict, List, Tuple, Set


class PIIAnonymizer:
    """Detects and anonymizes PII in text using spaCy and regex patterns."""
    
    # spaCy entity types to detect as PII
    SPACY_PII_ENTITIES = ['PERSON', 'GPE', 'ORG', 'DATE', 'MONEY', 'FAC', 'NORP']
    
    # Regex patterns for additional PII types
    REGEX_PATTERNS = {
        'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'PHONE': r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
        'CREDIT_CARD': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        'SSN': r'\b\d{3}-\d{2}-\d{4}\b'
    }
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize the PII anonymizer.
        
        Args:
            model_name: spaCy model to use for NER
        """
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            print(f"spaCy model '{model_name}' not found. Downloading...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", model_name])
            self.nlp = spacy.load(model_name)
        
        self.counter = 0
        self.mappings: Dict[str, str] = {}
    
    def detect_pii(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        Detect all PII entities in text using spaCy and regex.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of tuples (entity_text, entity_type, start_pos, end_pos)
        """
        entities = []
        seen_spans = set()
        
        # Detect using spaCy NER
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ in self.SPACY_PII_ENTITIES:
                span = (ent.start_char, ent.end_char)
                if span not in seen_spans:
                    entities.append((ent.text, ent.label_, ent.start_char, ent.end_char))
                    seen_spans.add(span)
        
        # Detect using regex patterns
        for entity_type, pattern in self.REGEX_PATTERNS.items():
            for match in re.finditer(pattern, text):
                span = (match.start(), match.end())
                # Avoid duplicates with spaCy entities
                if span not in seen_spans:
                    entities.append((match.group(), entity_type, match.start(), match.end()))
                    seen_spans.add(span)
        
        # Sort by start position (important for replacement)
        entities.sort(key=lambda x: x[2])
        
        return entities
    
    def pseudonymize(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Replace PII with reversible pseudonyms (PII_1, PII_2, etc.).
        
        Args:
            text: Input text containing PII
            
        Returns:
            Tuple of (anonymized_text, mappings_dict)
        """
        entities = self.detect_pii(text)
        self.counter = 0
        self.mappings = {}
        
        # Process entities in reverse order to maintain correct positions
        result = text
        offset = 0
        
        for entity_text, entity_type, start, end in entities:
            self.counter += 1
            placeholder = f"PII_{self.counter}"
            
            # Store mapping
            self.mappings[placeholder] = entity_text
            
            # Replace in text
            result = result[:start + offset] + placeholder + result[end + offset:]
            offset += len(placeholder) - (end - start)
        
        return result, self.mappings
    
    def mask(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Partially mask PII (show first char, mask rest with *).
        
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
            # Create masked version
            if entity_type == 'EMAIL':
                # Special handling for emails: show first char and domain
                parts = entity_text.split('@')
                if len(parts) == 2:
                    masked = f"{parts[0][0]}***@{parts[1]}"
                else:
                    masked = entity_text[0] + '*' * (len(entity_text) - 1)
            elif entity_type == 'CREDIT_CARD':
                # Show first 4 digits, mask rest
                clean_number = re.sub(r'[-\s]', '', entity_text)
                masked = clean_number[:4] + '---***'
            elif entity_type == 'PHONE':
                # Show area code, mask rest
                masked = re.sub(r'\d(?=.*\d{4})', '-', entity_text)
            else:
                # For names and other text: show first char of each word
                words = entity_text.split()
                masked_words = [w[0] + '*' * (len(w) - 1) for w in words]
                masked = ' '.join(masked_words)
            
            # Store mapping for potential reversal
            placeholder = f"MASKED_{start}_{end}"
            self.mappings[placeholder] = entity_text
            
            # Replace in text
            result = result[:start + offset] + masked + result[end + offset:]
            offset += len(masked) - (end - start)
        
        return result, self.mappings
    
    def replace(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Replace PII with entity type labels [PERSON], [EMAIL], etc.
        
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
            placeholder = f"[{entity_type}]"
            
            # Store mapping with unique identifier
            unique_key = f"{entity_type}_{self.counter}"
            self.mappings[unique_key] = entity_text
            
            # Replace in text
            result = result[:start + offset] + placeholder + result[end + offset:]
            offset += len(placeholder) - (end - start)
        
        return result, self.mappings
    
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
