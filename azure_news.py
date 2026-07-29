import feedparser
from datetime import datetime

RSS_URL = "https://www.microsoft.com/releasecommunications/api/v2/azure/rss"

feed = feedparser.parse(RSS_URL)

if not feed.entries:
    raise Exception("No Azure updates returned from Microsoft RSS feed.")

item = feed.entries[0]

title = item.title
link = item.link

summary = ""

if hasattr(item, "summary"):
    summary = item.summary

post = f"""
Latest Azure Update

Date: {datetime.utcnow().strftime('%Y-%m-%d')}

Title:
{title}

Summary:
{summary[:500]}

Read more:
{link}

#Azure #MicrosoftAzure #CloudComputing #AzureArchitecture #AzureMVP
"""

with open("linkedin_post.txt", "w", encoding="utf-8") as f:
    f.write(post)

print(post)
