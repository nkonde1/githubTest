#!/usr/bin/env python3
"""
Simple script to get a fresh access token
"""
import requests
import json

def get_token():
    """Get a fresh access token"""
    url = "http://localhost:8000/api/v1/auth/login-json"
    data = {
        "email": "demo@financeai.com",
        "password": "demo123"
    }
    try:
        response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            token = result.get('access_token')
            print(f"Access Token: {token}")
            print(f"\nUse this token in Postman Authorization header:")
            print(f"Bearer {token}")
            return token
        else:
            print(f"Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    get_token()


