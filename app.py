import os
from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()
from polygon_client import get_option_trades

app = Flask(__name__)

@app.route('/')
def home():
    return '✅ Options Trade API up!  Try GET /get-trades'

@app.route('/get-trades', methods=['GET'])
def get_trades():
    trades = get_option_trades()
    return jsonify(trades)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(debug=True, host="0.0.0.0", port=port)
