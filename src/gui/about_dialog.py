from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from src.utils.paths import resource_path

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Acerca de HydroOcean GRIB Studio")
        self.resize(540, 560)
        layout = QVBoxLayout(self)

        logo = QLabel()
        p = resource_path("src/logo-tecprog-world.png")
        if p.exists():
            pix = QPixmap(str(p))
            logo.setPixmap(pix.scaled(360, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        title = QLabel(
            "<h2>HydroOcean GRIB Studio v0.2.0</h2>"
            "<h3>Tecprog World E.I.R.L.</h3>"
        )
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        body = QLabel(
            "<p>Herramienta para lectura, adquisición y análisis de información "
            "GRIB2 aplicada a estudios hidro-oceanográficos.</p>"
            "<p><b>Correo:</b> grupotecprog@gmail.com<br>"
            "<b>WhatsApp:</b> +51 952 354 282</p>"
            "<p><b>Apoyo al mantenimiento del proyecto</b><br>"
            "Perú — Yape: +51 952 354 282<br>"
            "Internacional — PayPal: coordinación mediante correo electrónico.</p>"
            "<p>Si requiere adaptación a un estudio, automatización de descargas, "
            "reportes, nuevos modelos oceanográficos o desarrollo personalizado, "
            "puede contactar a Tecprog World E.I.R.L.</p>"
        )
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(body)

        row = QHBoxLayout()
        mail = QPushButton("Escribir correo")
        mail.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("mailto:grupotecprog@gmail.com"))
        )
        row.addWidget(mail)
        close = QPushButton("Cerrar")
        close.clicked.connect(self.accept)
        row.addWidget(close)
        layout.addLayout(row)
