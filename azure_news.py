import feedparser

rss = "https://techcommunity.microsoft.com/rss/board?board.id=AzureBlog"

feed = feedparser.parse(rss)

article = feed.entries[0]

title = article.title
link = article.link

post = f"""
🚀 New Microsoft Azure Update

{title}

🔗 {link}

Key takeaway:
This latest Azure update brings new capabilities that can help organizations modernize and optimize their cloud environments.

#Azure #MicrosoftAzure #CloudComputing #AzureArchitecture #AzureMVP
"""

with open("linkedin_post.txt", "w", encoding="utf-8") as f:
    f.write(post)

print(post)
