from __future__ import annotations
from pathlib import Path
from datetime import datetime
import webbrowser

import pandas as pd
from PySide6.QtCore import Qt, QDate, QThread
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QFileDialog, QMessageBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QGroupBox, QDateEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QProgressBar,
    QPlainTextEdit, QScrollArea, QToolBar
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

from src.utils.paths import resource_path, user_data_dir
from src.grib.reader import GribFile
from src.grib.collection import list_gribs, build_product_series
from src.plots.charts import time_series_figure, rose_figure
from src.acquisition.nomads import (
    Domain, DEFAULT_VARS, download_forecast_run, download_analysis_range
)
from src.gui.workers import FunctionWorker
from src.gui.about_dialog import AboutDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HydroOcean GRIB Studio 0.2 — Tecprog World E.I.R.L.")
        self.resize(1450, 860)
        self.setMinimumSize(980, 650)

        self.current_file = None
        self.current_folder = None
        self.paths = []
        self.series = pd.DataFrame()
        self.figure = None
        self.thread = None
        self.worker = None

        self._menu()
        self._toolbar()
        self._ui()
        self.statusBar().showMessage("Listo — Tecprog World E.I.R.L.")

    # ---------------- MENU ----------------
    def _menu(self):
        mfile = self.menuBar().addMenu("&Archivo")
        aopen = QAction("Abrir GRIB2...", self)
        aopen.setShortcut("Ctrl+O")
        aopen.triggered.connect(self.open_file)
        mfile.addAction(aopen)

        afolder = QAction("Abrir carpeta GRIB2...", self)
        afolder.setShortcut("Ctrl+Shift+O")
        afolder.triggered.connect(self.open_folder)
        mfile.addAction(afolder)
        mfile.addSeparator()

        aexport = QAction("Exportar serie CSV...", self)
        aexport.triggered.connect(self.export_csv)
        mfile.addAction(aexport)

        asave = QAction("Guardar gráfico...", self)
        asave.triggered.connect(self.save_chart)
        mfile.addAction(asave)
        mfile.addSeparator()

        aquit = QAction("Salir", self)
        aquit.triggered.connect(self.close)
        mfile.addAction(aquit)

        macq = self.menuBar().addMenu("&Adquisición")
        agfs = QAction("GFS-Wave operacional", self)
        agfs.triggered.connect(lambda: self.tabs.setCurrentWidget(self.tab_download))
        macq.addAction(agfs)
        ah = QAction("WAVEWATCH III histórico", self)
        ah.triggered.connect(lambda: self.tabs.setCurrentWidget(self.tab_history))
        macq.addAction(ah)

        man = self.menuBar().addMenu("&Análisis")
        ats = QAction("Construir serie temporal", self)
        ats.triggered.connect(self.build_series)
        man.addAction(ats)
        ar = QAction("Rosa direccional", self)
        ar.triggered.connect(self.make_rose)
        man.addAction(ar)

        mh = self.menuBar().addMenu("A&yuda")
        adocs = QAction("Fuentes NOAA / documentación", self)
        adocs.triggered.connect(
            lambda: webbrowser.open("https://polar.ncep.noaa.gov/waves/download2.shtml")
        )
        mh.addAction(adocs)
        aabout = QAction("Acerca de Tecprog World...", self)
        aabout.triggered.connect(lambda: AboutDialog(self).exec())
        mh.addAction(aabout)

    def _toolbar(self):
        tb = QToolBar("Principal")
        tb.setMovable(False)
        self.addToolBar(tb)
        for text, fn in [
            ("Abrir GRIB2", self.open_file),
            ("Abrir carpeta", self.open_folder),
            ("Construir serie", self.build_series),
            ("Exportar CSV", self.export_csv),
        ]:
            a = QAction(text, self)
            a.triggered.connect(fn)
            tb.addAction(a)

    # ---------------- UI ----------------
    def _ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(8,8,8,8)

        header = QHBoxLayout()
        logo = QLabel()
        p = resource_path("src/logo-tecprog-world.png")
        if p.exists():
            pix = QPixmap(str(p))
            logo.setPixmap(pix.scaled(180, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header.addWidget(logo)
        title = QLabel(
            "<b>HydroOcean GRIB Studio</b><br>"
            "<span style='color:#555'>Tecprog World E.I.R.L. · Ingeniería de datos hidro-oceanográficos</span>"
        )
        header.addWidget(title)
        header.addStretch(1)
        root.addLayout(header)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        self.tab_analysis = QWidget()
        self.tab_inventory = QWidget()
        self.tab_download = QWidget()
        self.tab_history = QWidget()
        self.tab_log = QWidget()
        self.tabs.addTab(self.tab_analysis, "Análisis")
        self.tabs.addTab(self.tab_inventory, "Inventario")
        self.tabs.addTab(self.tab_download, "GFS-Wave operacional")
        self.tabs.addTab(self.tab_history, "Histórico")
        self.tabs.addTab(self.tab_log, "Registro")

        self._analysis_ui()
        self._inventory_ui()
        self._download_ui()
        self._history_ui()
        self._log_ui()
        self.setCentralWidget(central)

    def _analysis_ui(self):
        layout = QHBoxLayout(self.tab_analysis)
        split = QSplitter(Qt.Horizontal)
        layout.addWidget(split)

        side = QWidget()
        side.setMinimumWidth(300)
        side.setMaximumWidth(410)
        form = QVBoxLayout(side)

        grp = QGroupBox("Punto virtual")
        gf = QFormLayout(grp)
        self.lat = QDoubleSpinBox()
        self.lat.setRange(-90,90); self.lat.setDecimals(5); self.lat.setValue(-12.0)
        self.lon = QDoubleSpinBox()
        self.lon.setRange(-180,180); self.lon.setDecimals(5); self.lon.setValue(-77.5)
        self.product = QComboBox()
        self.product.addItems(["Oleaje", "Viento", "Corrientes"])
        gf.addRow("Latitud:", self.lat)
        gf.addRow("Longitud:", self.lon)
        gf.addRow("Producto:", self.product)
        form.addWidget(grp)

        self.source_label = QLabel("Fuente: todavía no seleccionada")
        self.source_label.setWordWrap(True)
        form.addWidget(self.source_label)

        b1 = QPushButton("Construir serie temporal")
        b1.clicked.connect(self.build_series)
        form.addWidget(b1)
        b2 = QPushButton("Rosa direccional")
        b2.clicked.connect(self.make_rose)
        form.addWidget(b2)
        b3 = QPushButton("Exportar CSV")
        b3.clicked.connect(self.export_csv)
        form.addWidget(b3)
        form.addStretch(1)
        split.addWidget(side)

        self.chart_host = QWidget()
        self.chart_layout = QVBoxLayout(self.chart_host)
        self.chart_message = QLabel(
            "Seleccione un GRIB2 o una carpeta con varios GRIB2.\n\n"
            "Para una serie temporal real se requieren múltiples instantes."
        )
        self.chart_message.setAlignment(Qt.AlignCenter)
        self.chart_layout.addWidget(self.chart_message)
        split.addWidget(self.chart_host)
        split.setStretchFactor(1, 1)

    def _inventory_ui(self):
        layout = QVBoxLayout(self.tab_inventory)
        self.inventory = QTableWidget(0, 7)
        self.inventory.setHorizontalHeaderLabels(
            ["dataset","variable","shortName","long_name","units","dims","shape"]
        )
        self.inventory.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.inventory.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.inventory)

    def _download_ui(self):
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        container = QWidget()
        l = QVBoxLayout(container)

        info = QLabel(
            "<b>GFS-Wave operacional / NOMADS</b><br>"
            "Permite descargar una corrida completa de pronóstico o varios f000 por fechas/ciclos. "
            "La retención NOAA es corta (~9 días); no usar esta pestaña para años históricos."
        )
        info.setWordWrap(True)
        l.addWidget(info)

        g = QGroupBox("Dominio y variables")
        grid = QGridLayout(g)
        self.north = QDoubleSpinBox(); self.north.setRange(-90,90); self.north.setValue(1)
        self.south = QDoubleSpinBox(); self.south.setRange(-90,90); self.south.setValue(-20)
        self.west = QDoubleSpinBox(); self.west.setRange(-180,360); self.west.setValue(-90)
        self.east = QDoubleSpinBox(); self.east.setRange(-180,360); self.east.setValue(-68)
        grid.addWidget(QLabel("Norte"),0,0); grid.addWidget(self.north,0,1)
        grid.addWidget(QLabel("Sur"),1,0); grid.addWidget(self.south,1,1)
        grid.addWidget(QLabel("Oeste"),0,2); grid.addWidget(self.west,0,3)
        grid.addWidget(QLabel("Este"),1,2); grid.addWidget(self.east,1,3)

        self.var_checks = {}
        for i, v in enumerate(DEFAULT_VARS):
            cb = QCheckBox(v); cb.setChecked(True)
            self.var_checks[v] = cb
            grid.addWidget(cb, 2+i//4, i%4)
        l.addWidget(g)

        run = QGroupBox("A. Corrida de pronóstico → serie temporal")
        f = QFormLayout(run)
        self.run_date = QDateEdit(QDate.currentDate())
        self.run_date.setCalendarPopup(True)
        self.run_cycle = QComboBox(); self.run_cycle.addItems(["00","06","12","18"])
        self.fstart = QSpinBox(); self.fstart.setRange(0,384); self.fstart.setValue(0)
        self.fend = QSpinBox(); self.fend.setRange(0,384); self.fend.setValue(120)
        self.fstep = QSpinBox(); self.fstep.setRange(1,24); self.fstep.setValue(3)
        f.addRow("Fecha:", self.run_date)
        f.addRow("Ciclo UTC:", self.run_cycle)
        f.addRow("f inicial:", self.fstart)
        f.addRow("f final:", self.fend)
        f.addRow("Paso (h):", self.fstep)
        br = QPushButton("Descargar corrida completa")
        br.clicked.connect(self.download_run)
        f.addRow(br)
        l.addWidget(run)

        rng = QGroupBox("B. Rango operacional → f000 de varios ciclos")
        rf = QFormLayout(rng)
        self.range_start = QDateEdit(QDate.currentDate().addDays(-2)); self.range_start.setCalendarPopup(True)
        self.range_end = QDateEdit(QDate.currentDate()); self.range_end.setCalendarPopup(True)
        self.cycles_line = QLineEdit("00,06,12,18")
        rf.addRow("Fecha inicial:", self.range_start)
        rf.addRow("Fecha final:", self.range_end)
        rf.addRow("Ciclos:", self.cycles_line)
        bb = QPushButton("Descargar rango operacional")
        bb.clicked.connect(self.download_range)
        rf.addRow(bb)
        l.addWidget(rng)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        l.addWidget(self.progress)
        self.download_status = QLabel("")
        self.download_status.setWordWrap(True)
        l.addWidget(self.download_status)
        l.addStretch(1)

        sc.setWidget(container)
        lay = QVBoxLayout(self.tab_download)
        lay.addWidget(sc)

    def _history_ui(self):
        l = QVBoxLayout(self.tab_history)
        title = QLabel(
            "<h2>WAVEWATCH III — archivos históricos</h2>"
            "<p>Para rangos de años no debe consultarse NOMADS operacional.</p>"
        )
        title.setWordWrap(True)
        l.addWidget(title)

        txt = QLabel(
            "<b>1. CFSR/CFSRR hindcast 1979–2009</b><br>"
            "Simulación homogénea con una misma configuración y forzamiento de reanálisis; "
            "es la opción preferible cuando el objetivo es climatología de largo plazo.<br><br>"
            "<b>2. Production Hindcast 2005-02–2019-05</b><br>"
            "Archivos mensuales GRIB2 almacenados por NCEI. NOAA indica que la serie es "
            "estadísticamente inhomogénea porque los modelos operacionales fueron cambiando.<br><br>"
            "<b>Importante:</b> descargar años completos de campos globales puede implicar "
            "decenas o cientos de GB. Para un producto de ingeniería conviene implementar "
            "extracción por punto o dominio y caché local, no una descarga indiscriminada."
        )
        txt.setWordWrap(True)
        l.addWidget(txt)

        row = QHBoxLayout()
        b1 = QPushButton("Abrir CFSR 1979–2009")
        b1.clicked.connect(lambda: webbrowser.open("https://polar.ncep.noaa.gov/waves/CFSR_hindcast.shtml"))
        row.addWidget(b1)
        b2 = QPushButton("Abrir NCEI 2005–2019")
        b2.clicked.connect(lambda: webbrowser.open("https://www.ncei.noaa.gov/archive/accession/NCEP-WAVEWATCH"))
        row.addWidget(b2)
        l.addLayout(row)

        self.hist_start = QDateEdit(QDate(2005,2,1)); self.hist_start.setCalendarPopup(True)
        self.hist_end = QDateEdit(QDate(2019,5,31)); self.hist_end.setCalendarPopup(True)
        form = QFormLayout()
        form.addRow("Inicio del estudio:", self.hist_start)
        form.addRow("Fin del estudio:", self.hist_end)
        l.addLayout(form)

        bp = QPushButton("Generar plan mensual CSV")
        bp.clicked.connect(self.historical_plan)
        l.addWidget(bp)
        l.addStretch(1)

    def _log_ui(self):
        l = QVBoxLayout(self.tab_log)
        self.logbox = QPlainTextEdit()
        self.logbox.setReadOnly(True)
        l.addWidget(self.logbox)

    # ---------------- Helpers ----------------
    def log(self, msg):
        self.logbox.appendPlainText(
            f"[{datetime.now():%H:%M:%S}] {msg}"
        )

    def domain(self):
        return Domain(
            self.north.value(), self.south.value(),
            self.west.value(), self.east.value()
        )

    def variables(self):
        return tuple(v for v, cb in self.var_checks.items() if cb.isChecked())

    def open_file(self):
        p, _ = QFileDialog.getOpenFileName(
            self, "Abrir GRIB2", "",
            "GRIB2 (*.grib2 *.grb2 *.grib *.grb);;Todos (*.*)"
        )
        if not p: return
        self.current_file = Path(p)
        self.current_folder = None
        self.paths = [self.current_file]
        self.source_label.setText(f"Fuente: {self.current_file}")
        self.load_inventory(self.current_file)
        self.log(f"GRIB2 abierto: {p}")
        self.tabs.setCurrentWidget(self.tab_inventory)

    def open_folder(self):
        p = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta GRIB2")
        if not p: return
        self.current_folder = Path(p)
        self.current_file = None
        self.paths = list_gribs(p)
        self.source_label.setText(
            f"Fuente: {p}\n{len(self.paths)} archivos GRIB encontrados."
        )
        self.log(f"Carpeta: {p} — {len(self.paths)} GRIB2")
        if self.paths:
            self.load_inventory(self.paths[0])
        self.tabs.setCurrentWidget(self.tab_analysis)

    def load_inventory(self, p):
        try:
            inv = GribFile(p).open().inventory()
            self.inventory.setRowCount(len(inv))
            cols = ["dataset","variable","shortName","long_name","units","dims","shape"]
            for r, (_, row) in enumerate(inv.iterrows()):
                for c, key in enumerate(cols):
                    self.inventory.setItem(r,c,QTableWidgetItem(str(row[key])))
        except Exception as exc:
            QMessageBox.critical(self, "Inventario", str(exc))

    def build_series(self):
        if not self.paths:
            QMessageBox.warning(self, "Serie temporal", "Abra un GRIB2 o una carpeta.")
            return
        self.statusBar().showMessage("Construyendo serie temporal...")
        self.series = build_product_series(
            self.paths, self.lat.value(), self.lon.value(), self.product.currentText()
        )
        if self.series.empty:
            QMessageBox.warning(self, "Serie temporal", "No se obtuvieron muestras válidas.")
            return
        self.log(f"Serie construida: {len(self.series)} muestras.")
        if len(self.series) == 1:
            QMessageBox.information(
                self, "Solo una muestra",
                "El archivo seleccionado contiene un único instante. "
                "Para una serie temporal seleccione una carpeta con múltiples GRIB2 "
                "o descargue una corrida/rango desde GFS-Wave."
            )
        self.show_figure(time_series_figure(self.series, self.product.currentText()))
        self.tabs.setCurrentWidget(self.tab_analysis)
        self.statusBar().showMessage(f"Serie: {len(self.series)} muestras")

    def show_figure(self, fig):
        while self.chart_layout.count():
            item = self.chart_layout.takeAt(0)
            w = item.widget()
            if w: w.deleteLater()
        self.figure = fig
        canvas = FigureCanvasQTAgg(fig)
        self.chart_layout.addWidget(canvas)
        canvas.draw()

    def make_rose(self):
        if self.series.empty:
            self.build_series()
            if self.series.empty: return
        p = self.product.currentText()
        try:
            if p == "Oleaje":
                d, m = "WaveDir_deg", "Hs_m"
            elif p == "Viento":
                d, m = "WindDir_from_deg", "WindSpeed_m_s"
            else:
                d, m = "CurrentDir_to_deg", "CurrentSpeed_m_s"
            if d not in self.series or m not in self.series:
                raise ValueError(f"Faltan {d} / {m}.")
            self.show_figure(rose_figure(self.series[d], self.series[m], f"Rosa de {p.lower()}"))
        except Exception as exc:
            QMessageBox.warning(self, "Rosa direccional", str(exc))

    def export_csv(self):
        if self.series.empty:
            QMessageBox.warning(self, "CSV", "Primero construya una serie.")
            return
        p, _ = QFileDialog.getSaveFileName(
            self, "Exportar CSV",
            str(user_data_dir() / "serie_hidrooceanografica.csv"),
            "CSV (*.csv)"
        )
        if p:
            self.series.to_csv(p)
            self.log(f"CSV: {p}")

    def save_chart(self):
        if self.figure is None:
            QMessageBox.warning(self, "Gráfico", "No existe un gráfico activo.")
            return
        p, _ = QFileDialog.getSaveFileName(
            self, "Guardar gráfico",
            str(user_data_dir() / "grafico.png"),
            "PNG (*.png);;PDF (*.pdf)"
        )
        if p:
            self.figure.savefig(p, dpi=220, bbox_inches="tight")
            self.log(f"Gráfico: {p}")

    # ---------------- Async downloads ----------------
    def _start_worker(self, function, done):
        if self.thread and self.thread.isRunning():
            QMessageBox.warning(self, "Descarga", "Ya existe una descarga en curso.")
            return
        self.thread = QThread(self)
        self.worker = FunctionWorker(function)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._progress)
        self.worker.failed.connect(self._failed)
        self.worker.finished.connect(done)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.start()

    def _progress(self, i, total, text):
        self.progress.setMaximum(total)
        self.progress.setValue(i)
        self.download_status.setText(text)
        self.statusBar().showMessage(text)

    def _failed(self, text):
        self.log("ERROR: " + text)
        QMessageBox.critical(self, "Descarga", text)

    def download_run(self):
        qd = self.run_date.date()
        day = datetime(qd.year(), qd.month(), qd.day()).date()
        out = user_data_dir() / "downloads" / "gfswave"
        def fn(cb):
            return download_forecast_run(
                day, self.run_cycle.currentText(),
                self.fstart.value(), self.fend.value(), self.fstep.value(),
                self.domain(), self.variables(), out, 10, cb
            )
        self._start_worker(fn, self._download_done)

    def download_range(self):
        s = self.range_start.date(); e = self.range_end.date()
        sd = datetime(s.year(), s.month(), s.day()).date()
        ed = datetime(e.year(), e.month(), e.day()).date()
        cycles = [x.strip() for x in self.cycles_line.text().split(",") if x.strip()]
        bad = [x for x in cycles if x not in {"00","06","12","18"}]
        if bad:
            QMessageBox.warning(self, "Ciclos", f"Ciclos inválidos: {bad}")
            return
        out = user_data_dir() / "downloads" / "gfswave"
        def fn(cb):
            return download_analysis_range(
                sd, ed, cycles, self.domain(), self.variables(), out, 10, cb
            )
        self._start_worker(fn, self._download_done)

    def _download_done(self, results):
        ok = [p for p, st, err in results if p]
        errors = [err for p, st, err in results if err]
        self.progress.setValue(self.progress.maximum())
        self.log(f"Descarga: {len(ok)} archivos OK; {len(errors)} errores.")
        for er in errors[:8]:
            self.log("  " + er)

        if ok:
            # Solo usar los archivos de esta operación, no todo el histórico del disco.
            self.paths = [Path(p) for p in ok]
            self.current_folder = self.paths[0].parent
            self.current_file = None
            self.source_label.setText(
                f"Descarga activa: {len(self.paths)} GRIB2\n{self.current_folder}"
            )
            QMessageBox.information(
                self, "Descarga completada",
                f"Archivos válidos: {len(ok)}\nErrores: {len(errors)}\n\n"
                "Ahora se construirá la serie temporal."
            )
            self.build_series()
        else:
            QMessageBox.warning(
                self, "Sin archivos",
                "No se descargaron archivos válidos. Revise Registro. "
                "La fecha puede estar fuera de la retención de NOMADS."
            )

    def historical_plan(self):
        s = self.hist_start.date(); e = self.hist_end.date()
        start = pd.Timestamp(s.year(), s.month(), 1)
        end = pd.Timestamp(e.year(), e.month(), 1)
        months = pd.date_range(start, end, freq="MS")
        rows = []
        for m in months:
            if pd.Timestamp("1979-01-01") <= m <= pd.Timestamp("2009-12-01"):
                recommended = "CFSR/CFSRR hindcast (homogéneo)"
            elif pd.Timestamp("2005-02-01") <= m <= pd.Timestamp("2019-05-01"):
                recommended = "NCEI Production Hindcast (inhomogéneo)"
            else:
                recommended = "Fuera de los archivos WW3 integrados; investigar fuente adicional"
            rows.append({
                "year": m.year, "month": m.month,
                "YYYYMM": m.strftime("%Y%m"),
                "recommended_archive": recommended
            })
        df = pd.DataFrame(rows)
        p, _ = QFileDialog.getSaveFileName(
            self, "Guardar plan histórico",
            str(user_data_dir() / "plan_descarga_historica.csv"),
            "CSV (*.csv)"
        )
        if p:
            df.to_csv(p, index=False)
            self.log(f"Plan histórico: {p}")
            QMessageBox.information(
                self, "Plan histórico",
                f"Se generaron {len(df)} meses.\n\n"
                "Este plan evita solicitar años históricos al NOMADS operacional."
            )
