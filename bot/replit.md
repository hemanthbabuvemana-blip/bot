# ACTMS - Anti-Corruption Tender Management System

## Overview

ACTMS (Anti-Corruption Tender Management System) is a comprehensive web application designed to provide transparent and corruption-free tender management with AI-powered detection capabilities. The system enables government agencies and organizations to manage tenders, receive bids, and detect anomalous patterns that might indicate corruption. Built with both Streamlit for the web interface and FastAPI for API services, it provides a complete workflow from tender creation to bid evaluation with integrated AI analysis, chatbot assistance, and comprehensive dashboards for monitoring system activity.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Dual architecture with Streamlit multi-page application for main interface and optional HTML/JavaScript frontend for API interactions
- **Page Structure**: Main app.py serves as entry point with 5 specialized pages:
  - Tender Management (upload, view, analytics)
  - Bid Submission (submit, view, analysis)
  - AI Analysis (real-time alerts, anomaly dashboard, model training, pattern analysis)
  - Chatbot (AI assistant with conversation history)
  - Dashboard (overview, financial analysis, security insights, operational metrics, system admin)
- **Navigation**: Sidebar-based navigation system with wide layout configuration and tabbed interfaces for organized content presentation
- **UI Components**: Interactive forms, data visualization using Plotly and Chart.js, real-time chat interface, and responsive design with Tailwind CSS

### Backend Architecture
- **Database Layer**: SQLite database with custom DatabaseManager class handling CRUD operations for tenders, bids, and audit logs
- **API Layer**: FastAPI server (api_server.py) providing RESTful endpoints with CORS middleware for cross-origin requests
- **Service Layer**: Modular service architecture with specialized classes:
  - MLService for machine learning-based anomaly detection using Isolation Forest algorithm
  - NLPService for natural language processing and document analysis with spaCy integration
  - ChatbotService for AI-powered user assistance with Gemini API integration
- **Data Models**: Three core entities with foreign key relationships:
  - Tenders (document management with file storage and metadata)
  - Bids (submission tracking with anomaly scoring)
  - Audit logs (comprehensive activity monitoring)
- **File Management**: Dedicated FileHandler utility for secure file upload, validation, and storage with support for PDF, DOC, DOCX, TXT, and RTF formats up to 10MB

### Data Storage Solutions
- **Primary Database**: SQLite with three main tables supporting complete tender lifecycle management
- **File Storage**: Local file system with organized upload directory structure and comprehensive file validation
- **Model Storage**: Dedicated models directory for persisting trained ML models with joblib serialization
- **Configuration**: JSON-based FAQ storage for chatbot responses and system configuration management
- **Static Assets**: Dedicated static directory for serving HTML, CSS, and JavaScript files

### Authentication and Authorization
- **Session Management**: Streamlit session state for user interaction tracking and conversation history
- **Security Features**: File validation with size and type restrictions, comprehensive audit logging for all activities, secure file handling with unique filename generation
- **Access Control**: Page-based access through Streamlit's navigation system with role-based feature access
- **API Security**: CORS middleware configuration for secure cross-origin requests

### AI/ML Integration
- **Anomaly Detection**: Isolation Forest algorithm for identifying suspicious bidding patterns with 10% contamination threshold and 100 estimators
- **Feature Engineering**: Multi-dimensional feature extraction including:
  - Monetary values (bid amounts, estimated values)
  - Temporal features (submission timing, deadlines)
  - Textual features (proposal length, company name patterns)
  - Behavioral patterns (bidding frequency, amount variations)
- **NLP Processing**: spaCy-based text analysis with fallback to regex-based processing for document information extraction
- **Model Training**: Online learning capability with model persistence and retraining functionality using scikit-learn

## External Dependencies

### Core Framework Dependencies
- **Streamlit**: Web application framework for the entire frontend interface
- **FastAPI**: Modern API framework for building RESTful services with automatic OpenAPI documentation
- **SQLite3**: Built-in database for data persistence and management
- **Pandas**: Data manipulation and analysis for handling tender and bid data
- **NumPy**: Numerical computing for ML feature processing

### Machine Learning Dependencies
- **scikit-learn**: Machine learning library providing Isolation Forest for anomaly detection, StandardScaler for feature normalization, and TfidfVectorizer for text processing
- **joblib**: Model serialization and persistence for trained ML models

### Natural Language Processing
- **spaCy**: Advanced NLP library for text analysis, entity extraction, and document processing with fallback to regex-based processing
- **en_core_web_sm**: English language model for spaCy (optional, with graceful fallback)

### AI Integration
- **Google Gemini API**: AI-powered chatbot service using the latest "gemini-2.5-flash" model for user assistance and query handling
- **python_gemini**: Python client library for Google Gemini API integration

### Web and File Processing
- **Plotly**: Interactive data visualization library for charts and graphs in the Streamlit interface
- **Chart.js**: JavaScript charting library for frontend data visualization
- **Tailwind CSS**: Utility-first CSS framework for responsive web design
- **python-multipart**: File upload handling for FastAPI endpoints

### Development and Testing
- **TestDataGenerator**: Custom utility for generating realistic test data for system testing and ML model training
- **CORS Middleware**: Cross-Origin Resource Sharing support for API security

### File and Data Management
- **mimetypes**: File type detection and validation
- **hashlib**: Secure file naming and integrity checking
- **json**: Configuration and FAQ data management
- **datetime**: Timestamp handling and time-based feature extraction