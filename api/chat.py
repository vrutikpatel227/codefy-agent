from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

chat_history = []

def is_code_query(text):
    keywords = [
        "code", "error", "python", "java", "fix", "bug",
        "program", "c++", "html", "css", "javascript",
        "login", "function", "api", "react", "flask"
    ]
    return any(word in text.lower() for word in keywords)

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    global chat_history

    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json(silent=True) or {}
    user_input = (data.get("message") or "").strip()

    if not user_input:
        return jsonify({"reply": "Please enter a message"})

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return jsonify({"reply": "Missing OPENROUTER_API_KEY"}), 500

    chat_history.append({"role": "user", "content": user_input})
    recent_history = chat_history[-6:]

    if is_code_query(user_input):
        system_prompt = """
You are a professional coding AI.

STRICT RULES:
- Give WORKING code first
- Then give a SHORT explanation
- Keep answers compact and useful
- Use proper syntax
- If user asks for fix, give corrected code
- Prefer simple beginner-friendly code unless user asks advanced
"""
        max_tokens = 450
        temperature = 0.3
    else:
        system_prompt = """
You are a helpful AI assistant.
Reply clearly, briefly, and directly.
Avoid long unnecessary explanations.
"""
        max_tokens = 220
        temperature = 0.5

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "X-Title": "Codefy Agent"
            },
            json={
                "model": "deepseek/deepseek-r1-0528-qwen3-8b:free",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    *recent_history
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            },
            timeout=25
        )

        if response.status_code != 200:
            return jsonify({"reply": f"API Error {response.status_code}: {response.text}"})

        result = response.json()
        choices = result.get("choices", [])

        if not choices:
            return jsonify({"reply": "No response from AI."})

        reply = choices[0]["message"]["content"].strip()

    except Exception as e:
        reply = f"Error: {str(e)}"

    chat_history.append({"role": "assistant", "content": reply})
    chat_history[:] = chat_history[-12:]

    return jsonify({"reply": reply})