import os, logging
import requests
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv('POLYGON_API_KEY')
BASE_URL = 'https://api.polygon.io'

blue_chip_tickers = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
    'JPM', 'META', 'UNH', 'V', 'DIS'
]

def get_option_trades():
    if not API_KEY:
        logger.error("❌ POLYGON_API_KEY is not set!")
        return []

    logger.info(f"Using POLYGON_API_KEY={API_KEY[:4]}…")
    results = []
    today = datetime.today().date()

    for symbol in blue_chip_tickers:
        try:
            url = (
                f"{BASE_URL}/v3/reference/options/contracts"
                f"?underlying_ticker={symbol}"
                f"&limit=1000&apiKey={API_KEY}"
            )
            resp = requests.get(url)
            if resp.status_code != 200:
                logger.warning(f"[{symbol}] contracts → {resp.status_code}")
                continue
            contracts = resp.json().get('results', [])

            for c in contracts:
                try:
                    exp_date = datetime.strptime(c['expiration_date'], "%Y-%m-%d").date()
                    days_to_exp = (exp_date - today).days
                    if 30 <= days_to_exp <= 60 and c['type'] in ['call', 'put']:
                        snap_url = (
                            f"{BASE_URL}/v3/snapshot/options/"
                            f"{symbol}/{c['symb']}?apiKey={API_KEY}"
                        )
                        snap = requests.get(snap_url)
                        if snap.status_code != 200:
                            logger.warning(f"[{symbol}/{c['symb']}] snapshot → {snap.status_code}")
                            continue
                        last = snap.json().get('results', {}).get('last_quote', {})
                        ask = last.get('ask', 0)
                        if 0.10 <= ask <= 0.60:
                            results.append({
                                'ticker': symbol,
                                'option_symbol': c['symb'],
                                'type': c['type'],
                                'expiration': c['expiration_date'],
                                'strike': c['strike_price'],
                                'price': ask
                            })
                            if len(results) >= 10:
                                return results
                except Exception:
                    continue
        except Exception:
            continue

    return results

     
    
                   
