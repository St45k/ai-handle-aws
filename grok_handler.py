import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class GrokHandler:
    """Handles integration with Grok AI API."""
    
    def __init__(self, api_key: str, api_url: str, model: str, timeout: int = 60):
        """
        Initialize Grok API handler.
        
        Args:
            api_key: Grok API key
            api_url: Grok API endpoint URL
            model: Model name to use (e.g., 'grok-2-latest')
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def query(self, prompt: str, model: str = None) -> Dict[str, Any]:
        """
        Send a prompt to Grok API and get response.
        
        Args:
            prompt: The user's prompt/question
            model: Optional model override (uses default if not provided)
        
        Returns:
            Dict with 'response' key containing the Grok response, or error info
        
        Raises:
            requests.exceptions.RequestException: If API call fails
        """
        model = model or self.model
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            logger.info(f"Sending request to Grok API with model: {model}")
            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                response_text = message.get("content", "")
                logger.info("Successfully received response from Grok API")
                return {
                    "response": response_text,
                    "model": model,
                    "status": "success"
                }
            else:
                logger.error(f"Unexpected Grok API response format: {data}")
                return {
                    "response": "",
                    "error": "Unexpected response format from Grok API",
                    "status": "error"
                }
        
        except requests.exceptions.Timeout:
            logger.error(f"Grok API request timed out after {self.timeout}s")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"Grok API HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Grok API request failed: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Failed to parse Grok API response: {str(e)}")
            raise
