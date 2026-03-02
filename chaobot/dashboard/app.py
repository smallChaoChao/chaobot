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
        """Get list of recommended models in LiteLLM format.
        
        Note: LiteLLM supports 100+ providers. Users can use any model
        in the format: provider/model (e.g., "openai/gpt-4o", "anthropic/claude-3-5-sonnet")
        See: https://docs.litellm.ai/docs/providers
        """
        models = [
            # Popular models - Anthropic
            {"id": "anthropic/claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet"},
            {"id": "anthropic/claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku"},
            # Popular models - OpenAI
            {"id": "openai/gpt-4o", "name": "GPT-4o"},
            {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini"},
            {"id": "openai/o1-preview", "name": "o1 Preview"},
            # Popular models - DeepSeek
            {"id": "deepseek/deepseek-chat", "name": "DeepSeek Chat"},
            {"id": "deepseek/deepseek-coder", "name": "DeepSeek Coder"},
            # Popular models - Groq (fast inference)
            {"id": "groq/llama-3.1-70b-versatile", "name": "Llama 3.1 70B (Groq)"},
            # Popular models - Gemini
            {"id": "gemini/gemini-1.5-pro", "name": "Gemini 1.5 Pro"},
            {"id": "gemini/gemini-1.5-flash", "name": "Gemini 1.5 Flash"},
            # OpenRouter (multi-provider gateway)
            {"id": "openrouter/anthropic/claude-3-5-sonnet", "name": "Claude 3.5 Sonnet (OpenRouter)"},
            {"id": "openrouter/openai/gpt-4o", "name": "GPT-4o (OpenRouter)"},
            # Custom endpoints (Aliyun DashScope, etc.)
            {"id": "openai/qwen-max", "name": "Qwen Max (Custom)"},
            {"id": "openai/qwen3.5-plus", "name": "Qwen 3.5 Plus (Custom)"},
        ]
        return jsonify({"success": True, "data": models})

    return app


def main():
    """Run the web application."""
    app = create_app()
    app.run(host="127.0.0.1", port=8080, debug=True)


if __name__ == "__main__":
    main()
