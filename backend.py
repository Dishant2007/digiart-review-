from flask import Flask, request, Response, jsonify, stream_with_context, send_from_directory
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────────────────────────────────────────
# BUSINESS CONFIG
# To add a new client: copy one block, change the values, done.
# ─────────────────────────────────────────────────────────────
BUSINESSES = {
    "DigiArt Invitations": {
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

    "Jaydev Mobile": {
        "system_prompt": """You help a real customer write a short Google review for Jaydev Mobile.

Jaydev Mobile is a mobile shop/service business.
Known for: mobile phones, accessories, repair service, helpful support, and a smooth customer experience.

Write a natural review that can fit a general customer experience.

RULES:
- Output ONLY the review text. No labels, no explanations, nothing else.
- Keep it short, natural, and genuine.
- Do not mention a specific service unless the customer provided one.
- Never write more than 40 words total.""",
    },
    
}


app = Flask(__name__)
CORS(app)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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
                yield token

    return Response(stream_with_context(stream_review()), mimetype="text/plain")


@app.route("/", methods=["GET"])
def home():
    return send_from_directory(BASE_DIR, "index.htm")


@app.route("/jaydev-mobile", methods=["GET"])
def jaydev_mobile():
    return send_from_directory(BASE_DIR, "jaydev-mobile.htm")


@app.route("/jaydev-mobile-preview", methods=["GET"])
def jaydev_mobile_preview():
    return send_from_directory(BASE_DIR, "jaydev-mobile.preview.htm")


@app.route("/health", methods=["GET"])
def health():
    return "Review API is running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
