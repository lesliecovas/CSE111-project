# view_panels.py - COMPLETE VERSION
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Tuple
from gui_components import TreeTable, info_popup

def run_query(db_path: str, query: str, params: tuple = ()) -> Tuple[List[str], List[Tuple]]:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute(query, params)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()
        return cols, rows
    finally:
        conn.close()

class BasePanel(ttk.Frame):
    def __init__(self, parent, db_path: str, status_bar, **kwargs):
        super().__init__(parent, **kwargs)
        self.db_path = db_path
        self.status = status_bar
        self.topbar = ttk.Frame(self)
        self.topbar.pack(fill=tk.X, pady=6)
        self.filter_var = tk.StringVar()
        ttk.Label(self.topbar, text="Filter / Search:").pack(side=tk.LEFT, padx=(2,4))
        ttk.Entry(self.topbar, textvariable=self.filter_var, width=30).pack(side=tk.LEFT)
        ttk.Button(self.topbar, text="Refresh", command=self.refresh).pack(side=tk.LEFT, padx=6)
        ttk.Button(self.topbar, text="Export CSV", command=self.export_csv).pack(side=tk.LEFT)
        self.table = TreeTable(self)
        self.table.pack(fill=tk.BOTH, expand=True, pady=(6,0))

    def refresh(self):
        raise NotImplementedError

    def export_csv(self):
        rows = self.table.get_all_rows()
        cols = self.table.tree["columns"]
        if not rows:
            info_popup("No data to export")
            return
        import tkinter.filedialog as fd, csv
        path = fd.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(rows)
        info_popup(f"Exported {len(rows)} rows to {path}")

