# main.py
import sys
import os
sys.path.append(os.path.dirname(__file__))
import tkinter as tk
from ui.login_window import LoginWindow


def main():
    root = tk.Tk()
    root.title("AI Database Query System 🖥️")
    root.geometry("600x400")
    root.resizable(True, True)

    app = LoginWindow(root)
    app.pack(fill="both", expand=True)

    root.mainloop()

if __name__ == "__main__":
    main()
