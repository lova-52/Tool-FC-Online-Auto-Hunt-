import os
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
import sys
import requests
import uuid
import hashlib
from ui import init_ui


# Global Variables
hWnd = win32gui.FindWindow(None, "FC ONLINE")
if not hWnd:
    print("Window not found!")
else:
    print("Window found!")

init_ui()
