# Multi-Account JobRight Scraper

## Overview

This project is a web-based job scraping system that uses multiple JobRight accounts simultaneously to collect job data at scale. The application can leverage up to 80 different accounts to maximize job diversity and data collection while avoiding rate limits. It features a Flask web interface for configuration and monitoring, automated Google Sheets integration for data export, and intelligent load distribution across multiple accounts with thread-safe deduplication.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Flask Web Interface**: Enhanced HTML template-based UI with live progress tracking
- **Single-page Application**: Uses inline HTML template with form-based interaction and real-time updates
- **Live Progress Tracking**: Real-time progress bars, statistics, and animated logs display
- **Auto-Scale Intelligence**: Backend automatically determines optimal account count (1-80 accounts)
- **Enhanced User Experience**: Responsive design with smooth animations and immediate feedback

### Backend Architecture
- **Flask Application Server**: Core web application handling HTTP requests and UI rendering
- **Multi-threaded Scraper Engine**: Concurrent job scraping using ThreadPoolExecutor
- **Account Management System**: JSON-based configuration for managing multiple JobRight accounts
- **Session Management**: Maintains active sessions for each configured account
- **Queue-based Processing**: Uses Python queue for job distribution and result collection

### Data Storage Solutions
- **JSON Configuration Files**: Account credentials and settings stored in `accounts_config.json`
- **Google Sheets Integration**: Primary data export destination using gspread library
- **In-memory Deduplication**: Thread-safe set for tracking processed job IDs
- **No Local Database**: Relies on external Google Sheets for persistence

### Authentication and Authorization
- **Google Service Account**: Uses service account JSON credentials for Google Sheets API access
- **Environment Variable Security**: Service account credentials stored as environment variable
- **JobRight Account Management**: Multiple email/password combinations for job site access
- **Flask Secret Key**: Configurable secret key with production security enforcement

### Load Distribution and Concurrency
- **Intelligent Load Balancing**: Distributes scraping tasks across available accounts
- **Rate Limiting**: Configurable daily request limits per account
- **Thread-safe Operations**: Uses threading locks for shared resource access
- **Concurrent Execution**: Parallel processing with configurable worker threads

## External Dependencies

### Third-party Services
- **JobRight Platform**: Primary job data source requiring account authentication
- **Google Sheets API**: Data export and storage destination
- **Google Cloud Service Account**: Authentication mechanism for Sheets access

### Core Libraries
- **Flask 2.3.3**: Web framework for UI and API endpoints
- **requests 2.31.0**: HTTP client for JobRight API interactions
- **gspread 5.10.0**: Google Sheets Python API wrapper
- **google-auth**: Google authentication and authorization libraries
- **gunicorn 21.2.0**: WSGI HTTP server for production deployment

### Deployment Platform
- **Render**: Cloud platform for hosting with auto-deployment from GitHub
- **Environment Variables**: Configuration through platform environment settings
- **Auto-scaling**: Configurable worker processes and instance sizing

### API Integrations
- **Google Sheets API v4**: For reading/writing spreadsheet data
- **JobRight Internal API**: Job search and data extraction endpoints
- **OAuth2 Service Account**: Secure authentication flow for Google services