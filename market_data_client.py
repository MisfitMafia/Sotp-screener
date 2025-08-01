import os
from polygon import RESTClient

API_KEY = os.getenv('POLYGON_API_KEY')
client = RESTClient(API_KEY)

def fetch_equity_quote(symbol, market='USA'):
    quote = client.get_quote(symbol)
    return {
        'symbol': symbol.upper(),
        'last': quote.last.price,
        'bid': quote.bidprice,
        'ask': quote.askprice,
        'timestamp': quote.last.timestamp
    }

def fetch_option_chain(symbol, expiration, market='USA'):
    resp = client.list_trades(symbol, limit=1000)  # adjust to your needs
    # (Polygon’s RESTClient has different methods; use reference_options_contracts if available)
    contracts = getattr(resp, 'results', resp)
    return {
        'symbol': symbol.upper(),
        'expiration': expiration,
        'contracts': [
            {
                'symbol': c['symbol'],
                'expiration': c.get('expiration_date'),
                'strike': c.get('strike_price'),
                'type': c.get('contract_type')
            } for c in contracts
        ]
    }

def fetch_iv_rank(symbol, period=252, market='USA'):
    # You’ll need to calculate IV rank yourself by pulling historical IV.
    raise NotImplementedError('IV rank endpoint not implemented')
