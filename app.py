import os
import json
from flask import Flask, request, jsonify

import openai
from market_data_client import fetch_equity_quote, fetch_option_chain, fetch_iv_rank

app = Flask(__name__)

# ←— Set your OpenAI key from the environment
openai.api_key = os.getenv("OPENAI_API_KEY")

# ←— Declare the same function schemas you exposed in FUNCTIONS.json
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

    # 1️⃣ Send user prompt + function definitions to OpenAI
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

    # 2️⃣ If the model wants to call one of our functions…
    if msg.get("function_call"):
        name = msg["function_call"]["name"]
        args = json.loads(msg["function_call"]["arguments"])

        # 3️⃣ Dispatch to your internal handlers
        if name == "get_equity_quote":
            result = fetch_equity_quote(args["symbol"], args.get("market", "USA"))
        elif name == "get_option_chain":
            result = fetch_option_chain(args["symbol"], args["expiration"], args.get("market", "USA"))
        elif name == "get_iv_rank":
            result = fetch_iv_rank(args["symbol"], args.get("period", 252), args.get("market", "USA"))
        else:
            return jsonify({"error": f"Unknown function {name}"}), 400

        # 4️⃣ Send the function’s output back into OpenAI for a final answer
        followup = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a market-data assistant."},
                {"role": "user",   "content": prompt},
                msg,  # the function_call
                {
                    "role":    "function",
                    "name":    name,
                    "content": json.dumps(result)
                }
            ]
        )
        answer = followup.choices[0].message.content
    else:
        # 5️⃣ If no function was needed, just return the text
        answer = msg.content

    return jsonify({"answer": answer})
