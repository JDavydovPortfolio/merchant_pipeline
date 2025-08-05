import sys
import os
import logging
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import qtawesome as qta
import qdarkstyle

# Import processing modules
from src.pipeline import DocumentPipeline

class DocumentProcessorWorker(QThread):
    """Worker thread for document processing to keep UI responsive."""
    
    progress_updated = Signal(int, int, str)  # current, total, message
    document_processed = Signal(dict)  # processed document data
    processing_completed = Signal(list)  # all processed documents
    error_occurred = Signal(str)  # error message
    
    def __init__(self, pipeline: DocumentPipeline, files: List[str]):
        super().__init__()
        self.pipeline = pipeline
        self.files = files
        self.processed_documents = []
    
    def run(self):
        """Process documents in background thread."""
        try:
            for i, file_path in enumerate(self.files):
                self.progress_updated.emit(i, len(self.files), f"Processing {os.path.basename(file_path)}")
                
                result = self.pipeline.process_single_document(file_path)
                self.processed_documents.append(result)
                self.document_processed.emit(result)
                
                # Check if thread should stop
                if self.isInterruptionRequested():
                    break
            
            self.processing_completed.emit(self.processed_documents)
            
        except Exception as e:
            self.error_occurred.emit(str(e))

class DropArea(QLabel):
    """Custom drop area widget for file uploads."""
    
    files_dropped = Signal(list)
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(150)
        self.setText("📄 Drag & Drop Documents Here\n\nSupported: PDF, PNG, JPG, JPEG")
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #0078d4;
                border-radius: 10px;
                padding: 20px;
                font-size: 14px;
                background-color: rgba(0, 120, 212, 0.1);
                color: #0078d4;
            }
            QLabel:hover {
                background-color: rgba(0, 120, 212, 0.2);
            }
        """)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QLabel {
                    border: 2px solid #0078d4;
                    border-radius: 10px;
                    padding: 20px;
                    font-size: 14px;
                    background-color: rgba(0, 120, 212, 0.3);
                    color: #0078d4;
                }
            """)
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #0078d4;
                border-radius: 10px;
                padding: 20px;
                font-size: 14px;
                background-color: rgba(0, 120, 212, 0.1);
                color: #0078d4;
            }
        """)
    
    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
                files.append(file_path)
        
        if files:
            self.files_dropped.emit(files)
            self.setText(f"✅ {len(files)} file(s) selected")
        else:
            self.setText("❌ No supported files found")
        
        self.dragLeaveEvent(event)

class PremiumDocumentProcessor(QMainWindow):
    """Main application window with premium GUI."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Merchant Document Processing Suite")
        self.setMinimumSize(1400, 900)
        self.setWindowIcon(qta.icon('fa5s.file-invoice-dollar', color='white'))
        
        # Initialize variables
        self.selected_files = []
        self.processed_documents = []
        self.worker_thread = None
        
        # Initialize processing pipeline
        self.setup_pipeline()
        self.setup_ui()
        self.setup_connections()
        self.setup_menu_bar()
        
        # Test system components on startup
        QTimer.singleShot(1000, self.test_system_components)
    
    def setup_pipeline(self):
        """Initialize the document processing pipeline."""
        try:
            config = {
                'ollama_host': 'http://localhost:11434',
                'model': 'phi',
                'tesseract_path': None  # Auto-detect
            }
            self.pipeline = DocumentPipeline(output_dir="output", config=config)
        except Exception as e:
            QMessageBox.critical(self, "Initialization Error", 
                               f"Failed to initialize processing pipeline:\n{str(e)}")
    
    def setup_ui(self):
        """Setup the main user interface."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(20)
        
        # Left panel - Controls
        left_panel = self.create_control_panel()
        main_layout.addWidget(left_panel, 1)
        
        # Right panel - Results
        right_panel = self.create_results_panel()
        main_layout.addWidget(right_panel, 2)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready to process documents")
        
        # Progress bar in status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(300)
        self.status_bar.addPermanentWidget(self.progress_bar)
    
    def create_control_panel(self):
        """Create the left control panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # File selection group
        file_group = QGroupBox("📁 Document Upload")
        file_layout = QVBoxLayout(file_group)
        
        # Drop area
        self.drop_area = DropArea()
        file_layout.addWidget(self.drop_area)
        
        # Browse button
        browse_btn = QPushButton("📂 Browse Files")
        browse_btn.setIcon(qta.icon('fa5s.folder-open', color='white'))
        browse_btn.clicked.connect(self.browse_files)
        file_layout.addWidget(browse_btn)
        
        # Clear button
        clear_btn = QPushButton("🗑️ Clear Selection")
        clear_btn.setIcon(qta.icon('fa5s.trash', color='white'))
        clear_btn.clicked.connect(self.clear_selection)
        file_layout.addWidget(clear_btn)
        
        layout.addWidget(file_group)
        
        # Processing group
        process_group = QGroupBox("⚙️ Processing")
        process_layout = QVBoxLayout(process_group)
        
        # Process button
        self.process_btn = QPushButton("🚀 Process Documents")
        self.process_btn.setIcon(qta.icon('fa5s.play', color='white'))
        self.process_btn.setEnabled(False)
        self.process_btn.clicked.connect(self.process_documents)
        process_layout.addWidget(self.process_btn)
        
        # Stop button
        self.stop_btn = QPushButton("⏹️ Stop Processing")
        self.stop_btn.setIcon(qta.icon('fa5s.stop', color='white'))
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_processing)
        process_layout.addWidget(self.stop_btn)
        
        layout.addWidget(process_group)
        
        # Export group
        export_group = QGroupBox("📤 Export")
        export_layout = QVBoxLayout(export_group)
        
        # Export CSV button
        self.export_csv_btn = QPushButton("📊 Export CSV Summary")
        self.export_csv_btn.setIcon(qta.icon('fa5s.file-csv', color='white'))
        self.export_csv_btn.setEnabled(False)
        self.export_csv_btn.clicked.connect(self.export_csv)
        export_layout.addWidget(self.export_csv_btn)
        
        # Open output folder button
        self.open_folder_btn = QPushButton("📁 Open Output Folder")
        self.open_folder_btn.setIcon(qta.icon('fa5s.external-link-alt', color='white'))
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        export_layout.addWidget(self.open_folder_btn)
        
        layout.addWidget(export_group)
        
        # System status group
        status_group = QGroupBox("🔧 System Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        status_layout.addWidget(self.status_text)
        
        test_btn = QPushButton("🧪 Test System")
        test_btn.setIcon(qta.icon('fa5s.check-circle', color='white'))
        test_btn.clicked.connect(self.test_system_components)
        status_layout.addWidget(test_btn)
        
        layout.addWidget(status_group)
        
        layout.addStretch()
        return widget
    
    def create_results_panel(self):
        """Create the right results panel."""
        self.tab_widget = QTabWidget()
        
        # OCR Preview tab
        self.ocr_preview = QTextEdit()
        self.ocr_preview.setReadOnly(True)
        self.ocr_preview.setPlaceholderText("OCR extracted text will appear here...")
        self.tab_widget.addTab(self.ocr_preview, "📄 OCR Preview")
        
        # Parsed Data tab
        self.data_tree = QTreeWidget()
        self.data_tree.setHeaderLabels(["Field", "Value", "Status"])
        self.data_tree.setAlternatingRowColors(True)
        self.tab_widget.addTab(self.data_tree, "🏢 Extracted Data")
        
        # Validation Results tab
        self.validation_list = QListWidget()
        self.tab_widget.addTab(self.validation_list, "✅ Validation Results")
        
        # Processing Log tab
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.tab_widget.addTab(self.log_text, "📋 Processing Log")
        
        return self.tab_widget
    
    def setup_connections(self):
        """Setup signal connections."""
        self.drop_area.files_dropped.connect(self.files_selected)
    
    def setup_menu_bar(self):
        """Setup application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        open_action = QAction(qta.icon('fa5s.folder-open'), 'Open Files', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.browse_files)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(qta.icon('fa5s.times'), 'Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings menu
        settings_menu = menubar.addMenu('Settings')
        
        config_action = QAction(qta.icon('fa5s.cog'), 'Configuration', self)
        config_action.triggered.connect(self.show_configuration)
        settings_menu.addAction(config_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction(qta.icon('fa5s.info-circle'), 'About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def browse_files(self):
        """Open file browser dialog."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Documents",
            "",
            "Documents (*.pdf *.png *.jpg *.jpeg);;PDF Files (*.pdf);;Image Files (*.png *.jpg *.jpeg)"
        )
        
        if files:
            self.files_selected(files)
    
    def files_selected(self, files: List[str]):
        """Handle file selection."""
        self.selected_files = files
        self.process_btn.setEnabled(True)
        self.drop_area.setText(f"✅ {len(files)} file(s) selected")
        
        # Clear previous results
        self.clear_results()
        
        # Update status
        self.status_bar.showMessage(f"{len(files)} files selected")
        self.log_message(f"Selected {len(files)} files for processing")
    
    def clear_selection(self):
        """Clear file selection."""
        self.selected_files = []
        self.process_btn.setEnabled(False)
        self.export_csv_btn.setEnabled(False)
        self.drop_area.setText("📄 Drag & Drop Documents Here\n\nSupported: PDF, PNG, JPG, JPEG")
        self.clear_results()
        self.status_bar.showMessage("Ready to process documents")
    
    def clear_results(self):
        """Clear all result displays."""
        self.ocr_preview.clear()
        self.data_tree.clear()
        self.validation_list.clear()
        self.processed_documents = []
    
    def process_documents(self):
        """Start document processing in background thread."""
        if not self.selected_files:
            QMessageBox.warning(self, "Warning", "Please select documents first")
            return
        
        # Setup UI for processing
        self.process_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.selected_files))
        self.progress_bar.setValue(0)
        
        # Clear previous results
        self.clear_results()
        
        # Start worker thread
        self.worker_thread = DocumentProcessorWorker(self.pipeline, self.selected_files)
        self.worker_thread.progress_updated.connect(self.update_progress)
        self.worker_thread.document_processed.connect(self.document_processed)
        self.worker_thread.processing_completed.connect(self.processing_completed)
        self.worker_thread.error_occurred.connect(self.processing_error)
        self.worker_thread.start()
        
        self.log_message(f"Started processing {len(self.selected_files)} documents")
    
    def stop_processing(self):
        """Stop document processing."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.requestInterruption()
            self.worker_thread.wait(3000)  # Wait up to 3 seconds
            
            self.process_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.progress_bar.setVisible(False)
            
            self.status_bar.showMessage("Processing stopped")
            self.log_message("Processing stopped by user")
    
    def update_progress(self, current: int, total: int, message: str):
        """Update progress bar and status."""
        self.progress_bar.setValue(current)
        self.status_bar.showMessage(f"{message} ({current}/{total})")
    
    def document_processed(self, result: Dict):
        """Handle individual document processing completion."""
        filename = result.get('source_file', 'Unknown')
        status = result.get('processing_status', 'unknown')
        
        if status == 'completed':
            self.log_message(f"✅ Completed: {filename}")
            # Update UI with latest result
            self.update_results_display(result)
        else:
            error = result.get('error', 'Unknown error')
            self.log_message(f"❌ Failed: {filename} - {error}")
    
    def processing_completed(self, processed_documents: List[Dict]):
        """Handle completion of all document processing."""
        self.processed_documents = processed_documents
        
        # Update UI
        self.process_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.export_csv_btn.setEnabled(True)
        
        # Show completion statistics
        successful = sum(1 for doc in processed_documents if doc.get('processing_status') == 'completed')
        failed = len(processed_documents) - successful
        
        self.status_bar.showMessage(f"Processing completed: {successful} successful, {failed} failed")
        self.log_message(f"Processing completed: {successful} successful, {failed} failed")
        
        # Show summary dialog
        QMessageBox.information(
            self,
            "Processing Complete",
            f"Processed {len(processed_documents)} documents\n\n"
            f"✅ Successful: {successful}\n"
            f"❌ Failed: {failed}\n\n"
            f"Results saved to output folder."
        )
    
    def processing_error(self, error_message: str):
        """Handle processing errors."""
        self.process_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        self.status_bar.showMessage("Processing failed")
        self.log_message(f"❌ Processing error: {error_message}")
        
        QMessageBox.critical(self, "Processing Error", f"Processing failed:\n{error_message}")
    
    def update_results_display(self, result: Dict):
        """Update the results display with processed document data."""
        # Update OCR preview
        extracted_text = result.get('extracted_text', '')
        self.ocr_preview.setText(extracted_text)
        
        # Update data tree
        self.data_tree.clear()
        
        # Add merchant information
        merchant_item = QTreeWidgetItem(["Merchant Information", "", ""])
        self.data_tree.addTopLevelItem(merchant_item)
        
        merchant_name = result.get('merchant_name', '')
        name_item = QTreeWidgetItem(["Name", merchant_name, "✓" if merchant_name else "❌"])
        merchant_item.addChild(name_item)
        
        ein_ssn = result.get('ein_or_ssn', '')
        ein_item = QTreeWidgetItem(["EIN/SSN", ein_ssn, "✓" if len(ein_ssn.replace('-', '')) == 9 else "❌"])
        merchant_item.addChild(ein_item)
        
        # Add address information
        address_item = QTreeWidgetItem(["Address", "", ""])
        self.data_tree.addTopLevelItem(address_item)
        
        address = result.get('address', {})
        for field in ['street', 'city', 'state', 'zip']:
            value = address.get(field, '')
            status = "✓" if value else "❌"
            addr_field_item = QTreeWidgetItem([field.title(), value, status])
            address_item.addChild(addr_field_item)
        
        # Add contact information
        contact_item = QTreeWidgetItem(["Contact Information", "", ""])
        self.data_tree.addTopLevelItem(contact_item)
        
        contact = result.get('contact_info', {})
        for field in ['phone', 'email']:
            value = contact.get(field, '')
            status = "✓" if value else "❌"
            contact_field_item = QTreeWidgetItem([field.title(), value, status])
            contact_item.addChild(contact_field_item)
        
        # Expand all items
        self.data_tree.expandAll()
        
        # Update validation results
        self.validation_list.clear()
        
        validation_status = result.get('validation_status', 'unknown')
        confidence = result.get('confidence_score', 0.0)
        
        # Add overall status
        status_item = QListWidgetItem(f"Overall Status: {validation_status.upper()}")
        status_item.setIcon(qta.icon('fa5s.check-circle' if validation_status == 'passed' else 'fa5s.exclamation-triangle'))
        self.validation_list.addItem(status_item)
        
        confidence_item = QListWidgetItem(f"Confidence Score: {confidence:.2%}")
        confidence_item.setIcon(qta.icon('fa5s.chart-line'))
        self.validation_list.addItem(confidence_item)
        
        # Add flagged issues
        issues = result.get('flagged_issues', [])
        if issues:
            self.validation_list.addItem(QListWidgetItem(""))  # Separator
            header_item = QListWidgetItem("Flagged Issues:")
            header_item.setIcon(qta.icon('fa5s.flag'))
            self.validation_list.addItem(header_item)
            
            for issue in issues:
                issue_item = QListWidgetItem(f"• {issue}")
                issue_item.setIcon(qta.icon('fa5s.exclamation-circle'))
                self.validation_list.addItem(issue_item)
        else:
            self.validation_list.addItem(QListWidgetItem(""))  # Separator
            no_issues_item = QListWidgetItem("✅ No validation issues found")
            no_issues_item.setIcon(qta.icon('fa5s.check'))
            self.validation_list.addItem(no_issues_item)
    
    def export_csv(self):
        """Export processing results to CSV."""
        if not self.processed_documents:
            QMessageBox.warning(self, "Warning", "No processed documents to export")
            return
        
        try:
            csv_file = self.pipeline.crm.generate_csv_summary(self.processed_documents)
            
            QMessageBox.information(
                self,
                "Export Complete",
                f"CSV summary exported successfully!\n\nFile: {csv_file}"
            )
            
            self.log_message(f"CSV summary exported: {csv_file}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export CSV:\n{str(e)}")
    
    def open_output_folder(self):
        """Open the output folder in file explorer."""
        import subprocess
        import platform
        
        output_path = os.path.abspath("output")
        
        try:
            if platform.system() == "Windows":
                subprocess.run(["explorer", output_path])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", output_path])
            else:  # Linux
                subprocess.run(["xdg-open", output_path])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open folder:\n{str(e)}")
    
    def test_system_components(self):
        """Test all system components."""
        self.status_text.clear()
        self.status_text.append("Testing system components...\n")
        
        test_results = self.pipeline.test_system_components()
        
        for component, result in test_results.items():
            status = result['status']
            details = result['details']
            
            if status == 'ok':
                icon = "✅"
                self.status_text.append(f"{icon} {component.upper()}: {details}")
            else:
                icon = "❌"
                self.status_text.append(f"{icon} {component.upper()}: {details}")
        
        self.status_text.append("\nTest completed.")
    
    def show_configuration(self):
        """Show configuration dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Configuration")
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Ollama settings
        ollama_group = QGroupBox("Ollama Settings")
        ollama_layout = QFormLayout(ollama_group)
        
        host_edit = QLineEdit(self.pipeline.config.get('ollama_host', 'http://localhost:11434'))
        model_edit = QLineEdit(self.pipeline.config.get('model', 'phi'))
        
        ollama_layout.addRow("Host:", host_edit)
        ollama_layout.addRow("Model:", model_edit)
        
        layout.addWidget(ollama_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.Accepted:
            # Update configuration
            new_config = {
                'ollama_host': host_edit.text(),
                'model': model_edit.text()
            }
            self.pipeline.update_config(new_config)
            self.log_message("Configuration updated")
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Merchant Document Processor",
            """
            <h3>Merchant Document Processing Suite</h3>
            <p>Version 1.0.0</p>
            
            <p>An automated document processing pipeline that:</p>
            <ul>
            <li>Extracts text using OCR technology</li>
            <li>Parses documents using local AI models</li>
            <li>Validates data with business rules</li>
            <li>Prepares clean output for CRM systems</li>
            </ul>
            
            <p><b>Completely offline and secure</b> - your documents never leave your computer.</p>
            
            <p>Built with Python, PySide6, Tesseract OCR, and Ollama.</p>
            """
        )
    
    def log_message(self, message: str):
        """Add message to processing log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)
        
        # Auto-scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)
    
    def closeEvent(self, event):
        """Handle application close."""
        if self.worker_thread and self.worker_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Processing in Progress",
                "Document processing is still running. Do you want to stop and exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.stop_processing()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

def launch_application():
    """Launch the premium GUI application."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Apply dark theme
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyside6())
    
    # Set application properties
    app.setApplicationName("Merchant Document Processor")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Document Processing Suite")
    
    # Create and show main window
    window = PremiumDocumentProcessor()
    window.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    launch_application()