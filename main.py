import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from src.gui.main_window import MainWindow
from src.utils.paths import resource_path

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("HydroOcean GRIB Studio")
    app.setOrganizationName("Tecprog World E.I.R.L.")
    app.setOrganizationDomain("tecprog-world")
    icon = resource_path("src/logo-tecprog-world.png")
    if icon.exists():
        app.setWindowIcon(QIcon(str(icon)))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
