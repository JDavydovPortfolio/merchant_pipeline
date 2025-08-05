import json
import csv
import logging
from datetime import datetime
from typing import Dict, List
import os

class CRMSubmitter:
    """Handles CRM submission and logging."""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.log_file = os.path.join(output_dir, "crm.log")
        self.logger = logging.getLogger(__name__)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    def submit_document(self, parsed_data: Dict) -> Dict:
        """Submit document to CRM (mock implementation)."""
        try:
            # Generate clean JSON file
            json_filename = self._generate_json_file(parsed_data)
            
            # Mock CRM API call
            submission_result = self._mock_crm_submit(parsed_data)
            
            # Log submission
            self._log_submission(parsed_data, submission_result)
            
            return {
                "status": "success",
                "json_file": json_filename,
                "crm_response": submission_result
            }
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"CRM submission failed: {error_msg}")
            self._log_submission(parsed_data, {"status": "failed", "error": error_msg})
            return {
                "status": "failed",
                "error": error_msg
            }
    
    def generate_csv_summary(self, processed_documents: List[Dict]) -> str:
        """Generate CSV summary of all processed documents."""
        csv_filename = os.path.join(self.output_dir, f"submission_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        
        try:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'source_file', 'document_type', 'merchant_name', 'ein_or_ssn',
                    'requested_amount', 'phone', 'email', 'street', 'city', 'state', 'zip',
                    'validation_status', 'requires_human_review', 'confidence_score',
                    'flagged_issues_count', 'processing_timestamp'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for doc in processed_documents:
                    address = doc.get('address', {})
                    contact = doc.get('contact_info', {})
                    
                    row = {
                        'source_file': doc.get('source_file', ''),
                        'document_type': doc.get('document_type', ''),
                        'merchant_name': doc.get('merchant_name', ''),
                        'ein_or_ssn': doc.get('ein_or_ssn', ''),
                        'requested_amount': doc.get('requested_amount', ''),
                        'phone': contact.get('phone', ''),
                        'email': contact.get('email', ''),
                        'street': address.get('street', ''),
                        'city': address.get('city', ''),
                        'state': address.get('state', ''),
                        'zip': address.get('zip', ''),
                        'validation_status': doc.get('validation_status', ''),
                        'requires_human_review': doc.get('requires_human_review', False),
                        'confidence_score': doc.get('confidence_score', 0.0),
                        'flagged_issues_count': len(doc.get('flagged_issues', [])),
                        'processing_timestamp': doc.get('processing_timestamp', '')
                    }
                    writer.writerow(row)
            
            self.logger.info(f"CSV summary generated: {csv_filename}")
            return csv_filename
            
        except Exception as e:
            self.logger.error(f"Failed to generate CSV summary: {str(e)}")
            raise
    
    def _generate_json_file(self, parsed_data: Dict) -> str:
        """Generate clean JSON file for CRM upload."""
        source_file = parsed_data.get('source_file', 'unknown')
        base_name = os.path.splitext(source_file)[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_filename = os.path.join(self.output_dir, f"{base_name}_processed_{timestamp}.json")
        
        # Clean data for CRM submission
        crm_data = {
            "merchant_information": {
                "name": parsed_data.get('merchant_name', ''),
                "ein_or_ssn": parsed_data.get('ein_or_ssn', ''),
                "business_type": parsed_data.get('business_info', {}).get('business_type', ''),
                "years_in_business": parsed_data.get('business_info', {}).get('years_in_business', ''),
                "annual_revenue": parsed_data.get('business_info', {}).get('annual_revenue', '')
            },
            "contact_information": {
                "phone": parsed_data.get('contact_info', {}).get('phone', ''),
                "email": parsed_data.get('contact_info', {}).get('email', '')
            },
            "address": {
                "street": parsed_data.get('address', {}).get('street', ''),
                "city": parsed_data.get('address', {}).get('city', ''),
                "state": parsed_data.get('address', {}).get('state', ''),
                "zip": parsed_data.get('address', {}).get('zip', '')
            },
            "application_details": {
                "document_type": parsed_data.get('document_type', ''),
                "submission_date": parsed_data.get('submission_date', ''),
                "requested_amount": parsed_data.get('requested_amount', '')
            },
            "processing_metadata": {
                "source_file": parsed_data.get('source_file', ''),
                "validation_status": parsed_data.get('validation_status', ''),
                "requires_human_review": parsed_data.get('requires_human_review', False),
                "confidence_score": parsed_data.get('confidence_score', 0.0),
                "flagged_issues": parsed_data.get('flagged_issues', []),
                "processing_timestamp": parsed_data.get('processing_timestamp', ''),
                "validation_timestamp": parsed_data.get('validation_timestamp', '')
            }
        }
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(crm_data, f, indent=2, ensure_ascii=False)
        
        return json_filename
    
    def _mock_crm_submit(self, parsed_data: Dict) -> Dict:
        """Mock CRM API submission."""
        import random
        import time
        
        # Simulate API processing time
        time.sleep(random.uniform(0.5, 1.5))
        
        # Check validation status
        if parsed_data.get('validation_status') == 'failed':
            return {
                "status": "rejected",
                "reason": "Document failed validation checks",
                "crm_id": None,
                "timestamp": datetime.now().isoformat()
            }
        
        # Check confidence score
        confidence = parsed_data.get('confidence_score', 0.5)
        if confidence < 0.3:
            return {
                "status": "pending_review",
                "reason": "Low confidence score requires manual review",
                "crm_id": f"PENDING-{random.randint(10000, 99999)}",
                "timestamp": datetime.now().isoformat()
            }
        
        # Simulate 90% success rate for valid documents
        if random.random() < 0.9:
            return {
                "status": "accepted",
                "crm_id": f"CRM-{random.randint(100000, 999999)}",
                "submission_time": datetime.now().isoformat(),
                "processing_notes": "Document successfully processed and entered into CRM"
            }
        else:
            return {
                "status": "failed",
                "reason": "CRM system temporarily unavailable",
                "crm_id": None,
                "timestamp": datetime.now().isoformat(),
                "retry_suggested": True
            }
    
    def _log_submission(self, parsed_data: Dict, result: Dict):
        """Log submission attempt to file."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "source_file": parsed_data.get('source_file', ''),
            "merchant_name": parsed_data.get('merchant_name', ''),
            "document_type": parsed_data.get('document_type', ''),
            "validation_status": parsed_data.get('validation_status', ''),
            "confidence_score": parsed_data.get('confidence_score', 0.0),
            "submission_result": result
        }
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write to CRM log: {str(e)}")
    
    def get_submission_stats(self) -> Dict:
        """Get submission statistics from log file."""
        if not os.path.exists(self.log_file):
            return {"total": 0, "accepted": 0, "rejected": 0, "failed": 0, "pending": 0}
        
        stats = {"total": 0, "accepted": 0, "rejected": 0, "failed": 0, "pending": 0}
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        stats["total"] += 1
                        status = entry.get("submission_result", {}).get("status", "unknown")
                        if status == "accepted":
                            stats["accepted"] += 1
                        elif status == "rejected":
                            stats["rejected"] += 1
                        elif status == "pending_review":
                            stats["pending"] += 1
                        else:
                            stats["failed"] += 1
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            self.logger.error(f"Failed to read CRM log: {str(e)}")
        
        return stats