# ============ DASHBOARD ============
class DashboardPanel(ttk.Frame):
    def __init__(self, parent, db_path: str, status_bar, **kwargs):
        super().__init__(parent, **kwargs)
        self.db_path = db_path
        self.status = status_bar
        self.create_dashboard()

    def create_dashboard(self):
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(title_frame, text="📊 Agricultural Database Dashboard", font=('Arial', 16, 'bold')).pack()
        ttk.Label(title_frame, text="Real-time insights from agricultural data", font=('Arial', 10)).pack()

        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        self.content_frame = scrollable_frame
        
        self.create_key_metrics()
        self.create_production_insights()
        self.create_sustainability_insights()
        self.create_market_insights()
        self.create_quick_stats()

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_metric_card(self, parent, title: str, value: str, color: str = "#2196F3"):
        card = ttk.Frame(parent, relief=tk.RAISED, borderwidth=2)
        card.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        ttk.Label(card, text=title, font=('Arial', 9, 'bold'), foreground='gray').pack(pady=(10, 5))
        ttk.Label(card, text=value, font=('Arial', 20, 'bold'), foreground=color).pack(pady=(0, 10))
        return card

    def create_section_header(self, parent, text: str):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(15, 5))
        ttk.Separator(frame, orient='horizontal').pack(fill=tk.X, pady=(0, 5))
        ttk.Label(frame, text=text, font=('Arial', 12, 'bold')).pack(anchor='w')
        return frame

    def create_key_metrics(self):
        self.create_section_header(self.content_frame, "📈 Key Metrics")
        metrics_frame = ttk.Frame(self.content_frame)
        metrics_frame.pack(fill=tk.X, padx=10)
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(DISTINCT district_id) FROM districts")
        total_districts = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT crop_id) FROM crops")
        total_crops = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT market_id) FROM markets")
        total_markets = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM crop_production_statistic")
        total_records = cur.fetchone()[0]
        conn.close()
        self.create_metric_card(metrics_frame, "Total Districts", str(total_districts), "#4CAF50")
        self.create_metric_card(metrics_frame, "Total Crops", str(total_crops), "#2196F3")
        self.create_metric_card(metrics_frame, "Active Markets", str(total_markets), "#FF9800")
        self.create_metric_card(metrics_frame, "Production Records", str(total_records), "#9C27B0")

    def create_production_insights(self):
        self.create_section_header(self.content_frame, "🌾 Production Insights")
        insights_frame = ttk.Frame(self.content_frame)
        insights_frame.pack(fill=tk.BOTH, padx=10, expand=True)
        table_frame = ttk.LabelFrame(insights_frame, text="Top 5 Crops by Average Yield", padding=10)
        table_frame.pack(fill=tk.BOTH, pady=5, expand=True)
        columns = ("Rank", "Crop Name", "Avg Yield", "Total Production")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=5)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor='center')
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT c.crop_name, ROUND(AVG(p.yield), 3) as avg_yield, ROUND(SUM(p.production), 2) as total_prod
            FROM crop_production_statistic p
            JOIN crops c ON p.crop_id = c.crop_id
            WHERE p.yield IS NOT NULL
            GROUP BY c.crop_name
            ORDER BY avg_yield DESC
            LIMIT 5
        """)
        for idx, row in enumerate(cur.fetchall(), 1):
            tree.insert("", "end", values=(idx, row[0], row[1], row[2]))
        conn.close()
        tree.pack(fill=tk.BOTH, expand=True)

    def create_sustainability_insights(self):
        self.create_section_header(self.content_frame, "🌱 Sustainability Insights")
        sustain_frame = ttk.Frame(self.content_frame)
        sustain_frame.pack(fill=tk.X, padx=10)
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT ROUND(AVG(sustainability_score), 2) FROM sustainability_data WHERE sustainability_score IS NOT NULL")
        result = cur.fetchone()
        avg_sustain = result[0] if result and result[0] else 0
        cur.execute("SELECT COUNT(DISTINCT district_id) FROM pesticide_use WHERE high_estimate > 50")
        high_pesticide_districts = cur.fetchone()[0]
        cur.execute("SELECT ROUND(AVG(rainfall_mm), 2) FROM sustainability_data WHERE rainfall_mm IS NOT NULL")
        result = cur.fetchone()
        avg_rainfall = result[0] if result and result[0] else 0
        conn.close()
        self.create_metric_card(sustain_frame, "Avg Sustainability Score", f"{avg_sustain}/10", "#4CAF50")
        self.create_metric_card(sustain_frame, "High Pesticide Districts", str(high_pesticide_districts), "#F44336")
        self.create_metric_card(sustain_frame, "Avg Rainfall (mm)", str(avg_rainfall), "#03A9F4")

    def create_market_insights(self):
        self.create_section_header(self.content_frame, "💰 Market Insights")
        market_frame = ttk.Frame(self.content_frame)
        market_frame.pack(fill=tk.BOTH, padx=10, expand=True)
        table_frame = ttk.LabelFrame(market_frame, text="Recent Market Activity (Top 5)", padding=10)
        table_frame.pack(fill=tk.BOTH, pady=5, expand=True)
        columns = ("Crop", "Market", "Price (₹/Quintal)", "Arrival (Tonnes)")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=5)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor='center')
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT c.crop_name, m.market_name, ROUND(cap.modal_price_rs_per_quintal, 2) as price, ROUND(cap.arrival_tonnes, 2) as arrival
            FROM crop_arrival_price cap
            LEFT JOIN crops c ON cap.crop_id = c.crop_id
            LEFT JOIN markets m ON cap.market_id = m.market_id
            WHERE cap.modal_price_rs_per_quintal IS NOT NULL
            ORDER BY cap.arrival_date DESC
            LIMIT 5
        """)
        for row in cur.fetchall():
            tree.insert("", "end", values=row)
        conn.close()
        tree.pack(fill=tk.BOTH, expand=True)

    def create_quick_stats(self):
        self.create_section_header(self.content_frame, "⚡ Quick Statistics")
        stats_frame = ttk.Frame(self.content_frame)
        stats_frame.pack(fill=tk.BOTH, padx=10, pady=(5, 20), expand=True)
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(DISTINCT state_name) FROM districts WHERE state_name IS NOT NULL")
        states_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT compound) FROM pesticide_use WHERE compound IS NOT NULL")
        pesticide_compounds = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM farm_weather")
        weather_records = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM crop_requirements")
        requirements_count = cur.fetchone()[0]
        conn.close()
        info_frame = ttk.Frame(stats_frame)
        info_frame.pack(fill=tk.BOTH, expand=True)
        stats_data = [
            ("📍 States Covered", states_count),
            ("🧪 Pesticide Compounds", pesticide_compounds),
            ("🌤️ Weather Records", weather_records),
            ("📋 Crop Requirements", requirements_count)
        ]
        for i, (label, value) in enumerate(stats_data):
            row = i // 2
            col = i % 2
            card = ttk.Frame(info_frame, relief=tk.GROOVE, borderwidth=1)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            ttk.Label(card, text=label, font=('Arial', 10, 'bold')).pack(pady=(10, 5))
            ttk.Label(card, text=str(value), font=('Arial', 16), foreground='#2196F3').pack(pady=(0, 10))
        info_frame.columnconfigure(0, weight=1)
        info_frame.columnconfigure(1, weight=1)

    def refresh(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.create_key_metrics()
        self.create_production_insights()
        self.create_sustainability_insights()
        self.create_market_insights()
        self.create_quick_stats()
        self.status.set_status("Dashboard refreshed")

# ============ SIMPLE VIEW PANELS ============
class CropsPanel(BasePanel):
    def refresh(self):
        q = "SELECT crop_id, crop_name, crop_group FROM crops ORDER BY crop_name"
        cols, rows = run_query(self.db_path, q)
        self.table.set_columns(cols)
        self.table.clear()
        self.table.insert_rows(rows)

class DistrictsPanel(BasePanel):
    def refresh(self):
        q = "SELECT district_id, state_name, district_name FROM districts ORDER BY state_name, district_name"
        cols, rows = run_query(self.db_path, q)
        self.table.set_columns(cols)
        self.table.clear()
        self.table.insert_rows(rows)

class MarketsPanel(BasePanel):
    def refresh(self):
        q = """SELECT m.market_id, m.market_name, d.district_name, d.state_name
        FROM markets m LEFT JOIN districts d ON m.district_id = d.district_id
        ORDER BY d.state_name, m.market_name"""
        cols, rows = run_query(self.db_path, q)
        self.table.set_columns(cols)
        self.table.clear()
        self.table.insert_rows(rows)

class PesticidePanel(BasePanel):
    def refresh(self):
        q = "SELECT pesticide_id, district_id, compound, low_estimate, high_estimate FROM pesticide_use ORDER BY compound"
        cols, rows = run_query(self.db_path, q)
        self.table.set_columns(cols)
        self.table.clear()
        self.table.insert_rows(rows)

class CropDistrictPanel(BasePanel):
    def refresh(self):
        q = "SELECT crop_id, district_id, avg_yield, total_area, best_season FROM crop_district"
        cols, rows = run_query(self.db_path, q)
        self.table.set_columns(cols)
        self.table.clear()
        self.table.insert_rows(rows)

class CropPesticidePanel(BasePanel):
    def refresh(self):
        q = "SELECT crop_id, pesticide_id FROM crop_pesticide"
        cols, rows = run_query(self.db_path, q)
        self.table.set_columns(cols)
        self.table.clear()
        self.table.insert_rows(rows)

class WeatherPanel(BasePanel):
    def refresh(self):
        q = "SELECT weather_id, district_id, maxT, minT, windspeed, humidity, precipitation FROM farm_weather ORDER BY weather_id DESC"
        cols, rows = run_query(self.db_path, q)
        self.table.set_columns(cols)
        self.table.clear()
        self.table.insert_rows(rows)

class SustainabilityPanel(BasePanel):
    def refresh(self):
        q = "SELECT record_id, crop_id, district_id, rainfall_mm, pesticide_usage, sustainability_score FROM sustainability_data ORDER BY record_id DESC"
        cols, rows = run_query(self.db_path, q)
        self.table.set_columns(cols)
        self.table.clear()
        self.table.insert_rows(rows)

class RequirementsPanel(BasePanel):
    def refresh(self):
        q = "SELECT requirement_id, crop_id, N, P, K, temperature, humidity, ph, rainfall FROM crop_requirements"
        cols, rows = run_query(self.db_path, q)
        self.table.set_columns(cols)
        self.table.clear()
        self.table.insert_rows(rows)

# ============ QUERY PANELS ============
class CropsInDistrictPanel(BasePanel):
    def __init__(self, parent, db_path, status_bar, **kwargs):
        super().__init__(parent, db_path, status_bar, **kwargs)
        dd = ttk.Frame(self.topbar)
        dd.pack(side=tk.RIGHT)
        ttk.Label(dd, text="District ID:").pack(side=tk.LEFT)
        self.district_id_var = tk.StringVar()
        ttk.Entry(dd, textvariable=self.district_id_var, width=6).pack(side=tk.LEFT, padx=(4,6))
        ttk.Button(dd, text="Find Crops", command=self.refresh).pack(side=tk.LEFT)

    def refresh(self):
        did = self.district_id_var.get().strip()
        if not did:
            messagebox.showwarning("Input", "District ID required")
            return
        try:
            did_i = int(did)
        except:
            messagebox.showwarning("Input", "District ID must be integer")
            return
        q = """SELECT DISTINCT c.crop_id, c.crop_name
        FROM crop_district cd JOIN crops c ON cd.crop_id = c.crop_id
        WHERE cd.district_id = ?
        ORDER BY c.crop_name"""
        cols, rows = run_query(self.db_path, q, (did_i,))
        self.table.set_columns(cols)
        self.table.clear()
        self.table.insert_rows(rows)

class PesticidesInDistrictPanel(BasePanel):
    def __init__(self, parent, db_path, status_bar, **kwargs):
        super().__init__(parent, db_path, status_bar, **kwargs)
        dd = ttk.Frame(self.topbar)
        dd.pack(side=tk.RIGHT)
        ttk.Label(dd, text="District ID:").pack(side=tk.LEFT)
        self.district_id_var = tk.StringVar()
        ttk.Entry(dd, textvariable=self.district_id_var, width=6).pack(side=tk.LEFT, padx=(4,6))
        ttk.Button(dd, text="Find", command=self.refresh).pack(side=tk.LEFT)

    def refresh(self):
        did = self.district_id_var.get().strip()
        if not did:
            messagebox.showwarning("Input", "District ID required")
            return
        try:
            did_i = int(did)
        except:
            messagebox.showwarning("Input", "District ID must be integer")
            return
        q = """SELECT pu.pesticide_id, pu.compound, pu.low_estimate, pu.high_estimate
        FROM pesticide_use pu WHERE pu.district_id = ? ORDER BY pu.compound"""
        cols, rows = run_query(self.db_path, q, (did_i,))
        self.table.set_columns(cols)
        self.table.clear()
        self.table.insert_rows(rows)

# ============ ADVANCED PANELS ============
class ArrivalPricePanel(BasePanel):
    def refresh(self):
        q = """SELECT cap.arrival_id, c.crop_name, cap.variety, m.market_name, cap.arrival_date, cap.modal_price_rs_per_quintal, cap.arrival_tonnes
        FROM crop_arrival_price cap
        LEFT JOIN crops c ON cap.crop_id = c.crop_id
        LEFT JOIN markets m ON cap.market_id = m.market_id
        ORDER BY cap.arrival_date DESC LIMIT 500"""
        cols, rows = run_query(self.db_path, q)
        self.table.set_columns(cols)
        self.table.clear()
        self.table.insert_rows(rows)

class ProductionJoinPanel(BasePanel):
    def refresh(self):
        q = """SELECT p.stat_id, c.crop_name, d.district_name, p.season, p.area, p.production, p.yield
        FROM crop_production_statistic p
        LEFT JOIN crops c ON p.crop_id = c.crop_id
        LEFT JOIN districts d ON p.district_id = d.district_id
        ORDER BY p.production DESC LIMIT 500"""
        cols, rows = run_query(self.db_path, q)
        self.table.set_columns(cols)
        self.table.clear()
        self.table.insert_rows(rows)

class PesticidePerCropPanel(BasePanel):
    def refresh(self):
        q = """SELECT c.crop_name, pu.compound, pu.low_estimate, pu.high_estimate
        FROM crop_pesticide cp
        JOIN crops c ON cp.crop_id = c.crop_id
        JOIN pesticide_use pu ON cp.pesticide_id = pu.pesticide_id
        ORDER BY c.crop_name"""
        cols, rows = run_query(self.db_path, q)
        self.table.set_columns(cols)
        self.table.clear()
        self.table.insert_rows(rows)

class SustainabilityJoinPanel(BasePanel):
    def refresh(self):
        q = """SELECT s.record_id, d.district_name, c.crop_name, s.rainfall_mm, s.pesticide_usage, s.sustainability_score
        FROM sustainability_data s
        LEFT JOIN districts d ON s.district_id = d.district_id
        LEFT JOIN crops c ON s.crop_id = c.crop_id
        ORDER BY s.record_id DESC"""
        cols, rows = run_query(self.db_path, q)
        self.table.set_columns(cols)
        self.table.clear()
        self.table.insert_rows(rows)

class BestCropForDistrictPanel(BasePanel):
    def __init__(self, parent, db_path, status_bar, **kwargs):
        super().__init__(parent, db_path, status_bar, **kwargs)
        dd = ttk.Frame(self.topbar)
        dd.pack(side=tk.RIGHT)
        ttk.Label(dd, text="District ID:").pack(side=tk.LEFT)
        self.district_id_var = tk.StringVar()
        ttk.Entry(dd, textvariable=self.district_id_var, width=6).pack(side=tk.LEFT, padx=(4,6))
        ttk.Button(dd, text="Recommend", command=self.refresh).pack(side=tk.LEFT)

    def refresh(self):
        did = self.district_id_var.get().strip()
        if not did:
            messagebox.showwarning("Input", "District ID required")
            return
        try:
            did_i = int(did)
        except:
            messagebox.showwarning("Input", "District ID must be integer")
            return
        q = """SELECT c.crop_name,
               ROUND(AVG(sd.sustainability_score),3) as avg_sustain,
               ROUND(AVG(cd.avg_yield),3) as avg_yield,
               ROUND((COALESCE(AVG(sd.sustainability_score),0)*0.6 + COALESCE(AVG(cd.avg_yield),0)*0.4),3) as score
        FROM crops c
        LEFT JOIN sustainability_data sd ON sd.crop_id = c.crop_id AND sd.district_id = ?
        LEFT JOIN crop_district cd ON cd.crop_id = c.crop_id AND cd.district_id = ?
        GROUP BY c.crop_name ORDER BY score DESC LIMIT 10"""
        cols, rows = run_query(self.db_path, q, (did_i, did_i))
        self.table.set_columns(cols)
        self.table.clear()
        self.table.insert_rows(rows)

class HighProdLowSustainPanel(BasePanel):
    def refresh(self):
        q = """SELECT p.crop_id, c.crop_name, SUM(p.production) as total_production, AVG(sd.sustainability_score) as avg_sustain
        FROM crop_production_statistic p
        LEFT JOIN sustainability_data sd ON p.crop_id = sd.crop_id AND p.district_id = sd.district_id
        LEFT JOIN crops c ON p.crop_id = c.crop_id
        GROUP BY p.crop_id
        HAVING total_production > 1000 AND (avg_sustain IS NULL OR avg_sustain < 3)
        ORDER BY total_production DESC"""
        cols, rows = run_query(self.db_path, q)
        self.table.set_columns(cols)
        self.table.clear()
        self.table.insert_rows(rows)

class DistrictRiskPanel(BasePanel):
    def refresh(self):
        q = """SELECT d.district_id, d.district_name,
               AVG(pu.high_estimate) as avg_pesticide_hi,
               AVG(sd.rainfall_mm) as avg_rainfall,
               AVG(sd.sustainability_score) as avg_sustain
        FROM districts d
        LEFT JOIN pesticide_use pu ON pu.district_id = d.district_id
        LEFT JOIN sustainability_data sd ON sd.district_id = d.district_id
        GROUP BY d.district_id
        HAVING avg_pesticide_hi > 50 AND (avg_rainfall < 200 OR avg_sustain < 3)
        ORDER BY avg_pesticide_hi DESC"""
        cols, rows = run_query(self.db_path, q)
        self.table.set_columns(cols)
        self.table.clear()
        self.table.insert_rows(rows)

class YieldVsRainfallPanel(BasePanel):
    def refresh(self):
        q = """SELECT sd.district_id, d.district_name, ROUND(AVG(sd.rainfall_mm),2) as avg_rain, ROUND(AVG(sd.crop_yield),3) as avg_yield
        FROM sustainability_data sd
        JOIN districts d ON sd.district_id = d.district_id
        GROUP BY sd.district_id
        ORDER BY avg_rain DESC"""
        cols, rows = run_query(self.db_path, q)
        self.table.set_columns(cols)
        self.table.clear()
        self.table.insert_rows(rows)

class TopYieldCropsPanel(BasePanel):
    def refresh(self):
        q = """SELECT c.crop_name, ROUND(AVG(p.yield),3) as avg_yield
        FROM crop_production_statistic p
        JOIN crops c ON p.crop_id = c.crop_id
        GROUP BY p.crop_id
        ORDER BY avg_yield DESC LIMIT 10"""
        cols, rows = run_query(self.db_path, q)
        self.table.set_columns(cols)
        self.table.clear()
        self.table.insert_rows(rows)

# ============ CUSTOM QUERY ============
class CustomQueryPanel(ttk.Frame):
    def __init__(self, parent, db_path, status, **kwargs):
        super().__init__(parent, **kwargs)
        self.db_path = db_path
        self.status = status
        top = ttk.Frame(self)
        top.pack(fill=tk.X, pady=6)
        ttk.Label(top, text="Enter a SELECT query:").pack(anchor="w")
        self.qtext = tk.Text(top, height=6)
        self.qtext.pack(fill=tk.X)
        btns = ttk.Frame(top)
        btns.pack(fill=tk.X, pady=4)
        ttk.Button(btns, text="Run SELECT", command=self.run).pack(side=tk.LEFT)
        ttk.Button(btns, text="Clear", command=lambda: self.qtext.delete("1.0","end")).pack(side=tk.LEFT, padx=6)
        self.table = TreeTable(self)
        self.table.pack(fill=tk.BOTH, expand=True)

    def run(self):
        q = self.qtext.get("1.0","end").strip()
        if not q.lower().startswith("select"):
            messagebox.showwarning("Only SELECT", "Custom query panel allows only SELECT queries")
            return
        try:
            cols, rows = run_query(self.db_path, q)
            self.table.set_columns(cols)
            self.table.clear()
            self.table.insert_rows(rows)
        except Exception as e:
            messagebox.showerror("Query Error", str(e))