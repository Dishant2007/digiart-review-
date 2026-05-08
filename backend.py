from flask import Flask, request, Response, jsonify, stream_with_context
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os
import gspread
import json
import pytz
import threading
import requests
import time
from google.oauth2.service_account import Credentials
from datetime import datetime

load_dotenv()
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# ─────────────────────────────────────────────────────────────
# BUSINESS CONFIG
# To add a new client: copy one block, change the values, done.
# ─────────────────────────────────────────────────────────────
BUSINESSES = {
    "DigiArt Invitations": {
        "sheet_id": "1vcoQjEj0rPrxTQysI8vM2ZOe8gWkRWeYQ_0LsQf7riE",
        "system_prompt": """You are a real customer writing a Google review for DigiArt Invitations (Surat).
Digital invitations
Known for: fast delivery, premium designs, easy customization, good support, home delivery, smooth experience.

STEP 1 — PICK FORMAT (do this silently, output only the review):
Generate a random number 1–100.
FORMAT (pick randomly):
- 70% → MICRO: 3-6 words only
- 20% → SHORT: 8-12 words, 1 line
- 10% → DETAIL: 2 lines max, 25 words
STEP 2 — WRITE THE REVIEW:
- Tone: natural, friendly, genuine — never robotic
- Slight emotional touch (relief, happiness, convenience)
- No repetitive sentences
- 40% chance: mention Surat
- 10% chance: micro-detail (family loved it / got compliments / matched our theme)
- 30% chance: one emoji only, chosen randomly from: 😊 👍 🎉 🙌 ❤️ 💕 🥰 ✨ 💯 🌟 👏 🎊 💍 🔥 🫶
- Vary opening word — NEVER start with: I, Absolutely, DigiArt, So, Loved
- NEVER end with: recommend / highly recommend
- No quotes, no negative words
- Pick 1 keyword naturally like you want : elegant / seamless / effortless / beautiful / classy / gorgeous / perfect / delightful / smooth

RULES:
- Output ONLY the review text. No labels, no explanations, nothing else.
- Never write more than 40 words total under any format""",
    },
}


def get_sheet(sheet_id):
    creds_dict = json.loads(os.environ.get("GOOGLE_CREDENTIALS"))
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    gc = gspread.authorize(creds)
    return gc.open_by_key(sheet_id).sheet1


def save_to_sheet(sheet_id, business, service, review):
    try:
        sheet = get_sheet(sheet_id)
        india = pytz.timezone('Asia/Kolkata')
        now = datetime.now(india).strftime("%d-%m-%Y %I:%M %p")
        sheet.append_row([now, business, service, review])
    except Exception as e:
        print(f"Sheet error: {e}")


def keep_alive():
    while True:
        time.sleep(14 * 60)
        try:
            requests.get("https://digiart-review-backend.onrender.com/")
        except:
            pass


app = Flask(__name__)
CORS(app)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Keep server awake — prevents Render cold start
threading.Thread(target=keep_alive, daemon=True).start()


@app.route("/review", methods=["POST"])
def generate_review():
    data = request.get_json() or {}
    product  = data.get("product", "")
    rating   = data.get("rating", "5")
    business = data.get("business", "")

    config = BUSINESSES.get(business)
    if not config:
        return jsonify({"error": f"Unknown business: {business}"}), 400

    def stream_review():
        collected = []
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": config["system_prompt"]},
                {"role": "user",   "content": f"Occasion: {product}, Rating: {rating}"}
            ],
            max_tokens=200,
            temperature=1.0,
            stream=True,
        )
        for chunk in stream:
            token = chunk.choices[0].delta.content
            if token:
                collected.append(token)
                yield token

        # Save to sheet in background — does not slow down the response
        full_text = "".join(collected).strip()
        threading.Thread(
            target=save_to_sheet,
            args=(config["sheet_id"], business, product, full_text),
            daemon=True,
        ).start()

    return Response(stream_with_context(stream_review()), mimetype="text/plain")


@app.route("/", methods=["GET"])
def health():
    return "Review API is running ✅"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)