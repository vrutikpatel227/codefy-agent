from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

FREE_MODELS = [
    "meta-llama/llama-3.1-8b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "openchat/openchat-7b:free",
    "nousresearch/nous-capybara-7b:free"
]

@app.route("/")
def home():
    return "Backend is running!"

@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        user_message = data.get("message", "")

        if not user_message:
            return jsonify({"reply": "Please enter a message."})

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY.strip()}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://vrutikpatel227.github.io/codefy-agent/",
            "X-Title": "Codefy Agent"
        }

        for model in FREE_MODELS:
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Codefy Agent, a coding assistant. Give clean, useful, beginner-friendly coding answers."
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            }

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                result = response.json()
                reply = result["choices"][0]["message"]["content"]
                return jsonify({"reply": reply})

        return jsonify({"reply": "All free models are currently unavailable. Please try again later."})

    except Exception as e:
        return jsonify({"reply": f"Server Error: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True)