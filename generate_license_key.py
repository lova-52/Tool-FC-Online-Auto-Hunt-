import uuid
import hashlib
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin SDK
cred = credentials.Certificate("fconlinelicense-firebase-adminsdk-fbsvc-7b7e971f47.json")  # Replace with your JSON key
firebase_admin.initialize_app(cred)
db = firestore.client()

def generate_license_keys(n):
    keys = []
    for _ in range(n):
        key = uuid.uuid4().hex[:16].upper()  # Generate a 16-character key
        db.collection("license_keys").document(key).set({
            "status": "unused"
        })
        keys.append(key)
    return keys

# Generate 10 keys
keys = generate_license_keys(10)
print("Generated License Keys:", keys)
