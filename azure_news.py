import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

RSS_URL = "https://www.microsoft.com/releasecommunications/api/v2/azure/rss"

xml_data = urllib.request.urlopen(RSS_URL).read()

root = ET.fromstring(xml_data)

content = f"""🚀 Azure Executive Update

Date: {datetime.utcnow().strftime('%Y-%m-%d')}

"""

count = 0

for item in root.iter():
    if item.tag.endswith("item"):
        title = ""

        for child in item:
            if child.tag.endswith("title"):
                title = child.text or ""
                break

        if title:
            count += 1
            content += f"{count}. {title}\n\n"

        if count >= 5:
            break

content += """
Executive Summary

Top Azure updates automatically collected from Microsoft's Azure Updates feed.

#Azure #MicrosoftAzure #AzureMVP
"""

with open("linkedin_post.txt", "w", encoding="utf-8") as f:
    f.write(content)

print("linkedin_post.txt created successfully")

updates = [
{
"title": "Azure Monitor Logs mirroring into Microsoft Fabric",
"status": "Preview",
"category": "Management & Governance",
"summary": "Mirror Log Analytics data into Microsoft Fabric."
}
]
 
with open("azure_updates.json", "w", encoding="utf-8") as f:
json.dump(updates, f, indent=2, ensure_ascii=False)
 
print("Created: azure_updates.json")
