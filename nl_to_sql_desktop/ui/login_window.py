import tkinter as tk
from tkinter import ttk, messagebox
from db_connector import DBConnector
from ui.home_window import HomeWindow

class LoginWindow(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.master.title("Login - NL-to-SQL Workbench")
        self.master.geometry("440x500")
        self.master.configure(bg="#232B37")
        self.pack(fill=tk.BOTH, expand=True)
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.customize_style()
        self.create_widgets()

    def customize_style(self):
        accent = "#297FFB"
        card_bg = "#283B4C"
        self.style.configure(
            "Card.TFrame",
            background=card_bg,
            borderwidth=1,
            relief="ridge"
        )
        self.style.configure("Title.TLabel", background="#232B37", foreground="white", font=("Segoe UI", 18, "bold"))
        self.style.configure("Field.TLabel", background=card_bg, foreground="#F3F3F3", font=("Segoe UI", 12, "normal"))
        self.style.configure("TEntry", fieldbackground="#36495A", foreground="white", borderwidth=2, relief="solid", padding=8, font=("Segoe UI", 12))
        self.style.configure("Accent.TButton", font=("Segoe UI", 12, "bold"), background=accent, foreground="white", borderwidth=0)
        self.style.map("Accent.TButton", background=[("active", "#1858A1"), ("pressed", "#1858A1")], foreground=[("active", "white")])

    def create_widgets(self):
        # Floating card effect frame
        card = ttk.Frame(self, style="Card.TFrame")
        card.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=390, height=400)

        # Title
        ttk.Label(self, text="🗄️ Secure Database Login", style="Title.TLabel").place(relx=0.5, y=50, anchor="center")

        fields = [
            ("🔌 Database Type", "db_type", "mysql"),
            ("🌐 Host", "host", "localhost"),
            ("🛜 Port", "port", "3306"),
            ("📁 Database Name", "db_name", "livonia_extraction"),
            ("👤 Username", "username", "Ahmad10Raza"),
            ("🔑 Password", "password", "@786&md#AS"),
            ("🤖 Ollama API URL", "ollama_url", "http://localhost:11434"),
        ]
        self.entries = {}
        for i, (label, var, default) in enumerate(fields):
            ttk.Label(card, text=label, style="Field.TLabel").place(x=30, y=25 + i * 44)
            entry = ttk.Entry(card, style="TEntry")
            if label == "🔑 Password":
                entry.config(show="*")
            if default:
                entry.insert(0, default)
            entry.place(x=180, y=25 + i * 44, width=170)
            self.entries[var] = entry

        # Connect Button
        connect_btn = ttk.Button(card, text="🚀 Connect", style="Accent.TButton", command=self.connect_db)
        connect_btn.place(relx=0.5, y=345, anchor="center", width=250, height=38)

    def connect_db(self):
        db_type     = self.entries["db_type"].get().strip()
        host        = self.entries["host"].get().strip()
        port        = self.entries["port"].get().strip()
        db_name     = self.entries["db_name"].get().strip()
        username    = self.entries["username"].get().strip()
        password    = self.entries["password"].get().strip()
        ollama_url  = self.entries["ollama_url"].get().strip()

        if not all([db_type, host, port, db_name, username, password, ollama_url]):
            messagebox.showerror("Error", "All fields are required")
            return

        try:
            db_connector = DBConnector(db_type, host, port, db_name, username, password)
            db_connector.connect()
            self.destroy()
            HomeWindow(self.master, db_connector, ollama_url)
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
