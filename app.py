import os
import json
from flask import Flask, request, jsonify

import openai
from market_data_client import fetch_equity_quote, fetch_option_chain, fetch_iv_rank

app = Flask(__name__)

# Load API keys
openai.api_key = os.getenv("OPENAI_API_KEY")


# --- Health check to verify env vars are set ---
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "OPENAI_API_KEY_set":  bool(os.getenv("OPENAI_API_KEY")),
        "POLYGON_API_KEY_set": bool(os.getenv("POLYGON_API_KEY"))
    })


# --- Market-data GET routes for manual testing ---
@app.route('/quote/<symbol>', methods=['GET'])
def quote(symbol):
    data = fetch_equity_quote(symbol, request.args.get('market', 'USA'))
    return jsonify(data)

@app.route('/options', methods=['GET'])
def options():
    symbol     = request.args.get('symbol')
    expiration = request.args.get('expiration')
    market     = request.args.get('market', 'USA')
    if not symbol or not expiration:
        return jsonify({'error': 'symbol & expiration required'}), 400
    data = fetch_option_chain(symbol, expiration, market)
    return jsonify(data)

@app.route('/iv-rank', methods=['GET'])
def iv_rank():
    symbol = request.args.get('symbol')
    period = int(request.args.get('period', 252))
    market = request.args.get('market', 'USA')
    if not symbol:
        return jsonify({'error': 'symbol required'}), 400
    data = fetch_iv_rank(symbol, period, market)
    return jsonify(data)


# --- ChatGPT function-calling endpoint ---
FUNCTIONS = [
    {
        "name": "get_equity_quote",
        "description": "Fetches the latest equity quote (last, bid, ask, timestamp).",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Ticker, e.g. AAPL"},
                "market": {"type": "string", "default": "USA"}
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_option_chain",
        "description": "Retrieves the full options chain for a symbol and expiration.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol":     {"type": "string"},
                "expiration": {"type": "string", "format": "date"},
                "market":     {"type": "string", "default": "USA"}
            },
            "required": ["symbol", "expiration"]
        }
    },
    {
        "name": "get_iv_rank",
        "description": "Returns the IV rank percentile for a symbol over a look-back period.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "period": {"type": "integer", "default": 252},
                "market": {"type": "string", "default": "USA"}
            },
            "required": ["symbol"]
        }
    }
]

@app.route("/chat", methods=["POST"])
def chat():
    payload = request.get_json(force=True)
    prompt  = payload.get("prompt", "")

    # 1️⃣ First pass: send prompt + function definitions
    first = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a market-data assistant."},
            {"role": "user",   "content": prompt}
        ],
        functions=FUNCTIONS,
        function_call="auto"
    )
    msg = first.choices[0].message

    # 2️⃣ If the model decides to call a function…
    if msg.get("function_call"):
        name = msg["function_call"]["name"]
        args = json.loads(msg["function_call"]["arguments"])

        # 3️⃣ Dispatch to the right handler
        try:
            if name == "get_equity_quote":
                result = fetch_equity_quote(args["symbol"], args.get("market", "USA"))
            elif name == "get_option_chain":
                result = fetch_option_chain(args["symbol"], args["expiration"], args.get("market", "USA"))
            elif name == "get_iv_rank":
                result = fetch_iv_rank(args["symbol"], args.get("period", 252), args.get("market", "USA"))
            else:
                return jsonify({"error": f"Unknown function {name}"}), 400
        except Exception as e:
            app.logger.error(f"{name} raised exception", exc_info=True)
            return jsonify({"error": f"{name} error"}), 500

        # 4️⃣ Second pass: feed the function’s output back into the model
        followup = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a market-data assistant."},
                {"role": "user",   "content": prompt},
                msg,  # the function_call
                {"role": "function", "name": name, "content": json.dumps(result)}
            ]
        )
        answer = followup.choices[0].message.content

    else:
        # 5️⃣ No function call; just return the model’s text
        answer = msg.content

    return jsonify({"answer": answer})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
