import sys
import sqlite3
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QTableWidgetItem


class StartWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)
        self.setWindowTitle("Библиотека")
        self.con = sqlite3.connect("library.db")
        self.cur = self.con.cursor()
        self.loadTable()

    def loadTable(self):
        result = self.cur.execute("SELECT * FROM Books").fetchall()
        self.tableWidget.setRowCount(len(result))
        self.tableWidget.setColumnCount(len(result[0]))
        for i, elem in enumerate(result):
            for j, val in enumerate(elem):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))

    def add_book(self):
        pass

    def search_book(self):
        pass


app = QApplication(sys.argv)
ex = StartWidget()
ex.show()
sys.exit(app.exec_())
