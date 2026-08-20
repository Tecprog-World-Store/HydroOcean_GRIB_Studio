from __future__ import annotations
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.grib.reader import GribReader
from src.analysis.vectors import (
    speed_from_uv,
    meteorological_from_direction,
    oceanographic_to_direction,
)
from src.plots.rose import plot_directional_rose
from src.plots.timeseries import plot_timeseries
from src.acquisition.nomads_gfswave import GFSWaveRequest, download_gfswave

ALIASES = {
    "wind_u": ["u10", "u", "ugrd", "UGRD"],
    "wind_v": ["v10", "v", "vgrd", "VGRD"],
    "wind_speed": ["wind", "WIND", "si10"],
    "wind_direction": ["wdir", "WDIR"],
    "wave_height": ["swh", "htsgw", "HTSGW"],
    "wave_period": ["perpw", "PERPW", "mwp"],
    "wave_direction": ["dirpw", "DIRPW", "mwd"],
    "current_u": ["uo", "uogrd", "UOGRD", "eastcur", "EASTCUR"],
    "current_v": ["vo", "vogrd", "VOGRD", "nrthcur", "NRTHCUR"],
    "current_speed": ["spc", "SPC"],
    "current_direction": ["dirc", "DIRC"],
}

class HydroOceanApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HydroOcean GRIB Studio 0.1")
        self.geometry("1220x780")
        self.minsize(1050, 680)

        self.reader = GribReader()
        self.point_df = pd.DataFrame()
        self.current_figure = None
        self.loaded_path = None

        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self, padding=8)
        toolbar.grid(row=0, column=0, sticky="ew")
        ttk.Button(toolbar, text="Abrir GRIB2", command=self.open_grib).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Exportar CSV", command=self.export_csv).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Guardar figura", command=self.save_figure).pack(side="left", padx=4)
        self.file_label = ttk.Label(toolbar, text="Sin archivo cargado")
        self.file_label.pack(side="left", padx=12)

        self.nb = ttk.Notebook(self)
        self.nb.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0,8))

        self.tab_analysis = ttk.Frame(self.nb)
        self.tab_inventory = ttk.Frame(self.nb)
        self.tab_noaa = ttk.Frame(self.nb)
        self.tab_log = ttk.Frame(self.nb)

        self.nb.add(self.tab_analysis, text="Análisis")
        self.nb.add(self.tab_inventory, text="Inventario")
        self.nb.add(self.tab_noaa, text="NOAA / GFS-Wave")
        self.nb.add(self.tab_log, text="Registro")

        self._build_analysis()
        self._build_inventory()
        self._build_noaa()
        self._build_log()

    def _build_analysis(self):
        self.tab_analysis.columnconfigure(1, weight=1)
        self.tab_analysis.rowconfigure(0, weight=1)

        left = ttk.LabelFrame(self.tab_analysis, text="Punto virtual y producto", padding=10)
        left.grid(row=0, column=0, sticky="nsw", padx=8, pady=8)

        ttk.Label(left, text="Latitud").grid(row=0, column=0, sticky="w")
        self.lat_var = tk.StringVar(value="-12.0")
        ttk.Entry(left, textvariable=self.lat_var, width=16).grid(row=0, column=1, pady=3)

        ttk.Label(left, text="Longitud").grid(row=1, column=0, sticky="w")
        self.lon_var = tk.StringVar(value="-77.5")
        ttk.Entry(left, textvariable=self.lon_var, width=16).grid(row=1, column=1, pady=3)

        ttk.Label(left, text="Producto").grid(row=2, column=0, sticky="w")
        self.product_var = tk.StringVar(value="Viento")
        ttk.Combobox(
            left, textvariable=self.product_var,
            values=["Viento", "Oleaje", "Corrientes"],
            state="readonly", width=18
        ).grid(row=2, column=1, pady=3)

        ttk.Button(left, text="Extraer punto", command=self.extract_point).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(10,4)
        )
        ttk.Button(left, text="Rosa direccional", command=self.make_rose).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=4
        )
        ttk.Button(left, text="Serie temporal", command=self.make_timeseries).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=4
        )

        self.point_info = ttk.Label(left, text="Sin extracción.", wraplength=280)
        self.point_info.grid(row=6, column=0, columnspan=2, sticky="w", pady=10)

        self.plot_frame = ttk.Frame(self.tab_analysis)
        self.plot_frame.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)

    def _build_inventory(self):
        self.tab_inventory.columnconfigure(0, weight=1)
        self.tab_inventory.rowconfigure(0, weight=1)
        cols = ("dataset","variable","shortName","long_name","units","dims","shape")
        self.tree = ttk.Treeview(self.tab_inventory, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=130, anchor="w")
        self.tree.column("long_name", width=280)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ys = ttk.Scrollbar(self.tab_inventory, orient="vertical", command=self.tree.yview)
        ys.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=ys.set)

    def _build_noaa(self):
        frm = ttk.LabelFrame(self.tab_noaa, text="Descarga regional GFS-Wave / NOMADS", padding=12)
        frm.pack(fill="x", padx=12, pady=12)

        import datetime
        defaults = {
            "Fecha YYYYMMDD": datetime.datetime.utcnow().strftime("%Y%m%d"),
            "Ciclo": "00",
            "Pronóstico (h)": "0",
            "Norte": "1.0",
            "Sur": "-20.0",
            "Oeste": "-90.0",
            "Este": "-68.0",
        }
        self.noaa_vars = {}
        for i, (label, val) in enumerate(defaults.items()):
            ttk.Label(frm, text=label).grid(row=i, column=0, sticky="w", pady=3)
            sv = tk.StringVar(value=val)
            self.noaa_vars[label] = sv
            ttk.Entry(frm, textvariable=sv, width=22).grid(row=i, column=1, sticky="w", pady=3)

        ttk.Label(frm, text="Parámetros").grid(row=0, column=2, sticky="nw", padx=(30,0))
        self.param_vars = {}
        params = ["WIND","WDIR","UGRD","VGRD","HTSGW","PERPW","DIRPW","WVHGT","WVPER","WVDIR"]
        for j, p in enumerate(params):
            bv = tk.BooleanVar(value=p in {"WIND","WDIR","UGRD","VGRD","HTSGW","PERPW","DIRPW"})
            self.param_vars[p] = bv
            ttk.Checkbutton(frm, text=p, variable=bv).grid(
                row=1 + j//2, column=2 + j%2, sticky="w", padx=(30 if j%2==0 else 8,0)
            )

        ttk.Button(frm, text="Descargar GRIB2", command=self.download_noaa).grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=(12,4)
        )

        note = (
            "Esta opción usa el servicio oficial NOMADS Grib Filter. "
            "La disponibilidad depende de la retención del servidor. "
            "Para estudios históricos debe usarse un archivo archivado o una fuente histórica."
        )
        ttk.Label(self.tab_noaa, text=note, wraplength=900).pack(anchor="w", padx=16, pady=8)

    def _build_log(self):
        self.log_text = tk.Text(self.tab_log, wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)

    def log(self, text):
        self.log_text.insert("end", str(text) + "\n")
        self.log_text.see("end")

    def open_grib(self):
        path = filedialog.askopenfilename(
            title="Seleccionar archivo GRIB2",
            filetypes=[
                ("GRIB2", "*.grib2 *.grb2 *.grib *.grb"),
                ("Todos", "*.*"),
            ]
        )
        if not path:
            return
        try:
            self.config(cursor="watch")
            self.update_idletasks()
            datasets = self.reader.open(path)
            self.loaded_path = Path(path)
            self.file_label.config(text=self.loaded_path.name)
            self._populate_inventory()
            self.log(f"Archivo abierto: {path}")
            self.log(f"Datasets cfgrib detectados: {len(datasets)}")
            self.nb.select(self.tab_inventory)
        except Exception as exc:
            messagebox.showerror("Error GRIB2", str(exc))
            self.log(f"ERROR al abrir GRIB2: {exc}")
        finally:
            self.config(cursor="")

    def _populate_inventory(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        inv = self.reader.inventory()
        for _, row in inv.iterrows():
            self.tree.insert("", "end", values=[row.get(c,"") for c in self.tree["columns"]])

    def _extract_alias(self, key, lat, lon):
        return self.reader.extract_series(ALIASES[key], lat, lon)

    def extract_point(self):
        if not self.reader.datasets:
            messagebox.showwarning("GRIB2", "Primero abra un archivo GRIB2.")
            return
        try:
            lat = float(self.lat_var.get())
            lon = float(self.lon_var.get())
            product = self.product_var.get()

            data = {}
            location = None

            if product == "Viento":
                u = self._extract_alias("wind_u", lat, lon)
                v = self._extract_alias("wind_v", lat, lon)
                ws = self._extract_alias("wind_speed", lat, lon)
                wd = self._extract_alias("wind_direction", lat, lon)

                if u and v:
                    df = pd.concat([u["series"].rename("U_wind"), v["series"].rename("V_wind")], axis=1)
                    df["WindSpeed"] = speed_from_uv(df["U_wind"], df["V_wind"])
                    df["WindDir_from_deg"] = meteorological_from_direction(df["U_wind"], df["V_wind"])
                    location = u
                elif ws and wd:
                    df = pd.concat([ws["series"].rename("WindSpeed"), wd["series"].rename("WindDir_from_deg")], axis=1)
                    location = ws
                else:
                    raise ValueError("No se hallaron U/V ni WIND/WDIR para viento.")

            elif product == "Oleaje":
                hs = self._extract_alias("wave_height", lat, lon)
                tp = self._extract_alias("wave_period", lat, lon)
                dr = self._extract_alias("wave_direction", lat, lon)
                series = []
                for obj, name in ((hs,"Hs_m"), (tp,"Period_s"), (dr,"WaveDir_deg")):
                    if obj:
                        series.append(obj["series"].rename(name))
                        location = location or obj
                if not series:
                    raise ValueError("No se encontraron variables de oleaje configuradas.")
                df = pd.concat(series, axis=1)

            else:
                u = self._extract_alias("current_u", lat, lon)
                v = self._extract_alias("current_v", lat, lon)
                cs = self._extract_alias("current_speed", lat, lon)
                cd = self._extract_alias("current_direction", lat, lon)

                if u and v:
                    df = pd.concat([u["series"].rename("U_current"), v["series"].rename("V_current")], axis=1)
                    df["CurrentSpeed"] = speed_from_uv(df["U_current"], df["V_current"])
                    df["CurrentDir_to_deg"] = oceanographic_to_direction(df["U_current"], df["V_current"])
                    location = u
                elif cs and cd:
                    df = pd.concat([cs["series"].rename("CurrentSpeed"), cd["series"].rename("CurrentDir_to_deg")], axis=1)
                    location = cs
                else:
                    raise ValueError(
                        "No se hallaron componentes de corriente. "
                        "GFS-Wave no debe asumirse como fuente de corrientes; "
                        "use GRIB2/RTOFS/HYCOM que contenga UOGRD/VOGRD."
                    )

            self.point_df = df.sort_index()
            if location:
                self.point_info.config(
                    text=f"{product}: punto solicitado ({lat:.4f}, {lon:.4f}) | "
                         f"malla usada ({location['actual_lat']:.4f}, {location['actual_lon']:.4f}) | "
                         f"{len(df)} muestras"
                )
            self.log(f"Punto extraído: {product}, {len(df)} muestras")
            self.nb.select(self.tab_analysis)
            self.make_timeseries()
        except Exception as exc:
            messagebox.showerror("Extracción", str(exc))
            self.log(f"ERROR extracción: {exc}")

    def _show_figure(self, fig):
        for child in self.plot_frame.winfo_children():
            child.destroy()
        self.current_figure = fig
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def make_rose(self):
        if self.point_df.empty:
            messagebox.showwarning("Rosa", "Extraiga primero un punto.")
            return
        try:
            product = self.product_var.get()
            if product == "Viento":
                dcol, mcol, title = "WindDir_from_deg", "WindSpeed", "Rosa de vientos"
            elif product == "Oleaje":
                dcol = "WaveDir_deg"
                if "Hs_m" in self.point_df:
                    mcol = "Hs_m"
                elif "Period_s" in self.point_df:
                    mcol = "Period_s"
                else:
                    raise ValueError("Se requiere magnitud de oleaje (Hs o periodo).")
                title = "Rosa direccional de oleaje"
            else:
                dcol, mcol, title = "CurrentDir_to_deg", "CurrentSpeed", "Rosa de corrientes"

            if dcol not in self.point_df or mcol not in self.point_df:
                raise ValueError(f"Faltan columnas {dcol}/{mcol}.")
            fig = plot_directional_rose(self.point_df[dcol], self.point_df[mcol], title)
            self._show_figure(fig)
        except Exception as exc:
            messagebox.showerror("Rosa", str(exc))

    def make_timeseries(self):
        if self.point_df.empty:
            messagebox.showwarning("Serie", "Extraiga primero un punto.")
            return
        cols = list(self.point_df.columns)
        fig = plot_timeseries(self.point_df, cols, f"{self.product_var.get()} - serie temporal")
        self._show_figure(fig)

    def export_csv(self):
        if self.point_df.empty:
            messagebox.showwarning("CSV", "No hay datos extraídos.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV","*.csv")],
            initialfile="punto_hidrooceanografico.csv"
        )
        if path:
            self.point_df.to_csv(path, index=True)
            self.log(f"CSV exportado: {path}")

    def save_figure(self):
        if self.current_figure is None:
            messagebox.showwarning("Figura", "No hay una figura activa.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG","*.png"),("PDF","*.pdf")],
            initialfile="grafico_hidrooceanografico.png"
        )
        if path:
            self.current_figure.savefig(path, dpi=200, bbox_inches="tight")
            self.log(f"Figura guardada: {path}")

    def download_noaa(self):
        try:
            params = tuple(k for k,v in self.param_vars.items() if v.get())
            if not params:
                raise ValueError("Seleccione al menos un parámetro.")

            req = GFSWaveRequest(
                date=self.noaa_vars["Fecha YYYYMMDD"].get().strip(),
                cycle=self.noaa_vars["Ciclo"].get().strip().zfill(2),
                forecast_hour=int(self.noaa_vars["Pronóstico (h)"].get()),
                north=float(self.noaa_vars["Norte"].get()),
                south=float(self.noaa_vars["Sur"].get()),
                west=float(self.noaa_vars["Oeste"].get()),
                east=float(self.noaa_vars["Este"].get()),
                parameters=params,
            )
            if req.cycle not in {"00","06","12","18"}:
                raise ValueError("Ciclo válido: 00, 06, 12 o 18.")
            if req.north <= req.south:
                raise ValueError("Norte debe ser mayor que Sur.")

            self.log("Iniciando descarga GFS-Wave...")
            self.log(f"Fecha={req.date} ciclo={req.cycle} f={req.forecast} params={params}")

            def job():
                try:
                    out = download_gfswave(req, "data/downloads")
                    self.after(0, lambda: self._download_done(out))
                except Exception as exc:
                    self.after(0, lambda: self._download_error(str(exc)))

            threading.Thread(target=job, daemon=True).start()
        except Exception as exc:
            messagebox.showerror("NOAA", str(exc))

    def _download_done(self, out):
        self.log(f"Descarga completada: {out}")
        messagebox.showinfo("NOAA", f"GRIB2 descargado:\n{out}")
        try:
            self.reader.open(out)
            self.loaded_path = Path(out)
            self.file_label.config(text=self.loaded_path.name)
            self._populate_inventory()
            self.nb.select(self.tab_inventory)
        except Exception as exc:
            self.log(f"Descargado, pero no pudo abrirse automáticamente: {exc}")

    def _download_error(self, text):
        self.log(f"ERROR NOAA: {text}")
        messagebox.showerror("NOAA / NOMADS", text)
