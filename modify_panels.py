# modify_panels.py
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

def execute(db_path: str, query: str, params: tuple = ()):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute(query, params)
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

class AddRecordsPanel(ttk.Notebook):
    def __init__(self, parent, db_path, status, **kwargs):
        super().__init__(parent, **kwargs)
        self.db = db_path
        self.status = status
        self.create_tabs()

    def create_tabs(self):
        # Add Crop Tab
        crop = ttk.Frame(self); self.add(crop, text="Add Crop")
        self.crop_name = tk.StringVar(); self.crop_group = tk.StringVar()
        ttk.Label(crop, text="Crop Name").grid(row=0,column=0,sticky="w", padx=6, pady=6)
        ttk.Entry(crop, textvariable=self.crop_name).grid(row=0,column=1,sticky="ew")
        ttk.Label(crop, text="Crop Group").grid(row=1,column=0,sticky="w", padx=6, pady=6)
        ttk.Entry(crop, textvariable=self.crop_group).grid(row=1,column=1,sticky="ew")
        ttk.Button(crop, text="Add Crop", command=self.add_crop).grid(row=2,column=0,columnspan=2,pady=8)
        crop.columnconfigure(1, weight=1)

        # Add District Tab
        dist = ttk.Frame(self); self.add(dist, text="Add District")
        self.state_name = tk.StringVar(); self.district_name = tk.StringVar()
        ttk.Label(dist, text="State").grid(row=0,column=0,sticky="w", padx=6, pady=6)
        ttk.Entry(dist, textvariable=self.state_name).grid(row=0,column=1,sticky="ew")
        ttk.Label(dist, text="District").grid(row=1,column=0,sticky="w", padx=6, pady=6)
        ttk.Entry(dist, textvariable=self.district_name).grid(row=1,column=1,sticky="ew")
        ttk.Button(dist, text="Add District", command=self.add_district).grid(row=2,column=0,columnspan=2,pady=8)
        dist.columnconfigure(1, weight=1)

        # Add Market Tab
        market = ttk.Frame(self); self.add(market, text="Add Market")
        self.market_name = tk.StringVar(); self.market_district = tk.StringVar()
        ttk.Label(market, text="Market Name").grid(row=0,column=0,sticky="w", padx=6, pady=6)
        ttk.Entry(market, textvariable=self.market_name).grid(row=0,column=1,sticky="ew")
        ttk.Label(market, text="District ID").grid(row=1,column=0,sticky="w", padx=6, pady=6)
        ttk.Entry(market, textvariable=self.market_district).grid(row=1,column=1,sticky="ew")
        ttk.Button(market, text="Add Market", command=self.add_market).grid(row=2,column=0,columnspan=2,pady=8)
        market.columnconfigure(1, weight=1)

        # Add Production Tab
        prod = ttk.Frame(self); self.add(prod, text="Add Production")
        self.prod_crop_id = tk.StringVar(); self.prod_district_id = tk.StringVar()
        self.prod_season = tk.StringVar()
        self.prod_area = tk.StringVar(); self.prod_production = tk.StringVar()
        labels = ["Crop ID", "District ID", "Season", "Area", "Production"]
        vars_ = [self.prod_crop_id, self.prod_district_id, self.prod_season, self.prod_area, self.prod_production]
        for i, (lab, vr) in enumerate(zip(labels, vars_)):
            ttk.Label(prod, text=lab).grid(row=i, column=0, sticky="w", padx=6, pady=4)
            ttk.Entry(prod, textvariable=vr).grid(row=i, column=1, sticky="ew")
        ttk.Button(prod, text="Add Production", command=self.add_production).grid(row=len(labels), column=0, columnspan=2, pady=8)
        prod.columnconfigure(1, weight=1)

        # Add Sustainability Tab
        sust = ttk.Frame(self); self.add(sust, text="Add Sustainability")
        self.s_crop_id = tk.StringVar(); self.s_district_id = tk.StringVar()
        self.s_rainfall = tk.StringVar(); self.s_pesticide_usage = tk.StringVar(); self.s_score = tk.StringVar()
        labels = ["Crop ID", "District ID", "Rainfall(mm)", "Pesticide Usage", "Sustainability Score"]
        vars_ = [self.s_crop_id, self.s_district_id, self.s_rainfall, self.s_pesticide_usage, self.s_score]
        for i, (lab, vr) in enumerate(zip(labels, vars_)):
            ttk.Label(sust, text=lab).grid(row=i,column=0, sticky="w", padx=6, pady=4)
            ttk.Entry(sust, textvariable=vr).grid(row=i,column=1, sticky="ew")
        ttk.Button(sust, text="Add Sustainability", command=self.add_sustain).grid(row=len(labels), column=0, columnspan=2, pady=8)
        sust.columnconfigure(1, weight=1)

    # --- add handlers ---
    def add_crop(self):
        name = self.crop_name.get().strip()
        group = self.crop_group.get().strip() or None
        if not name:
            messagebox.showwarning("Input", "Crop name required")
            return
        ok, err = execute(self.db, "INSERT INTO crops (crop_name, crop_group) VALUES (?, ?)", (name, group))
        if ok:
            self.status.set_status(f"Added crop '{name}'"); messagebox.showinfo("Added", "Crop added")
            self.crop_name.set(""); self.crop_group.set("")
        else:
            messagebox.showerror("Error", err)

    def add_district(self):
        st = self.state_name.get().strip() or None
        dn = self.district_name.get().strip()
        if not dn:
            messagebox.showwarning("Input", "District name required"); return
        ok, err = execute(self.db, "INSERT INTO districts (state_name, district_name) VALUES (?, ?)", (st, dn))
        if ok:
            self.status.set_status(f"Added district '{dn}'"); messagebox.showinfo("Added", "District added")
            self.state_name.set(""); self.district_name.set("")
        else:
            messagebox.showerror("Error", err)

    def add_market(self):
        name = self.market_name.get().strip()
        did = self.market_district.get().strip()
        if not name or not did:
            messagebox.showwarning("Input", "Market name and district id required"); return
        try: did_i = int(did)
        except: messagebox.showwarning("Input", "District ID must be integer"); return
        ok, err = execute(self.db, "INSERT INTO markets (market_name, district_id) VALUES (?, ?)", (name, did_i))
        if ok:
            self.status.set_status(f"Added market '{name}'"); messagebox.showinfo("Added", "Market added")
            self.market_name.set(""); self.market_district.set("")
        else:
            messagebox.showerror("Error", err)

    def add_production(self):
        try:
            crop_id = int(self.prod_crop_id.get().strip())
            district_id = int(self.prod_district_id.get().strip())
            season = self.prod_season.get().strip() or None
            area = float(self.prod_area.get().strip())
            production = float(self.prod_production.get().strip())
        except Exception as e:
            messagebox.showwarning("Input", f"Bad input: {e}"); return
        try:
            yld = round(production / area, 3) if area != 0 else None
        except:
            yld = None
        ok, err = execute(self.db, """INSERT INTO crop_production_statistic (crop_id, district_id, season, area, production, yield)
                                      VALUES (?, ?, ?, ?, ?, ?)""", (crop_id, district_id, season, area, production, yld))
        if ok:
            self.status.set_status("Production record added"); messagebox.showinfo("Added", "Production added")
            self.prod_crop_id.set(""); self.prod_district_id.set(""); self.prod_season.set(""); self.prod_area.set(""); self.prod_production.set("")
        else:
            messagebox.showerror("Error", err)

    def add_sustain(self):
        try:
            crop_id = int(self.s_crop_id.get().strip())
            district_id = int(self.s_district_id.get().strip())
            rainfall = float(self.s_rainfall.get().strip())
            pesticide_usage = float(self.s_pesticide_usage.get().strip())
            score = float(self.s_score.get().strip())
        except Exception as e:
            messagebox.showwarning("Input", f"Bad input: {e}"); return
        ok, err = execute(self.db, """INSERT INTO sustainability_data (crop_id, district_id, rainfall_mm, pesticide_usage, sustainability_score)
                                      VALUES (?, ?, ?, ?, ?)""", (crop_id, district_id, rainfall, pesticide_usage, score))
        if ok:
            self.status.set_status("Sustainability added"); messagebox.showinfo("Added", "Sustainability added")
            self.s_crop_id.set(""); self.s_district_id.set(""); self.s_rainfall.set(""); self.s_pesticide_usage.set(""); self.s_score.set("")
        else:
            messagebox.showerror("Error", err)

