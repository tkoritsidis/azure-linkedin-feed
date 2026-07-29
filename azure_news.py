import urllib.request
import json

url = "https://azure.microsoft.com/api/v3/blog/posts/"

try:
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())

    if len(data) == 0:
        raise Exception("No Azure blog posts returned")

    article = data[0]

    title = article.get("title", "Azure Update")
    link = article.get("url", "https://azure.microsoft.com/blog")

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

except Exception as e:
    print(f"ERROR: {e}")
    raise
