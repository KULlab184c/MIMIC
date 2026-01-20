import sys
import os
from PyQt6.QtWidgets import QApplication
from src.gui.main_window import MainWindow
import InitializeMIMIC

if __name__ == "__main__":

    app = QApplication(sys.argv)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())
