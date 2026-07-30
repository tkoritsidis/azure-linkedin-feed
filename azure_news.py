from datetime import datetime

today = datetime.utcnow().strftime("%Y-%m-%d")

content = f"""
Azure Executive Update

Date: {today}

✅ Azure Arc
✅ Azure Local
✅ Azure Virtual Desktop
✅ Azure Networking
✅ Azure Security

Executive Summary

This is a test post generated from GitHub Actions.

#Azure #MicrosoftAzure #AzureMVP
"""

with open("linkedin_post.txt", "w", encoding="utf-8") as f:
    f.write(content)

print("linkedin_post.txt created successfully")
