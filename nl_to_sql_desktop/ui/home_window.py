# home_window.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from tkinter import scrolledtext
import pandas as pd
import sqlparse
import requests
import re
import json
from db_connector import DBConnector
import logging

# Setup logging
logging.basicConfig(
    filename="nl_to_sql.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class HomeWindow(tk.Frame):
    def __init__(self, master, db_connector, ollama_url):
        super().__init__(master)
        self.master = master
        self.db_connector = db_connector
        self.ollama_url = ollama_url
        self.master.title("NL-to-SQL Workbench")
        self.master.geometry("1200x700")
        self.master.configure(bg="#1E1E1E")

        # Modern theme for ttk
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="#1E1E1E")
        self.style.configure("TLabel", background="#1E1E1E", foreground="white", font=("Segoe UI", 10))
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=5)
        self.style.map("TButton", background=[("active", "#0078D4")], foreground=[("active", "white")])
        self.style.configure("Treeview", background="#2D2D2D", foreground="white",
                             fieldbackground="#2D2D2D", rowheight=25, font=("Consolas", 10))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#0078D4", foreground="white")

        self.create_widgets()
        self.load_schema()

    
           
    def create_widgets(self):
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=4, bg="#1E1E1E")
        main_pane.pack(fill=tk.BOTH, expand=True)

        # ───── LEFT: Schema Sidebar ─────
        schema_frame = ttk.LabelFrame(main_pane, text="📂 Database Schema", padding=3)
        self.schema_tree = ttk.Treeview(schema_frame, selectmode="browse")
        self.schema_tree.pack(fill=tk.BOTH, expand=True)
        main_pane.add(schema_frame, width=260)

        # ───── RIGHT: Main workspace ─────
        right_frame = ttk.Frame(main_pane, padding=2)
        main_pane.add(right_frame, stretch="always")

        # NL Query Frame (smaller gap)
        nl_frame = ttk.LabelFrame(right_frame, text="💬 Ask in Natural Language", padding=4)
        nl_frame.pack(fill=tk.X, pady=(1, 1), padx=4)
        # self.nl_entry = tk.Entry(nl_frame, font=("Segoe UI", 11))
        self.nl_entry = scrolledtext.ScrolledText(
                            nl_frame,
                            font=("Segoe UI", 11),
                            height=4,       # about 4–5 visible lines
                            wrap="word",    # wrap at word boundaries
                            undo=True
                        )
        self.nl_entry.pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        gen_sql_btn = ttk.Button(nl_frame, text="Generate SQL", command=self.generate_sql_from_nl)
        gen_sql_btn.pack(side=tk.LEFT, padx=4,pady=2)

        # SQL Query Frame – now taller & resizable
        sql_frame = ttk.LabelFrame(right_frame, text="🛠 SQL Query", padding=4)
        sql_frame.pack(fill=tk.BOTH, pady=(1, 1), padx=4, expand=True)
        self.query_entry = scrolledtext.ScrolledText(
            sql_frame,
            font=("Consolas", 11),
            height=12,      # Adjust to taste
            wrap="none",
            undo=True
        )
        self.query_entry.pack(side=tk.LEFT, padx=3, pady=3, fill=tk.BOTH, expand=True)
        run_btn = ttk.Button(sql_frame, text="Run Query", command=self.run_query)
        run_btn.pack(side=tk.LEFT, padx=4, pady=3)

        # Export buttons (tightened)
        export_frame = ttk.Frame(right_frame)
        export_frame.pack(fill=tk.X, pady=(0, 2), padx=4)
        ttk.Button(export_frame, text="💾 Export CSV", command=lambda: self.export_data("csv")).pack(side=tk.LEFT, padx=3)
        ttk.Button(export_frame, text="📊 Export Excel", command=lambda: self.export_data("excel")).pack(side=tk.LEFT, padx=3)

        # Results Section (fills remaining space)
        results_frame = ttk.LabelFrame(right_frame, text="📋 Query Results", padding=4)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(1, 1), padx=4)

        self.results_table = ttk.Treeview(results_frame)
        self.results_table.pack(fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_table.yview)
        hsb = ttk.Scrollbar(results_frame, orient="horizontal", command=self.results_table.xview)
        self.results_table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        self.pack(fill=tk.BOTH, expand=True)

            
            
    def load_schema(self):
        schema = self.db_connector.get_schema()
        for table, columns in schema.items():
            table_id = self.schema_tree.insert("", tk.END, text=table, open=True)
            for col in columns:
                self.schema_tree.insert(table_id, tk.END, text=col)

    # The rest of your methods (generate_sql_from_nl, run_query, etc.) remain unchanged.
    # ...

    def generate_sql_from_nl(self):
        # Step 1: Check connection before doing anything
        if not self.check_ollama_connection():
            messagebox.showerror("Error", "Ollama server is not reachable.")
            return

        # nl_query = self.nl_entry.get().strip()
        nl_query = self.nl_entry.get("1.0", "end-1c").strip()

        logger.info(f"User NL query: {nl_query}")
        if not nl_query:
            messagebox.showwarning("Warning", "Please enter a natural language query.")
            logger.warning("No NL query entered.")
            return

        schema_text = self.format_schema_for_prompt()
        prompt = f"""
    You are a SQL generator.
    Given the following database schema:
    {schema_text}

    And this request in natural language:
    {nl_query}

    Return ONLY a valid JSON object in this exact format:
    {{"sql": "SELECT ..."}}
    Do not include any explanations or extra text.
        """.strip()
        logger.debug(f"Prompt sent to Ollama: {prompt}")

        try:
            # Step 2: Stream response for safety
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": "llama3", "prompt": prompt, "stream": True},
                timeout=30,
                stream=True
            )
            logger.info(f"Ollama HTTP status: {response.status_code}")
            response.raise_for_status()

            # Step 3: Accumulate chunks
            raw_text_accumulated = ""
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    try:
                        obj = json.loads(line)
                        if "response" in obj:
                            raw_text_accumulated += obj["response"]
                    except json.JSONDecodeError:
                        logger.warning(f"Non-JSON line in Ollama stream: {line}")

            logger.debug(f"Accumulated Ollama text: {raw_text_accumulated}")

            # Step 4: Extract JSON from raw text
            match = re.search(r"\{.*\}", raw_text_accumulated, re.S)
            if not match:
                raise ValueError("No JSON object found in LLM response")

            json_str = match.group(0)
            data = json.loads(json_str)

            if "sql" not in data:
                raise ValueError("No 'sql' key in LLM JSON output")

            # Step 5: Clean & validate SQL
            sql_generated = data["sql"].strip()
            sql_generated = sql_generated.rstrip(';') + ';'  # Ensure single semicolon
            if not sql_generated.lower().startswith("select"):
                raise ValueError(f"Unexpected SQL output: {sql_generated}")

            logger.info(f"Generated SQL: {sql_generated}")

            # Step 6: Update GUI
            self.query_entry.delete("1.0", tk.END)
            self.query_entry.insert("1.0", sql_generated)

        except Exception as e:
            logger.exception("Error during SQL generation")
            messagebox.showerror("Error", f"Failed to generate SQL: {e}")


    def check_ollama_connection(self):
        """Check if Ollama server is reachable."""
        try:
            r = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if r.status_code == 200:
                logger.info("✅ Ollama server is reachable.")
                return True
            else:
                logger.error(f"❌ Ollama connection failed: HTTP {r.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Ollama connection error: {e}")
            return False

    def generate_sql_from_nl(self):
        # nl_query = self.nl_entry.get().strip()
        nl_query = self.nl_entry.get("1.0", "end-1c").strip()

        logger.info(f"User NL query: {nl_query}")
        if not nl_query:
            messagebox.showwarning("Warning", "Please enter a natural language query.")
            logger.warning("No NL query entered.")
            return

        schema_text = self.format_schema_for_prompt()
        prompt = f"""
You are a SQL generator.
Given the following database schema:
{schema_text}

And this request in natural language:
{nl_query}

Return ONLY a valid JSON object in this exact format:
{{"sql": "SELECT ..."}}
Do not include any explanations or extra text.
        """.strip()
        logger.debug(f"Prompt sent to Ollama: {prompt}")
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": "llama3", "prompt": prompt},
                timeout=20
            )
            
            logger.info(f"Ollama HTTP status: {response.status_code}")
            logger.debug(f"Ollama raw response text: {response.text}")

            response.raise_for_status()

            # Handle streaming JSON lines from Ollama
            raw_text_accumulated = ""
            for line in response.text.splitlines():
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line)
                    if "response" in chunk:
                        raw_text_accumulated += chunk["response"]
                except json.JSONDecodeError:
                    logger.warning(f"Skipping invalid JSON line: {line}")

            # Now find the JSON object inside the accumulated string
            match = re.search(r"\{.*\}", raw_text_accumulated, re.S)
            if not match:
                raise ValueError("No JSON object found in LLM response")

            json_str = match.group(0)
            data = json.loads(json_str)

            if "sql" not in data:
                raise ValueError("No 'sql' key in LLM JSON output")

            sql_generated = data["sql"].strip()
            logger.info(f"Generated SQL: {sql_generated}")
            self.query_entry.delete("1.0", tk.END)
            self.query_entry.insert("1.0", sql_generated)


        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate SQL: {e}")
            messagebox.showerror("Error", f"Failed to generate SQL: {e}")

    def format_schema_for_prompt(self):
        schema = self.db_connector.get_schema()
        return "\n".join([f"{table}: {', '.join(cols)}" for table, cols in schema.items()])

   
    
    
    def run_query(self):
        sql = self.query_entry.get("1.0", "end-1c").strip()  # Correct ScrolledText get()
        if not sql:
            messagebox.showwarning("Warning", "Please enter or generate a SQL query.")
            return
        if not self.is_read_only(sql):
            messagebox.showerror("Error", "Only SELECT queries are allowed.")
            return

        try:
            df = self.db_connector.execute_query(sql)
            if df.empty:
                messagebox.showinfo("Result", "Query executed successfully, but no data returned.")
                return

            # Try to extract table name from SQL for editing
            table_name = None
            primary_key_col = None
            tokens = sql.lower().split()
            if "from" in tokens:
                table_name = tokens[tokens.index("from") + 1]
                # You can set your own PK here
                primary_key_col = "id"  # change if needed

            self.display_results(df, table_name, primary_key_col)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to run query: {e}")


    def is_read_only(self, sql):
        parsed = sqlparse.parse(sql)
        if not parsed:
            return False
        first_token = parsed[0].tokens[0].value.upper()
        return first_token == "SELECT"

  
   

    def display_results(self, df, table_name=None, primary_key_col=None):
        # Remove old results if present
        for widget in self.results_table.winfo_children():
            widget.destroy()
        self.results_table.pack_forget()

        # Clear existing columns
        self.results_table["columns"] = list(df.columns)
        self.results_table["show"] = "headings"
        for col in df.columns:
            self.results_table.heading(col, text=col)
            self.results_table.column(col, minwidth=100, width=140, anchor="center")

        # Remove previous data
        for item in self.results_table.get_children():
            self.results_table.delete(item)

        # Insert rows
        for row in df.itertuples(index=False):
            self.results_table.insert("", tk.END, values=row)

        self.results_table.pack(fill=tk.BOTH, expand=True)

        # -- Place export buttons neatly below the table --
        if not hasattr(self, "results_export_frame"):
            self.results_export_frame = ttk.Frame(self.results_table.master)
            self.results_export_frame.pack(fill=tk.X, pady=8)

            csv_btn = ttk.Button(self.results_export_frame, text="💾 Export CSV",
                                command=lambda: self.export_data("csv"))
            csv_btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=8, ipady=3)

            excel_btn = ttk.Button(self.results_export_frame, text="📊 Export Excel",
                                command=lambda: self.export_data("excel"))
            excel_btn.pack(side=tk.LEFT, ipadx=8, ipady=3)
        else:
            # Already created; just repack if needed
            self.results_export_frame.pack_forget()
            self.results_export_frame.pack(fill=tk.X, pady=8)

        # --- Inline editing ---
        if table_name and primary_key_col:
            def on_double_click(event):
                selected_item = self.results_table.selection()
                if not selected_item:
                    return
                selected_item = selected_item[0]

                col_index = int(self.results_table.identify_column(event.x)[1:]) - 1
                col_name = df.columns[col_index]
                old_value = self.results_table.item(selected_item)["values"][col_index]

                new_value = simpledialog.askstring("Edit Value", f"Enter new value for {col_name}:", initialvalue=old_value)
                if new_value is not None and new_value != old_value:
                    self.results_table.set(selected_item, column=col_name, value=new_value)

                    # Find PK value safely
                    try:
                        cols_lower = [c.lower() for c in df.columns]
                        pk_index = cols_lower.index(primary_key_col.lower())
                        pk_value = self.results_table.item(selected_item, "values")[pk_index]
                    except ValueError:
                        messagebox.showerror("Error", f"Primary key column '{primary_key_col}' not found in results.")
                        return

                    # Update DB
                    update_sql = f"UPDATE {table_name} SET {col_name} = ? WHERE {primary_key_col} = ?"
                    try:
                        self.db_connector.execute_query(update_sql, (new_value, pk_value))
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to update DB: {e}")

            self.results_table.bind("<Double-1>", on_double_click)

    def execute_query(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            try:
                rows = self.cursor.fetchall()
                cols = [desc[0] for desc in self.cursor.description]
                return pd.DataFrame(rows, columns=cols)
            except:
                self.connection.commit()
                return pd.DataFrame()

        except Exception as e:
            raise Exception(f"Database error: {e}")

    
    
    def export_data(self, format_type):
        sql = self.query_entry.get().strip()
        if not sql:
            messagebox.showwarning("Warning", "Run a query before exporting.")
            return
        try:
            df = self.db_connector.execute_query(sql)
            if df.empty:
                messagebox.showinfo("Export", "No data to export.")
                return
            filetypes = [("CSV Files", "*.csv")] if format_type == "csv" else [("Excel Files", "*.xlsx")]
            extension = ".csv" if format_type == "csv" else ".xlsx"
            file_path = filedialog.asksaveasfilename(defaultextension=extension, filetypes=filetypes)
            if not file_path:
                return
            if format_type == "csv":
                df.to_csv(file_path, index=False)
            else:
                df.to_excel(file_path, index=False)
            messagebox.showinfo("Export", f"Data exported successfully to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")
