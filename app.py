from flask import Flask, jsonify, render_template_string, request
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "multi-account-key-2025"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Account JobRight Scraper</title>
    <style>
        body { 
            font-family: system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; margin: 0; padding: 20px;
        }
        .container { max-width: 900px; margin: 0 auto; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .stats { display: flex; justify-content: center; gap: 30px; margin-top: 20px; }
        .stat-item { 
            background: rgba(255,255,255,0.2); padding: 15px 25px; 
            border-radius: 10px; backdrop-filter: blur(10px);
        }
        .stat-number { font-size: 1.8em; font-weight: bold; display: block; }
        .form-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px; padding: 40px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; font-weight: 600; }
        .form-group input, .form-group select {
            width: 100%; padding: 12px; border: 2px solid #e0e0e0;
            border-radius: 8px; font-size: 16px;
        }
        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .submit-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border: none; padding: 15px 30px;
            font-size: 16px; font-weight: 600; border-radius: 8px;
            cursor: pointer; width: 100%;
        }
        .loading { display: none; text-align: center; padding: 30px; }
        .results { display: none; padding: 20px; background: white; border-radius: 10px; margin-top: 20px; }
        .success { color: #27ae60; }
        .error { color: #e74c3c; }
        @media (max-width: 768px) { .form-row { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Multi-Account JobRight Scraper</h1>
            <p>Simultaneously scrape from up to 80 JobRight accounts</p>
            <div class="stats">
                <div class="stat-item">
                    <span class="stat-number">80</span>
                    <span class="stat-label">Max Accounts</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">2000+</span>
                    <span class="stat-label">Jobs Per Run</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">20x</span>
                    <span class="stat-label">Faster</span>
                </div>
            </div>
        </div>

        <div class="form-container">
            <form id="scraperForm">
                <div class="form-group">
                    <label>📄 Google Sheet ID</label>
                    <input type="text" id="sheet_url" name="sheet_url" 
                           value="1iibXYJ5ZSFZzFIKUyM8d4u3x87FOereMESBfuFW7ZYI" required>
                    <small>Sheet must be shared with: sheetsservice@sheets-autoexpor.iam.gserviceaccount.com</small>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>🔍 Keyword Filter</label>
                        <input type="text" id="keyword" name="keyword" 
                               placeholder="python, react, data scientist">
                    </div>
                    <div class="form-group">
                        <label>🎯 Target Jobs</label>
                        <select id="target_jobs" name="target_jobs">
                            <option value="500">500 Jobs</option>
                            <option value="1000">1000 Jobs</option>
                            <option value="2000" selected>2000 Jobs</option>
                            <option value="3000">3000 Jobs</option>
                        </select>
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>👥 Concurrent Accounts</label>
                        <select id="max_accounts" name="max_accounts">
                            <option value="5">5 Accounts</option>
                            <option value="10">10 Accounts</option>
                            <option value="20" selected>20 Accounts</option>
                            <option value="30">30 Accounts</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>⚙️ Scraping Mode</label>
                        <select id="scrape_mode" name="scrape_mode">
                            <option value="balanced" selected>Balanced</option>
                            <option value="aggressive">Aggressive</option>
                            <option value="conservative">Conservative</option>
                        </select>
                    </div>
                </div>

                <button type="submit" class="submit-btn">
                    🚀 Start Multi-Account Scraping
                </button>
            </form>
        </div>

        <div class="loading" id="loading">
            <h3>Multi-Account Scraping in Progress...</h3>
            <p>Processing multiple JobRight accounts simultaneously</p>
        </div>

        <div class="results" id="results">
            <div id="results-content"></div>
        </div>
    </div>

    <script>
        document.getElementById('scraperForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').style.display = 'none';

            const formData = {
                sheet_url: document.getElementById('sheet_url').value,
                keyword: document.getElementById('keyword').value,
                target_jobs: parseInt(document.getElementById('target_jobs').value),
                max_accounts: parseInt(document.getElementById('max_accounts').value),
                scrape_mode: document.getElementById('scrape_mode').value
            };

            try {
                const response = await fetch('/scrape_multi_account', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                const result = await response.json();
                document.getElementById('loading').style.display = 'none';

                const resultsDiv = document.getElementById('results');
                const contentDiv = document.getElementById('results-content');

                if (result.success) {
                    contentDiv.innerHTML = `
                        <h2 class="success">✅ Multi-Account Scraping Complete!</h2>
                        <pre style="white-space: pre-line; margin-top: 20px;">${result.message}</pre>
                    `;
                } else {
                    contentDiv.innerHTML = `
                        <h2 class="error">❌ Scraping Failed</h2>
                        <p>${result.message}</p>
                    `;
                }
                resultsDiv.style.display = 'block';

            } catch (error) {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('results').style.display = 'block';
                document.getElementById('results-content').innerHTML = `
                    <h2 class="error">❌ Request Failed</h2>
                    <p>Error: ${error.message}</p>
                `;
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "scraper_type": "Multi-Account JobRight Scraper",
        "max_accounts": 80,
        "concurrent_support": True
    })

@app.route('/scrape_multi_account', methods=['POST'])
def scrape_multi_account():
    try:
        data = request.json or {}

        sheet_id = data.get('sheet_url', '').strip()
        keyword = data.get('keyword', '').strip()
        target_jobs = int(data.get('target_jobs', 2000))
        max_accounts = int(data.get('max_accounts', 20))
        scrape_mode = data.get('scrape_mode', 'balanced')

        if not sheet_id:
            return jsonify({"success": False, "message": "Sheet ID required"})

        try:
            from enhanced_multi_account_scraper import MultiAccountJobRightScraper

            scraper = MultiAccountJobRightScraper()

            # Adjust concurrency based on mode
            if scrape_mode == 'conservative':
                max_accounts = min(max_accounts, 10)
            elif scrape_mode == 'aggressive':
                max_accounts = min(max_accounts, 30)

            result = scraper.run_complete_multi_account_scraper(
                sheet_url=sheet_id,
                keyword=keyword,
                target_jobs=target_jobs,
                max_concurrent_accounts=max_accounts
            )

            return jsonify(result)

        except ImportError:
            return jsonify({"success": False, "message": "Multi-Account Scraper module not available"})
        except Exception as e:
            return jsonify({"success": False, "message": f"Scraping failed: {str(e)}"})

    except Exception as e:
        return jsonify({"success": False, "message": f"Request error: {str(e)}"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
