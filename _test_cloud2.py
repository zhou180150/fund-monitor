import requests

headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
url = "https://zhou180150-fund-monitor-app-v2-9ryt9v.streamlit.app/_stcore/health"

try:
    r = requests.get(url, headers=headers, timeout=10)
    print(f"Health: {r.status_code} {r.text[:200]}")
except Exception as e:
    print(f"Health check failed: {e}")

# Try to get log via streamlit cloud API
url2 = "https://share.streamlit.io/api/v1/apps?owner=zhou180150&repo=fund-monitor"
try:
    r2 = requests.get(url2, headers=headers, timeout=10)
    print(f"API: {r2.status_code}")
    print(r2.text[:500])
except Exception as e:
    print(f"API failed: {e}")