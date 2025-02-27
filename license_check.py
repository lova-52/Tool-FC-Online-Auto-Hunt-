import os
import requests
import uuid
import hashlib
import tkinter as tk
from tkinter import ttk, messagebox
import sys 

# Firebase API Configuration
FIREBASE_API_KEY = "AIzaSyCelw2i7_0_bmgwTWVl47zBmCStc-guZDE"
FIREBASE_PROJECT_ID = "fconlinelicense"

# Restart the program
def restart_program():
    python = sys.executable
    os.execv(python, [python] + sys.argv)  # Restart the entire program
    
# Generate HWID
def get_hwid():
    hwid = uuid.getnode()
    return hashlib.sha256(str(hwid).encode()).hexdigest()
    
# Check if HWID is registered
def check_license_ui(root):
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
                    return 1  # License is valid, continue program
                if status == "inactive":
                    messagebox.showerror("Lỗi", "Tài khoàn đã hết thời gian sử dụng! Hãy liên hệ admin để đăng ký tiếp!")
                    return 2
                    
    return 3
                    
    
# Show UI for License Key Entry
def show_registration_window(root):
    reg_window = tk.Toplevel()
    reg_window.iconbitmap("icon.ico")
    reg_window.title("FC Tool")
    reg_window.resizable(False, False)
    reg_window.geometry("400x250")
    reg_window.grab_set()  # Make this window modal

    tk.Label(reg_window, text="Máy chưa được đăng ký!", font=("Arial", 12, "bold"), fg="red").pack(pady=10)
    tk.Label(reg_window, text="Nhập key vào ô này:").pack()

    license_entry = tk.Entry(reg_window, width=30)
    license_entry.pack(pady=5)

    tk.Label(reg_window, text="Nhập số điện thoại của bạn:").pack()
    phone_entry = tk.Entry(reg_window, width=30)
    phone_entry.pack(pady=5)

    def submit_license():
        license_key = license_entry.get().strip().upper()
        phone_number = phone_entry.get().strip()
        if not phone_number.isdigit() or len(phone_number) < 7:
            messagebox.showerror("Lỗi", "Số điện thoại không hợp lệ!")
            return

        if register_license(license_key, phone_number):
            messagebox.showinfo("Thành công", "Đăng ký thành công. Bạn có thể dùng chương trình được rồi!")
            reg_window.destroy()
            restart_program()
        else:
            messagebox.showerror("Lỗi", "Key không hợp lệ. Hãy liên hệ admin để được hỗ trợ.")

    tk.Button(reg_window, text="Đăng ký", command=submit_license, bg="green", fg="white").pack(pady=10)
    reg_window.mainloop()
    return False  # Only return True if registered successfully

# Verify and Register License Key
def register_license(license_key, phone_number):
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
                "phone": {"stringValue": phone_number},
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
