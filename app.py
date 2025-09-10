# Multi-Account JobRight Scraper
# Created by: TND0N
# GitHub: https://github.com/tnd0n/multi-account-jobright-scraper

from flask import Flask, jsonify, render_template_string, request
import os
import json
import uuid
import threading
import time
from datetime import datetime

app = Flask(__name__)
# Enforce secure secret key in production
flask_env = os.environ.get('FLASK_ENV', 'development')
default_key = 'dev-key-please-change-in-production'
secret_key = os.environ.get('FLASK_SECRET_KEY', default_key)

if flask_env.lower() not in ['development', 'local', 'dev'] and secret_key == default_key:
    raise RuntimeError("FLASK_SECRET_KEY must be set in production environment")
    
app.secret_key = secret_key

# Global session storage for progress tracking
session_storage = {}
session_lock = threading.Lock()

# PUZZLE: 84 78 68 48 78 (ASCII: TND0N)
# Creator signature embedded in system architecture

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JobRight Enterprise Scraper - Professional Data Collection</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0f1419 0%, #1a202c 50%, #2d3748 100%);
            min-height: 100vh; color: #e2e8f0; line-height: 1.6;
        }
        
        .navbar {
            background: rgba(15, 20, 25, 0.95); backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(148, 163, 184, 0.1);
            padding: 1rem 2rem; position: sticky; top: 0; z-index: 100;
        }
        
        .nav-content {
            max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center;
        }
        
        .nav-brand {
            display: flex; align-items: center; gap: 12px;
        }
        
        .nav-brand i { font-size: 1.5rem; color: #3b82f6; }
        
        .nav-info {
            display: flex; align-items: center; gap: 20px; font-size: 0.875rem; color: #94a3b8;
        }
        
        .nav-badge {
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            color: white; padding: 4px 12px; border-radius: 20px; font-weight: 500;
        }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .hero-section {
            text-align: center; margin-bottom: 3rem; padding: 2rem 0;
        }
        
        .hero-title {
            font-size: 3rem; font-weight: 800; margin-bottom: 1rem;
            background: linear-gradient(135deg, #3b82f6, #06b6d4, #10b981);
            background-clip: text; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            line-height: 1.1;
        }
        
        .hero-subtitle {
            font-size: 1.25rem; color: #94a3b8; margin-bottom: 2rem;
            max-width: 600px; margin-left: auto; margin-right: auto;
        }
        
        .features-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem; margin-bottom: 3rem;
            background: transparent;
            padding: 0;
        }
        
        .feature-card {
            background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(51, 65, 85, 0.6)) !important;
            border: 1px solid rgba(148, 163, 184, 0.1); border-radius: 16px;
            padding: 1.5rem; text-align: center; transition: all 0.3s ease;
            backdrop-filter: blur(10px);
            color: #f8fafc !important;
        }
        
        .feature-card:hover {
            transform: translateY(-4px); border-color: #3b82f6;
            box-shadow: 0 20px 40px rgba(59, 130, 246, 0.15);
        }
        
        .feature-icon {
            font-size: 2.5rem; margin-bottom: 1rem; color: #3b82f6;
        }
        
        .feature-title {
            font-size: 1.125rem; font-weight: 600; margin-bottom: 0.5rem; color: #f8fafc !important;
        }
        
        .feature-desc {
            color: #94a3b8 !important; font-size: 0.875rem;
        }
        
        .stats-section {
            background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(51, 65, 85, 0.6)) !important;
            border: 1px solid rgba(148, 163, 184, 0.1); border-radius: 20px;
            padding: 2rem; margin-bottom: 3rem; text-align: center;
            backdrop-filter: blur(10px);
            color: #f8fafc !important;
        }
        
        .stats-title {
            font-size: 1.5rem; font-weight: 700; margin-bottom: 1.5rem; color: #f8fafc !important;
        }
        
        .stats-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 2rem;
        }
        
        .stat-item {
            display: flex; flex-direction: column; align-items: center;
        }
        
        .stat-number {
            font-size: 2.5rem; font-weight: 800; color: #3b82f6; margin-bottom: 0.5rem;
        }
        
        .stat-label {
            color: #94a3b8; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 1px;
        }
        
        .form-container {
            background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(51, 65, 85, 0.6));
            border: 1px solid rgba(148, 163, 184, 0.1); border-radius: 20px;
            padding: 2rem; margin-bottom: 2rem; backdrop-filter: blur(10px);
        }
        
        .form-title {
            font-size: 1.5rem; font-weight: 700; margin-bottom: 1.5rem; color: #f8fafc;
            text-align: center; display: flex; align-items: center; justify-content: center; gap: 0.5rem;
        }
        
        .form-grid {
            display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-group label {
            display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;
            font-weight: 600; color: #f8fafc; font-size: 0.875rem;
        }
        
        .form-group input, .form-group select {
            width: 100%; padding: 0.75rem 1rem;
            background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 12px; color: #e2e8f0; font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        .form-group input:focus, .form-group select:focus {
            outline: none; border-color: #3b82f6;
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
        }
        
        .form-group small {
            color: #64748b; font-size: 0.75rem; margin-top: 0.25rem; display: block;
        }
        
        .submit-btn {
            width: 100%; padding: 1rem; font-size: 1.125rem; font-weight: 600;
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            color: white; border: none; border-radius: 12px;
            cursor: pointer; transition: all 0.3s ease;
            text-transform: uppercase; letter-spacing: 1px;
            display: flex; align-items: center; justify-content: center; gap: 0.5rem;
        }
        
        .submit-btn:hover {
            transform: translateY(-2px); box-shadow: 0 10px 30px rgba(59, 130, 246, 0.3);
        }
        .loading, .progress-container, .results {
            background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(51, 65, 85, 0.6));
            border: 1px solid rgba(148, 163, 184, 0.1); border-radius: 20px;
            padding: 2rem; margin: 1rem 0; backdrop-filter: blur(10px);
        }
        
        .loading { display: none; text-align: center; }
        .progress-container { display: none; }
        .results { display: none; }
        
        .loading h3, .progress-container h3 {
            color: #f8fafc; font-size: 1.25rem; margin-bottom: 1rem;
            display: flex; align-items: center; justify-content: center; gap: 0.5rem;
        }
        
        .spinner {
            width: 48px; height: 48px; margin: 0 auto 1rem;
            border: 4px solid rgba(59, 130, 246, 0.2);
            border-top: 4px solid #3b82f6; border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        .progress-bar {
            width: 100%; height: 8px; background: rgba(148, 163, 184, 0.2);
            border-radius: 4px; overflow: hidden; margin: 1rem 0;
        }
        
        .progress-fill {
            height: 100%; background: linear-gradient(90deg, #10b981, #059669);
            width: 0%; transition: width 0.5s ease; position: relative;
        }
        
        .progress-text { 
            position: absolute; top: -25px; left: 50%; transform: translateX(-50%);
            color: #f8fafc; font-weight: 600; font-size: 0.875rem;
        }
        
        .live-logs {
            max-height: 300px; overflow-y: auto; 
            background: rgba(15, 23, 42, 0.8); border-radius: 12px;
            padding: 1rem; margin-top: 1rem; font-family: 'JetBrains Mono', monospace;
            border: 1px solid rgba(148, 163, 184, 0.1);
        }
        
        .log-entry {
            margin-bottom: 0.5rem; font-size: 0.875rem; line-height: 1.4;
            animation: fadeInUp 0.3s ease;
        }
        
        .log-info { color: #3b82f6; }
        .log-success { color: #10b981; }
        .log-warning { color: #f59e0b; }
        .log-error { color: #ef4444; }
        .stats-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px; margin-top: 20px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white; padding: 15px; border-radius: 10px; text-align: center;
        }
        .stat-value { font-size: 1.8em; font-weight: bold; display: block; }
        .stat-label { font-size: 0.9em; opacity: 0.9; }
        .results { display: none; padding: 20px; background: white; border-radius: 10px; margin-top: 20px; }
        .success { color: #27ae60; }
        .error { color: #e74c3c; }
        .spinner {
            width: 40px; height: 40px; margin: 10px auto;
            border: 4px solid #e0e0e0; border-top: 4px solid #667eea;
            border-radius: 50%; animation: spin 1s linear infinite;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @keyframes fadeInUp { 
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .pulse { animation: pulse 2s infinite; }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        @media (max-width: 768px) { .form-row { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-content">
            <div class="nav-brand">
                <i class="fas fa-rocket"></i>
            </div>
            <div class="nav-info">
                <span>Version 2.0</span>
                <span class="nav-badge">Production Ready</span>
            </div>
        </div>
    </nav>

    <div class="container">
        <div class="hero-section">
            <h1 class="hero-title">Advanced Job Data Collection</h1>
            <p class="hero-subtitle">
                Professional-grade scraping system with intelligent account management, 
                real-time progress tracking, and automated deduplication
            </p>
        </div>

        <div class="form-container">
            <div class="form-title">
                <i class="fas fa-cog"></i>
                Scraping Configuration
            </div>
            <form id="scraperForm">
                <div class="form-group">
                    <label>
                        <i class="fas fa-table"></i>
                        Google Sheet ID
                    </label>
                    <input type="text" id="sheet_url" name="sheet_url" 
                           value="1iibXYJ5ZSFZzFIKUyM8d4u3x87FOereMESBfuFW7ZYI" 
                           placeholder="Enter Google Sheets ID" required>
                    <small>Sheet must be shared with: sheetsservice@sheets-autoexpor.iam.gserviceaccount.com</small>
                </div>

                <div class="form-grid">
                    <div class="form-group">
                        <label>
                            <i class="fas fa-search"></i>
                            Keyword Filter
                        </label>
                        <input type="text" id="keyword" name="keyword" 
                               placeholder="e.g., python, react, data scientist">
                        <small>Optional: Filter jobs by keyword for targeted results</small>
                    </div>
                    <div class="form-group">
                        <label>
                            <i class="fas fa-bullseye"></i>
                            Target Jobs
                        </label>
                        <select id="target_jobs" name="target_jobs">
                            <option value="25">25 Jobs</option>
                            <option value="50" selected>50 Jobs</option>
                            <option value="100">100 Jobs</option>
                            <option value="200">200 Jobs</option>
                            <option value="300">300 Jobs</option>
                            <option value="400">400 Jobs</option>
                        </select>
                        <small>System automatically stops when target is reached</small>
                    </div>
                </div>

                <div class="form-group">
                    <label>
                        <i class="fas fa-sliders-h"></i>
                        Scraping Mode
                    </label>
                    <select id="scrape_mode" name="scrape_mode">
                        <option value="conservative">Conservative - Fewer accounts, safer approach</option>
                        <option value="balanced" selected>Balanced - Optimal speed and stability</option>
                        <option value="aggressive">Aggressive - Maximum accounts, fastest results</option>
                        <option value="hybrid">Hybrid - AI-powered adaptive selection</option>
                    </select>
                    <small>Auto-determines optimal account count (1-80 accounts) based on target and mode</small>
                </div>

                <button type="submit" class="submit-btn">
                    <i class="fas fa-rocket"></i>
                    Scrap
                </button>
            </form>
        </div>

        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon"><i class="fas fa-users"></i></div>
                <div class="feature-title">Multi-Account System</div>
                <div class="feature-desc">Auto-scales from 1-80 accounts based on target requirements</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon"><i class="fas fa-chart-line"></i></div>
                <div class="feature-title">Real-Time Tracking</div>
                <div class="feature-desc">Live progress monitoring with detailed analytics</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon"><i class="fas fa-brain"></i></div>
                <div class="feature-title">Smart Prioritization</div>
                <div class="feature-desc">AI-powered account selection based on keyword matching</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon"><i class="fas fa-shield-alt"></i></div>
                <div class="feature-title">Deduplication</div>
                <div class="feature-desc">Thread-safe job ID tracking prevents duplicate collection</div>
            </div>
        </div>

        <div class="stats-section">
            <div class="stats-title">System Capabilities</div>
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-number">80</span>
                    <span class="stat-label">Max Accounts</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">100%</span>
                    <span class="stat-label">Deduplication</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">4</span>
                    <span class="stat-label">Scrape Modes</span>
                </div>
            </div>
        </div>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <h3><i class="fas fa-cog fa-spin"></i> Initializing Professional Scraper</h3>
            <p style="color: #94a3b8;">Preparing optimal account selection and starting concurrent data collection</p>
        </div>

        <div class="progress-container" id="progress-container">
            <h3><i class="fas fa-chart-line"></i> Live Scraping Analytics</h3>
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill">
                    <div class="progress-text" id="progress-text">0%</div>
                </div>
            </div>
            
            <div class="stats-grid" id="stats-grid">
                <div class="stat-card">
                    <span class="stat-value" id="jobs-found">0</span>
                    <span class="stat-label">Jobs Found</span>
                </div>
                <div class="stat-card">
                    <span class="stat-value" id="accounts-used">0</span>
                    <span class="stat-label">Accounts Used</span>
                </div>
                <div class="stat-card">
                    <span class="stat-value" id="matching-jobs">0</span>
                    <span class="stat-label">Keyword Matches</span>
                </div>
                <div class="stat-card">
                    <span class="stat-value" id="current-account">-</span>
                    <span class="stat-label">Current Account</span>
                </div>
            </div>

            <div class="live-logs" id="live-logs">
                <div class="log-entry log-info"><i class="fas fa-rocket"></i> Enterprise scraper initialized</div>
                <div class="log-entry log-info"><i class="fas fa-brain"></i> Smart account prioritization active</div>
            </div>
        </div>

        <div class="results" id="results">
            <div id="results-content"></div>
        </div>
    </div>

    <script>
        let progressInterval;
        let sessionId = null;

        function addLog(message, type = 'info') {
            const logsContainer = document.getElementById('live-logs');
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry log-${type}`;
            logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            logsContainer.appendChild(logEntry);
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }

        function updateProgress(progress, text = '') {
            const progressFill = document.getElementById('progress-fill');
            const progressText = document.getElementById('progress-text');
            progressFill.style.width = progress + '%';
            progressText.textContent = text || `${progress}%`;
        }

        function updateStats(stats) {
            document.getElementById('jobs-found').textContent = stats.jobs_found || 0;
            document.getElementById('accounts-used').textContent = stats.accounts_used || 0;
            document.getElementById('matching-jobs').textContent = stats.matching_jobs || 0;
            document.getElementById('current-account').textContent = stats.current_account || '-';
        }

        function restoreSections() {
            // Restore features and stats sections for new runs
            const featuresGrid = document.querySelector('.features-grid');
            const statsSection = document.querySelector('.stats-section');
            if (featuresGrid) featuresGrid.style.display = 'grid';
            if (statsSection) statsSection.style.display = 'block';
        }

        function startProgressPolling(sessionId) {
            progressInterval = setInterval(async () => {
                try {
                    const response = await fetch(`/progress/${sessionId}`);
                    if (response.ok) {
                        const data = await response.json();
                        if (data.logs) {
                            data.logs.forEach(log => addLog(log.message, log.type));
                        }
                        if (data.progress !== undefined) {
                            updateProgress(data.progress, data.progress_text);
                        }
                        if (data.stats) {
                            updateStats(data.stats);
                        }
                        if (data.completed) {
                            clearInterval(progressInterval);
                            document.getElementById('loading').style.display = 'none';
                            showResults(data.result);
                        }
                    }
                } catch (error) {
                    console.log('Progress polling error:', error);
                }
            }, 2000);
        }

        function showResults(result) {
            const resultsDiv = document.getElementById('results');
            const contentDiv = document.getElementById('results-content');

            if (result.success) {
                contentDiv.innerHTML = `
                    <h2 class="success">✅ Multi-Account Scraping Complete!</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <span class="stat-value">${result.total_jobs}</span>
                            <span class="stat-label">Total Jobs</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-value">${result.filtered_jobs}</span>
                            <span class="stat-label">Keyword Matches</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-value">${result.accounts_used}</span>
                            <span class="stat-label">Accounts Used</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-value">${result.accounts_failed}</span>
                            <span class="stat-label">Failed</span>
                        </div>
                    </div>
                    ${result.all_jobs_sheet ? `<p><strong>📊 All Jobs Sheet:</strong> ${result.all_jobs_sheet}</p>` : ''}
                    ${result.filtered_sheet ? `<p><strong>🎯 Filtered Jobs Sheet:</strong> ${result.filtered_sheet}</p>` : ''}
                    <pre style="white-space: pre-line; margin-top: 20px; font-size: 14px;">${result.message}</pre>
                    <button onclick="restoreSections(); document.getElementById('results').style.display = 'none';" class="submit-btn" style="margin-top: 20px;">
                        <i class="fas fa-plus"></i> Start New Session
                    </button>
                `;
            } else {
                contentDiv.innerHTML = `
                    <h2 class="error">❌ Scraping Failed</h2>
                    <p>${result.message}</p>
                    <button onclick="restoreSections(); document.getElementById('results').style.display = 'none';" class="submit-btn" style="margin-top: 20px;">
                        <i class="fas fa-plus"></i> Start New Session
                    </button>
                `;
            }
            resultsDiv.style.display = 'block';
        }

        document.getElementById('scraperForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            // Reset UI
            document.getElementById('loading').style.display = 'block';
            document.getElementById('progress-container').style.display = 'block';
            document.getElementById('results').style.display = 'none';
            
            // Hide features and stats sections when scraping starts
            const featuresGrid = document.querySelector('.features-grid');
            const statsSection = document.querySelector('.stats-section');
            if (featuresGrid) featuresGrid.style.display = 'none';
            if (statsSection) statsSection.style.display = 'none';
            
            // Clear previous logs
            document.getElementById('live-logs').innerHTML = '';
            addLog('🚀 Starting multi-account scraping session...', 'info');
            
            // Reset progress and stats
            updateProgress(0, 'Initializing...');
            updateStats({});

            const formData = {
                sheet_url: document.getElementById('sheet_url').value,
                keyword: document.getElementById('keyword').value,
                target_jobs: parseInt(document.getElementById('target_jobs').value),
                scrape_mode: document.getElementById('scrape_mode').value
            };

            addLog(`🎯 Target: ${formData.target_jobs} jobs with "${formData.keyword}" keyword`, 'info');
            addLog(`🧠 Auto-selecting optimal accounts in ${formData.scrape_mode} mode`, 'info');

            try {
                const response = await fetch('/scrape_multi_account', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                const result = await response.json();

                if (response.ok && result.session_id) {
                    sessionId = result.session_id;
                    addLog('✅ Session started, monitoring progress...', 'success');
                    startProgressPolling(sessionId);
                } else {
                    // Fallback for immediate response
                    document.getElementById('loading').style.display = 'none';
                    updateProgress(100, 'Complete');
                    showResults(result);
                }

            } catch (error) {
                document.getElementById('loading').style.display = 'none';
                addLog(`❌ Request failed: ${error.message}`, 'error');
                document.getElementById('results').style.display = 'block';
                document.getElementById('results-content').innerHTML = `
                    <h2 class="error">❌ Request Failed</h2>
                    <p>Error: ${error.message}</p>
                `;
            }
        });

        // Cleanup on page unload
        window.addEventListener('beforeunload', function() {
            if (progressInterval) {
                clearInterval(progressInterval);
            }
        });
    </script>
</body>
</html>
<!-- PUZZLE: VE5EME4gKDIwMjUpIC0gTXVsdGktQWNjb3VudCBKb2JSaWdodCBTY3JhcGVy (Base64: TND0N (2025) - Multi-Account JobRight Scraper) -->
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

@app.route('/progress/<session_id>')
def get_progress(session_id):
    """Get real-time progress for a scraping session"""
    with session_lock:
        if session_id not in session_storage:
            return jsonify({"error": "Session not found"}), 404
        
        session_data = session_storage[session_id].copy()
        
        # Clear logs after sending to prevent sending duplicates
        if 'logs' in session_data:
            new_logs = session_data['logs'].copy()
            session_storage[session_id]['logs'] = []
            session_data['logs'] = new_logs
        
        return jsonify(session_data)

def run_scraper_background(session_id, sheet_id, keyword, target_jobs, max_accounts, scrape_mode):
    """Run scraper in background thread with progress tracking"""
    try:
        from enhanced_multi_account_scraper import MultiAccountJobRightScraper
        
        # Add a log to indicate background thread started
        with session_lock:
            if session_id in session_storage:
                session_storage[session_id]['logs'].append({
                    'message': '🔄 Background scraping thread started...',
                    'type': 'info',
                    'timestamp': datetime.now().isoformat()
                })
                session_storage[session_id]['progress_text'] = 'Starting scraper...'
        
        scraper = MultiAccountJobRightScraper(
            session_id=session_id,
            session_storage=session_storage,
            session_lock=session_lock
        )
        
        # Run the enhanced scraper with session tracking
        result = scraper.run_complete_multi_account_scraper(
            sheet_url=sheet_id,
            keyword=keyword,
            target_jobs=target_jobs,
            max_concurrent_accounts=max_accounts,
            scrape_mode=scrape_mode
        )
        
        # Mark as completed
        with session_lock:
            if session_id in session_storage:
                session_storage[session_id]['completed'] = True
                session_storage[session_id]['result'] = result
                session_storage[session_id]['progress'] = 100
                session_storage[session_id]['progress_text'] = 'Complete'
                
    except Exception as e:
        # Mark as failed
        with session_lock:
            if session_id in session_storage:
                session_storage[session_id]['completed'] = True
                session_storage[session_id]['result'] = {
                    'success': False,
                    'message': f'Scraping failed: {str(e)}'
                }
                session_storage[session_id]['progress'] = 100
                session_storage[session_id]['progress_text'] = 'Failed'

def determine_optimal_accounts(target_jobs, scrape_mode, keyword=''):
    """
    Auto-determine optimal number of accounts (1-80) based on target jobs, mode, and keyword.
    """
    # Load account config to check availability
    try:
        with open('accounts_config.json', 'r') as f:
            accounts_data = json.load(f)
            total_available = len(accounts_data['accounts'])
    except:
        total_available = 80  # Fallback
    
    # Calculate base accounts needed based on target
    if target_jobs <= 10:
        base_accounts = min(2, total_available)
    elif target_jobs <= 25:
        base_accounts = min(3, total_available)  
    elif target_jobs <= 50:
        base_accounts = min(5, total_available)
    elif target_jobs <= 100:
        base_accounts = min(8, total_available)
    elif target_jobs <= 200:
        base_accounts = min(15, total_available)
    elif target_jobs <= 400:
        base_accounts = min(25, total_available)
    elif target_jobs <= 800:
        base_accounts = min(40, total_available)
    else:
        base_accounts = min(60, total_available)  # Very large targets
    
    # Adjust based on scrape mode
    if scrape_mode == 'conservative':
        # Use fewer accounts, more careful approach
        optimal = max(1, int(base_accounts * 0.6))
    elif scrape_mode == 'balanced':
        # Use calculated base accounts
        optimal = base_accounts
    elif scrape_mode == 'aggressive':
        # Use more accounts for faster scraping
        optimal = min(int(base_accounts * 1.5), total_available)
    elif scrape_mode == 'hybrid':
        # Smart adjustment based on keyword availability
        if keyword:
            # If we have a keyword, we might have fewer matching accounts
            optimal = max(3, min(base_accounts, int(total_available * 0.3)))
        else:
            # No keyword filter, can use more accounts efficiently
            optimal = min(int(base_accounts * 1.2), total_available)
    else:
        optimal = base_accounts
    
    # Ensure we're within bounds
    optimal = max(1, min(optimal, total_available, 80))
    
    return optimal

@app.route('/scrape_multi_account', methods=['POST'])
def scrape_multi_account():
    try:
        data = request.json or {}

        sheet_id = data.get('sheet_url', '').strip()
        keyword = data.get('keyword', '').strip()
        target_jobs = int(data.get('target_jobs', 50))
        scrape_mode = data.get('scrape_mode', 'balanced')
        
        # Auto-determine optimal account count (1-80 accounts)
        max_accounts = determine_optimal_accounts(target_jobs, scrape_mode, keyword)

        if not sheet_id:
            return jsonify({"success": False, "message": "Sheet ID required"})

        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Initialize session data IMMEDIATELY to prevent race condition
        with session_lock:
            session_storage[session_id] = {
                'progress': 0,
                'progress_text': 'Initializing...',
                'logs': [{
                    'message': '🚀 Session created, preparing to start scraping...',
                    'type': 'info',
                    'timestamp': datetime.now().isoformat()
                }],
                'stats': {
                    'jobs_found': 0,
                    'accounts_used': 0,
                    'matching_jobs': 0,
                    'current_account': '-'
                },
                'completed': False,
                'result': None,
                'started_at': datetime.now().isoformat()
            }
        

        # Start background thread
        thread = threading.Thread(
            target=run_scraper_background,
            args=(session_id, sheet_id, keyword, target_jobs, max_accounts, scrape_mode),
            daemon=True
        )
        thread.start()
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "message": "Scraping started in background",
            "estimated_accounts": max_accounts,
            "target_jobs": target_jobs
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Request error: {str(e)}"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
