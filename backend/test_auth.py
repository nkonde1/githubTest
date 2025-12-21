#!/usr/bin/env python3
"""
Simple test script to check auth endpoints
"""

import requests
import json

def test_login():
    """Test the login endpoint"""
    url = "http://localhost:8000/api/v1/auth/login-json"
    data = {
        "email": "demo@financeai.com",
        "password": "demo123"
    }
    
    try:
        response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Login successful! Access token: {result.get('access_token', 'N/A')[:20]}...")
        else:
            print(f"Login failed: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login()
