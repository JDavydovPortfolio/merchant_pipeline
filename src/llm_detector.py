#!/usr/bin/env python3
"""
LLM Provider Detection and Management
Automatically detects available LLM providers and manages connections
"""

import logging
import requests
import json
import yaml
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import subprocess
import time

logger = logging.getLogger(__name__)

class LLMProviderDetector:
    """Detects and manages different LLM providers."""
    
    def __init__(self):
        self.providers = {
            'ollama': {
                'name': 'Ollama',
                'default_host': 'http://localhost:11434',
                'test_endpoint': '/api/tags',
                'models_endpoint': '/api/tags',
                'generate_endpoint': '/api/generate',
                'icon': '🐙'
            },
            'lm_studio': {
                'name': 'LM Studio',
                'default_host': 'http://localhost:1234',
                'test_endpoint': '/v1/models',
                'models_endpoint': '/v1/models',
                'generate_endpoint': '/v1/chat/completions',
                'icon': '🎯'
            },
            'lm_studio_ci': {
                'name': 'LM Studio CI',
                'default_host': 'http://localhost:1234',
                'test_endpoint': '/v1/models',
                'models_endpoint': '/v1/models',
                'generate_endpoint': '/v1/chat/completions',
                'icon': '🚀'
            },
            'llama_cpp': {
                'name': 'llama.cpp',
                'default_host': 'http://localhost:8080',
                'test_endpoint': '/v1/models',
                'models_endpoint': '/v1/models',
                'generate_endpoint': '/v1/chat/completions',
                'icon': '🦙'
            }
        }
        
        self.detected_providers = {}
        self.available_models = {}
    
    def detect_all_providers(self) -> Dict[str, Dict]:
        """Detect all available LLM providers."""
        logger.info("Detecting available LLM providers...")
        
        self.detected_providers = {}
        
        for provider_id, provider_info in self.providers.items():
            if self._test_provider_connection(provider_id, provider_info):
                self.detected_providers[provider_id] = provider_info
                logger.info(f"✅ Detected {provider_info['name']}")
            else:
                logger.info(f"❌ {provider_info['name']} not available")
        
        return self.detected_providers
    
    def _test_provider_connection(self, provider_id: str, provider_info: Dict) -> bool:
        """Test if a specific provider is available."""
        try:
            host = provider_info['default_host']
            endpoint = provider_info['test_endpoint']
            
            response = requests.get(f"{host}{endpoint}", timeout=5)
            
            if response.status_code == 200:
                # Store additional info about the provider
                provider_info['host'] = host
                provider_info['status'] = 'available'
                return True
            else:
                logger.debug(f"{provider_info['name']} returned status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.debug(f"{provider_info['name']} connection failed: {e}")
            return False
        except Exception as e:
            logger.debug(f"Error testing {provider_info['name']}: {e}")
            return False
    
    def get_available_models(self, provider_id: str) -> List[str]:
        """Get available models for a specific provider."""
        if provider_id not in self.detected_providers:
            return []
        
        try:
            provider_info = self.detected_providers[provider_id]
            host = provider_info['host']
            endpoint = provider_info['models_endpoint']
            
            response = requests.get(f"{host}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                models = []
                data = response.json()
                
                if provider_id == 'ollama':
                    # Ollama format
                    for model in data.get('models', []):
                        models.append(model['name'])
                elif provider_id in ['lm_studio', 'lm_studio_ci', 'llama_cpp']:
                    # OpenAI-compatible format
                    for model in data.get('data', []):
                        models.append(model['id'])
                
                self.available_models[provider_id] = models
                return models
            else:
                logger.warning(f"Failed to get models for {provider_info['name']}: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting models for {provider_id}: {e}")
            return []
    
    def test_model_connection(self, provider_id: str, model_name: str) -> bool:
        """Test if a specific model is available and working."""
        if provider_id not in self.detected_providers:
            return False
        
        try:
            provider_info = self.detected_providers[provider_id]
            host = provider_info['host']
            endpoint = provider_info['generate_endpoint']
            
            # Create a simple test prompt
            if provider_id == 'ollama':
                payload = {
                    "model": model_name,
                    "prompt": "Hello",
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 10
                    }
                }
            else:
                # OpenAI-compatible format
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": "Hello"}],
                    "temperature": 0.7,
                    "max_tokens": 10,
                    "stream": False
                }
            
            response = requests.post(
                f"{host}{endpoint}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error testing model {model_name} on {provider_id}: {e}")
            return False
    
    def get_provider_status(self) -> Dict[str, Dict]:
        """Get detailed status of all providers."""
        status = {}
        
        for provider_id, provider_info in self.providers.items():
            is_available = provider_id in self.detected_providers
            models = self.available_models.get(provider_id, [])
            
            status[provider_id] = {
                'name': provider_info['name'],
                'icon': provider_info['icon'],
                'available': is_available,
                'host': provider_info['default_host'],
                'model_count': len(models),
                'models': models
            }
        
        return status
    
    def get_recommended_provider(self) -> Optional[str]:
        """Get the recommended provider based on availability and model count."""
        if not self.detected_providers:
            return None
        
        # Prefer providers with more models
        best_provider = None
        max_models = 0
        
        for provider_id in self.detected_providers:
            models = self.available_models.get(provider_id, [])
            if len(models) > max_models:
                max_models = len(models)
                best_provider = provider_id
        
        return best_provider
    
    def create_config_for_provider(self, provider_id: str, model_name: str = None) -> Dict:
        """Create a configuration dictionary for a specific provider."""
        if provider_id not in self.detected_providers:
            raise ValueError(f"Provider {provider_id} not available")
        
        provider_info = self.detected_providers[provider_id]
        
        # If no model specified, use the first available one
        if not model_name:
            models = self.available_models.get(provider_id, [])
            if models:
                model_name = models[0]
            else:
                raise ValueError(f"No models available for {provider_id}")
        
        config = {
            'llm': {
                'provider': provider_id,
                provider_id: {
                    'host': provider_info['host'],
                    'model': model_name,
                    'temperature': 0.7,
                    'max_tokens': 1000
                }
            }
        }
        
        return config
    
    def save_config(self, config: Dict, config_path: str = "config.yaml"):
        """Save configuration to file."""
        try:
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            logger.info(f"Configuration saved to {config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def load_config(self, config_path: str = "config.yaml") -> Dict:
        """Load configuration from file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config or {}
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return {}
    
    def get_installation_instructions(self, provider_id: str) -> str:
        """Get installation instructions for a specific provider."""
        instructions = {
            'ollama': """
1. Download Ollama from https://ollama.ai/
2. Install and start Ollama
3. Pull a model: ollama pull gemma3n:e2b
4. Ollama will run on http://localhost:11434
            """,
            'lm_studio': """
1. Download LM Studio from https://lmstudio.ai/
2. Install and launch LM Studio
3. Download a model (search for "gemma3n:e2b")
4. Go to "Local Server" tab and click "Start Server"
5. Server will run on http://localhost:1234
            """,
            'lm_studio_ci': """
1. Install LM Studio CI (command line version)
2. Download a model using LM Studio CI commands
3. Start the server: lmstudio serve
4. Server will run on http://localhost:1234
            """,
            'llama_cpp': """
1. Install llama.cpp server
2. Download a model and start the server
3. Server will run on http://localhost:8080
4. Configure with appropriate model path
            """
        }
        
        return instructions.get(provider_id, "Installation instructions not available.")
    
    def get_provider_info(self, provider_id: str) -> Dict:
        """Get detailed information about a provider."""
        if provider_id in self.providers:
            info = self.providers[provider_id].copy()
            info['available'] = provider_id in self.detected_providers
            info['models'] = self.available_models.get(provider_id, [])
            info['installation_instructions'] = self.get_installation_instructions(provider_id)
            return info
        else:
            return {} 