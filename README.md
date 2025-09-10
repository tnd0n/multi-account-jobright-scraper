# Multi-Account JobRight Scraper 🚀

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/tnd0n/multi-account-jobright-scraper)

> **Created by TND0N** | Enhanced JobRight scraper that simultaneously uses up to 80 accounts for maximum job diversity and data collection.

## 🌟 Features

- Multi-Account simultaneous scraping (up to 80 accounts)
- Intelligent load distribution
- Thread-safe deduplication
- Enhanced Google Sheets Integration
- Configurable concurrency
- Real-time progress tracking

## 🚀 Quick Deploy

### One-Click Deploy to Render

Deploy instantly with pre-configured settings:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/tnd0n/multi-account-jobright-scraper)

### Manual Render Deployment

1. **Fork this repository** to your GitHub account
2. **Connect to Render**:
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
3. **Configure deployment**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 4 --reuse-port app:app`
4. **Set Environment Variables**:
   - `FLASK_SECRET_KEY`: Generate a secure random key
   - `GOOGLE_SERVICE_ACCOUNT_JSON`: Your Google service account credentials
5. **Deploy**: Click "Create Web Service"

## 📄 Local Setup

See detailed instructions in [SETUP.md](SETUP.md)

## 📈 Usage

- Open the deployed URL in your browser
- Fill form fields and click **Start Multi-Account Scraping**
- Monitor real-time progress and results

### Command-line option

```bash
python enhanced_multi_account_scraper.py --sheet YOUR_SHEET_ID --target 2000 --accounts 20 --keyword "python"
```

## 📚 Configuration

- Use the built-in `accounts_config.json` for account credentials
- Customize concurrency and target jobs via web UI or CLI

## 🆘 Support

For troubleshooting:
- Ensure correct Google Sheet permissions
- Validate environment variables
- Reduce `max_accounts` if encountering rate limits

---

**Note:** Never commit your Google credentials publicly.
