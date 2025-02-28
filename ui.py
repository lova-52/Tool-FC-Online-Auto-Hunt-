import os
import time
import threading
import win32gui
import win32api
import win32con
import win32ui
import tkinter as tk
from PIL import Image, ImageTk
import pytesseract
import re
import sys
import requests
import uuid
import hashlib
import winsound
import datetime
import pytz  # Import pytz for timezone handling
from license_check import check_license_ui
from tkinter import ttk, messagebox


# Define your timezone (Vietnam = UTC+7)
LOCAL_TIMEZONE = pytz.timezone("Asia/Ho_Chi_Minh")


hWnd = win32gui.FindWindow(None, "FC ONLINE")

# Set Base Path
base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

# Configure Tesseract Path
tesseract_path = os.path.join(base_path, "Tesseract-OCR", "tesseract.exe")
pytesseract.pytesseract.tesseract_cmd = tesseract_path


# Firebase
# Firebase Configuration
FIREBASE_PROJECT_ID = "fconlinelicense"

# Generate HWID
def get_hwid():
    hwid = uuid.getnode()
    return hashlib.sha256(str(hwid).encode()).hexdigest()
    
# Fetch account details directly in ui.py

def fetch_account_info():
    try:
        hwid = get_hwid()
        firestore_url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/licenses/{hwid}"
        response = requests.get(firestore_url, timeout=5).json()

        if "fields" in response:
            fields = response["fields"]
            phone = fields.get("phone", {}).get("stringValue", "Unknown")
            status = fields.get("status", {}).get("stringValue", "Unknown")
            
            # Extract expiry_date from Firebase timestamp
            expiry_timestamp = fields.get("expiry_date", {}).get("timestampValue", "Unknown")

            if expiry_timestamp != "Unknown":
                # Convert ISO timestamp to datetime object in UTC
                expiry_date_utc = datetime.datetime.fromisoformat(expiry_timestamp.replace("Z", "+00:00"))
                
                # Convert from UTC to local time (UTC+7)
                expiry_date_local = expiry_date_utc.astimezone(LOCAL_TIMEZONE)
                
                # Format to readable date
                expiry_date = expiry_date_local.strftime("%d-%m-%Y %H:%M:%S")
            else:
                expiry_date = "Unknown"

            return {
                "phone": phone,
                "hwid": hwid,
                "status": status,
                "expiry_date": expiry_date
            }
    
    except requests.exceptions.RequestException:
        messagebox.showerror("Lỗi", "Không thể kết nối đến server. Hãy kiểm tra mạng!")

    return None  # License not found or error occurred

# Refresh account info
def refresh_account_info(account_labels):
    info = fetch_account_info()
    if info:
        account_labels["phone"].config(text=f"📞 SĐT: {info['phone']}")
        account_labels["hwid"].config(text=f"💻 HWID: {info['hwid'][:10]}...")  # Partially hide HWID
        account_labels["status"].config(text=f"✅ Trạng thái: {info['status'].upper()}", 
                                        fg="green" if info["status"] == "active" else "red")
        account_labels["expiry_date"].config(text=f"📅 Ngày hết hạn: {info['expiry_date']}")

running = False

if not os.path.exists(tesseract_path):
    raise FileNotFoundError(f"Tesseract not found at: {tesseract_path}")
    
# Utility Functions
def stop_automation():
    global running
    running = False
    print("Automation Stopped!")

