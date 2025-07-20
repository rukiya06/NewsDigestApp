from transformers import pipeline
import yagmail
import os
import json
from datetime import datetime
from newsapi import NewsApiClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load API keys and email credentials
newsapi = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))
sender_email = os.getenv("EMAIL_USER")
sender_password = os.getenv("EMAIL_PASS")


# Load summarization model
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

# Load user preferences (topic & frequency)
with open("config.json", "r") as f:
    config = json.load(f)

topic = config.get("topic", "Climate India")
frequency = config.get("frequency", "daily")
recipient = config.get("receiver")
# Check if user unsubscribed
if frequency.lower() not in ["daily", "weekly"]:
    print("⚠️ You are currently unsubscribed from daily/weekly digests.")
    choice = input("👉 Do you want to receive today's news just once? (yes/no): ").lower()
    if choice != "yes":
        print("ℹ️ No digest sent. Have a good day!")
        exit()
else:
    choice = input("📅 Do you want to change to Daily or Weekly digest? (daily/weekly/skip): ").lower()
    if choice in ["daily", "weekly"]:
        config["frequency"] = choice
        with open("config.json", "w") as f:
            json.dump(config, f)
        print(f"✅ Digest frequency updated to {choice}.")
    else:
        print("ℹ️ Frequency unchanged.")      

# Function to fetch articles
def get_articles(topic):
    all_articles = newsapi.get_everything(q=topic, language='en', sort_by='relevancy', page_size=5)
    return all_articles['articles']

# Function to summarize article content
def summarize_article(content):
    if content:
        try:
            summary = summarizer(content, max_length=len(content.split()) - 10, min_length=15, do_sample=False)[0]['summary_text']
            return summary
        except:
            return "Summary generation failed."
    return "No content available to summarize."

# Generate the full digest
def generate_digest(topic):
    articles = get_articles(topic)
    digest = f"📰 News Digest for: {topic}\n\n"
    for i, article in enumerate(articles, 1):
        title = article['title']
        url = article['url']
        content = article.get('content') or article.get('description') or ''
        summary = summarize_article(content)
        digest += f"{i}. {title}\n🔗 {url}\n📝 Summary: {summary}\n\n"
    return digest

# Compose subject and body
subject = f"🗞️ Your {frequency.capitalize()} News Digest on '{topic}'"
body = generate_digest(topic)

# Send the email
yag = yagmail.SMTP(user=sender_email, password=sender_password, host='smtp.gmail.com', port=465, smtp_ssl=True)
yag.send(to=recipient, subject=subject, contents=body)

print("✅ News digest with summaries sent successfully.")
print(f"🗓️ Sending a {frequency} digest for today: {datetime.now().date()}")

# Ask user if they want to update their frequency
choice = input("📅 Do you want to change to Daily or Weekly digest? (daily/weekly/skip): ").lower()

if choice in ["daily", "weekly"]:
    config["frequency"] = choice
    with open("config.json", "w") as f:
        json.dump(config, f)
    print(f"✅ Digest frequency updated to {choice}.")
else:
    print("ℹ️ Frequency unchanged.")
with open("digest_log.txt", "a") as log:
    log.write(f"{datetime.now()} - Digest sent for topic: {topic}\n")
