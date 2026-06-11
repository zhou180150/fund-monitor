import requests

# Try to access Streamlit Cloud manage API
# Check if the app is running and what the raw error is
url = "https://zhou180150-fund-monitor-app-v2-9ryt9v.streamlit.app/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml"
}

try:
    r = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
    print(f"Status: {r.status_code}")
    print(f"URL: {r.url}")
    print(f"Content length: {len(r.text)}")
    # Look for error message
    if "error" in r.text.lower() or "Error" in r.text:
        # Find error-related sections
        for line in r.text.split("\n"):
            if "error" in line.lower() or "traceback" in line.lower() or "Exception" in line:
                print(line[:200])
    # Show last 500 chars
    print("\n--- Last 500 chars ---")
    print(r.text[-500:])
except Exception as e:
    print(f"Request failed: {e}")