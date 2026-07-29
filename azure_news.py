import feedparser

# Azure Blog RSS Feed
rss = "https://techcommunity.microsoft.com/plugins/custom/microsoft/o365/custom-blog-rss?tid=Azure"

feed = feedparser.parse(rss)

print(f"Entries found: {len(feed.entries)}")

if not feed.entries:
    raise Exception("RSS feed returned no articles")

article = feed.entries[0]

title = article.title
link = article.link

post = f"""
🚀 New Microsoft Azure Update

{title}

Read more:
{link}

#Azure #MicrosoftAzure #CloudComputing #AzureArchitecture #AzureMVP
"""

with open("linkedin_post.txt", "w", encoding="utf-8") as f:
    f.write(post)

print(post)
