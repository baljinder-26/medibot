import re
import json
import os

filepath = r'e:\medibot\medilex-rag\backend\src\auth_db.json'
with open(filepath, 'r', encoding='utf-8') as f:
    data = f.read()

users = []
matches = re.finditer(r'"username"\s*:\s*"([^"]+)",\s*"email"\s*:\s*"([^"]+)",\s*"password"\s*:\s*"([^"]+)",\s*"height"\s*:\s*"([^"]+)",\s*"weight"\s*:\s*"([^"]+)",\s*"bmi"\s*:\s*"([^"]+)"', data)

for match in matches:
    user = {
        "username": match.group(1),
        "email": match.group(2),
        "password": match.group(3),
        "height": match.group(4),
        "weight": match.group(5),
        "bmi": match.group(6),
        "sessions": []
    }
    users.append(user)

new_db = {"users": users}

with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(new_db, f, indent=4)

print("Recovered users:", [u['email'] for u in users])
