from flask import Flask, render_template, request
import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
SECRET_CODE = os.getenv("SECRET_CODE")

@app.route("/", methods=["GET", "POST"])
def home():
    news_data = []
    topic = ""
    frequency = ""
    user_email = ""
    error = None
    success = None

    if request.method == "POST":
        topic = request.form.get("topic")
        frequency = request.form.get("frequency")
        user_email = request.form.get("user_email")
        user_secret = request.form.get("secret")

        # Always fetch and show news
        url = f"https://newsapi.org/v2/everything?q={topic}&pageSize=5&apiKey={NEWS_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            news_data = data.get("articles", [])
        # ✅ Always update topic in config.json — even if code is wrong
        updated_config = {
            "topic": topic,
            "frequency": "unsubscribe",  # Default fallback if unauthorized
            "receiver": "",
            "authorized": False
        }
        # Check secret code
        if user_secret == SECRET_CODE:
            updated_config["frequency"] = frequency
            updated_config["receiver"] = user_email
            updated_config["authorized"] = True
            success = f"✅ Preferences saved! You'll receive news on '{topic}' {frequency}."
        else:
            error = "❌ Invalid secret code. You will not receive the digest."

        # Save preferences if code is valid
        with open("config.json", "w") as f:
            json.dump(updated_config, f)

        return render_template("index.html", news=news_data, topic=topic, success=success, error=error)
    return render_template("index.html", news=news_data, topic=topic)
if __name__ == "__main__":
    app.run(debug=True)
