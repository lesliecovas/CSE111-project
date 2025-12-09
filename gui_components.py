# gui_components.py
import tkinter as tk
from tkinter import ttk, messagebox

def error_popup(message: str):
    messagebox.showerror("Error", message)

def info_popup(message: str):
    messagebox.showinfo("Info", message)

class StatusBar(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.pack(side=tk.BOTTOM, fill=tk.X)
        self.var = tk.StringVar(value="Ready")
        self.label = ttk.Label(self, textvariable=self.var, relief=tk.SUNKEN, anchor='w')
        self.label.pack(fill=tk.X)

    def set_status(self, text: str):
        self.var.set(text)

class TreeTable(ttk.Frame):
    """Simple scrollable table using ttk.Treeview"""
    def __init__(self, parent, columns=()):
        super().__init__(parent)
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.hsb.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def set_columns(self, columns):
        self.tree["columns"] = columns
        for c in columns:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=130, anchor="w")

    def clear(self):
        for r in self.tree.get_children():
            self.tree.delete(r)

    def insert_rows(self, rows):
        for r in rows:
            self.tree.insert("", "end", values=r)

    def get_all_rows(self):
        return [self.tree.item(i)["values"] for i in self.tree.get_children()]