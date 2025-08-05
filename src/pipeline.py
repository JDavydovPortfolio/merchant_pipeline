import os
import logging
from typing import List, Dict
from datetime import datetime

# Import processing modules
from .ocr import OCRProcessor
from .llm import LLMParser
from .validator import DocumentValidator
from .crm_submit import CRMSubmitter

class DocumentPipeline:
    """Main pipeline orchestrator for document processing."""
    
    def __init__(self, output_dir: str = "output", config: Dict = None):
        """Initialize the document processing pipeline."""
        self.output_dir = output_dir
        self.config = config or {}
        
        # Initialize processing components
        self.ocr = OCRProcessor(tesseract_path=self.config.get('tesseract_path'))
        self.llm = LLMParser(
            ollama_host=self.config.get('ollama_host', 'http://localhost:11434'),
            model=self.config.get('model', 'phi')
        )
        self.validator = DocumentValidator()
        self.crm = CRMSubmitter(output_dir)
        
        self.logger = logging.getLogger(__name__)
        
        # Setup logging if not already configured
        if not self.logger.handlers:
            self._setup_logging()
    
    def process_directory(self, input_dir: str, progress_callback=None) -> List[Dict]:
        """Process all documents in a directory."""
        if not os.path.exists(input_dir):
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        # Find all supported files
        supported_extensions = ('.pdf', '.png', '.jpg', '.jpeg')
        files = [
            os.path.join(input_dir, f) 
            for f in os.listdir(input_dir) 
            if f.lower().endswith(supported_extensions)
        ]
        
        if not files:
            self.logger.warning(f"No supported documents found in {input_dir}")
            return []
        
        self.logger.info(f"Found {len(files)} documents to process")
        
        processed_documents = []
        for i, file_path in enumerate(files):
            try:
                if progress_callback:
                    progress_callback(i, len(files), f"Processing {os.path.basename(file_path)}")
                
                result = self.process_single_document(file_path)
                processed_documents.append(result)
                
            except Exception as e:
                self.logger.error(f"Failed to process {file_path}: {str(e)}")
                # Add error document to results
                processed_documents.append({
                    "source_file": os.path.basename(file_path),
                    "error": str(e),
                    "processing_status": "failed",
                    "processing_timestamp": datetime.now().isoformat()
                })
        
        # Generate CSV summary
        try:
            csv_file = self.crm.generate_csv_summary(processed_documents)
            self.logger.info(f"Generated CSV summary: {csv_file}")
        except Exception as e:
            self.logger.error(f"Failed to generate CSV summary: {str(e)}")
        
        return processed_documents
    
    def process_single_document(self, file_path: str) -> Dict:
        """Process a single document through the complete pipeline."""
        filename = os.path.basename(file_path)
        start_time = datetime.now()
        
        self.logger.info(f"Starting processing for {filename}")
        
        try:
            # Step 1: OCR Processing
            self.logger.debug(f"Step 1: OCR extraction for {filename}")
            extracted_text = self.ocr.extract_text(file_path)
            
            if not extracted_text.strip():
                raise Exception("No text could be extracted from document")
            
            # Step 2: LLM Parsing
            self.logger.debug(f"Step 2: LLM parsing for {filename}")
            parsed_data = self.llm.parse_document(extracted_text, filename)
            
            # Step 3: Validation
            self.logger.debug(f"Step 3: Validation for {filename}")
            validated_data = self.validator.validate_document(parsed_data)
            
            # Step 4: CRM Submission Preparation
            self.logger.debug(f"Step 4: CRM submission for {filename}")
            submission_result = self.crm.submit_document(validated_data)
            
            # Combine results
            final_result = {
                **validated_data,
                "submission_result": submission_result,
                "processing_status": "completed",
                "processing_time_seconds": (datetime.now() - start_time).total_seconds()
            }
            
            self.logger.info(f"Successfully processed {filename} in {final_result['processing_time_seconds']:.2f} seconds")
            return final_result
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Failed to process {filename}: {error_msg}")
            
            return {
                "source_file": filename,
                "error": error_msg,
                "processing_status": "failed",
                "processing_timestamp": datetime.now().isoformat(),
                "processing_time_seconds": (datetime.now() - start_time).total_seconds()
            }
    
    def test_system_components(self) -> Dict:
        """Test all system components and return status."""
        results = {
            "ocr": {"status": "unknown", "details": ""},
            "llm": {"status": "unknown", "details": ""},
            "output_directory": {"status": "unknown", "details": ""}
        }
        
        # Test OCR
        try:
            if self.ocr.test_installation():
                results["ocr"] = {"status": "ok", "details": "Tesseract OCR is working"}
            else:
                results["ocr"] = {"status": "error", "details": "Tesseract OCR test failed"}
        except Exception as e:
            results["ocr"] = {"status": "error", "details": f"OCR error: {str(e)}"}
        
        # Test LLM
        try:
            if self.llm.test_connection():
                results["llm"] = {"status": "ok", "details": f"LLM connection successful ({self.llm.model})"}
            else:
                results["llm"] = {"status": "error", "details": "Cannot connect to LLM service"}
        except Exception as e:
            results["llm"] = {"status": "error", "details": f"LLM error: {str(e)}"}
        
        # Test output directory
        try:
            test_file = os.path.join(self.output_dir, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            results["output_directory"] = {"status": "ok", "details": f"Output directory writable: {self.output_dir}"}
        except Exception as e:
            results["output_directory"] = {"status": "error", "details": f"Output directory error: {str(e)}"}
        
        return results
    
    def get_processing_statistics(self, processed_documents: List[Dict]) -> Dict:
        """Generate processing statistics."""
        if not processed_documents:
            return {}
        
        total = len(processed_documents)
        successful = sum(1 for doc in processed_documents if doc.get('processing_status') == 'completed')
        failed = total - successful
        
        validation_stats = self.validator.get_validation_summary(
            [doc for doc in processed_documents if doc.get('processing_status') == 'completed']
        )
        
        submission_stats = self.crm.get_submission_stats()
        
        avg_processing_time = sum(
            doc.get('processing_time_seconds', 0) 
            for doc in processed_documents
        ) / total if total > 0 else 0
        
        return {
            "processing": {
                "total_documents": total,
                "successful": successful,
                "failed": failed,
                "success_rate": successful / total if total > 0 else 0,
                "average_processing_time": avg_processing_time
            },
            "validation": validation_stats,
            "submission": submission_stats
        }
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_dir = os.path.join(self.output_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        file_handler = logging.FileHandler(
            os.path.join(log_dir, f"pipeline_{datetime.now().strftime('%Y%m%d')}.log")
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        # Configure logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.DEBUG)
    
    def update_config(self, new_config: Dict):
        """Update pipeline configuration and reinitialize components."""
        self.config.update(new_config)
        
        # Reinitialize components with new config
        if 'tesseract_path' in new_config:
            self.ocr = OCRProcessor(tesseract_path=new_config['tesseract_path'])
        
        if 'ollama_host' in new_config or 'model' in new_config:
            self.llm = LLMParser(
                ollama_host=self.config.get('ollama_host', 'http://localhost:11434'),
                model=self.config.get('model', 'phi')
            )