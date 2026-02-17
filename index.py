import serial
import serial.tools.list_ports
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import os

# ---------------- SERIAL GLOBAL ----------------
ser = None 

# ---------------- LOGIN & DASHBOARD REDIRECT ----------------
def open_admin_login():
    login_win = tk.Toplevel(root)
    login_win.title("Admin Login")
    login_win.geometry("350x280")
    login_win.configure(bg="white")
    login_win.resizable(False, False)
    login_win.grab_set()

    tk.Label(login_win, text="🔐 Admin Access", font=("Segoe UI", 16, "bold"), bg="white", fg="#1e293b").pack(pady=15)

    frame = tk.Frame(login_win, bg="white")
    frame.pack(pady=10)

    tk.Label(frame, text="Username", bg="white", font=("Segoe UI", 9)).pack(anchor="w")
    user_entry = ttk.Entry(frame, width=28)
    user_entry.pack(pady=5)

    tk.Label(frame, text="Password", bg="white", font=("Segoe UI", 9)).pack(anchor="w")
    pass_entry = ttk.Entry(frame, width=28, show="*")
    pass_entry.pack(pady=5)

    def verify_login():
        u = user_entry.get()
        p = pass_entry.get()
        
        # Checking your requested credentials
        if u == "admin" and p == "admin123":
            messagebox.showinfo("Success", "Login Verified! Launching Admin Dashboard...")
            login_win.destroy()
            
            # This points exactly to the HTML file you provided
            file_path = os.path.abspath("DASHBOARD.html")
            
            if os.path.exists(file_path):
                webbrowser.open(f"file://{file_path}")
            else:
                messagebox.showerror("File Error", "DASHBOARD.html not found in the script folder!")
        else:
            messagebox.showerror("Access Denied", "Invalid Username or Password")

    ttk.Button(login_win, text="Login to Dashboard", command=verify_login).pack(pady=20)

# ---------------- SERIAL PORT CONNECTION ----------------
def connect_serial():
    global ser
    selected_port = port_combobox.get()
    try:
        ser = serial.Serial(selected_port, 115200, timeout=1)
        time.sleep(2)
        messagebox.showinfo("Connected", f"Now receiving data from {selected_port}")
        threading.Thread(target=serial_reader, daemon=True).start()
    except Exception as e:
        messagebox.showerror("Connection Failed", f"Check if Pico is plugged into {selected_port}\nError: {e}")

# ---------------- MAIN MONITOR UI ----------------
root = tk.Tk()
root.title("Solar Monitoring System - Main Hub")
root.geometry("1000x600")
root.configure(bg="#eef2f7")
style = ttk.Style()
style.theme_use("clam")
# ---------------- STYLES ----------------
style.configure("Title.TLabel",
                font=("Segoe UI", 20, "bold"),
                background="#eef2f7",
                foreground="#1e293b")

style.configure("Card.TFrame",
                background="white",
                relief="ridge",
                borderwidth=2)

style.configure("CardTitle.TLabel",
                font=("Segoe UI", 12, "bold"),
                background="white")

style.configure("Value.TLabel",
                font=("Segoe UI", 14, "bold"),
                background="white")

style.configure("Fetch.TButton",
                font=("Segoe UI", 10, "bold"),
                background="#2563eb",
                foreground="white")

style.map("Fetch.TButton",
          background=[("active", "#1d4ed8")])
# ---------------- TITLE ----------------
ttk.Label(root, text="🌞 Solar Energy Monitoring System",
          style="Title.TLabel").pack(anchor="w", padx=25, pady=15)
# ---------------- LIVE DATA CARDS ----------------
cards_frame = tk.Frame(root, bg="#eef2f7")
cards_frame.pack(fill="x", padx=20)

cards = {}

card_info = [
    ("Date", "#fef3c7"),
    ("Time", "#e0f2fe"),
    ("Azimuth (°)", "#ede9fe"),
    ("Elevation (°)", "#fce7f3"),
    ("Voltage (V)", "#dcfce7"),
    ("Current (A)", "#ffe4e6"),
    ("Power (W)", "#ffedd5"),
]

for i, (title, color) in enumerate(card_info):
    card = tk.Frame(cards_frame, bg=color, bd=0, relief="ridge")
    card.grid(row=i//4, column=i%4, padx=15, pady=15, sticky="nsew")

    tk.Label(card, text=title, font=("Segoe UI", 11, "bold"),
             bg=color, fg="#1f2937").pack(anchor="w", padx=15, pady=(10,0))

    val = tk.StringVar(value="--")
    tk.Label(card, textvariable=val, font=("Segoe UI", 18, "bold"),
             bg=color, fg="#020617").pack(anchor="w", padx=15, pady=(5,15))

    cards[title] = val

# --- TOP CONTROL BAR ---
top_bar = tk.Frame(root, bg="#eef2f7")
top_bar.pack(fill="x", padx=25, pady=15)

tk.Label(top_bar, text="🔌 Port Selection:", bg="#eef2f7", font=("Segoe UI", 10, "bold")).pack(side="left")
ports = [p.device for p in serial.tools.list_ports.comports()]
port_combobox = ttk.Combobox(top_bar, values=ports, width=15, state="readonly")
port_combobox.pack(side="left", padx=10)
if ports: port_combobox.current(0)

ttk.Button(top_bar, text="Connect Pico", command=connect_serial).pack(side="left", padx=5)

# Admin Login Button (Launches your HTML)
admin_btn = ttk.Button(root, text="🔐 Admin Dashboard Login", command=open_admin_login)
admin_btn.place(relx=0.97, y=15, anchor="ne")

# --- LIVE CARDS ---
cards_frame = tk.Frame(root, bg="#eef2f7")
cards_frame.pack(fill="x", padx=20)
cards = {}
metrics = [("Voltage (V)", "#dcfce7"), ("Current (A)", "#ffe4e6"), ("Power (W)", "#ffedd5")]

for i, (label, color) in enumerate(metrics):
    card = tk.Frame(cards_frame, bg=color, highlightbackground="#ccc", highlightthickness=1, padx=20, pady=20)
    card.grid(row=0, column=i, padx=15, pady=10, sticky="nsew")
    tk.Label(card, text=label, bg=color, font=("Segoe UI", 10, "bold")).pack()
    var = tk.StringVar(value="0.00")
    tk.Label(card, textvariable=var, bg=color, font=("Segoe UI", 20, "bold")).pack()
    cards[label] = var

# ---------------- BACKGROUND DATA READER ----------------
def serial_reader():
    while ser and ser.is_open:
        try:
            line = ser.readline().decode(errors="ignore").strip()
            if line.startswith("DATE="):
                # Split the string: DATE=2026-02-16,TIME=12:00:00,V=18.5,I=1.2,P=22.2
                parts = dict(x.split("=") for x in line.split(","))
                cards["Voltage (V)"].set(parts.get("V", "0.00"))
                cards["Current (A)"].set(parts.get("I", "0.00"))
                cards["Power (W)"].set(parts.get("P", "0.00"))
        except:
            break

root.mainloop()
