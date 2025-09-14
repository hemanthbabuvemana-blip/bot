# ACTMS - Anti-Corruption Tender Management System

## Overview

ACTMS (Anti-Corruption Tender Management System) is a comprehensive web application built with Streamlit that provides transparent and corruption-free tender management with AI-powered detection capabilities. The system enables government agencies and organizations to manage tender processes from creation to bid evaluation while detecting suspicious patterns and maintaining audit trails. Key features include tender document management, bid submission with validation, AI-powered anomaly detection, an intelligent chatbot assistant, and comprehensive dashboards for monitoring system activity.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit multi-page application with component-based architecture
- **Page Structure**: Main app.py serves as entry point with 5 specialized pages for different functionalities (Tender Management, Bid Submission, AI Analysis, Chatbot, Dashboard)
- **Navigation**: Sidebar-based navigation system with wide layout configuration
- **UI Components**: Tabbed interfaces for organized content presentation with interactive forms and data visualization using Plotly

### Backend Architecture
- **Database Layer**: SQLite database with custom DatabaseManager class handling CRUD operations for tenders, bids, and audit logs
- **Service Layer**: Modular service architecture with specialized classes:
  - MLService for machine learning-based anomaly detection using Isolation Forest
  - NLPService for natural language processing and document analysis
  - ChatbotService for AI-powered user assistance with OpenAI integration
- **Data Models**: Three core entities with foreign key relationships: tenders (document management), bids (submission tracking), and audit_logs (activity monitoring)
- **File Management**: Dedicated FileHandler utility for secure file upload, validation, and storage with support for PDF, DOC, DOCX, TXT, and RTF formats

### Data Storage Solutions
- **Primary Database**: SQLite with three main tables supporting tender lifecycle management
- **File Storage**: Local file system with organized upload directory structure and file validation
- **Model Storage**: Dedicated models directory for persisting trained ML models with joblib serialization
- **Configuration**: JSON-based FAQ storage and system configuration management

### Authentication and Authorization
- **Session Management**: Streamlit session state for user interaction tracking
- **Security Features**: File validation, comprehensive audit logging, and secure file handling
- **Access Control**: Page-based access through Streamlit's navigation system

### AI/ML Integration
- **Anomaly Detection**: Isolation Forest algorithm for identifying suspicious bidding patterns with 10% contamination threshold
- **Feature Engineering**: Multi-dimensional feature extraction including monetary values, text length, submission timing, and proposal content analysis
- **NLP Processing**: spaCy-based text analysis with fallback to regex-based processing for document information extraction
- **Model Training**: Online learning capability with model persistence and retraining functionality

## External Dependencies

### Core Framework Dependencies
- **Streamlit**: Web application framework for the entire frontend interface
- **SQLite3**: Built-in database for data persistence and management
- **Pandas**: Data manipulation and analysis for handling tender and bid data
- **NumPy**: Numerical computing support for ML operations

### Machine Learning Dependencies
- **Scikit-learn**: Machine learning library providing Isolation Forest for anomaly detection and preprocessing tools
- **spaCy**: Advanced NLP library for document analysis and entity extraction (with fallback support)
- **Joblib**: Model serialization and persistence for trained ML models

### Data Visualization Dependencies
- **Plotly**: Interactive visualization library for dashboard charts and analytics
- **Plotly Express**: Simplified plotting interface for rapid dashboard development

### AI Integration Dependencies
- **OpenAI**: GPT-5 integration for intelligent chatbot functionality requiring API key configuration
- **JSON**: Configuration management for FAQ data and system settings

### Utility Dependencies
- **Hashlib**: File integrity verification and security hashing
- **Mimetypes**: File type validation and handling
- **DateTime**: Timestamp management and date processing
- **OS/Pathlib**: File system operations and path management
- **RE**: Regular expression support for text processing and validation