class UpdateRecordsPanel(ttk.Frame):
    def __init__(self, parent, db_path, status, **kwargs):
        super().__init__(parent, **kwargs)
        self.db = db_path; self.status = status
        self.create_ui()

    def create_ui(self):
        frm = ttk.Frame(self, padding=10); frm.pack(fill=tk.X)
        # update crop name example
        ttk.Label(frm, text="Crop ID").grid(row=0, column=0, sticky="w")
        self.up_crop_id = tk.StringVar(); ttk.Entry(frm, textvariable=self.up_crop_id).grid(row=0,column=1,sticky="ew")
        ttk.Label(frm, text="New Crop Name").grid(row=1,column=0,sticky="w")
        self.up_crop_name = tk.StringVar(); ttk.Entry(frm, textvariable=self.up_crop_name).grid(row=1,column=1,sticky="ew")
        ttk.Button(frm, text="Update Crop Name", command=self.update_crop).grid(row=2,column=0,columnspan=2,pady=6)
        frm.columnconfigure(1, weight=1)

    def update_crop(self):
        cid = self.up_crop_id.get().strip()
        name = self.up_crop_name.get().strip()
        if not cid or not name:
            messagebox.showwarning("Input", "Crop ID and new name required"); return
        try: cid_i = int(cid)
        except: messagebox.showwarning("Input", "Crop ID must be integer"); return
        ok, err = execute(self.db, "UPDATE crops SET crop_name = ? WHERE crop_id = ?", (name, cid_i))
        if ok: self.status.set_status(f"Crop {cid_i} updated"); messagebox.showinfo("Updated", "Crop updated"); self.up_crop_id.set(""); self.up_crop_name.set("")
        else: messagebox.showerror("Error", err)

