import os
import sys
import requests
import uuid
import hashlib
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

# Firebase API Configuration
FIREBASE_API_KEY = "AIzaSyCelw2i7_0_bmgwTWVl47zBmCStc-guZDE"
FIREBASE_PROJECT_ID = "fconlinelicense"

# Generate HWID
def get_hwid():
    hwid = uuid.getnode()
    return hashlib.sha256(str(hwid).encode()).hexdigest()
    
# Check if HWID is registered
def check_license_ui():
    hwid = get_hwid()
    firestore_url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/licenses"
    response = requests.get(firestore_url).json()

    # Check if HWID is already registered
    if "documents" in response:
        for doc in response["documents"]:
            fields = doc.get("fields", {})
            stored_hwid = fields.get("hwid", {}).get("stringValue", "")
            status = fields.get("status", {}).get("stringValue", "")

            if stored_hwid == hwid:
                if status == "active":
                    return True  # License is valid, continue program
                else:
                    messagebox.showerror("License Error", "❌ License inactive! Contact admin.")
                    return False

    # HWID is not found → Show registration UI
    show_registration_window()
    return False
    
    
# Show UI for License Key Entry
def show_registration_window():
    reg_window = tk.Tk()
    reg_window.title("License Registration")
    reg_window.geometry("400x200")
    reg_window.grab_set()  # Make this window modal


    tk.Label(reg_window, text="HWID not registered!", font=("Arial", 12, "bold"), fg="red").pack(pady=10)
    tk.Label(reg_window, text="Enter your license key:").pack()

    license_entry = tk.Entry(reg_window, width=30)
    license_entry.pack(pady=5)

    def submit_license():
        license_key = license_entry.get().strip().upper()
        if register_license(license_key):
            messagebox.showinfo("Success", "✅ Registration successful! You can now use the program.")
            reg_window.destroy()
        else:
            messagebox.showerror("Error", "❌ Invalid or already used license key.")

    tk.Button(reg_window, text="Register", command=submit_license, bg="green", fg="white").pack(pady=10)

# Verify and Register License Key
def register_license(license_key):
    hwid = get_hwid()

    # Verify license key
    license_url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/license_keys/{license_key}"
    license_response = requests.get(license_url).json()

    if "fields" in license_response and license_response["fields"].get("status", {}).get("stringValue", "") == "unused":
        # Register HWID
        register_url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/licenses/{hwid}"
        data = {
            "fields": {
                "hwid": {"stringValue": hwid},
                "status": {"stringValue": "active"}
            }
        }
        requests.patch(register_url, json=data)

        # Mark license as used
        update_license_url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/license_keys/{license_key}"
        update_data = {
            "fields": {
                "status": {"stringValue": "used"}
            }
        }
        requests.patch(update_license_url, json=update_data)

        return True

    return False
