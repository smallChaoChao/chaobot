"""Message history viewer web interface.

Provides a simple web UI to query and view message history by session ID.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, render_template_string, request, jsonify

from chaobot.config.manager import ConfigManager

app = Flask(__name__)

# HTML template for the viewer
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chaobot Message Viewer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
        }
        .search-box {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .search-box input {
            width: 100%;
            padding: 12px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 4px;
            margin-bottom: 10px;
        }
        .search-box button {
            background: #007bff;
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 4px;
            cursor: pointer;
        }
        .search-box button:hover {
            background: #0056b3;
        }
        .sessions-list {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .sessions-list h2 {
            margin-bottom: 15px;
            color: #555;
        }
        .session-item {
            padding: 10px;
            border: 1px solid #eee;
            border-radius: 4px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: background 0.2s;
        }
        .session-item:hover {
            background: #f0f0f0;
        }
        .session-item.active {
            background: #e3f2fd;
            border-color: #2196f3;
        }
        .messages-container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .messages-container h2 {
            margin-bottom: 15px;
            color: #555;
        }
        .message {
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 8px;
            border-left: 4px solid;
        }
        .message.user {
            background: #e3f2fd;
            border-left-color: #2196f3;
        }
        .message.assistant {
            background: #f3e5f5;
            border-left-color: #9c27b0;
        }
        .message.system {
            background: #fff3e0;
            border-left-color: #ff9800;
        }
        .message-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 14px;
            color: #666;
        }
        .message-role {
            font-weight: bold;
            text-transform: uppercase;
        }
        .message-content {
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 14px;
            line-height: 1.6;
        }
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        .error {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        .stats {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-item {
            background: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        .stat-label {
            font-size: 14px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Chaobot Message Viewer</h1>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value" id="total-sessions">{{ total_sessions }}</div>
                <div class="stat-label">Total Sessions</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="total-messages">{{ total_messages }}</div>
                <div class="stat-label">Total Messages</div>
            </div>
        </div>

        <div class="search-box">
            <input type="text" id="session-id" placeholder="Enter session ID (e.g., oc_2c8660e69a8a5952678600854a4a9af5 or default)" 
                   value="{{ current_session }}">
            <button onclick="loadSession()">Load Session</button>
            <button onclick="loadAllSessions()" style="background: #28a745;">Refresh Sessions List</button>
        </div>

        <div class="sessions-list" id="sessions-list">
            <h2>📁 Available Sessions</h2>
            <div id="sessions-container">
                {% for session in sessions %}
                <div class="session-item {% if session.id == current_session %}active{% endif %}" 
                     onclick="selectSession('{{ session.id }}')">
                    <strong>{{ session.id }}</strong>
                    <span style="float: right; color: #666;">{{ session.message_count }} messages</span>
                    <div style="font-size: 12px; color: #999; margin-top: 4px;">
                        {{ session.updated_at }}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="messages-container" id="messages-container">
            <h2>💬 Messages</h2>
            {% if messages %}
                {% for msg in messages %}
                <div class="message {{ msg.role }}">
                    <div class="message-header">
                        <span class="message-role">{{ msg.role }}</span>
                        <span>{{ msg.timestamp }}</span>
                    </div>
                    <div class="message-content">{{ msg.content }}</div>
                </div>
                {% endfor %}
            {% else %}
                <div class="empty-state">
                    <p>Select a session to view messages</p>
                </div>
            {% endif %}
        </div>
    </div>

    <script>
        function loadSession() {
            const sessionId = document.getElementById('session-id').value;
            if (sessionId) {
                window.location.href = '/?session=' + encodeURIComponent(sessionId);
            }
        }

        function selectSession(sessionId) {
            document.getElementById('session-id').value = sessionId;
            loadSession();
        }

        function loadAllSessions() {
            window.location.href = '/';
        }

        // Allow Enter key to submit
        document.getElementById('session-id').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                loadSession();
            }
        });
    </script>
</body>
</html>
"""


def get_workspace_path() -> Path:
    """Get the workspace path from config."""
    config = ConfigManager().load()
    return config.workspace_path


def load_session_messages(session_id: str) -> list[dict[str, Any]]:
    """Load messages from a session file.
    
    Args:
        session_id: Session identifier
        
    Returns:
        List of messages
    """
    workspace = get_workspace_path()
    session_file = workspace / "sessions" / f"{session_id}.jsonl"
    
    if not session_file.exists():
        return []
    
    messages = []
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    # Skip metadata lines
                    if data.get("_type") == "metadata":
                        continue
                    # Extract message fields
                    if "role" in data and "content" in data:
                        msg = {
                            "role": data["role"],
                            "content": data.get("content", ""),
                            "timestamp": data.get("timestamp", "")
                        }
                        messages.append(msg)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"Error loading session {session_id}: {e}")
    
    return messages


def get_all_sessions() -> list[dict[str, Any]]:
    """Get list of all available sessions.
    
    Returns:
        List of session info
    """
    workspace = get_workspace_path()
    sessions_dir = workspace / "sessions"
    
    if not sessions_dir.exists():
        return []
    
    sessions = []
    for session_file in sessions_dir.glob("*.jsonl"):
        session_id = session_file.stem
        message_count = 0
        updated_at = ""
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if data.get("_type") == "metadata":
                            message_count = data.get("message_count", 0)
                            updated_at = data.get("updated_at", "")
                        elif "role" in data:
                            message_count += 1
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        
        sessions.append({
            "id": session_id,
            "message_count": message_count,
            "updated_at": updated_at
        })
    
    # Sort by updated_at (newest first)
    sessions.sort(key=lambda x: x["updated_at"], reverse=True)
    return sessions


def get_stats() -> dict[str, int]:
    """Get overall statistics.
    
    Returns:
        Statistics dict
    """
    sessions = get_all_sessions()
    total_messages = sum(s["message_count"] for s in sessions)
    return {
        "total_sessions": len(sessions),
        "total_messages": total_messages
    }


@app.route('/')
def index():
    """Main page."""
    session_id = request.args.get('session', '')
    
    sessions = get_all_sessions()
    messages = []
    
    if session_id:
        messages = load_session_messages(session_id)
    
    stats = get_stats()
    
    return render_template_string(
        HTML_TEMPLATE,
        sessions=sessions,
        messages=messages,
        current_session=session_id,
        total_sessions=stats["total_sessions"],
        total_messages=stats["total_messages"]
    )


@app.route('/api/sessions')
def api_sessions():
    """API endpoint to get all sessions."""
    return jsonify(get_all_sessions())


@app.route('/api/messages/<session_id>')
def api_messages(session_id: str):
    """API endpoint to get messages for a session."""
    messages = load_session_messages(session_id)
    return jsonify(messages)


@app.route('/api/stats')
def api_stats():
    """API endpoint to get statistics."""
    return jsonify(get_stats())


def run_viewer(host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
    """Run the message viewer web server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        debug: Enable debug mode
    """
    print(f"🌐 Message viewer starting at http://{host}:{port}")
    print(f"📁 Workspace: {get_workspace_path()}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_viewer(debug=True)
