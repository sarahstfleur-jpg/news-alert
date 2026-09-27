import json
import os
import re
import sys
import time
import tkinter as tk
from tkinter import messagebox, simpledialog
import urllib.parse
import webbrowser
import feedparser
from bs4 import BeautifulSoup
from win11toast import toast

SETTINGS_FILE = "interests.json"

def load_saved_interests():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as file:
                return json.load(file).get("interests", [])
        except Exception:
            return []
    return []

def save_interests(interests):
    with open(SETTINGS_FILE, "w") as file:
        json.dump({"interests": interests}, file, indent=4)

def prompt_user_for_interests(current_interests=None):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    default_text = ", ".join(current_interests) if current_interests else "AI, SpaceX, Gaming"
    
    user_input = simpledialog.askstring(
        title="News Preferences",
        prompt="Enter topics (separated by commas):",
        initialvalue=default_text,
        parent=root
    )
    root.destroy()

    if user_input:
        return list(set([topic.strip() for topic in user_input.split(",") if topic.strip()]))
    return current_interests or []

def get_user_interests():
    saved = load_saved_interests()
    if not saved:
        new_topics = prompt_user_for_interests()
        if new_topics:
            save_interests(new_topics)
        return new_topics
    else:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        topics_str = "\n• " + "\n• ".join(saved)
        edit = messagebox.askyesno(
            title="Saved Preferences Found",
            message=f"Current topics:{topics_str}\n\nDo you want to edit them?",
            parent=root
        )
        root.destroy()

        if edit:
            updated = prompt_user_for_interests(saved)
            if updated:
                save_interests(updated)
                return updated
        return saved

def clean_summary(raw_html, headline_title=""):
    """Strips HTML tags and removes duplicate title text from the RSS summary."""
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text()
    cleaned = re.sub(r'\s+', ' ', text).strip()

    # Remove the headline if Google News duplicated it at the start of the summary
    if headline_title and cleaned.startswith(headline_title):
        cleaned = cleaned[len(headline_title):].strip(" -–:")

    # Handle empty or stripped down summaries
    if not cleaned or len(cleaned) < 5:
        return "Click to open full story."

    return (cleaned[:100] + '...') if len(cleaned) > 100 else cleaned

def fetch_and_notify(interests):
    for topic in interests:
        encoded_query = urllib.parse.quote(topic)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        feed = feedparser.parse(rss_url)
        if feed.entries:
            top_article = feed.entries[0]
            headline = top_article.title
            article_url = top_article.link

            print(f"\n[SENDING NOTIFICATION] {topic}: {headline}")

            # Send title-only toast; passing the URL to `on_click` makes it open on click
            toast(
                title=f"News: {topic}",
                body=headline,
                on_click=article_url
            )
            time.sleep(3)

if __name__ == "__main__":
    # Skip GUI edit dialog on startup
    if "--startup" in sys.argv:
        user_topics = load_saved_interests()
        if not user_topics:
            user_topics = get_user_interests()
    else:
        user_topics = get_user_interests()

    if user_topics:
        fetch_and_notify(user_topics)