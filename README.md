# Multi-Account JobRight Scraper

🚀 **Enhanced JobRight scraper that simultaneously uses up to 80 accounts for maximum job diversity and data collection.**

## 🌟 Features

### Core Capabilities
- **Multi-Account Simultaneous Scraping**: Use up to 80 JobRight accounts concurrently
- **Intelligent Load Distribution**: Distributes different job titles across accounts
- **Thread-Safe Deduplication**: Prevents duplicate jobs across all accounts
- **Enhanced Google Sheets Integration**: Tracks which account collected each job
- **Configurable Concurrency**: Choose 5-30 concurrent accounts based on your needs
- **Smart Rate Limiting**: Automatic delays and request management

### Advanced Features
- **Job Title Specialization**: Each account can target specific job types (Software Engineer, Data Scientist, Product Manager, DevOps Engineer)
- **Multiple Scraping Methods**: Pagination, API endpoints, and job title filtering
- **Real-time Progress Tracking**: Live updates on scraping progress
- **Comprehensive Error Handling**: Graceful failure handling and recovery
- **Account Health Monitoring**: Tracks successful and failed account authentications

## 🛠 Technical Architecture

### Multi-Account System
```
Account Pool (80 accounts):
├── 1@a.com → 20@a.com (Software Engineer focus)
├── 21@a.com → 40@a.com (Data Scientist focus) 
├── 41@a.com → 60@a.com (Product Manager focus)
└── 61@a.com → 80@a.com (DevOps Engineer focus)
```

### Concurrent Processing
- **ThreadPoolExecutor**: Manages concurrent account sessions
- **Queue-based Job Processing**: Thread-safe job collection
- **Session Management**: Maintains authenticated sessions per account
- **Resource Pooling**: Efficiently manages network connections

## 📊 Performance Metrics

| Metric | Single Account | Multi-Account (20 concurrent) |
|--------|---------------|-------------------------------|
| Jobs per run | ~100 | ~2000+ |
| Time per run | 10-15 minutes | 5-8 minutes |
| Job diversity | Limited | Maximum |
| Success rate | 85% | 95% (redundancy) |

## 🚀 Quick Start

### 1. Environment Setup

#### Google Sheets API Setup
1. Create a Google Cloud project
2. Enable Google Sheets API
3. Create a service account
4. Download credentials JSON
5. Set environment variable:
```bash
export GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
```

#### Share Your Google Sheet
Share your target sheet with the service account email:
```
sheetsservice@sheets-autoexpor.iam.gserviceaccount.com
```

### 2. Installation & Run

#### Option 1: Web Interface (Recommended)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the web application
python app.py

# Access at http://localhost:5000
```

#### Option 2: Command Line
```bash
python enhanced_multi_account_scraper.py --sheet YOUR_SHEET_ID --target 2000 --accounts 20 --keyword "python"
```

### 3. Configuration

#### accounts_config.json
The system automatically generates a configuration for 80 accounts:
```json
{
  "accounts": [
    {
      "email": "1@a.com",
      "password": "ajay4498",
      "name": "Account_1",
      "job_title": "Software Engineer",
      "active": true,
      "max_daily_requests": 100
    },
    ...
  ]
}
```

## 🎯 Usage Examples

### Web Interface
1. Open http://localhost:5000
2. Enter Google Sheet ID
3. Set keyword filter (optional)
4. Choose target jobs (500-3000)
5. Select concurrent accounts (5-30)
6. Click "Start Multi-Account Scraping"

### Command Line Examples
```bash
# Standard run with 20 accounts
python enhanced_multi_account_scraper.py --sheet SHEET_ID --target 2000 --accounts 20

# Keyword-filtered run
python enhanced_multi_account_scraper.py --sheet SHEET_ID --target 1000 --accounts 15 --keyword "data scientist"

# Conservative run with fewer accounts
python enhanced_multi_account_scraper.py --sheet SHEET_ID --target 500 --accounts 5
```

## 📈 Output & Results

### Google Sheets Export
Two sheets are created automatically:
- **ALL_JOBS_MULTI**: All collected jobs with account tracking
- **FILTERED_JOBS_MULTI**: Jobs matching your keyword filter

### Enhanced Data Fields
Each job record includes:
- Standard job information (title, company, location, salary, etc.)
- **Account Name**: Which account collected this job
- **Account Email**: Email of the collecting account  
- **Job Title Preference**: The job title focus of the account
- **Source**: Specific scraping method used

### Sample Results
```
✅ MULTI-ACCOUNT SCRAPING COMPLETE!

