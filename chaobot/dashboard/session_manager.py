"""Session management web interface.

Provides a web UI to manage conversation sessions with full CRUD operations.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, render_template_string, request, jsonify, redirect, url_for

from chaobot.config.manager import ConfigManager

app = Flask(__name__)

# HTML template for the session manager
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chaobot Session Manager</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0F172A;
            --bg-secondary: #1E293B;
            --bg-tertiary: #334155;
            --bg-card: #1E293B;
            --text-primary: #F8FAFC;
            --text-secondary: #94A3B8;
            --text-muted: #64748B;
            --accent-primary: #22C55E;
            --accent-secondary: #16A34A;
            --accent-hover: #15803D;
            --accent-blue: #3B82F6;
            --accent-purple: #8B5CF6;
            --accent-orange: #F97316;
            --border-color: #334155;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -2px rgba(0, 0, 0, 0.4);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -4px rgba(0, 0, 0, 0.5);
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 16px;
            --transition-fast: 150ms ease;
            --transition-normal: 200ms ease;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Open Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px;
        }

        /* Header */
        header {
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
            padding: 32px;
            border-radius: var(--radius-lg);
            margin-bottom: 24px;
            box-shadow: var(--shadow-lg);
            border: 1px solid var(--border-color);
            position: relative;
            overflow: hidden;
        }

        header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--accent-primary), var(--accent-blue));
        }

        header h1 {
            font-family: 'Poppins', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 16px;
        }

        header h1 .icon {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-blue));
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        header p {
            color: var(--text-secondary);
            font-size: 1rem;
        }

        /* Stats */
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }

        .stat-item {
            background: var(--bg-card);
            padding: 20px 24px;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-color);
            transition: transform var(--transition-normal), box-shadow var(--transition-normal);
        }

        .stat-item:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        .stat-value {
            font-family: 'Poppins', sans-serif;
            font-size: 28px;
            font-weight: 700;
            color: var(--accent-primary);
            margin-bottom: 4px;
        }

        .stat-label {
            font-size: 14px;
            color: var(--text-secondary);
        }

        /* Main Content */
        .main-content {
            display: grid;
            grid-template-columns: 380px 1fr;
            gap: 24px;
        }

        @media (max-width: 1024px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }

        /* Panel */
        .panel {
            background: var(--bg-card);
            padding: 24px;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-color);
        }

        .panel h2 {
            font-family: 'Poppins', sans-serif;
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 20px;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .panel h2 .icon {
            width: 28px;
            height: 28px;
            background: var(--bg-tertiary);
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* Toolbar */
        .toolbar {
            display: flex;
            gap: 10px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }

        /* Search Box */
        .search-box {
            position: relative;
            margin-bottom: 16px;
        }

        .search-box input {
            width: 100%;
            padding: 12px 16px 12px 44px;
            background: var(--bg-primary);
            border: 2px solid var(--border-color);
            border-radius: var(--radius-md);
            font-size: 14px;
            color: var(--text-primary);
            transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
        }

        .search-box input:focus {
            outline: none;
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.15);
        }

        .search-box input::placeholder {
            color: var(--text-muted);
        }

        .search-box::before {
            content: '';
            position: absolute;
            left: 16px;
            top: 50%;
            transform: translateY(-50%);
            width: 18px;
            height: 18px;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%2364748B' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cpath d='m21 21-4.3-4.3'/%3E%3C/svg%3E");
            background-size: contain;
        }

        /* Buttons */
        .btn {
            padding: 10px 18px;
            border: none;
            border-radius: var(--radius-md);
            cursor: pointer;
            font-family: 'Poppins', sans-serif;
            font-size: 13px;
            font-weight: 600;
            transition: all var(--transition-normal);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--accent-blue), #2563EB);
            color: white;
            box-shadow: 0 4px 14px rgba(59, 130, 246, 0.3);
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
        }

        .btn-success {
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            color: white;
            box-shadow: 0 4px 14px rgba(34, 197, 94, 0.3);
        }

        .btn-success:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(34, 197, 94, 0.4);
        }

        .btn-danger {
            background: linear-gradient(135deg, #EF4444, #DC2626);
            color: white;
            box-shadow: 0 4px 14px rgba(239, 68, 68, 0.3);
        }

        .btn-danger:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
        }

        .btn-warning {
            background: linear-gradient(135deg, var(--accent-orange), #EA580C);
            color: white;
            box-shadow: 0 4px 14px rgba(249, 115, 22, 0.3);
        }

        .btn-warning:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(249, 115, 22, 0.4);
        }

        .btn-secondary {
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }

        .btn-secondary:hover {
            background: var(--bg-secondary);
            border-color: var(--text-secondary);
        }

        .btn-sm {
            padding: 6px 12px;
            font-size: 12px;
        }

        .btn.loading {
            position: relative;
            color: transparent !important;
            pointer-events: none;
        }

        .btn.loading::after {
            content: '';
            position: absolute;
            width: 16px;
            height: 16px;
            top: 50%;
            left: 50%;
            margin-left: -8px;
            margin-top: -8px;
            border: 2px solid transparent;
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Session Item */
        .session-item {
            padding: 16px;
            background: var(--bg-primary);
            border: 2px solid var(--border-color);
            border-radius: var(--radius-md);
            margin-bottom: 10px;
            cursor: pointer;
            transition: all var(--transition-normal);
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }

        .session-item:hover {
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 1px var(--accent-primary);
        }

        .session-item.active {
            background: rgba(34, 197, 94, 0.1);
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 1px var(--accent-primary);
        }

        .session-info {
            flex: 1;
            min-width: 0;
        }

        .session-id {
            font-family: 'Poppins', sans-serif;
            font-weight: 600;
            color: var(--text-primary);
            font-size: 14px;
            word-break: break-all;
            margin-bottom: 6px;
        }

        .session-meta {
            font-size: 12px;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .session-meta .badge {
            background: var(--bg-tertiary);
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
        }

        .session-actions {
            display: flex;
            gap: 6px;
            margin-left: 10px;
        }

        /* Message */
        .message {
            padding: 20px;
            margin-bottom: 16px;
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-color);
            position: relative;
            transition: all var(--transition-normal);
        }

        .message:hover {
            border-color: var(--accent-blue);
            box-shadow: 0 0 0 1px var(--accent-blue);
        }

        .message.user {
            background: rgba(59, 130, 246, 0.08);
            border-left: 4px solid var(--accent-blue);
        }

        .message.assistant {
            background: rgba(139, 92, 246, 0.08);
            border-left: 4px solid var(--accent-purple);
        }

        .message.system {
            background: rgba(249, 115, 22, 0.08);
            border-left: 4px solid var(--accent-orange);
        }

        .message-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            font-size: 13px;
        }

        .message-role {
            font-family: 'Poppins', sans-serif;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
            padding: 4px 10px;
            border-radius: 4px;
        }

        .message.user .message-role {
            background: rgba(59, 130, 246, 0.2);
            color: #60A5FA;
        }

        .message.assistant .message-role {
            background: rgba(139, 92, 246, 0.2);
            color: #A78BFA;
        }

        .message.system .message-role {
            background: rgba(249, 115, 22, 0.2);
            color: #FB923C;
        }

        .message-timestamp {
            color: var(--text-muted);
            font-size: 12px;
        }

        .message-content {
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Fira Code', 'Monaco', 'Menlo', monospace;
            font-size: 13px;
            line-height: 1.7;
            background: var(--bg-primary);
            padding: 16px;
            border-radius: var(--radius-md);
            color: var(--text-primary);
            max-height: 400px;
            overflow-y: auto;
        }

        .message-actions {
            position: absolute;
            top: 16px;
            right: 16px;
            display: none;
            gap: 6px;
        }

        .message:hover .message-actions {
            display: flex;
        }

        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 80px 20px;
            color: var(--text-secondary);
        }

        .empty-state-icon {
            width: 64px;
            height: 64px;
            background: var(--bg-tertiary);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            color: var(--text-muted);
        }

        /* Form Elements */
        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-family: 'Poppins', sans-serif;
            font-weight: 500;
            font-size: 14px;
            color: var(--text-primary);
        }

        .form-group input,
        .form-group textarea,
        .form-group select {
            width: 100%;
            padding: 12px 16px;
            background: var(--bg-primary);
            border: 2px solid var(--border-color);
            border-radius: var(--radius-md);
            font-size: 14px;
            color: var(--text-primary);
            font-family: inherit;
            transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
        }

        .form-group input:focus,
        .form-group textarea:focus,
        .form-group select:focus {
            outline: none;
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.15);
        }

        .form-group input::placeholder,
        .form-group textarea::placeholder {
            color: var(--text-muted);
        }

        .form-group textarea {
            min-height: 120px;
            resize: vertical;
            font-family: 'Fira Code', 'Monaco', 'Menlo', monospace;
        }

        select {
            cursor: pointer;
            appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2394A3B8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 12px center;
            padding-right: 40px;
        }

        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            z-index: 1000;
            justify-content: center;
            align-items: center;
            backdrop-filter: blur(4px);
        }

        .modal.active {
            display: flex;
            animation: fadeIn 0.2s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .modal-content {
            background: var(--bg-secondary);
            padding: 28px;
            border-radius: var(--radius-lg);
            width: 90%;
            max-width: 560px;
            max-height: 90vh;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow-lg);
            animation: slideUp 0.3s ease;
        }

        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }

        .modal-header h3 {
            font-family: 'Poppins', sans-serif;
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
            margin: 0;
        }

        .close-btn {
            background: var(--bg-tertiary);
            border: none;
            width: 36px;
            height: 36px;
            border-radius: var(--radius-md);
            cursor: pointer;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all var(--transition-fast);
        }

        .close-btn:hover {
            background: var(--border-color);
            color: var(--text-primary);
        }

        /* Toast Notifications */
        .toast-container {
            position: fixed;
            top: 24px;
            right: 24px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .toast {
            padding: 16px 20px;
            border-radius: var(--radius-md);
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow-lg);
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 320px;
            max-width: 420px;
            animation: toastSlideIn 0.3s ease;
            cursor: pointer;
        }

        @keyframes toastSlideIn {
            from { opacity: 0; transform: translateX(100%); }
            to { opacity: 1; transform: translateX(0); }
        }

        @keyframes toastSlideOut {
            from { opacity: 1; transform: translateX(0); }
            to { opacity: 0; transform: translateX(100%); }
        }

        .toast.hiding {
            animation: toastSlideOut 0.3s ease forwards;
        }

        .toast-icon {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .toast.success .toast-icon {
            background: rgba(34, 197, 94, 0.2);
            color: #4ADE80;
        }

        .toast.error .toast-icon {
            background: rgba(239, 68, 68, 0.2);
            color: #F87171;
        }

        .toast-content {
            flex: 1;
        }

        .toast-title {
            font-family: 'Poppins', sans-serif;
            font-weight: 600;
            font-size: 14px;
            color: var(--text-primary);
            margin-bottom: 2px;
        }

        .toast-message {
            font-size: 13px;
            color: var(--text-secondary);
        }

        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-secondary);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--bg-tertiary);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-muted);
        }

        /* Focus Visible */
        *:focus-visible {
            outline: 2px solid var(--accent-primary);
            outline-offset: 2px;
        }

        button:focus-visible,
        input:focus-visible,
        select:focus-visible,
        textarea:focus-visible {
            outline: none;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .container {
                padding: 16px;
            }

            header {
                padding: 24px;
            }

            header h1 {
                font-size: 1.5rem;
                flex-direction: column;
                align-items: flex-start;
                gap: 12px;
            }

            .stats {
                grid-template-columns: 1fr;
            }

            .panel {
                padding: 20px;
            }

            .message-actions {
                display: flex;
                position: static;
                margin-top: 12px;
                justify-content: flex-end;
            }

            .toast {
                min-width: auto;
                max-width: calc(100vw - 32px);
                margin: 0 16px;
            }

            .toast-container {
                right: 0;
                left: 0;
                align-items: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>
                <span class="icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    </svg>
                </span>
                Session Manager
            </h1>
            <p>管理对话会话和消息历史</p>
        </header>

        <!-- Toast Container -->
        <div class="toast-container" id="toast-container"></div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value" id="total-sessions">{{ stats.total_sessions }}</div>
                <div class="stat-label">总会话数</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="total-messages">{{ stats.total_messages }}</div>
                <div class="stat-label">总消息数</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" style="font-size: 18px; word-break: break-all;">{{ current_session[:20] + '...' if current_session and current_session|length > 20 else current_session or '-' }}</div>
                <div class="stat-label">当前会话</div>
            </div>
        </div>

        <div class="main-content">
            <!-- Left Panel: Sessions List -->
            <div class="panel">
                <h2>
                    <span class="icon">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>
                        </svg>
                    </span>
                    会话列表
                </h2>
                
                <div class="toolbar">
                    <button class="btn btn-success" onclick="showCreateSessionModal()">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M5 12h14"/><path d="M12 5v14"/>
                        </svg>
                        新建会话
                    </button>
                    <button class="btn btn-secondary" onclick="loadSessions()">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M16 16h5v5"/>
                        </svg>
                        刷新
                    </button>
                </div>

                <div class="search-box">
                    <input type="text" id="session-search" placeholder="搜索会话..." onkeyup="filterSessions()">
                </div>

                <div id="sessions-list">
                    {% for session in sessions %}
                    <div class="session-item {% if session.id == current_session %}active{% endif %}" data-session-id="{{ session.id }}">
                        <div class="session-info" onclick="selectSession('{{ session.id }}')">
                            <div class="session-id">{{ session.id[:35] }}{% if session.id|length > 35 %}...{% endif %}</div>
                            <div class="session-meta">
                                <span class="badge">{{ session.message_count }} 条消息</span>
                                <span>{{ session.updated_at[:19] if session.updated_at else '未知时间' }}</span>
                            </div>
                        </div>
                        <div class="session-actions">
                            <button class="btn btn-danger btn-sm" onclick="deleteSession('{{ session.id }}', event)">删除</button>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Right Panel: Messages -->
            <div class="panel">
                <h2>
                    <span class="icon">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                        </svg>
                    </span>
                    消息记录
                </h2>
                
                {% if current_session %}
                <div class="toolbar">
                    <button class="btn btn-success" onclick="showAddMessageModal()">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M5 12h14"/><path d="M12 5v14"/>
                        </svg>
                        添加消息
                    </button>
                    <button class="btn btn-danger" onclick="clearSessionMessages('{{ current_session }}')">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                        </svg>
                        清空消息
                    </button>
                </div>
                {% endif %}

                <div id="messages-container">
                    {% if messages %}
                        {% for msg in messages %}
                        <div class="message {{ msg.role }}" data-message-index="{{ loop.index0 }}">
                            <div class="message-actions">
                                <button class="btn btn-warning btn-sm" onclick="editMessage({{ loop.index0 }})">编辑</button>
                                <button class="btn btn-danger btn-sm" onclick="deleteMessage({{ loop.index0 }})">删除</button>
                            </div>
                            <div class="message-header">
                                <span class="message-role">{{ msg.role }}</span>
                                <span class="message-timestamp">{{ msg.timestamp[:19] if msg.timestamp else '无时间戳' }}</span>
                            </div>
                            <div class="message-content">{{ msg.content }}</div>
                        </div>
                        {% endfor %}
                    {% else %}
                        <div class="empty-state">
                            <div class="empty-state-icon">
                                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                                </svg>
                            </div>
                            <p>选择一个会话查看消息</p>
                        </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>

    <!-- Create Session Modal -->
    <div class="modal" id="createSessionModal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>创建新会话</h3>
                <button class="close-btn" onclick="closeModal('createSessionModal')">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
                    </svg>
                </button>
            </div>
            <div class="form-group">
                <label>会话 ID（可选，留空将自动生成）</label>
                <input type="text" id="new-session-id" placeholder="例如: my-session-001">
            </div>
            <button class="btn btn-success" onclick="createSession()" id="btn-create-session">创建会话</button>
        </div>
    </div>

    <!-- Add Message Modal -->
    <div class="modal" id="addMessageModal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>添加消息</h3>
                <button class="close-btn" onclick="closeModal('addMessageModal')">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
                    </svg>
                </button>
            </div>
            <div class="form-group">
                <label>角色</label>
                <select id="new-message-role">
                    <option value="user">User</option>
                    <option value="assistant">Assistant</option>
                    <option value="system">System</option>
                </select>
            </div>
            <div class="form-group">
                <label>内容</label>
                <textarea id="new-message-content" placeholder="输入消息内容..."></textarea>
            </div>
            <button class="btn btn-success" onclick="addMessage()" id="btn-add-message">添加消息</button>
        </div>
    </div>

    <!-- Edit Message Modal -->
    <div class="modal" id="editMessageModal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>编辑消息</h3>
                <button class="close-btn" onclick="closeModal('editMessageModal')">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
                    </svg>
                </button>
            </div>
            <input type="hidden" id="edit-message-index">
            <div class="form-group">
                <label>角色</label>
                <select id="edit-message-role">
                    <option value="user">User</option>
                    <option value="assistant">Assistant</option>
                    <option value="system">System</option>
                </select>
            </div>
            <div class="form-group">
                <label>内容</label>
                <textarea id="edit-message-content"></textarea>
            </div>
            <button class="btn btn-primary" onclick="updateMessage()" id="btn-update-message">更新消息</button>
        </div>
    </div>

    <script>
        let currentSessionId = '{{ current_session }}';
        let messages = {{ messages | tojson }};

        // Toast 提示
        function showToast(title, message, type = 'success', duration = 3000) {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            
            const iconSvg = type === 'success' 
                ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>'
                : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" x2="9" y1="9" y2="15"/><line x1="9" x2="15" y1="9" y2="15"/></svg>';
            
            toast.innerHTML = `
                <div class="toast-icon">${iconSvg}</div>
                <div class="toast-content">
                    <div class="toast-title">${title}</div>
                    <div class="toast-message">${message}</div>
                </div>
            `;
            
            toast.addEventListener('click', () => hideToast(toast));
            container.appendChild(toast);
            
            setTimeout(() => hideToast(toast), duration);
        }

        function hideToast(toast) {
            toast.classList.add('hiding');
            setTimeout(() => toast.remove(), 300);
        }

        // 设置按钮加载状态
        function setButtonLoading(buttonId, loading = true) {
            const button = document.getElementById(buttonId);
            if (button) {
                if (loading) {
                    button.classList.add('loading');
                    button.disabled = true;
                } else {
                    button.classList.remove('loading');
                    button.disabled = false;
                }
            }
        }

        function selectSession(sessionId) {
            window.location.href = '/?session=' + encodeURIComponent(sessionId);
        }

        function filterSessions() {
            const searchTerm = document.getElementById('session-search').value.toLowerCase();
            const items = document.querySelectorAll('.session-item');
            items.forEach(item => {
                const sessionId = item.getAttribute('data-session-id').toLowerCase();
                item.style.display = sessionId.includes(searchTerm) ? 'flex' : 'none';
            });
        }

        function showCreateSessionModal() {
            document.getElementById('createSessionModal').classList.add('active');
            document.getElementById('new-session-id').focus();
        }

        function showAddMessageModal() {
            if (!currentSessionId) {
                showToast('请先选择会话', '请选择一个会话后再添加消息', 'error');
                return;
            }
            document.getElementById('addMessageModal').classList.add('active');
            document.getElementById('new-message-content').focus();
        }

        function editMessage(index) {
            const msg = messages[index];
            document.getElementById('edit-message-index').value = index;
            document.getElementById('edit-message-role').value = msg.role;
            document.getElementById('edit-message-content').value = msg.content;
            document.getElementById('editMessageModal').classList.add('active');
        }

        function closeModal(modalId) {
            document.getElementById(modalId).classList.remove('active');
        }

        async function createSession() {
            const sessionId = document.getElementById('new-session-id').value;
            setButtonLoading('btn-create-session', true);
            
            try {
                const response = await fetch('/api/sessions', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({session_id: sessionId})
                });
                const result = await response.json();
                if (result.success) {
                    showToast('创建成功', `会话 "${result.session_id}" 已创建`);
                    window.location.href = '/?session=' + encodeURIComponent(result.session_id);
                } else {
                    showToast('创建失败', result.error, 'error');
                    setButtonLoading('btn-create-session', false);
                }
            } catch (e) {
                showToast('创建失败', e.message, 'error');
                setButtonLoading('btn-create-session', false);
            }
        }

        async function deleteSession(sessionId, event) {
            event.stopPropagation();
            if (!confirm('确定要删除会话 "' + sessionId + '" 吗？此操作不可恢复。')) {
                return;
            }
            
            try {
                const response = await fetch('/api/sessions/' + encodeURIComponent(sessionId), {
                    method: 'DELETE'
                });
                const result = await response.json();
                if (result.success) {
                    showToast('删除成功', '会话已删除');
                    window.location.href = '/';
                } else {
                    showToast('删除失败', result.error, 'error');
                }
            } catch (e) {
                showToast('删除失败', e.message, 'error');
            }
        }

        async function addMessage() {
            const role = document.getElementById('new-message-role').value;
            const content = document.getElementById('new-message-content').value;
            if (!content.trim()) {
                showToast('内容不能为空', '请输入消息内容', 'error');
                return;
            }
            
            setButtonLoading('btn-add-message', true);
            
            try {
                const response = await fetch('/api/sessions/' + encodeURIComponent(currentSessionId) + '/messages', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({role, content})
                });
                const result = await response.json();
                if (result.success) {
                    showToast('添加成功', '消息已添加');
                    window.location.reload();
                } else {
                    showToast('添加失败', result.error, 'error');
                    setButtonLoading('btn-add-message', false);
                }
            } catch (e) {
                showToast('添加失败', e.message, 'error');
                setButtonLoading('btn-add-message', false);
            }
        }

        async function updateMessage() {
            const index = document.getElementById('edit-message-index').value;
            const role = document.getElementById('edit-message-role').value;
            const content = document.getElementById('edit-message-content').value;
            
            setButtonLoading('btn-update-message', true);
            
            try {
                const response = await fetch('/api/sessions/' + encodeURIComponent(currentSessionId) + '/messages/' + index, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({role, content})
                });
                const result = await response.json();
                if (result.success) {
                    showToast('更新成功', '消息已更新');
                    window.location.reload();
                } else {
                    showToast('更新失败', result.error, 'error');
                    setButtonLoading('btn-update-message', false);
                }
            } catch (e) {
                showToast('更新失败', e.message, 'error');
                setButtonLoading('btn-update-message', false);
            }
        }

        async function deleteMessage(index) {
            if (!confirm('确定要删除这条消息吗？')) {
                return;
            }
            
            try {
                const response = await fetch('/api/sessions/' + encodeURIComponent(currentSessionId) + '/messages/' + index, {
                    method: 'DELETE'
                });
                const result = await response.json();
                if (result.success) {
                    showToast('删除成功', '消息已删除');
                    window.location.reload();
                } else {
                    showToast('删除失败', result.error, 'error');
                }
            } catch (e) {
                showToast('删除失败', e.message, 'error');
            }
        }

        async function clearSessionMessages(sessionId) {
            if (!confirm('确定要清空此会话的所有消息吗？此操作不可恢复。')) {
                return;
            }
            
            try {
                const response = await fetch('/api/sessions/' + encodeURIComponent(sessionId) + '/messages', {
                    method: 'DELETE'
                });
                const result = await response.json();
                if (result.success) {
                    showToast('清空成功', '所有消息已清空');
                    window.location.reload();
                } else {
                    showToast('清空失败', result.error, 'error');
                }
            } catch (e) {
                showToast('清空失败', e.message, 'error');
            }
        }

        async function loadSessions() {
            window.location.reload();
        }

        // Close modals when clicking outside
        window.onclick = function(event) {
            if (event.target.classList.contains('modal')) {
                event.target.classList.remove('active');
            }
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                document.querySelectorAll('.modal').forEach(modal => {
                    modal.classList.remove('active');
                });
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
    """Load messages from a session file."""
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
                    if data.get("_type") == "metadata":
                        continue
                    if "role" in data and "content" in data:
                        msg = {
                            "role": data["role"],
                            "content": data.get("content", ""),
                            "timestamp": data.get("timestamp", datetime.now().isoformat())
                        }
                        messages.append(msg)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"Error loading session {session_id}: {e}")
    
    return messages


def save_session_messages(session_id: str, messages: list[dict[str, Any]]) -> bool:
    """Save messages to a session file."""
    workspace = get_workspace_path()
    session_file = workspace / "sessions" / f"{session_id}.jsonl"
    
    try:
        lines = []
        # Add metadata
        metadata = {
            "_type": "metadata",
            "key": f"web:{session_id}",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "message_count": len(messages)
        }
        lines.append(json.dumps(metadata, ensure_ascii=False))
        
        # Add messages
        for msg in messages:
            line = {
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg.get("timestamp", datetime.now().isoformat())
            }
            lines.append(json.dumps(line, ensure_ascii=False))
        
        with open(session_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        return True
    except Exception as e:
        print(f"Error saving session {session_id}: {e}")
        return False


def get_all_sessions() -> list[dict[str, Any]]:
    """Get list of all available sessions."""
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
    
    sessions.sort(key=lambda x: x["updated_at"], reverse=True)
    return sessions


def get_stats() -> dict[str, int]:
    """Get overall statistics."""
    sessions = get_all_sessions()
    total_messages = sum(s["message_count"] for s in sessions)
    return {
        "total_sessions": len(sessions),
        "total_messages": total_messages
    }


# Flask routes
@app.route('/')
def index():
    """Main page."""
    session_id = request.args.get('session', '')
    sessions = get_all_sessions()
    messages = load_session_messages(session_id) if session_id else []
    stats = get_stats()
    
    return render_template_string(
        HTML_TEMPLATE,
        sessions=sessions,
        messages=messages,
        current_session=session_id,
        stats=stats
    )


# API Routes
@app.route('/api/sessions', methods=['GET'])
def api_get_sessions():
    """Get all sessions."""
    return jsonify(get_all_sessions())


@app.route('/api/sessions', methods=['POST'])
def api_create_session():
    """Create a new session."""
    data = request.json or {}
    session_id = data.get('session_id') or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    # Create empty session
    if save_session_messages(session_id, []):
        return jsonify({"success": True, "session_id": session_id})
    else:
        return jsonify({"success": False, "error": "Failed to create session"}), 500


@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def api_delete_session(session_id: str):
    """Delete a session."""
    workspace = get_workspace_path()
    session_file = workspace / "sessions" / f"{session_id}.jsonl"
    
    try:
        if session_file.exists():
            session_file.unlink()
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Session not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/sessions/<session_id>/messages', methods=['GET'])
def api_get_messages(session_id: str):
    """Get messages for a session."""
    messages = load_session_messages(session_id)
    return jsonify(messages)


@app.route('/api/sessions/<session_id>/messages', methods=['POST'])
def api_add_message(session_id: str):
    """Add a message to a session."""
    data = request.json or {}
    role = data.get('role', 'user')
    content = data.get('content', '')
    
    if not content:
        return jsonify({"success": False, "error": "Content is required"}), 400
    
    messages = load_session_messages(session_id)
    messages.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    
    if save_session_messages(session_id, messages):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Failed to save message"}), 500


@app.route('/api/sessions/<session_id>/messages/<int:message_index>', methods=['PUT'])
def api_update_message(session_id: str, message_index: int):
    """Update a message in a session."""
    data = request.json or {}
    role = data.get('role')
    content = data.get('content')
    
    messages = load_session_messages(session_id)
    if message_index < 0 or message_index >= len(messages):
        return jsonify({"success": False, "error": "Message not found"}), 404
    
    if role:
        messages[message_index]["role"] = role
    if content is not None:
        messages[message_index]["content"] = content
    messages[message_index]["timestamp"] = datetime.now().isoformat()
    
    if save_session_messages(session_id, messages):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Failed to update message"}), 500


@app.route('/api/sessions/<session_id>/messages/<int:message_index>', methods=['DELETE'])
def api_delete_message(session_id: str, message_index: int):
    """Delete a message from a session."""
    messages = load_session_messages(session_id)
    if message_index < 0 or message_index >= len(messages):
        return jsonify({"success": False, "error": "Message not found"}), 404
    
    messages.pop(message_index)
    
    if save_session_messages(session_id, messages):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Failed to delete message"}), 500


@app.route('/api/sessions/<session_id>/messages', methods=['DELETE'])
def api_clear_messages(session_id: str):
    """Clear all messages from a session."""
    if save_session_messages(session_id, []):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Failed to clear messages"}), 500


@app.route('/api/stats')
def api_stats():
    """Get statistics."""
    return jsonify(get_stats())


def run_manager(host: str = "127.0.0.1", port: int = 5000):
    """Run the session manager web server."""
    print(f"🌐 Session manager starting at http://{host}:{port}")
    print(f"📁 Workspace: {get_workspace_path()}")
    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    run_manager(debug=True)
