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
    reg_window = tk.Toplevel(root)
    reg_window.title("License Registration")
    reg_window.geometry("400x200")
    reg_window.grab_set()  # Make this window modal

    # Disable the main window until registration is complete
    root.withdraw()

    tk.Label(reg_window, text="HWID not registered!", font=("Arial", 12, "bold"), fg="red").pack(pady=10)
    tk.Label(reg_window, text="Enter your license key:").pack()

    license_entry = tk.Entry(reg_window, width=30)
    license_entry.pack(pady=5)

    def submit_license():
        license_key = license_entry.get().strip().upper()
        if register_license(license_key):
            messagebox.showinfo("Success", "✅ Registration successful! You can now use the program.")
            reg_window.destroy()
            root.deiconify()  # Re-enable main UI
            initialize_main_ui()  # Now launch main program
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

# Initialize Main UI
def initialize_main_ui():
    tab_control = ttk.Notebook(root)
    tab1 = ttk.Frame(tab_control)
    tab_control.add(tab1, text="Săn từ Danh sách yêu thích")

    btn_hunt = tk.Button(tab1, text="Start Hunting", command=start_hunting)
    btn_hunt.pack(pady=10)

    btn_stop = tk.Button(tab1, text="Stop", command=stop_automation, bg="red", fg="white")
    btn_stop.pack(pady=10)

    tab2 = ttk.Frame(tab_control)
    tab_control.add(tab2, text="Bán từ Danh sách yêu thích")

    btn_sell = tk.Button(tab2, text="Start Selling", command=start_selling)
    btn_sell.pack(pady=20)

    lbl_image_text = tk.Label(root, text="Slot đặt cầu thủ sẽ được hiện ở đây: ", font=("Arial", 10, "bold"))
    lbl_image_text.pack(pady=5)

    lbl_img = tk.Label(root)
    lbl_img.pack(pady=10)

    lbl_text = tk.Label(root, text="", wraplength=400, justify="left", font=("Arial", 10))
    lbl_text.pack(pady=10)

    tab_control.pack(expand=1, fill="both")

    root.mainloop()

# Dummy Automation Functions
def start_hunting():
    global running
    running = True
    print("Started hunting...")

def start_selling():
    global running
    running = True
    print("Started selling...")

def stop_automation():
    global running
    running = False
    print("Automation Stopped!")

# UI Initialization
root = tk.Tk()
root.title("FC Online Automation")
root.geometry("500x500")
root.resizable(False, False)

# Run License Check
if check_license_ui():
    initialize_main_ui()  # If license is valid, run main UI
else:
    root.mainloop()  # Keep Tkinter running while user registers
