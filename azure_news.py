from datetime import datetime

today = datetime.utcnow().strftime("%Y-%m-%d")

post = f"""
🚀 Azure Daily Update

Date: {today}

Today's focus areas:
✅ Azure Arc
✅ Azure Local
✅ Azure Virtual Desktop
✅ Azure AI
✅ Azure Networking

Stay up to date with Microsoft's latest cloud innovations.

#Azure
#MicrosoftAzure
#CloudComputing
#AzureArchitecture
#AzureMVP
"""

with open("linkedin_post.txt", "w", encoding="utf-8") as f:
    f.write(post)

print(post)
