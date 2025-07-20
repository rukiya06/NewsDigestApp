from transformers import pipeline
import yagmail
import os
import json
from datetime import datetime
from newsapi import NewsApiClient
from dotenv import load_dotenv

load_dotenv()

newsapi = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))
sender_email = os.getenv("EMAIL_USER")
sender_password = os.getenv("EMAIL_PASS")

# Load config
try:
    with open("config.json", "r") as f:
        config = json.load(f)
except FileNotFoundError:
    print("❌ config.json not found.")
    exit()

# Validate access
if not config.get("authorized", False):
    print("❌ Digest access denied. You are not authorized. Please enter the correct secret code on the web form.")
    exit()

# Extract preferences
topic = config.get("topic", "AI India")
frequency = config.get("frequency", "daily")
recipient = config.get("receiver", "")

if not recipient:
    print("❌ No recipient email configured.")
    exit()

# Load summarizer
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

# Handle frequency logic
if frequency.lower() not in ["daily", "weekly"]:
    print("⚠️ You are currently unsubscribed from daily/weekly digests.")
    choice = input("👉 Do you want to receive today's news just once? (yes/no): ").lower()
    if choice != "yes":
        print("ℹ️ No digest sent. You need to subscribe for regular updates.")
        exit()
else:
    print("✅ You are subscribed to", frequency)

# Get articles
def get_articles(topic):
    all_articles = newsapi.get_everything(q=topic, language='en', sort_by='relevancy', page_size=5)
    return all_articles['articles']

# Summarize article
def summarize_article(content,max_length=100, min_length=30):
    if content:
        try:
            return summarizer(content, max_length=max_length, min_length=min_length)[0]['summary_text']
        except Exception as e:
            print("❌ Summarization failed:", e)
            return "Summary generation failed."
    return "No content available to summarize."

# Generate digest
def generate_digest(topic):
    articles = get_articles(topic)
    digest = f"📰 News Digest for: {topic}\n\n"
    for i, article in enumerate(articles, 1):
        title = article['title']
        url = article['url']
        content = article.get('content') or article.get('description') or ''
        summary = summarize_article(content,max_length=min(100, len(content.split()) - 5), min_length=15)
        digest += f"{i}. {title}\n🔗 {url}\n📝 Summary: {summary}\n\n"
    return digest

# Compose and send email
subject = f"🗞️ Your {frequency.capitalize()} News Digest on '{topic}'"
body = generate_digest(topic)

yag = yagmail.SMTP(user=sender_email, password=sender_password)
yag.send(to=recipient, subject=subject, contents=body)

print("✅ News digest with summaries sent successfully.")
print(f"🗓️ Sending a {frequency} digest for today: {datetime.now().date()}")

# Offer to update frequency
if frequency.lower() in ["daily", "weekly"]:
    change = input("📅 Do you want to change your frequency? (daily/weekly/unsubscribe/skip): ").lower()
    if change in ["daily", "weekly", "unsubscribe"]:
        config["frequency"] = change
        with open("config.json", "w") as f:
            json.dump(config, f)
        print(f"✅ Frequency updated to {change}.")
    else:
        print("ℹ️ Frequency unchanged.")
