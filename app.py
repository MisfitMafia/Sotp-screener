
from flask import Flask, jsonify
from polygon_client import get_option_trades

app = Flask(__name__)

@app.route('/get-trades', methods=['GET'])
def get_trades():
    trades = get_option_trades()
    return jsonify(trades)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
