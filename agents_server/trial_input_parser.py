"""
Enhanced clinical trial input parser
Handles both numbered format and natural language descriptions
"""
import re
from typing import Dict, Optional


def parse_trial_input(prompt: str) -> Optional[Dict[str, str]]:
    """
    Parse clinical trial input from multiple formats
    
    Returns dict with keys: drug, disease, inclusion_criteria, exclusion_criteria
    Returns None if not a trial prediction request
    """
    # Format 1: Numbered format (existing)
    # (1) drug: X; (2) disease: Y; (3) inclusion criteria: Z; (4) exclusion criteria: W
    numbered_match = re.search(r'\(1\)\s*drug:', prompt, re.IGNORECASE)
    if numbered_match:
        return None  # Let existing parser handle this
    
    # Format 2: Natural language with key phrases
    # Look for trial prediction indicators
    trial_indicators = [
        r'clinical trial',
        r'trial design',
        r'predict.*trial',
        r'trial.*pass',
        r'assess.*trial',
        r'evaluate.*trial'
    ]
    
    is_trial_request = any(re.search(pattern, prompt, re.IGNORECASE) for pattern in trial_indicators)
    
    if not is_trial_request:
        return None
    
    # Extract components
    result = {
        'drug': None,
        'disease': None,
        'inclusion_criteria': None,
        'exclusion_criteria': None
    }
    
    # Extract drug
    drug_patterns = [
        r'drug:\s*([^\n;]+)',
        r'treatment:\s*([^\n;]+)',
        r'medication:\s*([^\n;]+)',
        r'using\s+([A-Z][a-z]+(?:\s+[a-z]+)?)',  # Capitalized drug names
    ]
    for pattern in drug_patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            result['drug'] = match.group(1).strip().rstrip('.,;')
            break
    
    # Extract disease/condition
    disease_patterns = [
        r'disease:\s*([^\n;]+)',
        r'condition:\s*([^\n;]+)',
        r'for\s+(?:treating|preventing)\s+([^\n;]+)',
        r'in\s+patients\s+with\s+([^\n;]+?)(?:\s+aged|\s+inclusion|\s+exclusion|$)',
    ]
    for pattern in disease_patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            result['disease'] = match.group(1).strip().rstrip('.,;')
            break
    
    # Extract inclusion criteria
    inclusion_patterns = [
        r'inclusion criteria:\s*([^\n]+(?:\n(?!exclusion)[^\n]+)*)',
        r'inclusion:\s*([^\n]+(?:\n(?!exclusion)[^\n]+)*)',
        r'eligible.*?:([^\n]+(?:\n(?!exclusion)[^\n]+)*)',
    ]
    for pattern in inclusion_patterns:
        match = re.search(pattern, prompt, re.IGNORECASE | re.MULTILINE)
        if match:
            criteria = match.group(1).strip()
            # Clean up bullet points and line breaks
            criteria = re.sub(r'\n\s*[-•]\s*', '; ', criteria)
            criteria = re.sub(r'\s+', ' ', criteria)
            result['inclusion_criteria'] = criteria.strip().rstrip('.,;')
            break
    
    # Extract exclusion criteria
    exclusion_patterns = [
        r'exclusion criteria:\s*([^\n]+(?:\n(?!inclusion)[^\n]+)*)',
        r'exclusion:\s*([^\n]+(?:\n(?!inclusion)[^\n]+)*)',
        r'not eligible.*?:([^\n]+(?:\n(?!inclusion)[^\n]+)*)',
    ]
    for pattern in exclusion_patterns:
        match = re.search(pattern, prompt, re.IGNORECASE | re.MULTILINE)
        if match:
            criteria = match.group(1).strip()
            # Clean up bullet points and line breaks
            criteria = re.sub(r'\n\s*[-•]\s*', '; ', criteria)
            criteria = re.sub(r'\s+', ' ', criteria)
            result['exclusion_criteria'] = criteria.strip().rstrip('.,;')
            break
    
    # Only return if we found at least drug and disease
    if result['drug'] and result['disease']:
        return result
    
    return None


def format_to_numbered(parsed: Dict[str, str]) -> str:
    """Convert parsed trial data to numbered format for LangGraph workflow"""
    parts = []
    
    if parsed.get('drug'):
        parts.append(f"(1) drug: {parsed['drug']}")
    
    if parsed.get('disease'):
        parts.append(f"(2) disease: {parsed['disease']}")
    
    if parsed.get('inclusion_criteria'):
        parts.append(f"(3) inclusion criteria: {parsed['inclusion_criteria']}")
    
    if parsed.get('exclusion_criteria'):
        parts.append(f"(4) exclusion criteria: {parsed['exclusion_criteria']}")
    
    return '; '.join(parts) + ';'
