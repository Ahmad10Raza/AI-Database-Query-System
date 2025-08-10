import platform
import tkinter as tk
from tkinter import messagebox
from PIL import ImageTk, Image

class LoginWindow(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.master.title("Login - NL-to-SQL Workbench")

        # Cross-platform maximize
        if platform.system() == "Windows":
            self.master.state('zoomed')
        else:
            self.master.attributes('-zoomed', True)

        self.pack(fill=tk.BOTH, expand=True)

        # Load background image and bind resize
        self.original_bg = Image.open('images/background1.png')
        self.bg_panel = tk.Label(self.master)
        self.bg_panel.place(relwidth=1, relheight=1)
        self.master.bind("<Configure>", self.resize_bg)

        # Login frame
        self.lgn_frame = tk.Frame(self.master, bg='#040405', width=950, height=600)
        self.lgn_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(self.lgn_frame, text="🗄️ Secure Database Login",
                 font=('yu gothic ui', 25, "bold"),
                 bg="#040405", fg='white').place(x=80, y=30)

        # Fields
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
        start_y = 200
        for i, (label, var, default) in enumerate(fields):
            tk.Label(self.lgn_frame, text=label, bg="#040405", fg="#F3F3F3",
                     font=("yu gothic ui", 13, "bold")).place(x=550, y=start_y + i * 45)
            entry = tk.Entry(self.lgn_frame, bg="#040405", fg="white",
                             font=("yu gothic ui", 12), relief=tk.FLAT, insertbackground='white')
            if label == "🔑 Password":
                entry.config(show="*")
            entry.insert(0, default)
            entry.place(x=720, y=start_y + i * 45, width=200)
            tk.Canvas(self.lgn_frame, width=200, height=2, bg="#bdb9b1", highlightthickness=0)\
                .place(x=720, y=start_y + 22 + i * 45)
            self.entries[var] = entry

        # Connect button with image
        btn_img = ImageTk.PhotoImage(Image.open('images/btn1.png'))
        btn_label = tk.Label(self.lgn_frame, image=btn_img, bg='#040405')
        btn_label.image = btn_img
        btn_label.place(x=550, y=start_y + len(fields) * 45 + 40)
        tk.Button(btn_label, text='🚀 Connect', font=("yu gothic ui", 13, "bold"),
                  width=25, bd=0, bg='#3047ff', fg='white',
                  cursor='hand2', activebackground='#3047ff',
                  command=self.connect_db).place(x=20, y=10)

    def resize_bg(self, event):
        # Resize background image to window size
        resized = self.original_bg.resize((event.width, event.height), Image.LANCZOS)
        self.bg_img = ImageTk.PhotoImage(resized)
        self.bg_panel.config(image=self.bg_img)

    def connect_db(self):
        # your DB connection logic here
        pass
