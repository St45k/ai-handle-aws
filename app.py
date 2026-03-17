import json
import logging
import os
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from flask import Flask, request, jsonify
from grok_handler import GrokHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

executor = ThreadPoolExecutor(max_workers=10)

config = None
grok_handler = None


def load_config(config_path: str = "config.json"):
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        raise


def require_auth_code(f):
    """Decorator to check if request includes valid auth code."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_code = request.headers.get("X-Auth-Code") or request.args.get("auth_code")
        
        if not auth_code:
            logger.warning("Rejected request: missing auth code")
            return jsonify({
                "error": "Unauthorized",
                "message": "Auth code is required. Pass as X-Auth-Code header or auth_code query parameter"
            }), 401
        
        if auth_code != config.get("auth_code"):
            logger.warning(f"Rejected request: invalid auth code")
            return jsonify({
                "error": "Unauthorized",
                "message": "Invalid auth code"
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.route("/handle", methods=["POST"])
@require_auth_code
def handle_webhook():
    """
    Main webhook endpoint for handling prompts.
    
    Expected JSON body:
    {
        "prompt": "What is 2+2?",
        "model": "grok-3"  # optional, uses default if not provided
    }
    
    Required auth:
    - X-Auth-Code header, or
    - auth_code query parameter
    """
    try:
        # Parse request body
        data = request.get_json(force=True)
        
        if not data:
            logger.warning("Empty request body")
            return jsonify({
                "error": "Invalid request",
                "message": "Request body must be valid JSON"
            }), 400
        
        prompt = data.get("prompt", "").strip()
        model = data.get("model", "").strip()
        
        if not prompt:
            logger.warning("Missing or empty 'prompt' field")
            return jsonify({
                "error": "Invalid request",
                "message": "Field 'prompt' is required and cannot be empty"
            }), 400
        
        if not model:
            model = grok_handler.model
        
        logger.info(f"Received webhook request - Prompt length: {len(prompt)}, Model: {model}")
        
        try:
            result = grok_handler.query(prompt, model)
            
            if result.get("status") == "error":
                logger.error(f"Grok API returned error: {result.get('error')}")
                return jsonify({
                    "error": "API error",
                    "message": result.get("error", "Unknown error from Grok API")
                }), 500
            
            logger.info("Successfully processed request")
            return jsonify({
                "response": result.get("response", ""),
                "model": result.get("model", "")
            }), 200
        
        except Exception as e:
            logger.error(f"Grok API error: {str(e)}")
            return jsonify({
                "error": "API error",
                "message": f"Failed to query Grok API: {str(e)}"
            }), 503
    
    except Exception as e:
        logger.error(f"Request processing error: {str(e)}")
        return jsonify({
            "error": "Server error",
            "message": "An unexpected error occurred processing your request"
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "error": "Not found",
        "message": "The requested endpoint does not exist"
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        "error": "Method not allowed",
        "message": "This HTTP method is not allowed for this endpoint"
    }), 405


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500


def initialize_app():
    """Initialize the Flask app with config and handlers."""
    global config, grok_handler
    
    config = load_config()
    
    logger.info(f"Config loaded - Port: {config.get('port')}, Auth Code: {'*' * len(config.get('auth_code', ''))}, Model: {config.get('grok_model')}")
    
    grok_handler = GrokHandler(
        api_key=config.get("grok_api_key"),
        api_url=config.get("grok_api_url"),
        model=config.get("grok_model"),
        timeout=config.get("request_timeout_seconds", 60)
    )
    
    logger.info(f"Grok handler initialized - Model: {config.get('grok_model')}")


if __name__ == "__main__":
    initialize_app()
    
    host = config.get("host", "0.0.0.0")
    port = config.get("port", 5000)
    
    logger.info(f"Starting Grok AI backend handler on {host}:{port}")
    app.run(host=host, port=port, debug=False)
