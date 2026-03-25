from http.server import BaseHTTPRequestHandler
import json
import os
import requests

chat_history = []

def is_code_query(text):
    keywords = [
        "code", "error", "python", "java", "fix", "bug",
        "program", "c++", "html", "css", "javascript",
        "login", "function", "api", "react", "flask"
    ]
    return any(word in text.lower() for word in keywords)

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            user_input = data.get("message", "").strip()

            if not user_input:
                self.send_json({"reply": "Please enter a message"})
                return

            api_key = os.getenv("OPENROUTER_API_KEY")

            if not api_key:
                self.send_json({"reply": "Missing OPENROUTER_API_KEY"})
                return

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

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "X-Title": "Codefy Agent"
                },
                json={
                    "model": "openrouter/free",
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
                self.send_json({"reply": f"API Error {response.status_code}: {response.text}"})
                return

            result = response.json()
            choices = result.get("choices", [])

            if not choices:
                self.send_json({"reply": "No response from AI."})
                return

            reply = choices[0]["message"]["content"].strip()
            chat_history.append({"role": "assistant", "content": reply})
            del chat_history[:-12]

            self.send_json({"reply": reply})

        except Exception as e:
            self.send_json({"reply": f"Error: {str(e)}"})

    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())