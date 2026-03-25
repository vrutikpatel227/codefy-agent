from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

chat_history = []

# Better working free OpenRouter models
FREE_MODELS = [
    "mistralai/mistral-7b-instruct:free",
    "meta-llama/llama-3.1-8b-instruct:free",
    "qwen/qwen-2.5-7b-instruct:free",
    "openchat/openchat-7b:free"
]

def is_code_query(text):
    keywords = [
        "code", "error", "python", "java", "fix", "bug",
        "program", "c++", "html", "css", "javascript",
        "login", "function", "api", "react", "flask",
        "sql", "node", "backend", "frontend"
    ]
    return any(word in text.lower() for word in keywords)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Codefy Agent backend is running!"})

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    global chat_history

    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json(silent=True) or {}
    user_input = (data.get("message") or "").strip()

    if not user_input:
        return jsonify({"reply": "Please enter a message."})

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return jsonify({"reply": "Missing OPENROUTER_API_KEY"}), 500

    chat_history.append({"role": "user", "content": user_input})
    recent_history = chat_history[-6:]

    if is_code_query(user_input):
        system_prompt = """
You are Codefy Agent, a professional coding AI.

STRICT RULES:
- Give WORKING code first
- Then give a SHORT explanation
- Keep answers compact and useful
- Use proper syntax
- If user asks for fix, give corrected code
- Prefer simple beginner-friendly code unless user asks advanced
"""
        max_tokens = 500
        temperature = 0.3
    else:
        system_prompt = """
You are Codefy Agent, a helpful AI assistant.
Reply clearly, briefly, and directly.
Avoid long unnecessary explanations.
"""
        max_tokens = 250
        temperature = 0.5

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://vrutikpatel227.github.io/codefy-agent/",
        "X-Title": "Codefy Agent"
    }

    reply = None
    last_error = None

    for model in FREE_MODELS:
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    *recent_history
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                choices = result.get("choices", [])

                if choices and choices[0].get("message", {}).get("content"):
                    reply = choices[0]["message"]["content"].strip()
                    break
            else:
                last_error = f"{model} -> {response.status_code}: {response.text}"

        except Exception as e:
            last_error = f"{model} -> {str(e)}"

    if not reply:
        reply = f"All free AI models are currently unavailable. Try again later.\n\nLast error:\n{last_error}"

    chat_history.append({"role": "assistant", "content": reply})
    chat_history[:] = chat_history[-12:]

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)