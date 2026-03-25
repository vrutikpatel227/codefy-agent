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
        "login", "function", "api", "react", "flask",
        "sql", "node", "backend", "frontend"
    ]
    return any(word in text.lower() for word in keywords)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Codefy Agent backend is running with Groq!"})

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    global chat_history

    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json(silent=True) or {}
    user_input = (data.get("message") or "").strip()

    if not user_input:
        return jsonify({"reply": "Please enter a message."})

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return jsonify({"reply": "Missing GROQ_API_KEY"}), 500

    chat_history.append({"role": "user", "content": user_input})
    recent_history = chat_history[-6:]

    if is_code_query(user_input):
        system_prompt = """
You are Codefy Agent, a professional coding AI.

RULES:
- Give WORKING code first
- Then give a SHORT explanation
- Keep answers compact and useful
- Use proper syntax
- If user asks for fix, give corrected code
- Prefer beginner-friendly code unless user asks advanced
"""
        max_tokens = 700
        temperature = 0.3
    else:
        system_prompt = """
You are Codefy Agent, a helpful AI assistant.
Reply clearly, briefly, and directly.
"""
        max_tokens = 300
        temperature = 0.5

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key.strip()}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    *recent_history
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            },
            timeout=30
        )

        if response.status_code != 200:
            return jsonify({"reply": f"Groq API Error {response.status_code}: {response.text}"})

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

if __name__ == "__main__":
    app.run(debug=True)