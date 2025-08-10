# import tkinter as tk
# from tkinter import ttk, messagebox
# from db_connector import DBConnector
# from ui.home_window import HomeWindow


# class LoginWindow(tk.Frame):
#     def __init__(self, master):
#         super().__init__(master)
#         self.master = master
#         self.master.title("Login - NL-to-SQL Workbench")
#         self.master.geometry("440x500")
#         self.master.configure(bg="#232B37")
#         self.pack(fill=tk.BOTH, expand=True)
#         self.style = ttk.Style()
#         self.style.theme_use("clam")
#         self.customize_style()
#         self.create_widgets()


#     def customize_style(self):
#         accent = "#297FFB"
#         card_bg = "#283B4C"
#         self.style.configure(
#             "Card.TFrame",
#             background=card_bg,
#             borderwidth=1,
#             relief="ridge"
#         )
#         self.style.configure("Title.TLabel", background="#232B37", foreground="white", font=("Segoe UI", 18, "bold"))
#         self.style.configure("Field.TLabel", background=card_bg, foreground="#F3F3F3", font=("Segoe UI", 12, "normal"))
#         self.style.configure("TEntry", fieldbackground="#36495A", foreground="white", borderwidth=2, relief="solid", padding=8, font=("Segoe UI", 12))
#         self.style.configure("Accent.TButton", font=("Segoe UI", 12, "bold"), background=accent, foreground="white", borderwidth=0)
#         self.style.map("Accent.TButton", background=[("active", "#1858A1"), ("pressed", "#1858A1")], foreground=[("active", "white")])


#     def create_widgets(self):
#         # Floating card effect frame
#         card = ttk.Frame(self, style="Card.TFrame")
#         card.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=390, height=400)


#         # Title
#         ttk.Label(self, text="🗄️ Secure Database Login", style="Title.TLabel").place(relx=0.5, y=50, anchor="center")


#         fields = [
#             ("🔌 Database Type", "db_type", "mysql"),
#             ("🌐 Host", "host", "localhost"),
#             ("🛜 Port", "port", "3306"),
#             ("📁 Database Name", "db_name", "livonia_extraction"),
#             ("👤 Username", "username", "Ahmad10Raza"),
#             ("🔑 Password", "password", "@786&md#AS"),
#             ("🤖 Ollama API URL", "ollama_url", "http://localhost:11434"),
#         ]
#         self.entries = {}
#         for i, (label, var, default) in enumerate(fields):
#             ttk.Label(card, text=label, style="Field.TLabel").place(x=30, y=25 + i * 44)
#             entry = ttk.Entry(card, style="TEntry")
#             if label == "🔑 Password":
#                 entry.config(show="*")
#             if default:
#                 entry.insert(0, default)
#             entry.place(x=180, y=25 + i * 44, width=170)
#             self.entries[var] = entry


#         # Connect Button
#         connect_btn = ttk.Button(card, text="🚀 Connect", style="Accent.TButton", command=self.connect_db)
#         connect_btn.place(relx=0.5, y=345, anchor="center", width=250, height=38)


#     def connect_db(self):
#         db_type     = self.entries["db_type"].get().strip()
#         host        = self.entries["host"].get().strip()
#         port        = self.entries["port"].get().strip()
#         db_name     = self.entries["db_name"].get().strip()
#         username    = self.entries["username"].get().strip()
#         password    = self.entries["password"].get().strip()
#         ollama_url  = self.entries["ollama_url"].get().strip()


#         if not all([db_type, host, port, db_name, username, password, ollama_url]):
#             messagebox.showerror("Error", "All fields are required")
#             return


#         try:
#             db_connector = DBConnector(db_type, host, port, db_name, username, password)
#             db_connector.connect()
#             self.destroy()
#             HomeWindow(self.master, db_connector, ollama_url)
#         except Exception as e:
#             messagebox.showerror("Connection Error", str(e))