class DeleteRecordsPanel(ttk.Frame):
    def __init__(self, parent, db_path, status, **kwargs):
        super().__init__(parent, **kwargs)
        self.db = db_path; self.status = status
        self.create_ui()

    def create_ui(self):
        frm = ttk.Frame(self, padding=10); frm.pack(fill=tk.X)
        ttk.Label(frm, text="Table (crops/districts/markets/production/sustainability/pesticide)").grid(row=0,column=0,sticky="w")
        self.tbl = tk.StringVar(value="crops"); ttk.Entry(frm, textvariable=self.tbl).grid(row=0,column=1,sticky="ew")
        ttk.Label(frm, text="Primary ID").grid(row=1,column=0,sticky="w")
        self.pid = tk.StringVar(); ttk.Entry(frm, textvariable=self.pid).grid(row=1,column=1,sticky="ew")
        ttk.Button(frm, text="Delete", command=self.delete_record).grid(row=2,column=0,columnspan=2,pady=6)
        frm.columnconfigure(1, weight=1)

    def delete_record(self):
        table = self.tbl.get().strip()
        pid = self.pid.get().strip()
        if not table or not pid:
            messagebox.showwarning("Input", "Table and ID required"); return
        map_ids = {
            "crops": "crop_id", "districts": "district_id", "markets": "market_id",
            "production": "stat_id", "sustainability": "record_id", "pesticide": "pesticide_id"
        }
        if table not in map_ids:
            messagebox.showwarning("Error", "Unsupported table key"); return
        try: pid_i = int(pid)
        except: messagebox.showwarning("Input", "ID must be integer"); return
        real_table = table
        if table == "production": real_table = "crop_production_statistic"
        if table == "pesticide": real_table = "pesticide_use"
        q = f"DELETE FROM {real_table} WHERE {map_ids[table]} = ?"
        ok, err = execute(self.db, q, (pid_i,))
        if ok:
            self.status.set_status(f"Deleted {table} {pid_i}"); messagebox.showinfo("Deleted", f"Deleted {table} {pid_i}"); self.pid.set("")
        else:
            messagebox.showerror("Error", err)