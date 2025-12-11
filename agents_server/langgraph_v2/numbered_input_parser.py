"""
Parser for numbered clinical trial input format
Extracts structured data from user input like:
"Features contain (1) drug: Aggrenox capsule; (2) disease: cerebrovascular accident; ..."
"""

import re
from typing import Dict, Optional


class NumberedInputParser:
    """
    Parser for numbered format clinical trial input
    
    Expected format:
        "Features contain (1) drug: <drug_name>; (2) disease: <disease_name>; 
         (3) inclusion criteria: <criteria>; (4) exclusion criteria: <criteria>;"
    """
    
    # Regex patterns for extracting numbered items
    PATTERNS = {
        "drug": r'\(1\)\s*drug:\s*([^;]+)',
        "disease": r'\(2\)\s*disease:\s*([^;]+)',
        "inclusion_criteria": r'\(3\)\s*inclusion criteria:\s*([^;]+)',
        "exclusion_criteria": r'\(4\)\s*exclusion criteria:\s*([^;]+)',
    }
    
    # Words to remove from drug names (noise terms)
    DRUG_NOISE_TERMS = [
        "capsule", "capsules", "tablet", "tablets", "injection", "injections",
        "pill", "pills", "solution", "cream", "ointment", "gel", "patch",
        "powder", "spray", "drops", "syrup", "suspension"
    ]
    
    @classmethod
    def parse(cls, raw_input: str) -> Dict[str, Optional[str]]:
        """
        Parse numbered input format
        
        Args:
            raw_input: Raw user input string
            
        Returns:
            Dictionary with parsed fields:
            {
                "drug": str or None,
                "drug_cleaned": str or None,
                "disease": str or None,
                "inclusion_criteria": str or None,
                "exclusion_criteria": str or None,
                "parsing_errors": list of error messages
            }
        """
        result = {
            "drug": None,
            "drug_cleaned": None,
            "disease": None,
            "inclusion_criteria": None,
            "exclusion_criteria": None,
            "parsing_errors": []
        }
        
        # Case-insensitive matching
        input_lower = raw_input.lower()
        
        # Extract each field
        for field, pattern in cls.PATTERNS.items():
            match = re.search(pattern, input_lower, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Remove trailing semicolons/periods
                value = value.rstrip(';.,').strip()
                result[field] = value
            else:
                result["parsing_errors"].append(f"Could not find field: {field}")
        
        # Clean drug name if found
        if result["drug"]:
            result["drug_cleaned"] = cls.clean_drug_name(result["drug"])
        
        return result
    
    @classmethod
    def clean_drug_name(cls, drug_name: str) -> str:
        """
        Remove noise terms from drug name
        
        Example:
            "Aggrenox capsule" -> "Aggrenox"
            "aspirin tablet" -> "aspirin"
        
        Args:
            drug_name: Raw drug name
            
        Returns:
            Cleaned drug name
        """
        cleaned = drug_name.strip().lower()
        
        # Remove each noise term
        for term in cls.DRUG_NOISE_TERMS:
            # Use word boundary to avoid removing parts of the drug name
            pattern = r'\b' + re.escape(term) + r'\b'
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        cleaned = ' '.join(cleaned.split()).strip()
        
        return cleaned
    
    @classmethod
    def validate_parse(cls, parsed: Dict[str, Optional[str]]) -> tuple[bool, list[str]]:
        """
        Validate that required fields were parsed
        
        Args:
            parsed: Result from parse()
            
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        # Required fields
        required = ["drug", "disease"]
        for field in required:
            if not parsed.get(field):
                issues.append(f"Missing required field: {field}")
        
        # Optional but recommended
        if not parsed.get("inclusion_criteria") and not parsed.get("exclusion_criteria"):
            issues.append("Warning: No eligibility criteria provided")
        
        is_valid = len([i for i in issues if i.startswith("Missing")]) == 0
        
        return is_valid, issues


# Example usage and testing
if __name__ == "__main__":
    # Test cases
    test_inputs = [
        # Standard format
        """I have designed a clinical trial and hope you can help me predict whether this trial can pass. 
        Features contain (1) drug: Aggrenox capsule; (2) disease: cerebrovascular accident; 
        (3) inclusion criteria: adults over 18 years old with history of stroke; 
        (4) exclusion criteria: pregnant women, severe liver disease;""",
        
        # Minimal format
        "(1) drug: aspirin tablet; (2) disease: heart disease;",
        
        # With different formatting
        "Features: (1) Drug: Metformin; (2) Disease: Type 2 diabetes; (3) Inclusion Criteria: HbA1c > 7.0",
    ]
    
    print("="*60)
    print("Testing Numbered Input Parser")
    print("="*60)
    
    for i, test_input in enumerate(test_inputs, 1):
        print(f"\nTest Case {i}:")
        print(f"Input: {test_input[:100]}...")
        
        parsed = NumberedInputParser.parse(test_input)
        is_valid, issues = NumberedInputParser.validate_parse(parsed)
        
        print(f"\nParsed Results:")
        print(f"  Drug (raw): {parsed['drug']}")
        print(f"  Drug (cleaned): {parsed['drug_cleaned']}")
        print(f"  Disease: {parsed['disease']}")
        print(f"  Inclusion: {parsed['inclusion_criteria'][:50] if parsed['inclusion_criteria'] else None}...")
        print(f"  Exclusion: {parsed['exclusion_criteria'][:50] if parsed['exclusion_criteria'] else None}...")
        print(f"\nValidation: {'✅ VALID' if is_valid else '❌ INVALID'}")
        if issues:
            print(f"Issues: {', '.join(issues)}")
        print("-"*60)
