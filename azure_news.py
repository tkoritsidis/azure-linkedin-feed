import feedparser

rss = "https://techcommunity.microsoft.com/gxcuf89792/rss/board?board.id=Azure"

feed = feedparser.parse(rss)

print(f"Entries found: {len(feed.entries)}")

if len(feed.entries) == 0:
    raise Exception("RSS feed returned no articles")

article = feed.entries[0]

title = article.title
link = article.link

post = f"""
🚀 New Azure Article

{title}

Read more:
{link}

#Azure #MicrosoftAzure #Cloud #AzureArchitecture
"""

with open("linkedin_post.txt", "w", encoding="utf-8") as f:
    f.write(post)

print(post)
