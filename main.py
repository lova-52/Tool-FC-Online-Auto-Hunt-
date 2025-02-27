import tkinter as tk
from ui import init_ui
from license_check import check_license_ui, show_registration_window

# Global Tkinter root
root = tk.Tk()
root.withdraw()  # Hide main window initially

def start_main_ui():
    root.deiconify()  # Show main window only if the license is valid
    init_ui(root)

# Run License Check UI
check = check_license_ui(root)
if check == 1:
    start_main_ui()
elif check == 2:
    root.mainloop() 
else:
    show_registration_window(root)
