

# home_window.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import simpledialog
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
        self.master.title("NL-to-SQL Desktop")
        self.master.geometry("1100x650")

        self.create_widgets()
        self.load_schema()
        
        
        # New
       # Results table frame
        #results_frame = tk.Frame(self.root)
        results_frame = tk.Frame(self)

        results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create Treeview for results
        self.results_table = ttk.Treeview(results_frame)
        self.results_table.pack(fill="both", expand=True)

        # Optional: Scrollbars
        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_table.yview)
        hsb = ttk.Scrollbar(results_frame, orient="horizontal", command=self.results_table.xview)
        self.results_table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")


    def create_widgets(self):
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # Schema Sidebar
        schema_frame = tk.LabelFrame(main_pane, text="Database Schema")
        self.schema_tree = ttk.Treeview(schema_frame)
        self.schema_tree.pack(fill=tk.BOTH, expand=True)
        main_pane.add(schema_frame, width=250)

        # Right side frame
        right_frame = tk.Frame(main_pane)
        main_pane.add(right_frame, stretch="always")

        # NL Query
        nl_frame = tk.LabelFrame(right_frame, text="Ask in Natural Language")
        nl_frame.pack(fill=tk.X, pady=5, padx=5)
        self.nl_entry = tk.Entry(nl_frame, width=80)
        self.nl_entry.pack(side=tk.LEFT, padx=5, pady=5)
        gen_sql_btn = tk.Button(nl_frame, text="Generate SQL", command=self.generate_sql_from_nl)
        gen_sql_btn.pack(side=tk.LEFT, padx=5)

        # SQL Query
        sql_frame = tk.LabelFrame(right_frame, text="SQL Query")
        sql_frame.pack(fill=tk.X, pady=5, padx=5)
        self.query_entry = tk.Entry(sql_frame, width=80)
        self.query_entry.pack(side=tk.LEFT, padx=5, pady=5)
        run_btn = tk.Button(sql_frame, text="Run Query", command=self.run_query)
        run_btn.pack(side=tk.LEFT, padx=5)
        
       

        # Results
        # self.tree = ttk.Treeview(right_frame)
        # self.tree.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        self.result_frame = tk.Frame(self)
        self.result_frame.pack(fill=tk.BOTH, expand=True)

        # Export buttons
        export_frame = tk.Frame(right_frame)
        export_frame.pack(fill=tk.X, pady=5, padx=5)
        tk.Button(export_frame, text="Export CSV", command=lambda: self.export_data("csv")).pack(side=tk.LEFT, padx=5)
        tk.Button(export_frame, text="Export Excel", command=lambda: self.export_data("excel")).pack(side=tk.LEFT, padx=5)

        self.pack(fill=tk.BOTH, expand=True)

    def load_schema(self):
        schema = self.db_connector.get_schema()
        for table, columns in schema.items():
            table_id = self.schema_tree.insert("", tk.END, text=table)
            for col in columns:
                self.schema_tree.insert(table_id, tk.END, text=col)

    def generate_sql_from_nl(self):
        # Step 1: Check connection before doing anything
        if not self.check_ollama_connection():
            messagebox.showerror("Error", "Ollama server is not reachable.")
            return

        nl_query = self.nl_entry.get().strip()
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
            self.query_entry.delete(0, tk.END)
            self.query_entry.insert(0, sql_generated)

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
        nl_query = self.nl_entry.get().strip()
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
            self.query_entry.delete(0, tk.END)
            self.query_entry.insert(0, sql_generated)


        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate SQL: {e}")
            messagebox.showerror("Error", f"Failed to generate SQL: {e}")

    def format_schema_for_prompt(self):
        schema = self.db_connector.get_schema()
        return "\n".join([f"{table}: {', '.join(cols)}" for table, cols in schema.items()])

   
    
    def run_query(self):
        sql = self.query_entry.get().strip()
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
        # Remove old results frame if it exists
        if hasattr(self, "result_frame"):
            self.result_frame.destroy()

        # Create a new frame for results
        self.result_frame = tk.Frame(self)
        self.result_frame.pack(fill=tk.BOTH, expand=True)

        # Create Treeview
        self.tree = ttk.Treeview(self.result_frame, columns=list(df.columns), show="headings")

        # Set up headings and columns
        for col in df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")

        # Insert data
        for row in df.itertuples(index=False):
            self.tree.insert("", tk.END, values=row)

        # Add scrollbars
        y_scroll = ttk.Scrollbar(self.result_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(self.result_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Enable inline editing if table_name & primary_key_col provided
        if table_name and primary_key_col:
            def on_double_click(event):
                selected_item = self.tree.selection()
                if not selected_item:
                    return
                selected_item = selected_item[0]

                col_index = int(self.tree.identify_column(event.x)[1:]) - 1
                col_name = df.columns[col_index]
                old_value = self.tree.item(selected_item)["values"][col_index]

                new_value = simpledialog.askstring("Edit Value", f"Enter new value for {col_name}:", initialvalue=old_value)
                if new_value is not None and new_value != old_value:
                    self.tree.set(selected_item, column=col_name, value=new_value)

                    # Find PK value safely
                    try:
                        cols_lower = [c.lower() for c in df.columns]
                        pk_index = cols_lower.index(primary_key_col.lower())
                        pk_value = self.tree.item(selected_item, "values")[pk_index]
                    except ValueError:
                        messagebox.showerror("Error", f"Primary key column '{primary_key_col}' not found in results.")
                        return

                    update_sql = f"UPDATE {table_name} SET {col_name} = ? WHERE {primary_key_col} = ?"
                    try:
                        self.db_connector.execute_query(update_sql, (new_value, pk_value))
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to update DB: {e}")

            self.tree.bind("<Double-1>", on_double_click)

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
