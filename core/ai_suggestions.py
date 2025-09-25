from database.db_manager import fetch_all, fetch_one, execute_query
import requests
import os
import json
import traceback

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or "."

def generate_openai_tip(summary):
    # ensure summary is a safe string
    if not summary or not summary.strip():
        summary = "No summary provided."

    try:
        if not GROQ_API_KEY:
            return "⚠️ API key not configured"

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "llama3-70b-8192",
            "messages": [
                {"role": "system", "content": "You are a top-tier financial advisor. Be brief, impactful, and specific."},
                {"role": "user", "content": (
                    f"{summary}\n\n"
                    "Write exactly three sentences:\n"
                    "1. First line: Clearly state the financial problem in one sentence.\n"
                    "2. Second line: Begin with '1.' and give the first solution in one sentence.\n"
                    "3. Third line: Begin with '2.' and give the second solution in one sentence.\n"
                    "Do not add any introduction, explanation, or extra words before or after.\n"
                    "The response must be exactly 3 lines and immediately usable in Word."
                )}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }

        # DEBUG: print payload
        print("Sending to GROQ:", json.dumps(data, indent=2))

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=10
        )

        if response.status_code == 429:
            return "⚠️ API quota exceeded - upgrade your plan"
        elif response.status_code == 401:
            return "⚠️ Invalid API key"
        elif response.status_code == 400:
            return "⚠️ API returned Bad Request – skipping this tip"

        response.raise_for_status()
        content = response.json().get("choices", [{}])[0].get("message", {}).get("content")
        if not content:
            return "⚠️ No content returned from API"

        return content.strip()

    except requests.exceptions.RequestException as e:
        return f"⚠️ API error: {str(e)}"
    except Exception as e:
        traceback.print_exc()
        return f"⚠️ Error generating tip: {str(e)}"


def get_recent_suggestions(user_id):
    try:
        table_exists = fetch_one("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='ai_suggestions'
        """)

        if not table_exists:
            print("⚠️ ai_suggestions table doesn't exist")
            return []

        return fetch_all("""
            SELECT * FROM ai_suggestions
            WHERE user_id = ? 
            ORDER BY generated_at DESC
            LIMIT 3
        """, (user_id,))

    except Exception as e:
        print(f"❌ Error fetching suggestions: {e}")
        traceback.print_exc()
        return []


def insert_tip(user_id, content):
    if not content or not content.strip():
        return  # skip empty content
    execute_query("""
        INSERT INTO ai_suggestions (user_id, content, is_read)
        VALUES (?, ?, 0)
    """, (user_id, content), commit=True)
