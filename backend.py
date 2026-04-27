from flask import Flask, request, Response
from flask_cors import CORS
from openai import OpenAI
import os

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key="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")

SYSTEM_PROMPT = """You are a real customer writing a Google review for DigiArt Invitations (Surat).
Digital invitations — wedding, birthday, baby shower, engagement, ceremony.
Known for: fast delivery, premium designs, easy customization, good support, home delivery, smooth experience.

STEP 1 — PICK FORMAT (do this silently, output only the review):
Generate a random number 1–100.
- 1–70 → SHORT: exactly 1 line, 8–15 words
- 71–90 → MEDIUM: exactly 1 line, 5–8 words
- 91–95 → MICRO: 2–4 words only (e.g. "Totally worth it" / "Perfect design")
- 96–100 → DETAILED: 4–6 lines, genuine storytelling, still max ~80 words total

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
    return Response(review_text, mimetype="text/plain")

@app.route("/", methods=["GET"])
def health():
    return "DigiArt Review API is running ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)