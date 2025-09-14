# ACTMS - Anti-Corruption Tender Management System

## Overview

ACTMS (Anti-Corruption Tender Management System) is a comprehensive web application built with Streamlit that provides transparent and corruption-free tender management with AI-powered detection capabilities. The system facilitates the complete tender lifecycle from creation and document upload to bid submission, evaluation, and analysis. It incorporates machine learning algorithms for anomaly detection, natural language processing for document analysis, and an AI-powered chatbot for user assistance. The application is designed to ensure transparency, prevent corruption, and provide comprehensive audit trails for all tender and bidding activities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit multi-page application with component-based architecture
- **Page Structure**: Main app.py serves as entry point with 5 specialized pages:
  - Tender Management (upload, view, analytics)
  - Bid Submission (submit, view, analysis)  
  - AI Analysis (real-time alerts, anomaly dashboard, model training, pattern analysis)
  - Chatbot (AI assistant with conversation history)
  - Dashboard (overview, financial analysis, security insights, operational metrics, system admin)
- **Navigation**: Sidebar-based navigation system with wide layout configuration
- **UI Components**: Tabbed interfaces for organized content presentation with interactive forms, data visualization using Plotly, and real-time chat interface

### Backend Architecture
- **Database Layer**: SQLite database with custom DatabaseManager class handling CRUD operations for tenders, bids, and audit logs
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

### Authentication and Authorization
- **Session Management**: Streamlit session state for user interaction tracking and conversation history
- **Security Features**: File validation with size and type restrictions, comprehensive audit logging for all activities, secure file handling with unique filename generation
- **Access Control**: Page-based access through Streamlit's navigation system with role-based feature access

### AI/ML Integration
- **Anomaly Detection**: Isolation Forest algorithm for identifying suspicious bidding patterns with 10% contamination threshold and 100 estimators
- **Feature Engineering**: Multi-dimensional feature extraction including:
  - Monetary values (bid amounts, estimated values)
  - Text analysis (proposal length, company name patterns)
  - Temporal features (submission timing, hour of day, weekday patterns)
  - Content analysis (proposal quality, technical specifications)
- **NLP Processing**: spaCy-based text analysis with fallback to regex-based processing for:
  - Entity extraction (organizations, monetary values, dates)
  - Document information extraction (requirements, specifications, contact info)
  - Text statistics and quality assessment
- **Model Training**: Online learning capability with model persistence, retraining functionality, and performance monitoring

## External Dependencies

### Core Framework Dependencies
- **Streamlit**: Web application framework for the entire frontend interface and page management
- **SQLite3**: Built-in database for data persistence and relationship management
- **Pandas**: Data manipulation and analysis for handling tender and bid datasets
- **NumPy**: Numerical computing for feature engineering and statistical analysis

### Machine Learning Dependencies
- **scikit-learn**: Machine learning library providing Isolation Forest for anomaly detection, StandardScaler for feature normalization, and TfidfVectorizer for text feature extraction
- **joblib**: Model serialization and persistence for trained ML models

### Natural Language Processing Dependencies
- **spaCy**: Advanced NLP library for entity recognition, text analysis, and document processing with en_core_web_sm model
- **Regular Expressions (re)**: Pattern matching for extracting monetary values, dates, and contact information from documents

### Data Visualization Dependencies
- **Plotly Express & Graph Objects**: Interactive data visualization for dashboards, charts, and analytics displays
- **Plotly Subplots**: Multi-panel visualizations for comprehensive dashboard views

### AI Integration Dependencies
- **Google Gemini API**: AI-powered chatbot service using gemini-2.5-flash model for natural language conversations and user assistance

### Development and Testing Dependencies
- **hashlib**: File integrity checking and unique identifier generation
- **mimetypes**: File type validation and security checking
- **datetime**: Comprehensive timestamp management and time-based feature extraction
- **json**: Configuration management and data serialization for FAQs and system settings
- **os**: File system operations and environment variable management for secure API key handling