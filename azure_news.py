from datetime import datetime

post = f"""
🚀 Azure Daily Update

Generated automatically on:
{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

Today's focus:
✅ Azure Architecture
✅ Azure Arc
✅ Azure Local
✅ Azure Virtual Desktop

Follow Microsoft Azure announcements for the latest updates.

#Azure #MicrosoftAzure #CloudComputing #AzureArchitecture #AzureMVP
"""

with open("linkedin_post.txt", "w", encoding="utf-8") as f:
    f.write(post)

print(post)
