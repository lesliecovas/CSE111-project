import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import sqlite3
from typing import List, Tuple

DB_FILE = "agriculture.db"

def open_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def run_query(query, params=()):
    try:
        conn = open_conn()
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        rows = cur.fetchall()
        col_names = [description[0] for description in cur.description] if cur.description else []
        conn.close()
        return rows, col_names
    except Exception as e:
        messagebox.showerror("SQL Error", str(e))
        return [], []

def list_tables() -> List[str]:
    conn = open_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows

def table_columns(table: str) -> List[Tuple]:
    conn = open_conn()
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_sample_values(table: str, column: str, limit=50):
    conn = open_conn()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL LIMIT ?", (limit,))
        vals = [str(r[0]) for r in cur.fetchall()]
    except Exception:
        vals = []
    conn.close()
    return vals

PREDEFINED_QUERIES = {
    "Show all crops": "SELECT crop_id, crop_name, crop_group FROM crops;",
    "List districts": "SELECT district_id, state_name, district_name FROM districts ORDER BY state_name;",
    "Production overview": """SELECT p.stat_id, d.state_name, d.district_name, c.crop_name, p.season, p.area, p.production, p.yield
        FROM crop_production_statistic p
        LEFT JOIN districts d ON p.district_id = d.district_id
        LEFT JOIN crops c ON p.crop_id = c.crop_id
        LIMIT 100;""",
    "Total production per state": """SELECT d.state_name, SUM(p.production) AS total_production
        FROM crop_production_statistic p
        JOIN districts d ON p.district_id = d.district_id
        GROUP BY d.state_name
        ORDER BY total_production DESC;""",
    "Average yield by crop": """SELECT c.crop_name, ROUND(AVG(p.yield),2) AS avg_yield
        FROM crop_production_statistic p
        JOIN crops c ON p.crop_id = c.crop_id
        GROUP BY c.crop_name
        ORDER BY avg_yield DESC;""",
    "Pesticides for Rice": """SELECT c.crop_name, pu.compound, pu.low_estimate, pu.high_estimate
        FROM crop_pesticide cp
        JOIN crops c ON cp.crop_id = c.crop_id
        JOIN pesticide_use pu ON cp.pesticide_id = pu.pesticide_id
        WHERE c.crop_name LIKE '%Rice%';""",
    "Weather data sample": "SELECT * FROM farm_weather LIMIT 100;",
    "Market prices": """SELECT m.market_name, c.crop_name, cap.modal_price_rs_per_quintal, cap.arrival_tonnes
        FROM crop_arrival_price cap
        JOIN markets m ON cap.market_id = m.market_id
        JOIN crops c ON cap.crop_id = c.crop_id
        LIMIT 100;""",
    "Crop Rainfall Requirements": """SELECT c.crop_name, 
        ROUND(AVG(fw.rainfall_mm), 2) as avg_rainfall_mm,
        ROUND(MIN(fw.rainfall_mm), 2) as min_rainfall_mm,
        ROUND(MAX(fw.rainfall_mm), 2) as max_rainfall_mm,
        COUNT(*) as data_points
        FROM crops c
        LEFT JOIN crop_production_statistic cps ON c.crop_id = cps.crop_id
        LEFT JOIN farm_weather fw ON cps.district_id = fw.district_id
        WHERE fw.rainfall_mm IS NOT NULL
        GROUP BY c.crop_name
        ORDER BY avg_rainfall_mm DESC;""",
    "Crop Pesticide Usage": """SELECT c.crop_name,
        COUNT(DISTINCT cp.pesticide_id) as pesticide_types,
        ROUND(AVG(pu.low_estimate), 2) as avg_low_estimate,
        ROUND(AVG(pu.high_estimate), 2) as avg_high_estimate,
        GROUP_CONCAT(DISTINCT pu.compound) as compounds_used
        FROM crops c
        LEFT JOIN crop_pesticide cp ON c.crop_id = cp.crop_id
        LEFT JOIN pesticide_use pu ON cp.pesticide_id = pu.pesticide_id
        WHERE pu.compound IS NOT NULL
        GROUP BY c.crop_name
        ORDER BY pesticide_types DESC;""",
    "Sustainability Score Analysis": """SELECT 
        c.crop_name,
        ROUND(AVG(p.yield), 2) as avg_yield,
        ROUND(AVG(fw.rainfall_mm), 2) as avg_rainfall,
        COUNT(DISTINCT cp.pesticide_id) as pesticide_count,
        CASE 
            WHEN COUNT(DISTINCT cp.pesticide_id) <= 2 THEN 'High'
            WHEN COUNT(DISTINCT cp.pesticide_id) <= 5 THEN 'Medium'
            ELSE 'Low'
        END as sustainability_score
        FROM crops c
        LEFT JOIN crop_production_statistic p ON c.crop_id = p.crop_id
        LEFT JOIN farm_weather fw ON p.district_id = fw.district_id
        LEFT JOIN crop_pesticide cp ON c.crop_id = cp.crop_id
        GROUP BY c.crop_name
        HAVING avg_yield IS NOT NULL
        ORDER BY pesticide_count ASC, avg_yield DESC;""",
    "Top Performing Crops by State": """SELECT 
        d.state_name,
        c.crop_name,
        ROUND(AVG(p.yield), 2) as avg_yield,
        ROUND(SUM(p.production), 2) as total_production,
        ROUND(SUM(p.area), 2) as total_area
        FROM crop_production_statistic p
        JOIN districts d ON p.district_id = d.district_id
        JOIN crops c ON p.crop_id = c.crop_id
        WHERE p.yield IS NOT NULL
        GROUP BY d.state_name, c.crop_name
        ORDER BY d.state_name, avg_yield DESC;""",
    "Weather Impact on Yield": """SELECT 
        c.crop_name,
        CASE 
            WHEN fw.rainfall_mm < 500 THEN 'Low Rainfall'
            WHEN fw.rainfall_mm BETWEEN 500 AND 1000 THEN 'Medium Rainfall'
            ELSE 'High Rainfall'
        END as rainfall_category,
        ROUND(AVG(p.yield), 2) as avg_yield,
        COUNT(*) as samples
        FROM crop_production_statistic p
        JOIN crops c ON p.crop_id = c.crop_id
        JOIN farm_weather fw ON p.district_id = fw.district_id
        WHERE p.yield IS NOT NULL AND fw.rainfall_mm IS NOT NULL
        GROUP BY c.crop_name, rainfall_category
        ORDER BY c.crop_name, rainfall_category;""",
    "Market Price Trends": """SELECT 
        c.crop_name,
        m.market_name,
        ROUND(AVG(cap.modal_price_rs_per_quintal), 2) as avg_price,
        ROUND(MIN(cap.modal_price_rs_per_quintal), 2) as min_price,
        ROUND(MAX(cap.modal_price_rs_per_quintal), 2) as max_price,
        ROUND(SUM(cap.arrival_tonnes), 2) as total_arrival
        FROM crop_arrival_price cap
        JOIN crops c ON cap.crop_id = c.crop_id
        JOIN markets m ON cap.market_id = m.market_id
        WHERE cap.modal_price_rs_per_quintal IS NOT NULL
        GROUP BY c.crop_name, m.market_name
        ORDER BY avg_price DESC;""",
    "Crop Efficiency Analysis": """SELECT 
        c.crop_name,
        ROUND(AVG(p.production / NULLIF(p.area, 0)), 2) as production_per_area,
        ROUND(AVG(p.yield), 2) as avg_yield,
        COUNT(DISTINCT cp.pesticide_id) as pesticide_usage,
        ROUND(AVG(fw.rainfall_mm), 2) as avg_rainfall_req,
        CASE 
            WHEN AVG(p.yield) > 2000 AND COUNT(DISTINCT cp.pesticide_id) < 3 THEN 'Excellent'
            WHEN AVG(p.yield) > 1000 AND COUNT(DISTINCT cp.pesticide_id) < 5 THEN 'Good'
            WHEN AVG(p.yield) > 500 THEN 'Average'
            ELSE 'Poor'
        END as efficiency_rating
        FROM crops c
        LEFT JOIN crop_production_statistic p ON c.crop_id = p.crop_id
        LEFT JOIN crop_pesticide cp ON c.crop_id = cp.crop_id
        LEFT JOIN farm_weather fw ON p.district_id = fw.district_id
        WHERE p.production IS NOT NULL AND p.area > 0
        GROUP BY c.crop_name
        ORDER BY production_per_area DESC;""",
    "Season-wise Production": """SELECT 
        p.season,
        c.crop_name,
        COUNT(*) as records,
        ROUND(AVG(p.area), 2) as avg_area,
        ROUND(AVG(p.production), 2) as avg_production,
        ROUND(AVG(p.yield), 2) as avg_yield
        FROM crop_production_statistic p
        JOIN crops c ON p.crop_id = c.crop_id
        WHERE p.season IS NOT NULL
        GROUP BY p.season, c.crop_name
        ORDER BY p.season, avg_production DESC;"""
}

class ModernApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Agriculture Database Manager")
        self.root.geometry("1500x900")
        self.root.configure(bg="#1e1e1e")
        
        self.filters = []
        self.selected_tables = []
        self.all_tables = list_tables()
        self.selected_columns_widgets = {}
        self.group_by_cols = []
        self.order_by_cols = []
        
        self.setup_styles()
        self.create_layout()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("Treeview", background="#2d2d2d", foreground="#e0e0e0",
                       fieldbackground="#2d2d2d", borderwidth=0, rowheight=26)
        style.configure("Treeview.Heading", background="#3d3d3d", foreground="#e0e0e0",
                       borderwidth=1, relief="flat")
        style.map("Treeview.Heading", background=[("active", "#4a9eff")])
        
    def create_layout(self):
        main = tk.Frame(self.root, bg="#1e1e1e")
        main.pack(fill="both", expand=True, padx=15, pady=15)
        
        header = tk.Frame(main, bg="#1e1e1e", height=60)
        header.pack(fill="x", pady=(0, 15))
        
        tk.Label(header, text="🌾 Agriculture Database Manager", 
                font=("Segoe UI", 24, "bold"), bg="#1e1e1e", fg="#4a9eff").pack(side="left")
        
        crud_frame = tk.Frame(header, bg="#1e1e1e")
        crud_frame.pack(side="right")
        
        tk.Button(crud_frame, text="INSERT", bg="#10b981", fg="white",
                 font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                 padx=15, pady=8, activebackground="#059669",
                 command=self.insert_record).pack(side="left", padx=5)
        
        tk.Button(crud_frame, text="UPDATE", bg="#f59e0b", fg="white",
                 font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                 padx=15, pady=8, activebackground="#d97706",
                 command=self.update_record).pack(side="left", padx=5)
        
        tk.Button(crud_frame, text="DELETE", bg="#ef4444", fg="white",
                 font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                 padx=15, pady=8, activebackground="#dc2626",
                 command=self.delete_record).pack(side="left", padx=5)
        
        content = tk.Frame(main, bg="#1e1e1e")
        content.pack(fill="both", expand=True)
        
        left_panel = tk.Frame(content, bg="#2d2d2d", width=480)
        left_panel.pack(side="left", fill="y", padx=(0, 15))
        left_panel.pack_propagate(False)
        
        self.create_operations_panel(left_panel)
        
        right_panel = tk.Frame(content, bg="#1e1e1e")
        right_panel.pack(side="left", fill="both", expand=True)
        
        self.create_results_panel(right_panel)
        
    def create_operations_panel(self, parent):
        canvas = tk.Canvas(parent, bg="#2d2d2d", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg="#2d2d2d")
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        container = tk.Frame(scrollable, bg="#2d2d2d")
        container.pack(fill="both", expand=True, padx=15, pady=15)
        
        self.create_section_header(container, "⚡ QUICK QUERIES")
        query_frame = tk.Frame(container, bg="#2d2d2d")
        query_frame.pack(fill="x", pady=(0, 15))
        
        self.query_combo = ttk.Combobox(query_frame, values=list(PREDEFINED_QUERIES.keys()),
                                        state="readonly", font=("Segoe UI", 10))
        self.query_combo.pack(fill="x", pady=(0, 8))
        self.query_combo.set("Choose a query...")
        
        tk.Button(query_frame, text="▶ RUN QUICK QUERY", bg="#5865F2", fg="white",
                 font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2",
                 activebackground="#4752C4", command=self.run_quick_query, pady=10).pack(fill="x")
        
        ttk.Separator(container, orient="horizontal").pack(fill="x", pady=15)
        
        tk.Label(container, text="🔧 CUSTOM QUERY BUILDER", font=("Segoe UI", 13, "bold"),
                bg="#2d2d2d", fg="#4a9eff").pack(anchor="w", pady=(0, 10))
        
        self.create_section_header(container, "TABLES")
        tables_frame = tk.Frame(container, bg="#2d2d2d")
        tables_frame.pack(fill="x", pady=(0, 15))
        
        self.table_vars = {}
        for table in self.all_tables:
            var = tk.BooleanVar()
            self.table_vars[table] = var
            tk.Checkbutton(tables_frame, text=table, variable=var, bg="#2d2d2d", fg="#e0e0e0", 
                          selectcolor="#3d3d3d", activebackground="#2d2d2d", activeforeground="#4a9eff",
                          font=("Segoe UI", 10), cursor="hand2",
                          command=self.update_selected_tables).pack(anchor="w", pady=2)
        
        self.create_section_header(container, "COLUMNS")
        self.columns_frame = tk.Frame(container, bg="#2d2d2d")
        self.columns_frame.pack(fill="x", pady=(0, 15))
        tk.Label(self.columns_frame, text="Select tables first...", bg="#2d2d2d", fg="#7f8c8d",
                font=("Segoe UI", 9, "italic")).pack(anchor="w")
        
        self.create_section_header(container, "SHOW")
        show_frame = tk.Frame(container, bg="#2d2d2d")
        show_frame.pack(fill="x", pady=(0, 15))
        self.show_mode = tk.StringVar(value="all")
        for text, value in [("All Data", "all"), ("Count", "count")]:
            tk.Radiobutton(show_frame, text=text, variable=self.show_mode, value=value,
                          bg="#2d2d2d", fg="#e0e0e0", selectcolor="#3d3d3d",
                          activebackground="#2d2d2d", font=("Segoe UI", 10),
                          cursor="hand2").pack(anchor="w", pady=2)
        
        self.create_section_header(container, "GROUP BY")
        group_frame = tk.Frame(container, bg="#2d2d2d")
        group_frame.pack(fill="x", pady=(0, 15))
        self.group_by_combo = ttk.Combobox(group_frame, state="readonly", font=("Segoe UI", 10))
        self.group_by_combo.pack(fill="x", pady=(0, 5))
        tk.Button(group_frame, text="Add to GROUP BY", bg="#3d3d3d", fg="#4a9eff",
                 font=("Segoe UI", 9), relief="flat", cursor="hand2",
                 command=self.add_group_by).pack(fill="x")
        self.group_by_label = tk.Label(group_frame, text="", bg="#2d2d2d", fg="#a0a0a0",
                                       font=("Segoe UI", 9), wraplength=400, justify="left")
        self.group_by_label.pack(anchor="w", pady=(5, 0))
        
        self.create_section_header(container, "ORDER BY")
        order_frame = tk.Frame(container, bg="#2d2d2d")
        order_frame.pack(fill="x", pady=(0, 15))
        order_sub = tk.Frame(order_frame, bg="#2d2d2d")
        order_sub.pack(fill="x")
        self.order_by_combo = ttk.Combobox(order_sub, state="readonly", font=("Segoe UI", 10), width=20)
        self.order_by_combo.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.order_dir = tk.StringVar(value="ASC")
        tk.Radiobutton(order_sub, text="ASC", variable=self.order_dir, value="ASC",
                      bg="#2d2d2d", fg="#e0e0e0", selectcolor="#3d3d3d",
                      font=("Segoe UI", 9)).pack(side="left", padx=2)
        tk.Radiobutton(order_sub, text="DESC", variable=self.order_dir, value="DESC",
                      bg="#2d2d2d", fg="#e0e0e0", selectcolor="#3d3d3d",
                      font=("Segoe UI", 9)).pack(side="left", padx=2)
        tk.Button(order_frame, text="Add to ORDER BY", bg="#3d3d3d", fg="#4a9eff",
                 font=("Segoe UI", 9), relief="flat", cursor="hand2",
                 command=self.add_order_by).pack(fill="x", pady=(5, 0))
        self.order_by_label = tk.Label(order_frame, text="", bg="#2d2d2d", fg="#a0a0a0",
                                       font=("Segoe UI", 9), wraplength=400, justify="left")
        self.order_by_label.pack(anchor="w", pady=(5, 0))
        
        self.create_section_header(container, "WHERE / HAVING")
        filter_add = tk.Frame(container, bg="#2d2d2d")
        filter_add.pack(fill="x", pady=(0, 10))
        
        row1 = tk.Frame(filter_add, bg="#2d2d2d")
        row1.pack(fill="x", pady=2)
        self.filter_table = ttk.Combobox(row1, width=12, state="readonly", font=("Segoe UI", 9))
        self.filter_table.pack(side="left", padx=(0, 3))
        self.filter_table.bind("<<ComboboxSelected>>", self.on_filter_table_change)
        self.filter_field = ttk.Combobox(row1, width=12, state="readonly", font=("Segoe UI", 9))
        self.filter_field.pack(side="left", padx=3)
        self.filter_field.bind("<<ComboboxSelected>>", self.on_filter_field_change)
        
        row2 = tk.Frame(filter_add, bg="#2d2d2d")
        row2.pack(fill="x", pady=2)
        self.filter_op = ttk.Combobox(row2, width=8, state="readonly",
                                      values=["=", ">", "<", ">=", "<=", "LIKE", "IN"], font=("Segoe UI", 9))
        self.filter_op.set("=")
        self.filter_op.pack(side="left", padx=(0, 3))
        self.filter_value = ttk.Combobox(row2, width=16, font=("Segoe UI", 9))
        self.filter_value.pack(side="left", padx=3)
        
        tk.Button(filter_add, text="+ Add Filter", bg="#10b981", fg="white",
                 font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                 activebackground="#059669", command=self.add_filter).pack(fill="x", pady=(3, 0))
        
        self.active_filters_label = tk.Label(container, text="", bg="#2d2d2d", fg="#95a5a6",
                                            font=("Segoe UI", 8), wraplength=420, justify="left")
        self.active_filters_label.pack(anchor="w", pady=(3, 0))
        
        self.create_section_header(container, "LIMIT")
        limit_frame = tk.Frame(container, bg="#2d2d2d")
        limit_frame.pack(fill="x", pady=(0, 20))
        self.limit_var = tk.StringVar(value="100")
        tk.Entry(limit_frame, textvariable=self.limit_var, font=("Segoe UI", 10), width=10).pack(anchor="w")
        
        tk.Button(container, text="🗑️ Clear All Filters & Settings", bg="#6b7280", fg="white",
                 font=("Segoe UI", 10), relief="flat", cursor="hand2",
                 activebackground="#4b5563", command=self.clear_filters).pack(fill="x", pady=(0, 10))
        
        ttk.Separator(container, orient="horizontal").pack(fill="x", pady=15)
        tk.Button(container, text="⚡ EXECUTE CUSTOM QUERY", bg="#f97316", fg="white",
                 font=("Segoe UI", 13, "bold"), relief="flat", cursor="hand2",
                 activebackground="#ea580c", height=2,
                 command=self.execute_custom_query).pack(fill="x")
        
    def create_results_panel(self, parent):
        top_section = tk.Frame(parent, bg="#2d2d2d", relief="flat")
        top_section.pack(fill="both", expand=True, pady=(0, 15))
        
        results_header = tk.Frame(top_section, bg="#2d2d2d", height=50)
        results_header.pack(fill="x", padx=15, pady=(15, 10))
        tk.Label(results_header, text="🔍 Query Results", font=("Segoe UI", 16, "bold"),
                bg="#2d2d2d", fg="#e0e0e0").pack(side="left")
        self.result_count_label = tk.Label(results_header, text="", font=("Segoe UI", 11),
                                           bg="#2d2d2d", fg="#a0a0a0")
        self.result_count_label.pack(side="right")
        
        table_frame = tk.Frame(top_section, bg="#2d2d2d")
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")
        self.tree = ttk.Treeview(table_frame, yscrollcommand=vsb.set,
                                xscrollcommand=hsb.set, selectmode="browse")
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)
        
        bottom_section = tk.Frame(parent, bg="#2d2d2d", relief="flat", height=280)
        bottom_section.pack(fill="x")
        bottom_section.pack_propagate(False)
        self.create_sql_preview_panel(bottom_section)
        
    def create_sql_preview_panel(self, parent):
        container = tk.Frame(parent, bg="#2d2d2d")
        container.pack(fill="both", expand=True, padx=15, pady=15)
        
        header_frame = tk.Frame(container, bg="#2d2d2d")
        header_frame.pack(fill="x", pady=(0, 10))
        tk.Label(header_frame, text="📝 SQL Query Preview", font=("Segoe UI", 14, "bold"),
                bg="#2d2d2d", fg="#e0e0e0").pack(side="left")
        tk.Button(header_frame, text="📋 Copy SQL", bg="#6366f1", fg="white",
                 font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                 activebackground="#4f46e5", command=self.copy_sql).pack(side="right")
        tk.Button(header_frame, text="💾 Export Results", bg="#10b981", fg="white",
                 font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                 activebackground="#059669", command=self.export_results).pack(side="right", padx=5)
        
        self.sql_preview_text = scrolledtext.ScrolledText(container, height=10, bg="#1e1e1e", fg="#61dafb",
                                                          font=("Courier New", 10), relief="flat", wrap="word",
                                                          insertbackground="#4a9eff", selectbackground="#3d5a80")
        self.sql_preview_text.pack(fill="both", expand=True)
        self.sql_preview_text.insert("1.0", "-- Your SQL query will appear here\n-- Build a query or run a quick query to see the SQL")
        self.sql_preview_text.config(state="disabled")
        
    def create_section_header(self, parent, text):
        tk.Label(parent, text=text, font=("Segoe UI", 11, "bold"),
                bg="#2d2d2d", fg="#4a9eff").pack(anchor="w", pady=(5, 5))
        
    def update_selected_tables(self):
        self.selected_tables = [t for t, var in self.table_vars.items() if var.get()]
        
        if self.selected_tables:
            self.filter_table["values"] = self.selected_tables
            if not self.filter_table.get() or self.filter_table.get() not in self.selected_tables:
                self.filter_table.set(self.selected_tables[0])
                self.on_filter_table_change(None)
        
        for widget in self.columns_frame.winfo_children():
            widget.destroy()
        
        self.selected_columns_widgets = {}
        
        if not self.selected_tables:
            tk.Label(self.columns_frame, text="Select tables first...", bg="#2d2d2d", fg="#7f8c8d",
                    font=("Segoe UI", 9, "italic")).pack(anchor="w")
        else:
            for table in self.selected_tables:
                table_frame = tk.Frame(self.columns_frame, bg="#2d2d2d")
                table_frame.pack(fill="x", pady=5)
                tk.Label(table_frame, text=f"{table}:", bg="#2d2d2d", fg="#e0e0e0",
                        font=("Segoe UI", 10, "bold")).pack(anchor="w")
                
                cols = table_columns(table)
                col_frame = tk.Frame(table_frame, bg="#2d2d2d")
                col_frame.pack(fill="x", padx=(10, 0))
                
                all_var = tk.BooleanVar(value=True)
                tk.Checkbutton(col_frame, text="* (All)", variable=all_var, bg="#2d2d2d", fg="#4a9eff",
                              selectcolor="#3d3d3d", font=("Segoe UI", 9), cursor="hand2").pack(anchor="w")
                
                col_vars = {}
                for col_info in cols:
                    col_name = col_info[1]
                    var = tk.BooleanVar(value=False)
                    col_vars[col_name] = var
                    tk.Checkbutton(col_frame, text=col_name, variable=var, bg="#2d2d2d", fg="#e0e0e0",
                                  selectcolor="#3d3d3d", font=("Segoe UI", 9), cursor="hand2").pack(anchor="w")
                
                self.selected_columns_widgets[table] = {"all": all_var, "cols": col_vars}
        
        all_cols = []
        for table in self.selected_tables:
            cols = table_columns(table)
            for col in cols:
                all_cols.append(f"{table}.{col[1]}")
        
        self.group_by_combo["values"] = all_cols
        self.order_by_combo["values"] = all_cols
        
    def on_filter_table_change(self, event):
        table = self.filter_table.get()
        if table:
            cols = table_columns(table)
            col_names = [col[1] for col in cols]
            self.filter_field["values"] = col_names
            if col_names:
                self.filter_field.set(col_names[0])
                self.on_filter_field_change(None)
    
    def on_filter_field_change(self, event):
        table = self.filter_table.get()
        field = self.filter_field.get()
        if table and field:
            values = get_sample_values(table, field)
            self.filter_value["values"] = values
    
    def add_filter(self):
        table = self.filter_table.get()
        field = self.filter_field.get()
        op = self.filter_op.get()
        value = self.filter_value.get()
        
        if not all([table, field, op, value]):
            messagebox.showwarning("Incomplete", "Please fill all filter fields")
            return
        
        self.filters.append((table, field, op, value))
        self.update_filters_display()
    
    def update_filters_display(self):
        filter_texts = [f"{table}.{field} {op} '{value}'" for table, field, op, value in self.filters]
        if filter_texts:
            self.active_filters_label.config(text="Active: " + " AND ".join(filter_texts))
        else:
            self.active_filters_label.config(text="")
    
    def update_sql_preview(self, query, params=()):
        self.sql_preview_text.config(state="normal")
        self.sql_preview_text.delete("1.0", "end")
        
        formatted = query.replace(" FROM", "\nFROM")
        formatted = formatted.replace(" LEFT JOIN", "\n  LEFT JOIN")
        formatted = formatted.replace(" WHERE", "\nWHERE")
        formatted = formatted.replace(" AND", "\n  AND")
        formatted = formatted.replace(" GROUP BY", "\nGROUP BY")
        formatted = formatted.replace(" ORDER BY", "\nORDER BY")
        formatted = formatted.replace(" LIMIT", "\nLIMIT")
        
        self.sql_preview_text.insert("1.0", formatted)
        if params:
            self.sql_preview_text.insert("end", f"\n\n-- Parameters: {params}")
        
        self.sql_preview_text.config(state="disabled")
        self.last_query = query
        self.last_params = params
    
    def clear_filters(self):
        self.filters = []
        self.group_by_cols = []
        self.order_by_cols = []
        self.update_filters_display()
        self.group_by_label.config(text="")
        self.order_by_label.config(text="")
    
    def copy_sql(self):
        if hasattr(self, 'last_query'):
            self.root.clipboard_clear()
            self.root.clipboard_append(self.last_query)
            messagebox.showinfo("Copied", "SQL query copied to clipboard!")
        else:
            messagebox.showwarning("No Query", "No query to copy. Run a query first.")
    
    def export_results(self):
        if not self.tree.get_children():
            messagebox.showwarning("No Data", "No results to export")
            return
        
        try:
            import csv
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(defaultextension=".csv",
                                                   filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
            
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    headers = [self.tree.heading(col)['text'] for col in self.tree['columns']]
                    writer.writerow(headers)
                    for item in self.tree.get_children():
                        values = self.tree.item(item)['values']
                        writer.writerow(values)
                
                messagebox.showinfo("Success", f"Exported {len(self.tree.get_children())} rows to {filename}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))
    
    def add_group_by(self):
        col = self.group_by_combo.get()
        if col and col not in self.group_by_cols:
            self.group_by_cols.append(col)
            self.group_by_label.config(text="GROUP BY: " + ", ".join(self.group_by_cols))
    
    def add_order_by(self):
        col = self.order_by_combo.get()
        direction = self.order_dir.get()
        if col:
            order_str = f"{col} {direction}"
            if order_str not in self.order_by_cols:
                self.order_by_cols.append(order_str)
                self.order_by_label.config(text="ORDER BY: " + ", ".join(self.order_by_cols))
    
    def build_custom_query(self):
        if not self.selected_tables:
            messagebox.showwarning("No Tables", "Please select at least one table")
            return None
        
        select_parts = []
        for table in self.selected_tables:
            if table in self.selected_columns_widgets:
                widgets = self.selected_columns_widgets[table]
                if widgets["all"].get():
                    select_parts.append(f"{table}.*")
                else:
                    selected = [f"{table}.{col}" for col, var in widgets["cols"].items() if var.get()]
                    select_parts.extend(selected)
        
        if not select_parts:
            for table in self.selected_tables:
                select_parts.append(f"{table}.*")
        
        if self.show_mode.get() == "count":
            select_clause = "SELECT COUNT(*) as count"
        else:
            select_clause = "SELECT " + ", ".join(select_parts)
        
        from_clause = f"FROM {self.selected_tables[0]}"
        
        if len(self.selected_tables) > 1:
            for i, table in enumerate(self.selected_tables[1:], 1):
                prev_table = self.selected_tables[i-1]
                prev_cols = set([c[1] for c in table_columns(prev_table)])
                curr_cols = set([c[1] for c in table_columns(table)])
                common = prev_cols.intersection(curr_cols)
                
                if common:
                    join_key = list(common)[0]
                    from_clause += f" LEFT JOIN {table} ON {prev_table}.{join_key} = {table}.{join_key}"
                else:
                    from_clause += f" , {table}"
        
        where_parts = []
        params = []
        for table, field, op, value in self.filters:
            if op == "LIKE":
                where_parts.append(f"{table}.{field} LIKE ?")
                params.append(f"%{value}%")
            elif op == "BETWEEN":
                vals = value.split(",")
                if len(vals) == 2:
                    where_parts.append(f"{table}.{field} BETWEEN ? AND ?")
                    params.extend([v.strip() for v in vals])
            elif op == "IN":
                vals = [v.strip() for v in value.split(",")]
                placeholders = ",".join(["?"] * len(vals))
                where_parts.append(f"{table}.{field} IN ({placeholders})")
                params.extend(vals)
            else:
                where_parts.append(f"{table}.{field} {op} ?")
                params.append(value)
        
        where_clause = ""
        if where_parts:
            where_clause = "WHERE " + " AND ".join(where_parts)
        
        group_clause = ""
        if self.group_by_cols:
            group_clause = "GROUP BY " + ", ".join(self.group_by_cols)
        
        order_clause = ""
        if self.order_by_cols:
            order_clause = "ORDER BY " + ", ".join(self.order_by_cols)
        
        limit = self.limit_var.get()
        limit_clause = f"LIMIT {limit}" if limit and limit.isdigit() else "LIMIT 100"
        
        query_parts = [select_clause, from_clause]
        if where_clause:
            query_parts.append(where_clause)
        if group_clause:
            query_parts.append(group_clause)
        if order_clause:
            query_parts.append(order_clause)
        query_parts.append(limit_clause)
        
        query = " ".join(query_parts) + ";"
        return query, tuple(params)
    
    def execute_custom_query(self):
        result = self.build_custom_query()
        if not result:
            return
        
        query, params = result
        self.update_sql_preview(query, params)
        self.execute_query(query, params)
    
    def run_quick_query(self):
        query_name = self.query_combo.get()
        if query_name in PREDEFINED_QUERIES:
            query = PREDEFINED_QUERIES[query_name]
            self.update_sql_preview(query, ())
            self.execute_query(query, ())
        else:
            messagebox.showwarning("No Query", "Please select a query from the dropdown")
    
    def execute_query(self, query, params=()):
        rows, col_names = run_query(query, params)
        
        if not col_names:
            messagebox.showinfo("Complete", "Query executed successfully (no results to display)")
            return
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.tree["columns"] = col_names
        self.tree["show"] = "headings"
        
        for col in col_names:
            self.tree.heading(col, text=col, anchor="w")
            self.tree.column(col, width=120, anchor="w")
        
        for row in rows:
            self.tree.insert("", "end", values=row)
        
        self.result_count_label.config(text=f"{len(rows)} results")
    
    def insert_record(self):
        table = simpledialog.askstring("Insert", f"Enter table name:\n{', '.join(self.all_tables)}")
        if not table or table not in self.all_tables:
            return
        
        cols = table_columns(table)
        values = []
        
        for col_info in cols:
            col_name = col_info[1]
            col_type = col_info[2]
            is_pk = col_info[5]
            
            if is_pk and "INTEGER" in col_type.upper():
                continue
            
            val = simpledialog.askstring("Insert", f"Enter value for {col_name} ({col_type}):")
            if val is None:
                return
            values.append(val if val else None)
        
        non_auto_cols = [c[1] for c in cols if not (c[5] and "INTEGER" in c[2].upper())]
        placeholders = ",".join(["?"] * len(values))
        query = f"INSERT INTO {table} ({','.join(non_auto_cols)}) VALUES ({placeholders})"
        
        run_query(query, values)
        messagebox.showinfo("Success", "Record inserted successfully!")
    
    def update_record(self):
        table = simpledialog.askstring("Update", f"Enter table name:\n{', '.join(self.all_tables)}")
        if not table or table not in self.all_tables:
            return
        
        col = simpledialog.askstring("Update", "Column to update:")
        if not col:
            return
        
        val = simpledialog.askstring("Update", f"New value for {col}:")
        if val is None:
            return
        
        cond = simpledialog.askstring("Update", "WHERE condition (e.g., id=1):")
        if not cond:
            return
        
        query = f"UPDATE {table} SET {col} = ? WHERE {cond}"
        run_query(query, (val,))
        messagebox.showinfo("Success", "Record updated successfully!")
    
    def delete_record(self):
        table = simpledialog.askstring("Delete", f"Enter table name:\n{', '.join(self.all_tables)}")
        if not table or table not in self.all_tables:
            return
        
        cond = simpledialog.askstring("Delete", "WHERE condition (e.g., id=1):")
        if not cond:
            return
        
        confirm = messagebox.askyesno("Confirm", f"Delete from {table} WHERE {cond}?")
        if not confirm:
            return
        
        query = f"DELETE FROM {table} WHERE {cond}"
        run_query(query, ())
        messagebox.showinfo("Success", "Record deleted successfully!")

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernApp(root)
    root.mainloop()