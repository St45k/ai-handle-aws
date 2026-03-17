#!/usr/bin/env python3
"""
Test script for Grok AI backend handler.

Run this script to validate the webhook endpoint and API integration.
Make sure the Flask app is running before executing this script.
"""

import requests
import json
import sys
import time
from typing import Tuple

BASE_URL = "http://localhost:8000"
HEALTH_ENDPOINT = f"{BASE_URL}/health"
WEBHOOK_ENDPOINT = f"{BASE_URL}/handle"
AUTH_CODE = "060712"
AUTH_HEADERS = {"X-Auth-Code": AUTH_CODE}
INVALID_AUTH_HEADERS = {"X-Auth-Code": "wrongcode"}


def test_health_check() -> Tuple[bool, str]:
    """Test the health check endpoint."""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            return True, "✓ Health check passed"
        else:
            return False, f"✗ Health check failed: {response.status_code}"
    except requests.ConnectionError:
        return False, f"✗ Cannot connect to {BASE_URL} - is the Flask app running?"
    except Exception as e:
        return False, f"✗ Health check error: {str(e)}"


def test_webhook_valid_request() -> Tuple[bool, str]:
    """Test valid webhook request with auth code."""
    payload = {
        "prompt": "What is the capital of France?",
        "model": "grok-3"
    }
    
    try:
        response = requests.post(WEBHOOK_ENDPOINT, json=payload, headers=AUTH_HEADERS, timeout=65)
        
        if response.status_code == 200:
            data = response.json()
            if "response" in data and len(data["response"]) > 0:
                return True, f"✓ Valid webhook request passed - Response length: {len(data['response'])} chars"
            else:
                return False, f"✗ Invalid response format: {data}"
        else:
            return False, f"✗ Request failed with status {response.status_code}: {response.json()}"
    except Exception as e:
        return False, f"✗ Webhook request error: {str(e)}"


def test_webhook_missing_auth() -> Tuple[bool, str]:
    """Test webhook request without auth code."""
    payload = {
        "prompt": "What is 2+2?"
    }
    
    try:
        response = requests.post(WEBHOOK_ENDPOINT, json=payload, timeout=5)
        
        if response.status_code == 401:
            data = response.json()
            if "error" in data:
                return True, "✓ Missing auth validation passed - Correctly rejected"
            else:
                return False, f"✗ Unexpected response: {data}"
        else:
            return False, f"✗ Expected 401, got {response.status_code}"
    except Exception as e:
        return False, f"✗ Auth validation test error: {str(e)}"


def test_webhook_invalid_auth() -> Tuple[bool, str]:
    """Test webhook request with invalid auth code."""
    payload = {
        "prompt": "What is 2+2?"
    }
    
    try:
        response = requests.post(WEBHOOK_ENDPOINT, json=payload, headers=INVALID_AUTH_HEADERS, timeout=5)
        
        if response.status_code == 401:
            data = response.json()
            if "error" in data:
                return True, "✓ Invalid auth validation passed - Correctly rejected"
            else:
                return False, f"✗ Unexpected response: {data}"
        else:
            return False, f"✗ Expected 401, got {response.status_code}"
    except Exception as e:
        return False, f"✗ Invalid auth test error: {str(e)}"


def test_webhook_missing_prompt() -> Tuple[bool, str]:
    """Test webhook request with missing prompt."""
    payload = {
        "model": "grok-3"
    }
    
    try:
        response = requests.post(WEBHOOK_ENDPOINT, json=payload, headers=AUTH_HEADERS, timeout=5)
        
        if response.status_code == 400:
            data = response.json()
            if "error" in data:
                return True, "✓ Missing prompt validation passed - Correctly rejected"
            else:
                return False, f"✗ Unexpected response: {data}"
        else:
            return False, f"✗ Expected 400, got {response.status_code}"
    except Exception as e:
        return False, f"✗ Validation test error: {str(e)}"


def test_webhook_empty_prompt() -> Tuple[bool, str]:
    """Test webhook request with empty prompt."""
    payload = {
        "prompt": "",
        "model": "grok-3"
    }
    
    try:
        response = requests.post(WEBHOOK_ENDPOINT, json=payload, headers=AUTH_HEADERS, timeout=5)
        
        if response.status_code == 400:
            return True, "✓ Empty prompt validation passed - Correctly rejected"
        else:
            return False, f"✗ Expected 400, got {response.status_code}: {response.json()}"
    except Exception as e:
        return False, f"✗ Validation test error: {str(e)}"


def test_webhook_invalid_json() -> Tuple[bool, str]:
    """Test webhook request with invalid JSON."""
    try:
        response = requests.post(
            WEBHOOK_ENDPOINT,
            data="not valid json",
            headers=AUTH_HEADERS,
            timeout=5
        )
        
        if response.status_code == 400:
            return True, "✓ Invalid JSON validation passed - Correctly rejected"
        else:
            return False, f"✗ Expected 400, got {response.status_code}: {response.json()}"
    except Exception as e:
        return False, f"✗ Invalid JSON test error: {str(e)}"


def test_webhook_default_model() -> Tuple[bool, str]:
    """Test webhook request without specifying model (uses default)."""
    payload = {
        "prompt": "Briefly explain artificial intelligence"
    }
    
    try:
        response = requests.post(WEBHOOK_ENDPOINT, json=payload, headers=AUTH_HEADERS, timeout=65)
        
        if response.status_code == 200:
            data = response.json()
            if "response" in data and len(data["response"]) > 0:
                return True, f"✓ Default model test passed - Model used: {data.get('model', 'unknown')}"
            else:
                return False, f"✗ Invalid response format: {data}"
        else:
            return False, f"✗ Request failed with status {response.status_code}: {response.json()}"
    except Exception as e:
        return False, f"✗ Default model test error: {str(e)}"


def test_nonexistent_endpoint() -> Tuple[bool, str]:
    """Test requesting nonexistent endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/nonexistent", timeout=5)
        
        if response.status_code == 404:
            return True, "✓ 404 handling passed - Correctly returned Not Found"
        else:
            return False, f"✗ Expected 404, got {response.status_code}"
    except Exception as e:
        return False, f"✗ 404 test error: {str(e)}"


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Grok AI Backend Handler - Test Suite")
    print("="*60 + "\n")
    
    tests = [
        ("Health Check", test_health_check),
        ("Non-existent Endpoint (404)", test_nonexistent_endpoint),
        ("Missing Auth Code", test_webhook_missing_auth),
        ("Invalid Auth Code", test_webhook_invalid_auth),
        ("Valid Webhook Request", test_webhook_valid_request),
        ("Missing Prompt Validation", test_webhook_missing_prompt),
        ("Empty Prompt Validation", test_webhook_empty_prompt),
        ("Invalid JSON Validation", test_webhook_invalid_json),
        ("Default Model Usage", test_webhook_default_model),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"{test_name}...", end=" ")
        success, message = test_func()
        
        if success:
            print(message)
            passed += 1
        else:
            print(message)
            failed += 1
        
        # Small delay between tests
        time.sleep(0.5)
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
