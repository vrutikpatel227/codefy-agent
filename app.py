from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# 🔐 API key from environment variable
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found. Set it in Render.")

chat_history = []
MODEL_NAME = "openrouter/free"

def is_code_query(text):
    keywords = [
        "code", "error", "python", "java", "fix", "bug",
        "program", "c++", "html", "css", "javascript",
        "login", "function", "api", "react", "node", "sql",
        "flask", "django", "cpp", "c language", "javafx"
    ]
    text = text.lower()
    return any(word in text for word in keywords)

def ask_ai(user_input, coding_mode=False):
    global chat_history

    chat_history.append({"role": "user", "content": user_input})
    recent_history = chat_history[-6:]

    if coding_mode:
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
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "X-Title": "Codefy Agent"
            },
            json={
                "model": MODEL_NAME,
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
            return f"API Error {response.status_code}: {response.text}"

        data = response.json()
        choices = data.get("choices", [])

        if not choices:
            return "No response from AI."

        reply = choices[0]["message"]["content"].strip()

    except requests.exceptions.Timeout:
        reply = "AI is taking too long. Please try again."
    except Exception as e:
        reply = f"Error: {str(e)}"

    chat_history.append({"role": "assistant", "content": reply})
    chat_history[:] = chat_history[-12:]

    return reply

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_input = (data.get("message") or "").strip()

    if not user_input:
        return jsonify({"reply": "Please enter a message"})

    reply = ask_ai(user_input, coding_mode=is_code_query(user_input))
    return jsonify({"reply": reply})

@app.route("/", methods=["GET"])
def home():
    return "Codefy Agent Backend is Running 🚀"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)