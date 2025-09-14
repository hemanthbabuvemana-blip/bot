import os
import hashlib
import mimetypes
from datetime import datetime
import streamlit as st

class FileHandler:
    def __init__(self, upload_dir="uploads"):
        self.upload_dir = upload_dir
        self.allowed_extensions = {'.pdf', '.doc', '.docx', '.txt', '.rtf'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
        # Create upload directory if it doesn't exist
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def validate_file(self, uploaded_file):
        """Validate uploaded file"""
        errors = []
        
        if not uploaded_file:
            return False, ["No file uploaded"]
        
        # Check file size
        if uploaded_file.size > self.max_file_size:
            errors.append(f"File size ({uploaded_file.size / (1024*1024):.1f}MB) exceeds maximum allowed size (10MB)")
        
        # Check file extension
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        if file_extension not in self.allowed_extensions:
            errors.append(f"File type '{file_extension}' not allowed. Supported types: {', '.join(self.allowed_extensions)}")
        
        # Check filename
        if len(uploaded_file.name) > 255:
            errors.append("Filename too long (maximum 255 characters)")
        
        if not uploaded_file.name.strip():
            errors.append("Invalid filename")
        
        return len(errors) == 0, errors
    
    def save_file(self, uploaded_file, prefix="tender"):
        """Save uploaded file to disk"""
        try:
            # Validate file first
            is_valid, errors = self.validate_file(uploaded_file)
            if not is_valid:
                return None, errors
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            
            # Create hash of file content for uniqueness
            file_content = uploaded_file.read()
            file_hash = hashlib.md5(file_content).hexdigest()[:8]
            
            # Reset file pointer
            uploaded_file.seek(0)
            
            # Generate safe filename
            safe_filename = f"{prefix}_{timestamp}_{file_hash}{file_extension}"
            file_path = os.path.join(self.upload_dir, safe_filename)
            
            # Save file
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            return file_path, []
            
        except Exception as e:
            return None, [f"Error saving file: {str(e)}"]
    
    def read_file_content(self, file_path):
        """Read content from saved file"""
        try:
            if not os.path.exists(file_path):
                return None, "File not found"
            
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read(), None
            
            elif file_extension == '.pdf':
                return self._read_pdf(file_path)
            
            elif file_extension in ['.doc', '.docx']:
                return self._read_word_document(file_path)
            
            elif file_extension == '.rtf':
                return self._read_rtf(file_path)
            
            else:
                return None, f"Unsupported file type: {file_extension}"
                
        except Exception as e:
            return None, f"Error reading file: {str(e)}"
    
    def _read_pdf(self, file_path):
        """Read PDF file content"""
        try:
            # Try to import PyPDF2 for PDF reading
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    return text, None
            except ImportError:
                return None, "PyPDF2 not available. Cannot read PDF files."
                
        except Exception as e:
            return None, f"Error reading PDF: {str(e)}"
    
    def _read_word_document(self, file_path):
        """Read Word document content"""
        try:
            # Try to import python-docx for Word documents
            try:
                from docx import Document
                doc = Document(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text, None
            except ImportError:
                return None, "python-docx not available. Cannot read Word documents."
                
        except Exception as e:
            return None, f"Error reading Word document: {str(e)}"
    
    def _read_rtf(self, file_path):
        """Read RTF file content"""
        try:
            # Basic RTF reading - just extract plain text
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Simple RTF text extraction (removes most RTF formatting)
                import re
                # Remove RTF control words
                text = re.sub(r'\\[a-z]+\d*', '', content)
                # Remove remaining RTF syntax
                text = re.sub(r'[{}]', '', text)
                # Clean up whitespace
                text = re.sub(r'\s+', ' ', text).strip()
                return text, None
                
        except Exception as e:
            return None, f"Error reading RTF file: {str(e)}"
    
    def get_file_info(self, file_path):
        """Get information about a saved file"""
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            file_extension = os.path.splitext(file_path)[1].lower()
            
            return {
                'filename': os.path.basename(file_path),
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'extension': file_extension,
                'mime_type': mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            }
            
        except Exception as e:
            return None
    
    def delete_file(self, file_path):
        """Delete a file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True, "File deleted successfully"
            else:
                return False, "File not found"
        except Exception as e:
            return False, f"Error deleting file: {str(e)}"
    
    def get_upload_widget(self, label="Upload File", help_text=None, key=None):
        """Create a Streamlit file upload widget with validation"""
        if not help_text:
            help_text = f"Supported formats: {', '.join(self.allowed_extensions)}. Maximum size: 10MB"
        
        uploaded_file = st.file_uploader(
            label,
            type=[ext[1:] for ext in self.allowed_extensions],  # Remove the dot
            help=help_text,
            key=key
        )
        
        if uploaded_file:
            # Show file information
            st.info(f"📁 **File:** {uploaded_file.name} ({uploaded_file.size / (1024*1024):.2f} MB)")
            
            # Validate file
            is_valid, errors = self.validate_file(uploaded_file)
            if not is_valid:
                for error in errors:
                    st.error(f"❌ {error}")
                return None
            else:
                st.success("✅ File validation passed")
                return uploaded_file
        
        return None
    
    def create_download_link(self, file_path, download_name=None):
        """Create a download link for a file"""
        try:
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            if not download_name:
                download_name = os.path.basename(file_path)
            
            return st.download_button(
                label=f"📥 Download {download_name}",
                data=file_data,
                file_name=download_name,
                mime=mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            )
            
        except Exception as e:
            st.error(f"Error creating download link: {str(e)}")
            return None
