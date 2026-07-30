from datetime import datetime

post = f"""🚀 Azure Executive Update

Date: {datetime.utcnow().strftime('%Y-%m-%d')}

✅ Azure Arc
✅ Azure Local
✅ Azure Virtual Desktop
✅ Azure Networking
✅ Azure Security

Executive Summary

This is a test generated from GitHub Actions.

#Azure #MicrosoftAzure #AzureMVP
"""

with open("linkedin_post.txt", "w", encoding="utf-8") as f:
    f.write(post)

print("Created: linkedin_post.txt")
print(post)
