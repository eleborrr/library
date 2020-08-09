import sys
import sqlite3
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QTableWidgetItem


class StartWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)

    def loadTable(self):
        pass

    def add_book(self):
        pass

    def search_book(self):
        pass


app = QApplication(sys.argv)
ex = StartWidget()
ex.show()
sys.exit(app.exec_())
