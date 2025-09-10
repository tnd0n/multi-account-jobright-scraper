# Multi-Account JobRight Scraper

🚀 **Enhanced JobRight scraper that simultaneously uses up to 80 accounts for maximum job diversity and data collection.**

## 🌟 Features

- Multi-Account simultaneous scraping (up to 80 accounts)
- Intelligent load distribution
- Thread-safe deduplication
- Enhanced Google Sheets Integration
- Configurable concurrency
- Real-time progress tracking

## 🚀 Deployment

### Deploy to Render

1. **Sign up / log in to Render**: https://render.com

2. **Create a new Web Service**
   - Connect your GitHub account
   - Select the `tnd0n/multi-account-jobright-scraper` repository
   - Branch: `main`

3. **Configure build and start commands**

   **Build Command:**
   ```bash
   pip install -r requirements.txt
   ```

   **Start Command:**
   ```bash
   gunicorn --bind 0.0.0.0:$PORT --workers 4 app:app
   ```

4. **Set Environment Variables**
   - Add `GOOGLE_SERVICE_ACCOUNT_JSON` with your service account JSON string

5. **Specify instance details**
   - Select instance type (e.g., Starter or Standard based on needs)
   - Set region close to your users

6. **Deploy**
   - Click Deploy

7. **Access your app**
   - Use the Render-provided URL, e.g., `https://your-app-name.onrender.com`

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
