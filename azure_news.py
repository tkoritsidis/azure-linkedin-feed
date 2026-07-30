import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

RSS_URL = "https://www.microsoft.com/releasecommunications/api/v2/azure/rss"

xml_data = urllib.request.urlopen(RSS_URL).read()

root = ET.fromstring(xml_data)

updates = []

for item in root.iter():
    if item.tag.endswith("item"):
        title = ""
        link = ""

        for child in item:
            if child.tag.endswith("title"):
                title = child.text or ""
            elif child.tag.endswith("link"):
                link = child.text or ""

        if title:
            updates.append((title, link))

content = f"🚀 Azure Executive Update\n"
content += f"Date: {datetime.utcnow().strftime('%Y-%m-%d')}\n\n"

for i[ in root.iter():
 item.tag.endswith("item"):rt=1):
    content += f"{i}. {title}\n"
    content += f"{link}\n\n"

content += "#Azure #MicrosoftAzure #AzureMVP\n"

with open("linkedin_post.txt", "w", encoding="utf-8") as f:
    f.write(content)

print("linkedin_post.txt created successfully")
