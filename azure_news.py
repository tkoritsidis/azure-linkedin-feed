import feedparser

rss = "https://azure.microsoft.com/en-us/updates/feed/"

feed = feedparser.parse(rss)

if len(feed.entries) == 0:
    print("No articles found in feed")
    exit(1)

article = feed.entries[0]

title = article.title
link = article.link

post = f"""
🚀 New Azure Update

{title}

Read more:
{link}

#Azure #MicrosoftAzure #CloudComputing #AzureArchitect
"""

with open("linkedin_post.txt", "w", encoding="utf-8") as f:
    f.write(post)

print(post)
