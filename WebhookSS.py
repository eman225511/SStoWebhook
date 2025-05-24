import pyautogui
import requests
import time
import threading
import keyboard
import tkinter as tk
from io import BytesIO
from datetime import datetime
import getpass
import pyautogui

# ========== CONFIG ==========

WEBHOOK_URL = input("Enter your Discord webhook URL: ").strip()
try:
    INTERVAL_SECONDS = int(input("Enter screenshot interval in seconds (e.g., 600): ").strip())
except ValueError:
    INTERVAL_SECONDS = 600
    print("Invalid input. Using default interval: 600 seconds.")
KILL_KEY = input("Enter the kill key (default 'k'): ").strip() or 'k'
DISCORD_USER_ID = input("Enter your Discord User ID to @mention: ").strip()

# ============================

region = None
running = True

def select_region():
    global region

    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.attributes('-alpha', 0.3)
    root.configure(background='gray')
    root.title("Select region")

    canvas = tk.Canvas(root, cursor="cross", bg='gray')
    canvas.pack(fill=tk.BOTH, expand=True)

    rect = None
    start_x = start_y = 0

    def on_mouse_down(event):
        nonlocal start_x, start_y, rect
        start_x, start_y = event.x, event.y
        rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline='black', width=2)

    def on_mouse_drag(event):
        nonlocal rect
        canvas.coords(rect, start_x, start_y, event.x, event.y)

    def on_mouse_up(event):
        global region
        x1, y1 = min(start_x, event.x), min(start_y, event.y)
        x2, y2 = max(start_x, event.x), max(start_y, event.y)
        width, height = x2 - x1, y2 - y1
        region = (x1, y1, width, height)
        root.destroy()

    canvas.bind("<ButtonPress-1>", on_mouse_down)
    canvas.bind("<B1-Motion>", on_mouse_drag)
    canvas.bind("<ButtonRelease-1>", on_mouse_up)

    root.mainloop()

def take_screenshot(region):
    return pyautogui.screenshot(region=region)

def send_to_discord(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    buffered.seek(0)

    # Info gathering
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    username = getpass.getuser()
    screen_width, screen_height = pyautogui.size()

    # Message content
    message = (
        f"<@{DISCORD_USER_ID}>\n"
        f"📸 Screenshot captured at `{timestamp}`\n"
        f"👤 User: `{username}`\n"
        f"🖥️ Resolution: `{screen_width}x{screen_height}`"
    )

    files = {
        'file': ('screenshot.png', buffered, 'image/png')
    }
    payload = {
        "content": message
    }

    response = requests.post(WEBHOOK_URL, data=payload, files=files)
    if response.status_code not in (200, 204):
        print(f"❌ Failed to send to Discord: {response.status_code} - {response.text}")
    else:
        print(f"✅ Screenshot sent to Discord at {timestamp}")

def monitor_kill_key():
    global running
    print(f"🛑 Press '{KILL_KEY.upper()}' to stop the screenshot loop.")
    keyboard.wait(KILL_KEY)
    running = False
    print("🔒 Kill key pressed. Exiting...")

def main():
    global running

    print("📐 Please select the region for screenshot...")
    select_region()
    if region is None:
        print("❌ No region selected. Exiting.")
        return

    print(f"✅ Region selected: {region}")
    threading.Thread(target=monitor_kill_key, daemon=True).start()

    while running:
        screenshot = take_screenshot(region)
        send_to_discord(screenshot)
        for _ in range(INTERVAL_SECONDS):
            if not running:
                break
            time.sleep(1)

if __name__ == '__main__':
    main()