import platform
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageTk, Image
from db_connector import DBConnector
from ui.home_window import HomeWindow


class LoginWindow(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.master.title("Login - NL-to-SQL Workbench")
        self.master.geometry("1166x718")
        #self.master.state('zoomed')
        if platform.system() == "Windows":
            self.master.state('zoomed')
        else:
                self.master.attributes('-zoomed', True)  # Works on Linux
        self.pack(fill=tk.BOTH, expand=True)

        # self.bg_frame = Image.open('./assets/background1.png')
        # bg_photo = ImageTk.PhotoImage(self.bg_frame)
        # self.bg_panel = tk.Label(self.master, image=bg_photo)
        # self.bg_panel.image = bg_photo
        # self.bg_panel.place(relwidth=1, relheight=1)

        # Load background image and bind resize
        self.original_bg = Image.open('./assets/background1.png')
        self.bg_panel = tk.Label(self.master)
        self.bg_panel.place(relwidth=1, relheight=1)
        self.master.bind("<Configure>", self.resize_bg)

        
        # Login Frame
        self.lgn_frame = tk.Frame(self.master, bg='#040405', width=950, height=650)
        self.lgn_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Heading
        tk.Label(self.lgn_frame, text="🗄️ Secure Database Login",
                 font=('yu gothic ui', 25, "bold"),
                 bg="#040405", fg='white').place(x=80, y=30)

        # Side Image
        side_img = ImageTk.PhotoImage(Image.open('./assets/vector.png'))
        side_img_label = tk.Label(self.lgn_frame, image=side_img, bg='#040405')
        side_img_label.image = side_img
        side_img_label.place(x=5, y=100)

        # Sign In Image
        sign_in_img = ImageTk.PhotoImage(Image.open('./assets/hyy.png'))
        sign_in_label = tk.Label(self.lgn_frame, image=sign_in_img, bg='#040405')
        sign_in_label.image = sign_in_img
        sign_in_label.place(x=620, y=130)

        # Database Fields
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
            tk.Label(self.lgn_frame, text=label, bg="#040405", fg="#F3F3F3",
                     font=("yu gothic ui", 13, "bold")).place(x=550, y=300 + i * 45)
            entry = tk.Entry(self.lgn_frame, bg="#040405", fg="white",
                             font=("yu gothic ui", 12), relief=tk.FLAT, insertbackground='white')
            if label == "🔑 Password":
                entry.config(show="*")
            entry.insert(0, default)
            entry.place(x=720, y=300 + i * 45, width=200)
            tk.Canvas(self.lgn_frame, width=200, height=2, bg="#bdb9b1", highlightthickness=0)\
                .place(x=720, y=322 + i * 45)
            self.entries[var] = entry

       # Connect Button
        # btn_img = ImageTk.PhotoImage(Image.open('./assets/btn1.png'))
        # btn_label = tk.Label(self.lgn_frame, image=btn_img, bg='#040405')
        # btn_label.image = btn_img
        # btn_label.place(x=550, y=600)
        # tk.Button(btn_label, text='🚀 Connect', font=("yu gothic ui", 13, "bold"),
        #           width=25, bd=0, bg='#3047ff', fg='white',
        #           cursor='hand2', activebackground='#3047ff',
        #           command=self.connect_db).place(x=20, y=10)
        
        tk.Button(
                self.lgn_frame,
                text='🚀 Connect',
                font=("yu gothic ui", 13, "bold"),
                width=25,
                bd=0,
                bg='#040405',      # same as login frame background
                fg='white',
                cursor='hand2',
                activebackground='#3047ff',
                command=self.connect_db
            ).place(x=550, y=600)

        
        
        
        

    def resize_bg(self, event):
        # Resize background image to window size
        resized = self.original_bg.resize((event.width, event.height), Image.LANCZOS)
        self.bg_img = ImageTk.PhotoImage(resized)
        self.bg_panel.config(image=self.bg_img)


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
