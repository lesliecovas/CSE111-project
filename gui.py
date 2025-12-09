# gui.py
import tkinter as tk
from tkinter import ttk, messagebox
from gui_components import StatusBar
from view_panels import (
    CropsPanel, DistrictsPanel, MarketsPanel, PesticidePanel, CropDistrictPanel,
    CropPesticidePanel, WeatherPanel, SustainabilityPanel, RequirementsPanel,
    CropsInDistrictPanel, PesticidesInDistrictPanel, ArrivalPricePanel, ProductionJoinPanel,
    PesticidePerCropPanel, SustainabilityJoinPanel, BestCropForDistrictPanel,
    HighProdLowSustainPanel, DistrictRiskPanel, YieldVsRainfallPanel, TopYieldCropsPanel,
    CustomQueryPanel, DashboardPanel
)
from modify_panels import AddRecordsPanel, UpdateRecordsPanel, DeleteRecordsPanel

DB_PATH = "agriculture.db"

class AgricultureApp:
    def __init__(self, root):
        self.root = root
        root.title("Agricultural DB Management")
        root.geometry("1200x750")

        # Header
        header = ttk.Frame(root, padding=10); header.pack(fill=tk.X)
        ttk.Label(header, text="🌾 Agricultural DB Management", font=('Arial',16,'bold')).pack()
        ttk.Label(header, text="Interactive GUI for CSE111 project", font=('Arial',10)).pack()

        # Main content
        container = ttk.Frame(root); container.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        # Sidebar
        self.sidebar = ttk.Frame(container, width=260); self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10))
        self.sidebar.pack_propagate(False)
        ttk.Label(self.sidebar, text="Navigation", font=('Arial',11,'bold')).pack(pady=(4,8), anchor='w')

        # Main panel
        self.main_panel = ttk.Frame(container); self.main_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # status bar
        self.status = StatusBar(root)
        self.status.set_status("Ready — connected to agriculture.db")

        # Buttons list
        self.sections = [
            ("Dashboard", self.show_dashboard),
            ("View: Crops", self.show_crops),
            ("View: Districts", self.show_districts),
            ("View: Markets", self.show_markets),
            ("View: Crop-District", self.show_crop_district),
            ("View: Crop-Pesticide", self.show_crop_pesticide),
            ("View: Pesticide Use", self.show_pesticide_use),
            ("View: Weather", self.show_weather),
            ("View: Sustainability", self.show_sustainability),
            ("View: Requirements", self.show_requirements),
            ("Query: Crops in District", self.show_crops_in_district),
            ("Query: Pesticides in District", self.show_pesticides_in_district),
            ("Join: Arrival Prices", self.show_arrival_prices),
            ("Join: Production Stats", self.show_production_join),
            ("Join: Pesticide per Crop", self.show_pesticide_per_crop),
            ("Join: Sustainability", self.show_sustainability_join),
            ("Advanced: Best Crops (District)", self.show_best_crop_for_district),
            ("Advanced: HighProd-LowSustain", self.show_highprod_lowsustain),
            ("Advanced: District Risk", self.show_district_risk),
            ("Advanced: Yield vs Rainfall", self.show_yield_vs_rainfall),
            ("Advanced: Top Yield Crops", self.show_top_yield_crops),
            ("Custom Query", self.show_custom_query),
            ("➕ Add Records", self.show_add_records),
            ("✏️ Update Records", self.show_update_records),
            ("🗑️ Delete Records", self.show_delete_records),
        ]

        for (text, cmd) in self.sections:
            b = ttk.Button(self.sidebar, text=text, command=cmd); b.pack(fill=tk.X, pady=2)

        ttk.Separator(self.sidebar, orient="horizontal").pack(fill=tk.X, pady=8)
        ttk.Button(self.sidebar, text="Exit", command=self.on_close).pack(fill=tk.X)

        self.show_dashboard()
        root.protocol("WM_DELETE_WINDOW", self.on_close)

    def clear_main(self):
        for w in self.main_panel.winfo_children():
            w.destroy()

    # show functions
    def show_dashboard(self): self._show_panel(DashboardPanel)
    def show_crops(self): self._show_panel(CropsPanel)
    def show_districts(self): self._show_panel(DistrictsPanel)
    def show_markets(self): self._show_panel(MarketsPanel)
    def show_crop_district(self): self._show_panel(CropDistrictPanel)
    def show_crop_pesticide(self): self._show_panel(CropPesticidePanel)
    def show_pesticide_use(self): self._show_panel(PesticidePanel)
    def show_weather(self): self._show_panel(WeatherPanel)
    def show_sustainability(self): self._show_panel(SustainabilityPanel)
    def show_requirements(self): self._show_panel(RequirementsPanel)
    def show_crops_in_district(self): self._show_panel(CropsInDistrictPanel)
    def show_pesticides_in_district(self): self._show_panel(PesticidesInDistrictPanel)
    def show_arrival_prices(self): self._show_panel(ArrivalPricePanel)
    def show_production_join(self): self._show_panel(ProductionJoinPanel)
    def show_pesticide_per_crop(self): self._show_panel(PesticidePerCropPanel)
    def show_sustainability_join(self): self._show_panel(SustainabilityJoinPanel)
    def show_best_crop_for_district(self): self._show_panel(BestCropForDistrictPanel)
    def show_highprod_lowsustain(self): self._show_panel(HighProdLowSustainPanel)
    def show_district_risk(self): self._show_panel(DistrictRiskPanel)
    def show_yield_vs_rainfall(self): self._show_panel(YieldVsRainfallPanel)
    def show_top_yield_crops(self): self._show_panel(TopYieldCropsPanel)
    def show_custom_query(self): self._show_panel(CustomQueryPanel)

    def show_add_records(self): self._show_modify(AddRecordsPanel)
    def show_update_records(self): self._show_modify(UpdateRecordsPanel)
    def show_delete_records(self): self._show_modify(DeleteRecordsPanel)

    def _show_panel(self, panel_cls):
        self.clear_main()
        self.status.set_status("Loading...")
        frame = panel_cls(self.main_panel, DB_PATH, self.status)
        frame.pack(fill=tk.BOTH, expand=True)
        # call refresh when panel has refresh method
        if hasattr(frame, "refresh"):
            try:
                frame.refresh()
                self.status.set_status("Loaded")
            except Exception as e:
                messagebox.showerror("Error", str(e))
                self.status.set_status("Error loading panel")

    def _show_modify(self, panel_cls):
        self.clear_main()
        self.status.set_status("Opening modification panel...")
        frame = panel_cls(self.main_panel, DB_PATH, self.status)
        frame.pack(fill=tk.BOTH, expand=True)
        self.status.set_status("Ready")

    def on_close(self):
        if messagebox.askokcancel("Quit", "Exit application?"):
            self.root.destroy()

def main():
    root = tk.Tk()
    app = AgricultureApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()