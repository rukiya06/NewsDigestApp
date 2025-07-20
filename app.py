from flask import Flask, render_template, request, redirect
import requests
import os
import json
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

app = Flask(__name__)
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

@app.route("/", methods=["GET", "POST"])
def home():
    news_data = []
    topic = ""
    frequency = ""

    if request.method == "POST":
        topic = request.form.get("topic")
        frequency = request.form.get("frequency")

        # Save to config.json
        with open("config.json", "w") as f:
            json.dump({"topic": topic, "frequency": frequency}, f)

        # Get top news
        url = f"https://newsapi.org/v2/everything?q={topic}&pageSize=5&apiKey={NEWS_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            news_data = data.get("articles", [])
        else:
            print("❌ ERROR from NewsAPI:", response.text)

        return render_template("index.html", news=news_data, topic=topic, saved=True)

    return render_template("index.html", news=news_data, topic=topic, saved=False)


if __name__ == "__main__":
    app.run(debug=True)
