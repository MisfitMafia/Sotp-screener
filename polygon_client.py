--- a/polygon_client.py
+++ b/polygon_client.py
@@
-import os
+import os, logging
 from datetime import datetime, timedelta
 import requests

+logging.basicConfig(level=logging.INFO)
+logger = logging.getLogger(__name__)

 API_KEY = os.getenv('POLYGON_API_KEY')
 BASE_URL = 'https://api.polygon.io'
@@
 def get_option_trades():
-    results = []
+    if not API_KEY:
+        logger.error("❌ POLYGON_API_KEY is not set!")
+        return []
+    logger.info(f"Using POLYGON_API_KEY={API_KEY[:4]}…")

+    results = []
     today = datetime.today().date()
     for symbol in blue_chip_tickers:
         try:
             url = f"{BASE_URL}/v3/reference/options/contracts?underlying_ticker={symbol}&limit=1000&apiKey={API_KEY}"
-            res = requests.get(url).json()
+            resp = requests.get(url)
+            if resp.status_code != 200:
+                logger.warning(f"[{symbol}] contracts call → {resp.status_code}: {resp.text}")
+                continue
+            res = resp.json()
             contracts = res.get('results', [])
import os
import requests
from datetime import datetime, timedelta

API_KEY = os.getenv('POLYGON_API_KEY')
BASE_URL = 'https://api.polygon.io'

blue_chip_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'JPM', 'META', 'UNH', 'V', 'DIS']

def get_option_trades():
    results = []
    today = datetime.today().date()
    for symbol in blue_chip_tickers:
        try:
            url = f"{BASE_URL}/v3/reference/options/contracts?underlying_ticker={symbol}&limit=1000&apiKey={API_KEY}"
            res = requests.get(url).json()
            contracts = res.get('results', [])
            for c in contracts:
                try:
                    exp_date = datetime.strptime(c['expiration_date'], "%Y-%m-%d").date()
                    if 30 <= (exp_date - today).days <= 60 and c['type'] in ['call', 'put']:
                        market_url = f"{BASE_URL}/v3/snapshot/options/{symbol}/{c['symb']}/?apiKey={API_KEY}"
                        market_res = requests.get(market_url).json()
                        last_quote = market_res.get('results', {}).get('last_quote', {})
                        price = last_quote.get('ask', 0)
                        if 0.10 <= price <= 0.60:
                            results.append({
                                'ticker': symbol,
                                'option_symbol': c['symb'],
                                'type': c['type'],
                                'expiration': c['expiration_date'],
                                'strike': c['strike_price'],
                                'price': price
                            })
                        if len(results) >= 10:
                            return results
                except:
                    continue
        except:
            continue
    return results
