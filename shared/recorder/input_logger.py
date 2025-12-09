from pynput import mouse, keyboard
import time
import pyautogui
import os

log_file = "assets/actions.log"
screenshot_dir = "assets"
listener_mouse = None
listener_keyboard = None
screenshot_callback = None  # Callback function for screenshot capture

def on_click(x, y, button, pressed):
    if pressed:
        # Call the callback function if it's set (for screenshot mode)
        if screenshot_callback:
            screenshot_callback(x, y)
        # Log the click
        with open(log_file, "a") as f:
            f.write(f"{time.time()} CLICK {button} at ({x},{y})\n")

def on_key(key):
    with open(log_file, "a") as f:
        f.write(f"{time.time()} KEY {key}\n")

def start_logging(output="assets/actions.log", screenshot_dir_path="assets", click_callback=None):
    global listener_mouse, listener_keyboard, log_file, screenshot_dir, screenshot_callback
    log_file = output
    screenshot_dir = screenshot_dir_path
    screenshot_callback = click_callback
    
    # Create log file
    with open(log_file, "w") as f:
        f.write(f"# Actions Log - {time.ctime()}\n")
    
    listener_mouse = mouse.Listener(on_click=on_click)
    listener_keyboard = keyboard.Listener(on_press=on_key)
    listener_mouse.start()
    listener_keyboard.start()

def stop_logging():
    global listener_mouse, listener_keyboard, screenshot_callback
    if listener_mouse: listener_mouse.stop()
    if listener_keyboard: listener_keyboard.stop()
    screenshot_callback = None
