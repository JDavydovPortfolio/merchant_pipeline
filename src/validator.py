import re
import logging
from typing import Dict, List
from datetime import datetime

class DocumentValidator:
    """Applies business rules and validation to parsed document data."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_document(self, parsed_data: Dict) -> Dict:
        """Apply validation rules and update flagged issues."""
        validation_issues = []
        
        # EIN/SSN validation
        ein_ssn = parsed_data.get('ein_or_ssn', '')
        if not self._validate_ein_ssn(ein_ssn):
            validation_issues.append(f"Invalid EIN/SSN format: '{ein_ssn}' (must be exactly 9 digits)")
        
        # ZIP code validation
        zip_code = parsed_data.get('address', {}).get('zip', '')
        if not self._validate_zip(zip_code):
            validation_issues.append(f"Invalid ZIP code: '{zip_code}' (must be exactly 5 digits)")
        
        # Requested amount validation
        amount = parsed_data.get('requested_amount', '')
        if amount and not self._validate_amount(amount):
            validation_issues.append(f"Invalid requested amount: '{amount}' (must be numeric)")
        
        # Phone validation
        phone = parsed_data.get('contact_info', {}).get('phone', '')
        if phone and not self._validate_phone(phone):
            validation_issues.append(f"Invalid phone format: '{phone}' (must be 10 digits)")
        
        # Email validation
        email = parsed_data.get('contact_info', {}).get('email', '')
        if email and not self._validate_email(email):
            validation_issues.append(f"Invalid email format: '{email}'")
        
        # State validation
        state = parsed_data.get('address', {}).get('state', '')
        if state and not self._validate_state(state):
            validation_issues.append(f"Invalid state: '{state}' (must be 2-letter abbreviation)")
        
        # Required fields validation
        required_fields = ['merchant_name', 'document_type']
        for field in required_fields:
            if not parsed_data.get(field, '').strip():
                validation_issues.append(f"Missing required field: {field}")
        
        # Address completeness check
        address = parsed_data.get('address', {})
        if any(address.values()) and not all([address.get('street'), address.get('city'), address.get('state'), address.get('zip')]):
            validation_issues.append("Incomplete address information")
        
        # Merge with existing flagged issues
        existing_issues = parsed_data.get('flagged_issues', [])
        all_issues = existing_issues + validation_issues
        
        # Update document with validation results
        parsed_data['flagged_issues'] = all_issues
        parsed_data['validation_status'] = 'passed' if not validation_issues else 'failed'
        parsed_data['requires_human_review'] = len(all_issues) > 0
        parsed_data['validation_timestamp'] = datetime.now().isoformat()
        
        # Lower confidence score if there are validation issues
        if validation_issues:
            current_confidence = parsed_data.get('confidence_score', 0.5)
            penalty = min(0.2 * len(validation_issues), 0.4)
            parsed_data['confidence_score'] = max(current_confidence - penalty, 0.1)
        
        self.logger.info(f"Validation completed for {parsed_data.get('source_file', 'unknown')}: {len(validation_issues)} issues found")
        
        return parsed_data
    
    def _validate_ein_ssn(self, ein_ssn: str) -> bool:
        """Validate EIN/SSN format (exactly 9 digits)."""
        if not ein_ssn:
            return False
        clean_ein = re.sub(r'[^\d]', '', ein_ssn)
        return len(clean_ein) == 9 and clean_ein.isdigit()
    
    def _validate_zip(self, zip_code: str) -> bool:
        """Validate ZIP code format (exactly 5 digits)."""
        if not zip_code:
            return False
        clean_zip = re.sub(r'[^\d]', '', zip_code)
        return len(clean_zip) == 5 and clean_zip.isdigit()
    
    def _validate_amount(self, amount: str) -> bool:
        """Validate requested amount is numeric."""
        if not amount:
            return True  # Empty amount is okay
        try:
            clean_amount = re.sub(r'[^\d.]', '', str(amount))
            if not clean_amount:
                return False
            float(clean_amount)
            return True
        except (ValueError, TypeError):
            return False
    
    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format (exactly 10 digits)."""
        if not phone:
            return False
        clean_phone = re.sub(r'[^\d]', '', phone)
        return len(clean_phone) == 10 and clean_phone.isdigit()
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email.strip()) is not None
    
    def _validate_state(self, state: str) -> bool:
        """Validate state abbreviation."""
        if not state:
            return False
        
        valid_states = {
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
            'DC'  # Washington D.C.
        }
        
        return state.upper().strip() in valid_states
    
    def get_validation_summary(self, processed_documents: List[Dict]) -> Dict:
        """Generate validation summary statistics."""
        total_docs = len(processed_documents)
        if total_docs == 0:
            return {}
        
        passed = sum(1 for doc in processed_documents if doc.get('validation_status') == 'passed')
        failed = total_docs - passed
        needs_review = sum(1 for doc in processed_documents if doc.get('requires_human_review', False))
        
        avg_confidence = sum(doc.get('confidence_score', 0) for doc in processed_documents) / total_docs
        
        common_issues = {}
        for doc in processed_documents:
            for issue in doc.get('flagged_issues', []):
                common_issues[issue] = common_issues.get(issue, 0) + 1
        
        return {
            'total_documents': total_docs,
            'validation_passed': passed,
            'validation_failed': failed,
            'requires_human_review': needs_review,
            'pass_rate': passed / total_docs if total_docs > 0 else 0,
            'average_confidence': avg_confidence,
            'common_issues': sorted(common_issues.items(), key=lambda x: x[1], reverse=True)[:5]
        }