#!/usr/bin/env python3
"""
Test script to test the sync endpoint with authentication
"""
import requests
import json

def test_sync():
    """Test the sync endpoint"""
    # First get a token
    login_url = "http://localhost:8000/api/v1/auth/login-json"
    login_data = {
        "email": "demo@financeai.com",
        "password": "demo123"
    }
    
    try:
        # Login to get token
        login_response = requests.post(login_url, json=login_data, headers={"Content-Type": "application/json"})
        print(f"Login Status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.text}")
            return
            
        token_data = login_response.json()
        access_token = token_data.get('access_token')
        print(f"Got access token: {access_token[:20]}...")
        
        # Test sync endpoint
        sync_url = "http://localhost:8000/api/v1/payments/sync?provider=shopify"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        sync_response = requests.post(sync_url, headers=headers)
        print(f"Sync Status: {sync_response.status_code}")
        print(f"Sync Response: {sync_response.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_sync()


