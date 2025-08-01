import os
from flask import Flask, jsonify, request
from market_data_client import fetch_equity_quote, fetch_option_chain, fetch_iv_rank

app = Flask(__name__)

@app.route('/quote/<symbol>', methods=['GET'])
def quote(symbol):
    market = request.args.get('market', 'USA')
    data = fetch_equity_quote(symbol, market)
    return jsonify(data)

@app.route('/options', methods=['GET'])
def options():
    symbol = request.args.get('symbol')
    expiration = request.args.get('expiration')
    market = request.args.get('market', 'USA')
    if not symbol or not expiration:
        return jsonify({'error': 'symbol and expiration are required'}), 400
    data = fetch_option_chain(symbol, expiration, market)
    return jsonify(data)

@app.route('/iv-rank', methods=['GET'])
def iv_rank():
    symbol = request.args.get('symbol')
    market = request.args.get('market', 'USA')
    period = request.args.get('period', default=252, type=int)
    if not symbol:
        return jsonify({'error': 'symbol is required'}), 400
    try:
        ivr = fetch_iv_rank(symbol, period, market)
        return jsonify({'symbol': symbol.upper(), 'iv_rank': ivr})
    except NotImplementedError as e:
        return jsonify({'error': str(e)}), 501

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
