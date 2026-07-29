import feedparser
from datetime import datetime

RSS_URL = "https://www.microsoft.com/releasecommunications/api/v2/azure/rss"

feed = feedparser.parse(RSS_URL)

if not feed.entries:
    raise Exception("No Azure updates returned from Microsoft RSS")

updates = feed.entries[:5]

post = f"""
Latest Azure Updates

Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

"""

for i, item in enumerate(updates, start=1):

    title = item.get("title", "Azure Update")
    link = item.get("link", "")

    summary = item.get("summary", "")
    summary = summary.replace("\n", " ")
    summary = summary[:250]

    post += f"""
{i}. {title}

{summary}

Read more:
{link}

--------------------------------------------------

"""

post += """
#Azure
#MicrosoftAzure
#AzureArc
#AzureLocal
#AzureNetworking
#AzureMVP
"""

with open("linkedin_post.txt", "w", encoding="utf-8") as f:
    f.write(post)

print(post)
