"""Flask dashboard application for chaobot configuration management."""

import json
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from chaobot.config.manager import ConfigManager
from chaobot.config.schema import Config


def create_app() -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__, template_folder=str(Path(__file__).parent / "templates"))
    app.config["SECRET_KEY"] = "chaobot-web-ui-secret-key"

    config_manager = ConfigManager()

    @app.route("/")
    def index():
        """Render main configuration page."""
        return render_template("index.html")

    @app.route("/api/config", methods=["GET"])
    def get_config():
        """Get current configuration."""
        try:
            config = config_manager.load(reload=True)
            # Convert to dict for JSON serialization
            data = config.model_dump(exclude={"config_path", "workspace_path"})
            return jsonify({"success": True, "data": data})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/config", methods=["POST"])
    def save_config():
        """Save configuration."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "error": "No data provided"}), 400

            # Create new config from data
            config = Config(**data)
            config.config_path = config_manager.config_path
            config.workspace_path = config_manager.workspace_path

            # Save to file
            config_manager.save(config)

            return jsonify({"success": True, "message": "Configuration saved successfully"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/config/raw", methods=["GET"])
    def get_raw_config():
        """Get raw config file content."""
        try:
            if config_manager.config_path.exists():
                with open(config_manager.config_path) as f:
                    content = f.read()
                return jsonify({"success": True, "content": content})
            else:
                return jsonify({"success": False, "error": "Config file not found"}), 404
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/config/raw", methods=["POST"])
    def save_raw_config():
        """Save raw config file content."""
        try:
            data = request.get_json()
            if not data or "content" not in data:
                return jsonify({"success": False, "error": "No content provided"}), 400

            # Validate JSON
            json.loads(data["content"])

            # Write to file
            config_manager.config_dir.mkdir(parents=True, exist_ok=True)
            with open(config_manager.config_path, "w") as f:
                f.write(data["content"])

            return jsonify({"success": True, "message": "Configuration saved successfully"})
        except json.JSONDecodeError as e:
            return jsonify({"success": False, "error": f"Invalid JSON: {e}"}), 400
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/config/reset", methods=["POST"])
    def reset_config():
        """Reset configuration to defaults."""
        try:
            default_config = Config()
            default_config.config_path = config_manager.config_path
            default_config.workspace_path = config_manager.workspace_path
            config_manager.save(default_config)
            return jsonify({"success": True, "message": "Configuration reset to defaults"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/providers", methods=["GET"])
    def get_providers():
        """Get list of available providers."""
        providers = [
            {"id": "openrouter", "name": "OpenRouter", "description": "Multi-provider API gateway"},
            {"id": "anthropic", "name": "Anthropic", "description": "Claude models"},
            {"id": "openai", "name": "OpenAI", "description": "GPT models"},
            {"id": "deepseek", "name": "DeepSeek", "description": "DeepSeek models"},
            {"id": "groq", "name": "Groq", "description": "Fast inference"},
            {"id": "gemini", "name": "Gemini", "description": "Google Gemini models"},
            {"id": "custom", "name": "Custom", "description": "Custom OpenAI-compatible endpoint"},
        ]
        return jsonify({"success": True, "data": providers})

    @app.route("/api/models", methods=["GET"])
    def get_models():
        """Get list of recommended models."""
        models = [
            # OpenRouter
            {"id": "anthropic/claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "provider": "openrouter"},
            {"id": "anthropic/claude-3-opus-20240229", "name": "Claude 3 Opus", "provider": "openrouter"},
            {"id": "openai/gpt-4o", "name": "GPT-4o", "provider": "openrouter"},
            {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openrouter"},
            {"id": "deepseek/deepseek-chat", "name": "DeepSeek Chat", "provider": "openrouter"},
            {"id": "google/gemini-pro", "name": "Gemini Pro", "provider": "openrouter"},
            {"id": "meta-llama/llama-3.1-70b-instruct", "name": "Llama 3.1 70B", "provider": "openrouter"},
            # Qwen (Alibaba)
            {"id": "qwen-max", "name": "Qwen Max", "provider": "custom"},
            {"id": "qwen-plus", "name": "Qwen Plus", "provider": "custom"},
            {"id": "qwen-turbo", "name": "Qwen Turbo", "provider": "custom"},
            {"id": "qwen3.5-plus", "name": "Qwen 3.5 Plus", "provider": "custom"},
            # Anthropic direct
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "provider": "anthropic"},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "provider": "anthropic"},
            # OpenAI direct
            {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "provider": "openai"},
            # DeepSeek direct
            {"id": "deepseek-chat", "name": "DeepSeek Chat", "provider": "deepseek"},
            {"id": "deepseek-coder", "name": "DeepSeek Coder", "provider": "deepseek"},
            # Groq
            {"id": "llama-3.1-70b-versatile", "name": "Llama 3.1 70B", "provider": "groq"},
            {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B", "provider": "groq"},
            # Gemini
            {"id": "gemini-pro", "name": "Gemini Pro", "provider": "gemini"},
            {"id": "gemini-pro-vision", "name": "Gemini Pro Vision", "provider": "gemini"},
        ]
        return jsonify({"success": True, "data": models})

    return app


def main():
    """Run the web application."""
    app = create_app()
    app.run(host="127.0.0.1", port=8080, debug=True)


if __name__ == "__main__":
    main()