def click(x, y, num_clicks=1, interval=0):
    if not running:
        return
    lParam = win32api.MAKELONG(x, y)
    for _ in range(num_clicks):
        win32api.PostMessage(hWnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
        time.sleep(0.05)
        win32api.PostMessage(hWnd, win32con.WM_LBUTTONUP, 0, lParam)
        if interval != 0:
            time.sleep(interval)

def send_escape_key():
    win32api.PostMessage(hWnd, win32con.WM_KEYDOWN, win32con.VK_ESCAPE, 0)
    time.sleep(0.05)
    win32api.PostMessage(hWnd, win32con.WM_KEYUP, win32con.VK_ESCAPE, 0)

def is_valid_price(text):
    text = text.strip()
    if " " in text:
        return False

    price_pattern = r"^\d{1,3}(,\d{3})*$|^\d+(\.\d+)?[MB]$"
    return re.match(price_pattern, text) is not None

def wait_for_price_window_SanDSYT(x, y, width, length):
    extracted_text = ""
    attempts = 0
    max_attempts = 100  
    while not is_valid_price(extracted_text) and attempts < max_attempts and running:
        img = capture_hidden_window(x, y, width, length)
        extracted_text = ocr_extraction(img).strip()
        second_extracted_text = ocr_extraction(img).strip()
        if extracted_text != second_extracted_text:
            extracted_text = ocr_extraction(img).strip()
        print(f"Attempt {attempts}: Extracted Text = '{extracted_text}'")
        time.sleep(0.1)
        attempts += 1        
        if attempts % 5 == 0 and attempts >= 5 :
            send_escape_key()
            time.sleep(0.1)
            click(874, 630, num_clicks=1, interval=0)
    return extracted_text

def resize_and_reposition_window():
    if hWnd:
        win32gui.MoveWindow(hWnd, 0, 0, 1280, 720, True)

# Window Capture Functions
def capture_hidden_window(x, y, width, height):
    hWndDC = win32gui.GetWindowDC(hWnd)
    mfcDC = win32ui.CreateDCFromHandle(hWndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    saveBitmap = win32ui.CreateBitmap()
    saveBitmap.CreateCompatibleBitmap(mfcDC, width, height)
    saveDC.SelectObject(saveBitmap)
    saveDC.BitBlt((0, 0), (width, height), mfcDC, (x, y), win32con.SRCCOPY)
    bmpinfo = saveBitmap.GetInfo()
    bmpstr = saveBitmap.GetBitmapBits(True)
    img = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
    win32gui.DeleteObject(saveBitmap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hWnd, hWndDC)
    return img

def show_img(img):
    img = img.resize((250, 150))
    img_tk = ImageTk.PhotoImage(img)
    lbl_img.config(image=img_tk)
    lbl_img.image = img_tk

def ocr_extraction(img):
    return pytesseract.image_to_string(img, lang="eng")

def stop_with_hotkey(event):
    stop_automation()

# Automation Functions
def hunt_players():
    global running
    running = True
    resize_and_reposition_window()  
    thread = threading.Thread(target=hunt_players_loop, daemon=True)
    thread.start()

def hunt_players_loop():
    global running
    click(874, 630, num_clicks=1, interval=0)
    extracted_text = wait_for_price_window_SanDSYT(950, 305 ,100, 30)
    previous_price = extracted_text
    click(1000, 287, num_clicks=1, interval=0)
    time.sleep(0.3) 
    click(836, 549, num_clicks=1, interval=0)
    time.sleep(1)
    while running:
        click(874, 630, num_clicks=1, interval=0)
        extracted_text = wait_for_price_window_SanDSYT(950, 305 ,100, 30)
        if extracted_text != previous_price:
            time.sleep(0.1)
            confirmed_extracted_text = wait_for_price_window_SanDSYT(950, 305 ,100, 30)
            if confirmed_extracted_text != extracted_text and confirmed_extracted_text == previous_price:
                continue
            print(extracted_text)
            previous_price = extracted_text
            click(1004, 282, num_clicks=1, interval=0)
            print("Stop") 
            time.sleep(0.1)
            click(819, 553, num_clicks=1, interval=0)
            time.sleep(3)
            slot_img = capture_hidden_window(583, 325, 500, 330)
            show_img(slot_img)
                                  
            if hunt_sound_var.get():
                winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
                
        print("The same price, skipping")
        send_escape_key()

def sell_players():
    global running
    running = True
    resize_and_reposition_window()
    thread = threading.Thread(target=sell_players_loop, daemon=True)
    thread.start()
    
def sell_players_loop():
    global running
    click (1000, 630, num_clicks=1, interval=0)
    extracted_text = wait_for_price_window_SanDSYT(941, 318 , 130, 30)
    previous_price = extracted_text
    send_escape_key()
    time.sleep(1)
    while running:
        click(1000, 630, num_clicks=1, interval=0)
        extracted_text = wait_for_price_window_SanDSYT(941, 318 , 130, 30)
        if extracted_text != previous_price:
            time.sleep(0.1)
            confirmed_extracted_text = wait_for_price_window_SanDSYT(950, 305 ,100, 30)
            if confirmed_extracted_text != extracted_text and confirmed_extracted_text == previous_price:
               continue
            print(extracted_text)
            previous_price = extracted_text
            click(1011, 299, num_clicks=1, interval=0)
            print("Stop")
            time.sleep(0.01)
            click(828, 587, num_clicks=1, interval=0)
            time.sleep(3)
            slot_img = capture_hidden_window(583, 310, 500, 380)
            show_img(slot_img)
            
            if sell_sound_var.get():
                winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)

        print("The same price, skipping")
        send_escape_key()

def toggle_automation_hunting():
    global running
    if running:
        stop_automation()
        btn_hunt_toggle.config(text="Bắt đầu", bg="blue", fg="white")  # Switch to start mode
    else:
        hunt_players()
        btn_hunt_toggle.config(text="Dừng", bg="red", fg="white")  # Switch to stop mode
        
def toggle_automation_selling():
    global running
    if running:
        stop_automation()
        btn_sell_toggle.config(text="Bắt đầu", bg="blue", fg="white")  # Switch to start mode
    else:
        sell_players()
        btn_sell_toggle.config(text="Dừng", bg="red", fg="white")  # Switch to stop mode
        
#  **Disable the Entire UI When Expired**
def disable_ui(root):
    for widget in root.winfo_children():
        try:
            widget.config(state="disabled")  # Disable only if the widget supports "state"
        except tk.TclError:
            pass  # Ignore widgets that don't support "state"
    
    messagebox.showwarning("Hết thời gian sử dụng", "Hết thời gian sử dụng, hãy nạp thêm!")


# 🔄 **Function to Constantly Check Expiry**
def check_expiry_status(root):
    while True:
        account_info = fetch_account_info()
        if account_info:
            expiry_date_str = account_info["expiry_date"]
            now = datetime.datetime.now(LOCAL_TIMEZONE)

            try:
                expiry_date = datetime.datetime.strptime(expiry_date_str, "%d-%m-%Y %H:%M:%S")  # Convert string to datetime
                expiry_date = LOCAL_TIMEZONE.localize(expiry_date)  # Ensure it's timezone-aware

                print(now, "compare with", expiry_date)
                if now >= expiry_date:
                    root.after(0, disable_ui, root)  # Disable UI from the main thread
                    break  # Stop checking
            except ValueError as e:
                print("Error parsing expiry_date:", e)

        time.sleep(60)  # Check every 60 seconds
        
# 🔥 **Start Expiry Checking Thread**
def start_expiry_checker(root):
    expiry_thread = threading.Thread(target=check_expiry_status, args=(root,), daemon=True)
    expiry_thread.start()
              
def init_ui(root):
    global lbl_img_hunt, lbl_img_sell, btn_hunt_toggle, btn_sell_toggle, hunt_sound_var, sell_sound_var  

    root.iconbitmap("icon.ico")
    root.title("FC Tool")
    root.geometry("600x700")
    root.resizable(False, False)
    
    # Fetch account info
    license_info = fetch_account_info()
    phone = license_info["phone"] if license_info else "Unknown"
    hwid = license_info["hwid"] if license_info else "Unknown"
    status = license_info["status"] if license_info else "Unknown"
    expiry_date = license_info["expiry_date"] if license_info else "Unknown"
  
   # Start expiry checking thread
    start_expiry_checker(root)  

    # Account Info Frame
    account_frame = tk.Frame(root, relief="solid", borderwidth=1, padx=10, pady=5, bg="lightgray")
    account_frame.pack(fill="x", pady=5)

    tk.Label(account_frame, text="📌 Thông tin tài khoản", font=("Arial", 12, "bold"), bg="lightgray").pack()
    
    lbl_phone = tk.Label(account_frame, text=f"📞 SĐT: {phone}", font=("Arial", 10), bg="lightgray")
    lbl_phone.pack()
    
    lbl_hwid = tk.Label(account_frame, text=f"💻 HWID: {hwid[:10]}...", font=("Arial", 10), bg="lightgray")  # Partially hidden HWID
    lbl_hwid.pack()
    
    lbl_status = tk.Label(account_frame, text=f"✅ Trạng thái: {status.upper()}", font=("Arial", 10), 
                          fg="green" if status == "active" else "red", bg="lightgray")
    lbl_status.pack()
    
    lbl_expiry_date = tk.Label(account_frame, text=f"📅 Ngày hết hạn: {expiry_date}", font=("Arial", 10), bg="lightgray")
    lbl_expiry_date.pack()

    # Store labels for refreshing
    account_labels = {
        "phone": lbl_phone,
        "hwid": lbl_hwid,
        "status": lbl_status,
        "expiry_date": lbl_expiry_date
    }
    
    # Sound Variables (MAKE THEM GLOBAL)
    hunt_sound_var = tk.BooleanVar(value=True)
    sell_sound_var = tk.BooleanVar(value=True)


    # Refresh Button
    btn_refresh = tk.Button(account_frame, text="🔄 Làm mới", font=("Arial", 8, "bold"),
                            bg="blue", fg="white", command=lambda: refresh_account_info(account_labels))
    btn_refresh.pack(pady=5)

    # Run License Check
    if check_license_ui(root):
        print("Valid")
    else:
        root.mainloop()
    
    tab_control = ttk.Notebook(root)

    # Tab săn cầu thủ -----------------
    tab1 = ttk.Frame(tab_control)
    tab_control.add(tab1, text="Săn từ Danh sách yêu thích")

    btn_hunt_toggle = tk.Button(tab1, text="Bắt đầu", command=toggle_automation_hunting)  # Now defined globally
    btn_hunt_toggle.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)  # Góc phải dưới cùng    
    
    lbl_image_text_hunt = tk.Label(tab1, text="Khi săn thành công, hình chụp màn hình lại slot đặt sẽ hiện ở đây:", font=("Arial", 10, "bold"))
    lbl_image_text_hunt.pack(pady=5)
    
    # Hunting Image Frame
    frame_hunt_img = tk.Frame(tab1, width=500, height=380, borderwidth=2, relief="groove", bg="white")
    frame_hunt_img.pack(pady=10)
    frame_hunt_img.pack_propagate(False) 
      
    lbl_img_hunt = tk.Label(frame_hunt_img, bg="white")
    lbl_img_hunt.place(relx=0.5, rely=0.5, anchor="center")  
    lbl_img_hunt.image = None  
    
    hunt_sound_var = tk.BooleanVar(value=True)
    hunt_sound_checkbox = tk.Checkbutton(tab1, text="Phát âm thanh khi săn thành công", variable=hunt_sound_var)
    hunt_sound_checkbox.pack() 
    
    # Tab bán cầu thủ -----------------
    tab2 = ttk.Frame(tab_control)
    tab_control.add(tab2, text="Bán từ Danh sách yêu thích")

    btn_sell_toggle = tk.Button(tab2, text="Bắt đầu", command=toggle_automation_selling)  # Also declare btn_sell_toggle globally
    btn_sell_toggle.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)  

    lbl_image_text_sell = tk.Label(tab2, text="Khi bán thành công, hình ảnh sẽ hiện ở đây:", font=("Arial", 10, "bold"))
    lbl_image_text_sell.pack()

    # Selling Image Frame
    frame_sell_img = tk.Frame(tab2, width=500, height=380, borderwidth=2, relief="groove", bg="white")
    frame_sell_img.pack(pady=10)
    frame_sell_img.pack_propagate(False)

    lbl_img_sell = tk.Label(frame_sell_img, bg="white")
    lbl_img_sell.place(relx=0.5, rely=0.5, anchor="center")  
    lbl_img_sell.image = None  
    
    sell_sound_var = tk.BooleanVar(value=True)
    sell_sound_checkbox = tk.Checkbutton(tab2, text="Phát âm thanh khi bán thành công", variable=sell_sound_var)
    sell_sound_checkbox.pack(pady=5)

    tab_control.pack(expand=1, fill="both")
    root.bind("<F3>", stop_with_hotkey)

    root.mainloop()


def show_img(img, mode="hunt"):
    img = img.resize((480, 290))
    img_tk = ImageTk.PhotoImage(img)
    if mode == "hunt":
        lbl_img_hunt.config(image=img_tk)
        lbl_img_hunt.image = img_tk
    else:
        lbl_img_sell.config(image=img_tk)
        lbl_img_sell.image = img_tk
