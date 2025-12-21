import requests
try:
    print(requests.get('https://api.ipify.org').text)
except Exception as e:
    print(f"Error: {e}")
