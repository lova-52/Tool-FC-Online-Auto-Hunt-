import time
import threading
import win32gui
import win32api
import win32con
import win32ui
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import pytesseract
import re

# Set the Tesseract-OCR path (Modify this based on your installation)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Global flag to control automation
running = False

hWnd = win32gui.FindWindow(None, "FC ONLINE")
if not hWnd:
    print("Window not found!")
else:
    print("Window found!")

def stop_automation():
    """ Stops the automation loop """
    global running
    running = False
    print("Automation Stopped!")

def click(x, y, num_clicks=1, interval=0):
    """ Simulate mouse clicks inside the game window """
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
    """ Simulate pressing the Escape key inside the game """
    win32api.PostMessage(hWnd, win32con.WM_KEYDOWN, win32con.VK_ESCAPE, 0)
    time.sleep(0.05)
    win32api.PostMessage(hWnd, win32con.WM_KEYUP, win32con.VK_ESCAPE, 0)

def is_valid_price(text):
    """ Validate price format using regex """
    text = text.strip().replace(" ", "")
    price_pattern = r"^\d{1,3}(,\d{3})*$|^\d+(\.\d+)?[MB]$"
    return re.match(price_pattern, text) is not None

def wait_for_real_text():
    """ Capture and validate text until a correct price format is detected """
    extracted_text = ""
    attempts = 0
    max_attempts = 50  

    while not is_valid_price(extracted_text) and attempts < max_attempts and running:
        img = capture_hidden_window(950, 305, 100, 30)
        extracted_text = ocr_extraction(img).strip()
        print(f"Attempt {attempts}: Extracted Text = '{extracted_text}'")
        attempts += 1
        time.sleep(0.3)
        
        if attempts >= 10:
            click(874, 630, num_clicks=1, interval=0)
    
    show_img(img)
    return extracted_text

def hunt_players():
    """ Runs the hunting automation in a separate thread """
    global running
    running = True  
    thread = threading.Thread(target=hunt_players_loop, daemon=True)
    thread.start()

def hunt_players_loop():
    """ Main automation loop for hunting players """
    global running

    click(874, 630, num_clicks=1, interval=0)
    extracted_text = wait_for_real_text()
    
    previous_price = extracted_text
    click(1000, 287, num_clicks=1, interval=0)
    time.sleep(0.3) 
    click(836, 549, num_clicks=1, interval=0)
    time.sleep(1)

    while running:
        click(874, 630, num_clicks=1, interval=0)
        extracted_text = wait_for_real_text()
        
        # Price changed
        if extracted_text != previous_price:
            print(extracted_text)
            print("Stop")
            click(819, 553, num_clicks=1, interval=0)
            break  # Stop if price changes
        
        # Price unchanged - Send Escape key
        print("The same price, skipping")
        send_escape_key()

def sell_players():
    """ Placeholder function for selling players """
    print("Selling players...")

def capture_hidden_window(x, y, width, height):
    """ Capture a hidden/background window area """
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
    """ Show captured image in Tkinter UI """
    img = img.resize((250, 150))
    img_tk = ImageTk.PhotoImage(img)
    lbl_img.config(image=img_tk)
    lbl_img.image = img_tk

def ocr_extraction(img):
    """ Extract text from image using Tesseract OCR """
    return pytesseract.image_to_string(img, lang="eng")

def stop_with_hotkey(event):
    """ Stops automation when 'F3' key is pressed """
    stop_automation()

# Create the main application window
root = tk.Tk()
root.title("FC Online Automation")
root.geometry("500x500")

# Create tab control
tab_control = ttk.Notebook(root)

# Create first tab (Hunt Players)
tab1 = ttk.Frame(tab_control)
tab_control.add(tab1, text="Săn cầu thủ")
btn_hunt = tk.Button(tab1, text="Start Hunting", command=hunt_players)
btn_hunt.pack(pady=10)

# Create stop button
btn_stop = tk.Button(tab1, text="Stop", command=stop_automation, bg="red", fg="white")
btn_stop.pack(pady=10)

# Create second tab (Sell Players)
tab2 = ttk.Frame(tab_control)
tab_control.add(tab2, text="Bán cầu thủ")
btn_sell = tk.Button(tab2, text="Start Selling", command=sell_players)
btn_sell.pack(pady=20)

# **Added Label for Image Display**
lbl_image_text = tk.Label(root, text="Slot đặt cầu thủ sẽ được hiện ở đây: ", font=("Arial", 10, "bold"))
lbl_image_text.pack(pady=5)

# Display captured image in the main UI
lbl_img = tk.Label(root)
lbl_img.pack(pady=10)

# Display extracted text in UI
lbl_text = tk.Label(root, text="", wraplength=400, justify="left", font=("Arial", 10))
lbl_text.pack(pady=10)

# Pack tab control
tab_control.pack(expand=1, fill="both")

# Bind 'F3' key to stop automation
root.bind("<F3>", stop_with_hotkey)

# Run the main loop
root.mainloop()
