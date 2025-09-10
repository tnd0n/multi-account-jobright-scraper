# Setup Instructions

## 1. Environment Variables Setup

You need to set up the Google Service Account credentials as an environment variable:

```bash
export GOOGLE_SERVICE_ACCOUNT_JSON='your-service-account-json-here'
```

**Note:** The actual service account JSON will be provided separately for security reasons.

## 2. Google Sheet Access

Make sure to share your target Google Sheet with the service account email:
```
sheetsservice@sheets-autoexpor.iam.gserviceaccount.com
```

Give it "Editor" permissions.

## 3. Default Google Sheet

The system is pre-configured to use this Google Sheet:
```
https://docs.google.com/spreadsheets/d/1iibXYJ5ZSFZzFIKUyM8d4u3x87FOereMESBfuFW7ZYI/edit
```

## 4. Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variable (replace with actual credentials)
export GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'

# Run the web application
python app.py

# Access at http://localhost:5000
```

## 5. Deploy to Production

### Using Gunicorn
```bash
gunicorn --bind 0.0.0.0:5000 app:app
```

### Using Docker
```bash
docker build -t multi-account-scraper .
docker run -p 5000:5000 -e GOOGLE_SERVICE_ACCOUNT_JSON='...' multi-account-scraper
```

## 6. Configuration

### Account Configuration
The system comes with 80 pre-configured accounts in `accounts_config.json`:
- Accounts 1-20: Software Engineer focus
- Accounts 21-40: Data Scientist focus  
- Accounts 41-60: Product Manager focus
- Accounts 61-80: DevOps Engineer focus

### Concurrent Settings
- **Conservative**: 5-10 accounts
- **Balanced**: 10-20 accounts (recommended)
- **Aggressive**: 20-30 accounts

## 7. Troubleshooting

### Common Issues
1. **Google Sheets Permission Error**: Verify service account has access
2. **Account Authentication Failures**: Some accounts may be temporarily blocked
3. **Network Issues**: Ensure stable internet connection
4. **Resource Limits**: Start with fewer concurrent accounts

### Health Check
Access `/health` endpoint to verify system status:
```
http://localhost:5000/health
```

## 8. Support

For additional support or questions:
- Check the troubleshooting section
- Review application logs
- Test with fewer concurrent accounts first
- Verify Google Sheets permissions

---

**Important:** Keep your Google Service Account credentials secure and never commit them to version control.
