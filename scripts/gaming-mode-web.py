#!/usr/bin/env python3
"""
Web-based Gaming Mode Dashboard
Run with: python gaming-mode-web.py
Access at: http://localhost:8080
"""

from flask import Flask, render_template_string, jsonify, request
import requests
import threading
import time
from datetime import datetime

app = Flask(__name__)
MANAGER_URL = "http://localhost:8000"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Local AI Gaming Mode</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #1e1e1e 0%, #2b2b2b 100%);
            color: #ffffff;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #4a9eff 0%, #51c878 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .status-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
        }
        
        .status-card h2 {
            font-size: 1.2em;
            margin-bottom: 15px;
            color: #4a9eff;
        }
        
        .status-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .status-item:last-child {
            border-bottom: none;
        }
        
        .status-label {
            font-weight: 500;
        }
        
        .status-value {
            font-weight: bold;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 0.9em;
        }
        
        .status-value.enabled {
            background: #4a9eff;
            color: #ffffff;
        }
        
        .status-value.disabled {
            background: rgba(255, 255, 255, 0.1);
            color: #888888;
        }
        
        .status-value.safe {
            background: #51c878;
            color: #ffffff;
        }
        
        .status-value.not-safe {
            background: #ff6b6b;
            color: #ffffff;
        }
        
        .status-value.connected {
            background: #51c878;
            color: #ffffff;
        }
        
        .status-value.disconnected {
            background: #ff6b6b;
            color: #ffffff;
        }
        
        .models-list {
            max-height: 300px;
            overflow-y: auto;
            margin-top: 10px;
        }
        
        .model-item {
            background: rgba(255, 255, 255, 0.03);
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 8px;
            border-left: 3px solid #4a9eff;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9em;
        }
        
        .model-item.empty {
            text-align: center;
            color: #888888;
            border-left: none;
            padding: 20px;
        }
        
        .buttons {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 20px;
        }
        
        button {
            padding: 15px 25px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-gaming-mode {
            background: linear-gradient(135deg, #4a9eff 0%, #5aaeff 100%);
            color: #ffffff;
        }
        
        .btn-gaming-mode.enabled {
            background: linear-gradient(135deg, #ff6b6b 0%, #ff7b7b 100%);
        }
        
        .btn-stop-all {
            background: linear-gradient(135deg, #ff6b6b 0%, #ff7b7b 100%);
            color: #ffffff;
        }
        
        .btn-refresh {
            background: rgba(255, 255, 255, 0.1);
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .error-message {
            background: rgba(255, 107, 107, 0.2);
            border: 1px solid #ff6b6b;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
            color: #ff6b6b;
        }
        
        .last-updated {
            text-align: center;
            color: #888888;
            font-size: 0.85em;
            margin-top: 20px;
        }
        
        .spinner {
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top: 3px solid #4a9eff;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
            display: inline-block;
            margin-left: 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @media (max-width: 600px) {
            .buttons {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 Gaming Mode</h1>
            <p style="color: #888888;">Local AI Resource Management</p>
        </div>
        
        <div class="status-card">
            <h2>Connection Status</h2>
            <div class="status-item">
                <span class="status-label">Manager</span>
                <span class="status-value" id="connection-status">Checking...</span>
            </div>
            <div class="status-item">
                <span class="status-label">Last Updated</span>
                <span class="status-value" id="last-updated">-</span>
            </div>
        </div>
        
        <div class="status-card">
            <h2>System Status</h2>
            <div class="status-item">
                <span class="status-label">Gaming Mode</span>
                <span class="status-value" id="gaming-mode-status">Checking...</span>
            </div>
            <div class="status-item">
                <span class="status-label">Safe to Game</span>
                <span class="status-value" id="safe-status">Checking...</span>
            </div>
        </div>
        
        <div class="status-card">
            <h2>Running Models</h2>
            <div class="models-list" id="models-list">
                <div class="model-item empty">Loading...</div>
            </div>
        </div>
        
        <div class="buttons">
            <button class="btn-gaming-mode" id="gaming-mode-btn" onclick="toggleGamingMode()" disabled>
                Enable Gaming Mode
            </button>
            <button class="btn-stop-all" id="stop-all-btn" onclick="stopAllModels()" disabled>
                Stop All Models
            </button>
        </div>
        
        <button class="btn-refresh" onclick="refreshStatus()" style="width: 100%; margin-top: 10px;">
            🔄 Refresh Status
        </button>
        
        <div id="error-message" style="display: none;"></div>
        
        <div class="last-updated" id="last-updated-text"></div>
    </div>
    
    <script>
        let autoRefreshInterval;
        
        function updateConnectionStatus(connected) {
            const statusEl = document.getElementById('connection-status');
            if (connected) {
                statusEl.textContent = 'Connected';
                statusEl.className = 'status-value connected';
            } else {
                statusEl.textContent = 'Disconnected';
                statusEl.className = 'status-value disconnected';
            }
        }
        
        function updateStatus(data) {
            if (!data) {
                updateConnectionStatus(false);
                document.getElementById('gaming-mode-status').textContent = 'Unknown';
                document.getElementById('safe-status').textContent = 'Unknown';
                document.getElementById('models-list').innerHTML = '<div class="model-item empty">Cannot connect to manager</div>';
                document.getElementById('gaming-mode-btn').disabled = true;
                document.getElementById('stop-all-btn').disabled = true;
                showError('Cannot connect to Local AI Manager. Make sure it\'s running at ' + '{{ manager_url }}');
                return;
            }
            
            updateConnectionStatus(true);
            hideError();
            
            // Update gaming mode status
            const gamingMode = data.gaming_mode || false;
            const gamingModeEl = document.getElementById('gaming-mode-status');
            const gamingModeBtn = document.getElementById('gaming-mode-btn');
            
            if (gamingMode) {
                gamingModeEl.textContent = 'ENABLED';
                gamingModeEl.className = 'status-value enabled';
                gamingModeBtn.textContent = 'Disable Gaming Mode';
                gamingModeBtn.classList.add('enabled');
            } else {
                gamingModeEl.textContent = 'DISABLED';
                gamingModeEl.className = 'status-value disabled';
                gamingModeBtn.textContent = 'Enable Gaming Mode';
                gamingModeBtn.classList.remove('enabled');
            }
            
            // Update safe to game status
            const safeToGame = data.safe_to_game || false;
            const safeEl = document.getElementById('safe-status');
            if (safeToGame) {
                safeEl.textContent = 'YES ✓';
                safeEl.className = 'status-value safe';
            } else {
                const runningCount = (data.running_models || []).length;
                safeEl.textContent = runningCount > 0 ? `NO (${runningCount} running)` : 'NO';
                safeEl.className = 'status-value not-safe';
            }
            
            // Update models list
            const modelsList = document.getElementById('models-list');
            const runningModels = data.running_models || [];
            
            if (runningModels.length === 0) {
                modelsList.innerHTML = '<div class="model-item empty">(no models running)</div>';
            } else {
                modelsList.innerHTML = runningModels.map(model => {
                    const idle = model.idle_seconds !== null 
                        ? `${Math.floor(model.idle_seconds / 60)}m ${model.idle_seconds % 60}s idle`
                        : 'active';
                    return `<div class="model-item">${model.name} (${model.type}) - ${idle}</div>`;
                }).join('');
            }
            
            // Enable buttons
            document.getElementById('gaming-mode-btn').disabled = false;
            document.getElementById('stop-all-btn').disabled = false;
            
            // Update last updated time
            const now = new Date();
            document.getElementById('last-updated').textContent = now.toLocaleTimeString();
            document.getElementById('last-updated-text').textContent = `Last updated: ${now.toLocaleString()}`;
        }
        
        async function refreshStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                updateStatus(data);
            } catch (error) {
                updateStatus(null);
            }
        }
        
        async function toggleGamingMode() {
            const btn = document.getElementById('gaming-mode-btn');
            btn.disabled = true;
            
            try {
                const currentMode = document.getElementById('gaming-mode-status').textContent === 'ENABLED';
                const response = await fetch('/api/gaming-mode', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ enable: !currentMode })
                });
                
                if (response.ok) {
                    await refreshStatus();
                } else {
                    const error = await response.json();
                    showError('Failed to toggle gaming mode: ' + (error.error || 'Unknown error'));
                }
            } catch (error) {
                showError('Error: ' + error.message);
            } finally {
                btn.disabled = false;
            }
        }
        
        async function stopAllModels() {
            if (!confirm('Stop all running models? This will free up GPU memory.')) {
                return;
            }
            
            const btn = document.getElementById('stop-all-btn');
            btn.disabled = true;
            
            try {
                const response = await fetch('/api/stop-all', {
                    method: 'POST'
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    if (result.failed && result.failed.length > 0) {
                        showError(`Stopped ${result.stopped.length} model(s), but ${result.failed.length} failed.`);
                    } else {
                        showError(`Successfully stopped ${result.stopped.length} model(s).`, 'success');
                    }
                    await refreshStatus();
                } else {
                    showError('Failed to stop models: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                showError('Error: ' + error.message);
            } finally {
                btn.disabled = false;
            }
        }
        
        function showError(message, type = 'error') {
            const errorEl = document.getElementById('error-message');
            errorEl.textContent = message;
            errorEl.style.display = 'block';
            errorEl.className = 'error-message';
            if (type === 'success') {
                errorEl.style.background = 'rgba(81, 200, 120, 0.2)';
                errorEl.style.borderColor = '#51c878';
                errorEl.style.color = '#51c878';
            }
            setTimeout(() => {
                errorEl.style.display = 'none';
            }, 5000);
        }
        
        function hideError() {
            document.getElementById('error-message').style.display = 'none';
        }
        
        // Auto-refresh every 2 seconds
        function startAutoRefresh() {
            refreshStatus();
            autoRefreshInterval = setInterval(refreshStatus, 2000);
        }
        
        // Initial load
        startAutoRefresh();
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE.replace('{{ manager_url }}', MANAGER_URL))


@app.route('/api/status')
def api_status():
    """Proxy status request to manager."""
    try:
        response = requests.get(f"{MANAGER_URL}/status", timeout=2)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 503


@app.route('/api/gaming-mode', methods=['POST'])
def api_gaming_mode():
    """Proxy gaming mode toggle to manager."""
    try:
        data = request.json
        response = requests.post(
            f"{MANAGER_URL}/gaming-mode",
            json=data,
            timeout=5
        )
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 503


@app.route('/api/stop-all', methods=['POST'])
def api_stop_all():
    """Proxy stop-all request to manager."""
    try:
        response = requests.post(f"{MANAGER_URL}/stop-all", timeout=10)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 503


if __name__ == '__main__':
    print("=" * 60)
    print("Local AI Gaming Mode Web Dashboard")
    print("=" * 60)
    print(f"Access at: http://localhost:8080")
    print(f"Manager URL: {MANAGER_URL}")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8080, debug=False)

