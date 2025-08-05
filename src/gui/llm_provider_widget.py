#!/usr/bin/env python3
"""
LLM Provider Selection Widget
Provides a dropdown for selecting LLM providers with auto-detection
"""

import sys
import os
from typing import Dict, List, Optional, Callable
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import qtawesome as qta

try:
    from src.llm_detector import LLMProviderDetector
except ImportError:
    # Fallback for relative imports
    from ..llm_detector import LLMProviderDetector

class LLMProviderWidget(QWidget):
    """Widget for selecting and configuring LLM providers."""
    
    provider_changed = Signal(str, str)  # provider_id, model_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.detector = LLMProviderDetector()
        self.current_provider = None
        self.current_model = None
        self.setup_ui()
        self.detect_providers()
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel("🤖 LLM Provider Selection")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Auto-detection status
        self.status_label = QLabel("🔍 Detecting available providers...")
        self.status_label.setStyleSheet("color: #0078d4; font-size: 12px;")
        layout.addWidget(self.status_label)
        
        # Provider selection group
        provider_group = QGroupBox("Provider Settings")
        provider_layout = QVBoxLayout(provider_group)
        
        # Provider dropdown
        provider_layout.addWidget(QLabel("LLM Provider:"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItem("🔄 Auto-detect", "auto")
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        provider_layout.addWidget(self.provider_combo)
        
        # Model dropdown
        provider_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItem("Select a provider first", "")
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        provider_layout.addWidget(self.model_combo)
        
        # Provider status display
        self.provider_status = QTextEdit()
        self.provider_status.setMaximumHeight(120)
        self.provider_status.setReadOnly(True)
        self.provider_status.setPlaceholderText("Provider status will appear here...")
        provider_layout.addWidget(self.provider_status)
        
        layout.addWidget(provider_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Refresh Detection")
        self.refresh_btn.setIcon(qta.icon('fa5s.sync', color='white'))
        self.refresh_btn.clicked.connect(self.detect_providers)
        button_layout.addWidget(self.refresh_btn)
        
        self.test_btn = QPushButton("🧪 Test Connection")
        self.test_btn.setIcon(qta.icon('fa5s.check-circle', color='white'))
        self.test_btn.clicked.connect(self.test_connection)
        self.test_btn.setEnabled(False)
        button_layout.addWidget(self.test_btn)
        
        self.help_btn = QPushButton("❓ Help")
        self.help_btn.setIcon(qta.icon('fa5s.question-circle', color='white'))
        self.help_btn.clicked.connect(self.show_help)
        button_layout.addWidget(self.help_btn)
        
        layout.addLayout(button_layout)
        
        # Progress bar for detection
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
    
    def detect_providers(self):
        """Detect available LLM providers."""
        self.status_label.setText("🔍 Detecting available providers...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.refresh_btn.setEnabled(False)
        
        # Run detection in background
        QTimer.singleShot(100, self._run_detection)
    
    def _run_detection(self):
        """Run provider detection in background."""
        try:
            # Detect providers
            detected = self.detector.detect_all_providers()
            
            # Get models for each detected provider
            for provider_id in detected:
                models = self.detector.get_available_models(provider_id)
                self.detector.available_models[provider_id] = models
            
            # Update UI on main thread
            QTimer.singleShot(0, lambda: self._update_ui_after_detection(detected))
            
        except Exception as e:
            QTimer.singleShot(0, lambda: self._detection_error(str(e)))
    
    def _update_ui_after_detection(self, detected_providers):
        """Update UI after provider detection."""
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
        
        # Update provider combo
        self.provider_combo.clear()
        self.provider_combo.addItem("🔄 Auto-detect", "auto")
        
        if detected_providers:
            # Add detected providers
            for provider_id, provider_info in detected_providers.items():
                icon = provider_info.get('icon', '🤖')
                name = provider_info.get('name', provider_id)
                models = self.detector.available_models.get(provider_id, [])
                model_count = len(models)
                
                display_text = f"{icon} {name} ({model_count} models)"
                self.provider_combo.addItem(display_text, provider_id)
            
            # Auto-select the recommended provider
            recommended = self.detector.get_recommended_provider()
            if recommended:
                for i in range(self.provider_combo.count()):
                    if self.provider_combo.itemData(i) == recommended:
                        self.provider_combo.setCurrentIndex(i)
                        break
            
            self.status_label.setText(f"✅ Detected {len(detected_providers)} provider(s)")
            self.test_btn.setEnabled(True)
        else:
            self.status_label.setText("❌ No providers detected")
            self.test_btn.setEnabled(False)
        
        # Update status display
        self._update_status_display()
    
    def _detection_error(self, error_message):
        """Handle detection error."""
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
        self.status_label.setText(f"❌ Detection failed: {error_message}")
        self.test_btn.setEnabled(False)
    
    def _update_status_display(self):
        """Update the provider status display."""
        status_text = ""
        provider_status = self.detector.get_provider_status()
        
        for provider_id, status in provider_status.items():
            icon = status['icon']
            name = status['name']
            available = status['available']
            model_count = status['model_count']
            host = status['host']
            
            if available:
                status_text += f"{icon} <b>{name}</b> ✅ Available\n"
                status_text += f"   Host: {host}\n"
                status_text += f"   Models: {model_count}\n"
                
                if status['models']:
                    status_text += f"   Available models: {', '.join(status['models'][:3])}"
                    if len(status['models']) > 3:
                        status_text += f" (+{len(status['models']) - 3} more)"
                    status_text += "\n"
            else:
                status_text += f"{icon} <b>{name}</b> ❌ Not available\n"
                status_text += f"   Expected host: {host}\n"
            
            status_text += "\n"
        
        self.provider_status.setHtml(status_text)
    
    def on_provider_changed(self, text):
        """Handle provider selection change."""
        provider_id = self.provider_combo.currentData()
        
        # Update model dropdown
        self.model_combo.clear()
        
        if provider_id == "auto":
            # Auto-detect mode - use recommended provider
            recommended = self.detector.get_recommended_provider()
            if recommended:
                models = self.detector.available_models.get(recommended, [])
                for model in models:
                    self.model_combo.addItem(model)
                if models:
                    self.model_combo.setCurrentText(models[0])
                    self.current_provider = recommended
                    self.current_model = models[0]
        elif provider_id in self.detector.detected_providers:
            # Specific provider selected
            models = self.detector.available_models.get(provider_id, [])
            for model in models:
                self.model_combo.addItem(model)
            if models:
                self.model_combo.setCurrentText(models[0])
                self.current_provider = provider_id
                self.current_model = models[0]
        else:
            self.model_combo.addItem("No models available")
            self.current_provider = None
            self.current_model = None
        
        # Enable/disable test button
        self.test_btn.setEnabled(self.current_provider is not None)
        
        # Emit signal
        if self.current_provider and self.current_model:
            self.provider_changed.emit(self.current_provider, self.current_model)
    
    def on_model_changed(self, model_name):
        """Handle model selection change."""
        if model_name and self.current_provider:
            self.current_model = model_name
            self.provider_changed.emit(self.current_provider, self.current_model)
    
    def test_connection(self):
        """Test the current provider and model connection."""
        if not self.current_provider or not self.current_model:
            QMessageBox.warning(self, "Warning", "Please select a provider and model first.")
            return
        
        try:
            # Test the connection
            success = self.detector.test_model_connection(self.current_provider, self.current_model)
            
            if success:
                QMessageBox.information(
                    self,
                    "Connection Test",
                    f"✅ Connection successful!\n\nProvider: {self.detector.providers[self.current_provider]['name']}\nModel: {self.current_model}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Connection Test",
                    f"❌ Connection failed!\n\nProvider: {self.detector.providers[self.current_provider]['name']}\nModel: {self.current_model}\n\nPlease check if the provider is running and the model is loaded."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Connection Test Error",
                f"Error testing connection:\n{str(e)}"
            )
    
    def show_help(self):
        """Show help dialog with installation instructions."""
        dialog = QDialog(self)
        dialog.setWindowTitle("LLM Provider Help")
        dialog.setModal(True)
        dialog.resize(600, 500)
        
        layout = QVBoxLayout(dialog)
        
        # Help text
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <h2>🤖 LLM Provider Setup Guide</h2>
        
        <h3>Supported Providers:</h3>
        <ul>
        <li><b>🐙 Ollama</b> - Easy to use, great for beginners</li>
        <li><b>🎯 LM Studio</b> - GUI-based, user-friendly</li>
        <li><b>🚀 LM Studio CI</b> - Command-line version of LM Studio</li>
        <li><b>🦙 llama.cpp</b> - High-performance, advanced users</li>
        </ul>
        
        <h3>Quick Setup:</h3>
        <ol>
        <li>Choose your preferred provider from the list above</li>
        <li>Follow the installation instructions for your chosen provider</li>
        <li>Download and load a model (recommended: gemma3n:e2b)</li>
        <li>Start the provider's server</li>
        <li>Click "Refresh Detection" in this dialog</li>
        <li>Select your provider and model from the dropdowns</li>
        <li>Test the connection</li>
        </ol>
        
        <h3>Installation Instructions:</h3>
        """)
        
        # Add provider-specific instructions
        for provider_id, provider_info in self.detector.providers.items():
            instructions = self.detector.get_installation_instructions(provider_id)
            help_text.append(f"<h4>{provider_info['icon']} {provider_info['name']}:</h4>")
            help_text.append(f"<pre>{instructions}</pre>")
        
        help_text.append("""
        <h3>Tips:</h3>
        <ul>
        <li>Make sure your firewall allows connections to the provider's port</li>
        <li>Some models require significant RAM (8GB+ recommended)</li>
        <li>GPU acceleration can significantly improve performance</li>
        <li>Start with smaller models (2B-7B parameters) for testing</li>
        </ul>
        """)
        
        layout.addWidget(help_text)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def get_current_config(self) -> Dict:
        """Get the current provider configuration."""
        if self.current_provider and self.current_model:
            return self.detector.create_config_for_provider(self.current_provider, self.current_model)
        return {}
    
    def save_config(self, config_path: str = "config.yaml") -> bool:
        """Save the current configuration to file."""
        config = self.get_current_config()
        if config:
            return self.detector.save_config(config, config_path)
        return False
    
    def get_selected_provider(self) -> Optional[str]:
        """Get the currently selected provider ID."""
        return self.current_provider
    
    def get_selected_model(self) -> Optional[str]:
        """Get the currently selected model name."""
        return self.current_model 