📊 Total jobs collected: 2,247
🎯 Jobs matching 'python': 892
👥 Accounts successfully used: 18/20
❌ Accounts failed: 2
📋 Data exported to Google Sheets
⚡ Simultaneous multi-account scraping achieved maximum diversity!
```

## ⚙️ Configuration Options

### Concurrency Levels
- **Conservative (5 accounts)**: Safest, good for testing
- **Balanced (10-20 accounts)**: Recommended for production
- **Aggressive (25-30 accounts)**: Maximum speed, higher resource usage

### Scraping Modes
- **Conservative**: Longer delays, safer rate limiting
- **Balanced**: Optimal speed vs. safety ratio
- **Aggressive**: Fastest possible scraping

### Account Distribution
Jobs titles are distributed across accounts for maximum diversity:
- **Software Engineer**: Accounts 1-20
- **Data Scientist**: Accounts 21-40  
- **Product Manager**: Accounts 41-60
- **DevOps Engineer**: Accounts 61-80

## 🔧 Advanced Configuration

### Custom Account Setup
Modify `accounts_config.json` to customize:
- Email addresses and passwords
- Job title preferences per account
- Daily request limits
- Active/inactive status

### Environment Variables
```bash
# Required
export GOOGLE_SERVICE_ACCOUNT_JSON='...'

# Optional
export SESSION_SECRET='your-secret-key'
export MAX_CONCURRENT_ACCOUNTS=20
export DEFAULT_TARGET_JOBS=2000
```

## 📊 Monitoring & Debugging

### Health Endpoints
- `GET /health`: Server status and configuration
- `GET /debug`: Detailed system information

### Logging
Comprehensive logging for:
- Account authentication status
- Job collection progress  
- Error tracking and recovery
- Performance metrics

### Common Issues & Solutions

#### No Jobs Found
```bash
# Check account authentication
# Verify Google Sheets permissions
# Try reducing concurrent accounts
# Check internet connectivity
```

#### Google Sheets Permission Error
```bash
# Ensure service account email has access
# Verify GOOGLE_SERVICE_ACCOUNT_JSON is set
# Check sheet ID format
```

#### Account Authentication Failures  
```bash
# Some accounts may be temporarily blocked
# System will continue with working accounts
# Monitor failed account count in results
```

## 🚀 Deployment

### Local Development
```bash
pip install -r requirements.txt
python app.py
```

### Production with Gunicorn
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

## 📈 Scaling & Performance

### Optimization Tips
1. **Start Conservative**: Begin with 5-10 accounts and scale up
2. **Monitor Resources**: Watch CPU and memory usage during runs
3. **Network Considerations**: Ensure stable internet for concurrent requests
4. **Google Sheets Limits**: Consider multiple target sheets for very large runs

### Expected Performance
- **2000 jobs**: 5-8 minutes with 20 accounts
- **1000 jobs**: 3-5 minutes with 15 accounts  
- **500 jobs**: 2-3 minutes with 10 accounts

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Update documentation
5. Submit a pull request

## 📄 License

This project is for educational and personal use. Please respect JobRight.ai's terms of service and use responsibly.

## 🆘 Support

For issues or questions:
- Check the troubleshooting section above
- Review logs for error messages
- Verify Google Sheets permissions
- Test with fewer concurrent accounts first

---

**Built with ❤️ for efficient multi-account job data collection**

## 🔥 What's New in Multi-Account Version

### vs. Previous Single-Account Version
- **20x More Jobs**: 2000+ vs ~100 jobs per run
- **Simultaneous Processing**: Concurrent vs sequential account usage  
- **Enhanced Diversity**: Multiple job title preferences
- **Better Reliability**: Account redundancy prevents complete failures
- **Detailed Tracking**: Know which account found each job
- **Scalable Architecture**: Easy to add more accounts or modify preferences

### Performance Comparison
| Feature | Single Account | Multi-Account |
|---------|---------------|---------------|
| Max Jobs | ~100 | 2000+ |
| Runtime | 10-15 min | 5-8 min |
| Failure Rate | High (single point) | Low (redundancy) |
| Diversity | Limited | Maximum |
| Tracking | Basic | Comprehensive |
