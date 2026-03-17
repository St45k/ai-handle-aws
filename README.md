# Grok AI Backend Handler

Lightweight Flask webhook server for processing prompts through Grok AI API on AWS EC2.

## Quick Start

### Local
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py  # Runs on http://localhost:5000
```

### EC2 Deployment
```bash
ssh -i key.pem ec2-user@instance-ip
cd /opt/grok-handler
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sudo cp grok-handler.service /etc/systemd/system/
sudo systemctl enable --now grok-handler
```

## API Endpoints

### POST /handle
Send prompts to Grok AI.

**Headers:**
```
X-Auth-Code: YOUR_AUTH_CODE_HERE
Content-Type: application/json
```

**Request:**
```json
{"prompt": "Your question", "model": "grok-3"}
```

**Response:**
```json
{"response": "AI answer", "model": "grok-3"}
```

### GET /health
Health check.

## Configuration

Edit `config.json` with your credentials:

### Required Credentials

1. **Grok API Key** (`grok_api_key`)
   - Get from: https://console.x.ai
   - Sign up for free account
   - Generate API key in your dashboard
   - Replace `YOUR_GROK_API_KEY_HERE` with your actual key

2. **Auth Code** (`auth_code`)
   - Choose any secure string (e.g., "MySecureCode123")
   - Replace `YOUR_AUTH_CODE_HERE` with your chosen code
   - Use this code in X-Auth-Code header when calling the endpoint

### Example config.json

```json
{
  "grok_api_key": "xai-XXXXXXXXXXXXXXXXXXXXXXXX",
  "grok_api_url": "https://api.x.ai/openai/",
  "grok_model": "grok-3",
  "auth_code": "MySecureCode123",
  "request_timeout_seconds": 60,
  "port": 5000,
  "host": "0.0.0.0",
  "log_level": "INFO"
}
```

### Other Settings

- `grok_model` - Model name (grok-3, etc.)
- `port` - Server port (default 5000)
- `request_timeout_seconds` - API timeout (default 60)

## HTTP Status Codes

- `200` - Success
- `400` - Bad request (missing prompt, invalid JSON)
- `401` - Unauthorized (invalid auth code)
- `404` - Not found
- `503` - Grok API error

## Logs (EC2)

```bash
sudo journalctl -u grok-handler -f  # Real-time
sudo systemctl status grok-handler   # Status
```

## Files

- `app.py` - Main Flask app
- `grok_handler.py` - Grok API integration
- `config.json` - Configuration
- `requirements.txt` - Dependencies
- `grok-handler.service` - Systemd service

## Security

- Keep `config.json` out of git (use .gitignore)
- Set permissions: `chmod 600 config.json`
- Auth code required for all requests
- Use AWS Security Group to restrict access

