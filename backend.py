from flask import Flask, request, Response
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os
import gspread
import json
from google.oauth2.service_account import Credentials
from datetime import datetime
load_dotenv()  # reads your .env file
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

SHEET_IDS = {
    "DigiArt Invitations": "1vcoQjEj0rPrxTQysI8vM2ZOe8gWkRWeYQ_0LsQf7riE",
    
}
def get_sheet(business_name):
    creds = Credentials.from_service_account_file(
        'google-credentials.json',
        scopes=SCOPES
    )
    gc = gspread.authorize(creds)
    sheet_id = SHEET_IDS.get(business_name)
    if not sheet_id:
        return None
    return gc.open_by_key(sheet_id).sheet1

def save_to_sheet(business, service, review):
    try:
        sheet = get_sheet(business)
        if sheet:
            now = datetime.now().strftime("%d-%m-%Y %H:%M")
            sheet.append_row([now, business, service, review])
    except Exception as e:
        print(f"Sheet error: {e}")
app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are a real customer writing a Google review for DigiArt Invitations (Surat).
Digital invitations — wedding, birthday, baby shower, engagement, ceremony.
Known for: fast delivery, premium designs, easy customization, good support, home delivery, smooth experience.

STEP 1 — PICK FORMAT (do this silently, output only the review):
Generate a random number 1–100.
- 1–60 → MICRO: 2–5 words only (e.g. "Totally worth it" / "Perfect design")
- 61–90 → SHORT: exactly 1 line, 6–10 words
- 91–97 → MEDIUM: exactly 1 line, 10–15 words
- 98–100 → DETAILED: 2–3 lines, max 40 words total
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
- Pick 1 keyword naturally from: elegant / seamless / effortless / beautiful / classy / gorgeous / perfect / delightful / smooth

RULES:
- Output ONLY the review text. No labels, no explanations, nothing else.
- Never write more than 80 words total under any format"""

@app.route("/review", methods=["POST"])
def generate_review():
    data = request.get_json()
    product = data.get("product", "")
    rating = data.get("rating", "5")
    business = data.get("business", "DigiArt Invitations")
    city = data.get("city", "Surat")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Occasion: {product}, Rating: {rating}"}
        ],
        max_tokens=200,
        temperature=1.0
    )

    review_text = response.choices[0].message.content.strip()
    save_to_sheet(business, product, review_text)
    return Response(review_text, mimetype="text/plain")

@app.route("/", methods=["GET"])
def health():
    return "DigiArt Review API is running ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)