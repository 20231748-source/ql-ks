import sys
import sqlite3
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem
from Staff import Ui_StaffWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_StaffWindow()
        self.ui.setupUi(self)
        
        self.ui.stackedWidget.setCurrentIndex(0)
        
        # Navigation
        self.ui.BtnCheckIn.clicked.connect(lambda: self.switch_page(0))
        self.ui.btnCheckOut.clicked.connect(lambda: self.switch_page(1))
        self.ui.BtnList.clicked.connect(lambda: self.switch_page(2))
        self.ui.BtnService.clicked.connect(lambda: self.switch_page(3))
        self.ui.BtnInvoice.clicked.connect(lambda: self.switch_page(4))
        self.ui.BtnAcccount.clicked.connect(lambda: self.switch_page(5))
        
        # Logout logic
        try:
            self.ui.BtnLogOut.clicked.connect(self.logout)
        except: pass

        self.load_checkouts()
        self.load_rooms()
        self.load_services()
        self.load_invoices()
        
    def switch_page(self, index):
        self.ui.stackedWidget.setCurrentIndex(index)
        if index == 1:
            self.load_checkouts()
        elif index == 2:
            self.load_rooms()
        elif index == 3:
            self.load_services()
        elif index == 4:
            self.load_invoices()

    def load_checkouts(self):
        try:
            conn = sqlite3.connect("hotel.db")
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DatPhong.Room_ID, KhachHang.Name, DatPhong.CheckIn, DatPhong.CheckOut, '', ''
                FROM DatPhong
                JOIN KhachHang ON DatPhong.Customer_ID = KhachHang.Customer_ID
            ''')
            records = cursor.fetchall()
            self.ui.tableWidget.setRowCount(0)
            for row_idx, row_data in enumerate(records):
                self.ui.tableWidget.insertRow(row_idx)
                for col_idx, data in enumerate(row_data):
                    self.ui.tableWidget.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))
            conn.close()
        except: pass

    def load_rooms(self):
        try:
            conn = sqlite3.connect("hotel.db")
            cursor = conn.cursor()
            cursor.execute("SELECT Room_ID, Type, '1', Price, Status FROM Phong")
            records = cursor.fetchall()
            self.ui.tableWidget_2.setRowCount(0)
            for row_idx, row_data in enumerate(records):
                self.ui.tableWidget_2.insertRow(row_idx)
                for col_idx, data in enumerate(row_data):
                    self.ui.tableWidget_2.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))
            conn.close()
        except: pass
        
    def load_services(self):
        try:
            conn = sqlite3.connect("hotel.db")
            cursor = conn.cursor()
            cursor.execute("SELECT Name, '1', Price, Price FROM DichVu")
            records = cursor.fetchall()
            self.ui.tableWidget_4.setRowCount(0)
            for row_idx, row_data in enumerate(records):
                self.ui.tableWidget_4.insertRow(row_idx)
                for col_idx, data in enumerate(row_data):
                    self.ui.tableWidget_4.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))
            conn.close()
        except: pass

    def load_invoices(self):
        pass # Handle invoice data

    def logout(self):
        self.hide()
        from mainLogin import LoginDialog
        self.login_window = LoginDialog()
        self.login_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())