#!/usr/bin/env python3
"""
Test script to verify that all modules can be imported without errors.
This helps check for syntax errors and import issues.
"""

import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test importing all key modules."""
    try:
        logger.info("Testing OCR module import...")
        from ocr import OCRProcessor
        logger.info("OCR module imported successfully")
        
        logger.info("Testing LLM module import...")
        from llm import LLMParser
        logger.info("LLM module imported successfully")
        
        logger.info("Testing validator module import...")
        from validator import DocumentValidator
        logger.info("Validator module imported successfully")
        
        logger.info("Testing CRM module import...")
        from crm_submit import CRMSubmitter
        logger.info("CRM module imported successfully")
        
        logger.info("Testing pipeline module import...")
        from pipeline import DocumentPipeline
        logger.info("Pipeline module imported successfully")
        
        logger.info("Testing GUI module import...")
        from gui.premium_gui import PremiumDocumentProcessor
        logger.info("GUI module imported successfully")
        
        logger.info("All modules imported successfully!")
        return True
    except Exception as e:
        logger.error(f"Import error: {e}")
        return False

def test_class_instantiation():
    """Test instantiating key classes."""
    try:
        logger.info("Testing OCRProcessor instantiation...")
        from ocr import OCRProcessor
        ocr = OCRProcessor()
        logger.info("OCRProcessor instantiated successfully")
        
        logger.info("Testing DocumentValidator instantiation...")
        from validator import DocumentValidator
        validator = DocumentValidator()
        logger.info("DocumentValidator instantiated successfully")
        
        logger.info("Testing CRMSubmitter instantiation...")
        from crm_submit import CRMSubmitter
        crm = CRMSubmitter()
        logger.info("CRMSubmitter instantiated successfully")
        
        # Skip LLMParser and DocumentPipeline as they require model downloads
        
        logger.info("Class instantiation tests completed successfully!")
        return True
    except Exception as e:
        logger.error(f"Instantiation error: {e}")
        return False

if __name__ == "__main__":
    print("Testing module imports...")
    import_success = test_imports()
    
    if import_success:
        print("Testing class instantiation...")
        instantiation_success = test_class_instantiation()
    
    if import_success and instantiation_success:
        print("All tests passed! The code should be free of syntax and import errors.")
    else:
        print("Tests failed. Please check the logs for details.")