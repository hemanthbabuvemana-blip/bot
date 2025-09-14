# ACTMS - Anti-Corruption Tender Management System

## Overview

ACTMS (Anti-Corruption Tender Management System) is a comprehensive web application built with Streamlit that provides transparent and corruption-free tender management with AI-powered detection capabilities. The system enables government agencies and organizations to manage tender processes, collect bids, and detect suspicious patterns through machine learning analysis.

The application provides a complete workflow from tender creation to bid evaluation, with integrated AI analysis, chatbot assistance, and comprehensive dashboards for monitoring system activity and detecting potential corruption indicators.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit multi-page application with component-based architecture
- **Page Structure**: Main app.py serves as entry point with 5 specialized pages for different functionalities
- **Navigation**: Sidebar-based navigation system with dedicated pages for Tender Management, Bid Submission, AI Analysis, Chatbot, and Dashboard
- **UI Components**: Wide layout configuration with tabbed interfaces for organized content presentation

### Backend Architecture
- **Database Layer**: SQLite database with custom DatabaseManager class handling CRUD operations
- **Service Layer**: Modular service architecture with specialized classes:
  - MLService for machine learning and anomaly detection
  - NLPService for natural language processing and document analysis
  - ChatbotService for AI-powered user assistance
- **Data Models**: Three core entities - tenders, bids, and audit logs with foreign key relationships
- **File Management**: Dedicated FileHandler utility for secure file upload and validation

### Data Storage Solutions
- **Primary Database**: SQLite with three main tables (tenders, bids, audit_logs)
- **File Storage**: Local file system with organized upload directory structure
- **Model Storage**: Dedicated models directory for persisting trained ML models
- **Configuration**: JSON-based FAQ storage and system configuration

### Authentication and Authorization
- **Current State**: Basic Streamlit session state management
- **Security Features**: File validation, audit logging, and secure file handling
- **Access Control**: Page-based access through Streamlit's navigation system

### AI/ML Integration
- **Anomaly Detection**: Isolation Forest algorithm for identifying suspicious bidding patterns
- **NLP Processing**: spaCy-based text analysis with fallback to basic processing
- **Feature Engineering**: Multi-dimensional feature extraction from bid data including monetary, temporal, and textual features
- **Model Training**: Online learning capability with model persistence

## External Dependencies

### Core Framework Dependencies
- **Streamlit**: Web application framework for the entire frontend
- **SQLite3**: Built-in database engine for data persistence
- **Pandas**: Data manipulation and analysis throughout the application

### Machine Learning Dependencies
- **scikit-learn**: Primary ML library for anomaly detection algorithms
- **NumPy**: Numerical computing for data processing and feature engineering
- **Joblib**: Model serialization and persistence

### Natural Language Processing
- **spaCy**: Advanced NLP library for document analysis and entity extraction
- **TfidfVectorizer**: Text feature extraction for ML analysis

### Data Visualization
- **Plotly Express**: Interactive charting for dashboard visualizations
- **Plotly Graph Objects**: Custom interactive plots and analytics

### AI Services
- **OpenAI GPT-5**: Chatbot functionality through OpenAI API integration
- **Environment Variables**: API key management for external service authentication

### Development and Deployment
- **Python Standard Library**: Core functionality including os, json, datetime, hashlib
- **File Type Support**: PDF, DOC, DOCX, TXT, RTF document processing capabilities

### Optional Dependencies
- **Web3**: Blockchain integration capability (referenced in setup but not actively implemented)
- **Jupyter**: Analytics notebook support for advanced data analysis