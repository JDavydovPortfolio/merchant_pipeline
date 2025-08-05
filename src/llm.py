#!/usr/bin/env python3
"""
LLM Integration Module
Handles document parsing using local LLMs via transformers
"""

import logging
import re
from pathlib import Path
from typing import Dict, Any, List
import torch
from transformers import pipeline

logger = logging.getLogger(__name__)

class LLMParser:
    import torch
    from transformers import pipeline
    
    class LLMParser:
        def __init__(self, model_name: str = "microsoft/phi-2", ollama_host: str = "http://localhost:11434", model: str = None):
            try:
                if model and not model_name:
                    model_name = model
                    
                self.model = model_name
                self.ollama_host = ollama_host
                
                if ollama_host and model_name in ["llama", "phi", "mistral"]:
                    logger.info(f"Using Ollama model {model_name} at {ollama_host}")
                    # For Ollama models, we would configure differently
                    # This is a placeholder for Ollama integration
                
                self.generator = pipeline(
                    "text-generation",
                    model=model_name,
                    device="cuda" if torch.cuda.is_available() else "cpu"
                )
                logger.info(f"Initialized LLM with model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize LLM: {e}")
                raise

    def parse_document(self, text: str, filename: str = None) -> Dict[str, Any]:
        """
        Parse document text to extract structured information.

        Args:
            text: OCR-extracted text from document
            filename: Optional source filename for logging and context

        Returns:
            Dictionary containing extracted fields
        """
        try:
            # Split text into manageable chunks
            chunks = self._chunk_text(text)

            # Initialize structured data with the expected structure for validator and CRM
            structured_data = {
                "merchant_name": "",
                "ein_or_ssn": "",  # Changed from tax_id to match validator expectations
                "document_type": "application",  # Default document type
                "address": {  # Nested structure for address
                    "street": "",
                    "city": "",
                    "state": "",
                    "zip": ""
                },
                "contact_info": {  # Nested structure for contact info
                    "phone": "",
                    "email": ""
                },
                "business_info": {  # Nested structure for business info
                    "business_type": "",
                    "annual_revenue": "",
                    "years_in_business": "",
                    "processing_volume": ""
                },
                "requested_amount": "",
                "source_file": filename if filename else "unknown",
                "confidence_score": 0.7,  # Default confidence score
                "flagged_issues": []  # Initialize empty issues list
            }

            # Process top-level fields with specific prompts
            # Define which fields to process directly (not nested dictionaries)
            direct_fields = ["merchant_name", "ein_or_ssn", "document_type", "requested_amount"]
            
            # Process direct fields
            for field in direct_fields:
                prompt = self._get_field_prompt(field, chunks[0])  # Use first chunk for basic info
                response = self.generator(prompt, max_length=100, num_return_sequences=1)
                # Handle different response formats from transformers pipeline
                if isinstance(response, list) and len(response) > 0:
                    if isinstance(response[0], dict) and 'generated_text' in response[0]:
                        structured_data[field] = self._clean_response(response[0]['generated_text'])
                    else:
                        structured_data[field] = self._clean_response(str(response[0]))
                else:
                    structured_data[field] = ""
            
            # Process address fields
            address_fields = ["street", "city", "state", "zip"]
            for field in address_fields:
                prompt = self._get_field_prompt(f"address_{field}", chunks[0])
                response = self.generator(prompt, max_length=100, num_return_sequences=1)
                if isinstance(response, list) and len(response) > 0:
                    if isinstance(response[0], dict) and 'generated_text' in response[0]:
                        structured_data["address"][field] = self._clean_response(response[0]['generated_text'])
                    else:
                        structured_data["address"][field] = self._clean_response(str(response[0]))
            
            # Process contact fields
            contact_fields = ["phone", "email"]
            for field in contact_fields:
                prompt = self._get_field_prompt(f"contact_{field}", chunks[0])
                response = self.generator(prompt, max_length=100, num_return_sequences=1)
                if isinstance(response, list) and len(response) > 0:
                    if isinstance(response[0], dict) and 'generated_text' in response[0]:
                        structured_data["contact_info"][field] = self._clean_response(response[0]['generated_text'])
                    else:
                        structured_data["contact_info"][field] = self._clean_response(str(response[0]))
            
            # Process business info fields
            business_fields = ["business_type", "annual_revenue", "years_in_business", "processing_volume"]
            for field in business_fields:
                prompt = self._get_field_prompt(field, chunks[0])
                response = self.generator(prompt, max_length=100, num_return_sequences=1)
                if isinstance(response, list) and len(response) > 0:
                    if isinstance(response[0], dict) and 'generated_text' in response[0]:
                        structured_data["business_info"][field] = self._clean_response(response[0]['generated_text'])
                    else:
                        structured_data["business_info"][field] = self._clean_response(str(response[0]))

            logger.info("Successfully parsed document")
            return structured_data

        except Exception as e:
            logger.error(f"Error parsing document: {e}")
            raise

    def _chunk_text(self, text: str, max_length: int = 512) -> List[str]:
        """Split text into manageable chunks."""
        # Use simple paragraph-based splitting
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_length = 0

        for para in paragraphs:
            para_length = len(para.split())
            if current_length + para_length > max_length:
                chunks.append(' '.join(current_chunk))
                current_chunk = [para]
                current_length = para_length
            else:
                current_chunk.append(para)
                current_length += para_length

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def _get_field_prompt(self, field: str, text: str) -> str:
        """Generate appropriate prompt for each field."""
        prompts = {
            # Direct fields
            "merchant_name": f"Extract the merchant or business name from this text: {text}",
            "ein_or_ssn": f"Find the tax ID, EIN number, or SSN from this text: {text}",
            "document_type": f"What type of document is this (application, statement, invoice, etc.): {text}",
            "requested_amount": f"Extract the requested loan or funding amount from this text: {text}",
            
            # Address fields
            "address_street": f"Extract only the street address (no city/state/zip) from this text: {text}",
            "address_city": f"Extract only the city name from this address information: {text}",
            "address_state": f"Extract only the state (2-letter abbreviation preferred) from this address: {text}",
            "address_zip": f"Extract only the ZIP code from this address: {text}",
            
            # Contact fields
            "contact_phone": f"Find the phone number from this text: {text}",
            "contact_email": f"Find the email address from this text: {text}",
            
            # Business info fields
            "business_type": f"What type of business is described in this text: {text}",
            "annual_revenue": f"Extract the annual revenue amount from this text: {text}",
            "years_in_business": f"How many years has this business been operating according to the text: {text}",
            "processing_volume": f"Find the credit card processing volume from this text: {text}"
        }
        return prompts.get(field, f"Extract the {field.replace('_', ' ')} from this text: {text}")

    def _clean_response(self, text: str) -> str:
        """Clean up model response to extract relevant information."""
        # Remove the original prompt if present
        if ":" in text:
            text = text.split(":")[-1]

        # Clean up whitespace and special characters
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)

        return text
        
    def test_connection(self) -> bool:
        """Test if the LLM is properly initialized and working."""
        try:
            # Try a simple generation to test the model
            test_prompt = "Hello, this is a test."
            response = self.generator(test_prompt, max_length=20, num_return_sequences=1)
            
            # If we get here without an exception, the model is working
            logger.info(f"LLM connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"LLM connection test failed: {e}")
            return False
