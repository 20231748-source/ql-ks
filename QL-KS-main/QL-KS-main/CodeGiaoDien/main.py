import sys
import sqlite3
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt
from GDAdmin import Ui_MainWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.ui.stackedWidget.setCurrentIndex(0)
        
        # Navigation
        self.ui.BtnDashBoard.clicked.connect(lambda: self.switch_page(0))
        self.ui.BtnRoom.clicked.connect(lambda: self.switch_page(1))
        self.ui.BtnCustomer.clicked.connect(lambda: self.switch_page(2))
        self.ui.BtnStaff.clicked.connect(lambda: self.switch_page(3))
        self.ui.BtnAddRoom.clicked.connect(lambda: self.switch_page(4))
        self.ui.BtnSerVice.clicked.connect(lambda: self.switch_page(5))
        self.ui.BtnReport.clicked.connect(lambda: self.switch_page(6))

        # Logout
        try:
            self.ui.Btnlog.clicked.connect(self.logout)
        except: pass
        
        self.load_rooms()
        self.load_customers()
        self.load_staff()
        self.load_bookings()
        self.load_services()

    def switch_page(self, index):
        self.ui.stackedWidget.setCurrentIndex(index)
        if index == 1:
            self.load_rooms()
        elif index == 2:
            self.load_customers()
        elif index == 3:
            self.load_staff()
        elif index == 4:
            self.load_bookings()
        elif index == 5:
            self.load_services()

    # --- Loading Methods ---
    def load_rooms(self):
        try:
            conn = sqlite3.connect("hotel.db")
            cursor = conn.cursor()
            cursor.execute("SELECT Room_ID, Type, Price, Status FROM Phong")
            records = cursor.fetchall()
            self.ui.tableWidget_6.setRowCount(0)
            for row_idx, row_data in enumerate(records):
                self.ui.tableWidget_6.insertRow(row_idx)
                for col_idx, data in enumerate(row_data):
                    self.ui.tableWidget_6.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))
            conn.close()
        except Exception as e: print("Room err:", e)

    def load_customers(self):
        try:
            conn = sqlite3.connect("hotel.db")
            cursor = conn.cursor()
            cursor.execute("SELECT Customer_ID, Name, Phone, CCCD, '', '' FROM KhachHang")
            records = cursor.fetchall()
            self.ui.tableWidget_2.setRowCount(0)
            for row_idx, row_data in enumerate(records):
                self.ui.tableWidget_2.insertRow(row_idx)
                for col_idx, data in enumerate(row_data):
                    self.ui.tableWidget_2.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))
            conn.close()
        except Exception as e: print("Cus err:", e)

    def load_staff(self):
        try:
            conn = sqlite3.connect("hotel.db")
            cursor = conn.cursor()
            cursor.execute("SELECT Username, '', Username, '', Role, 'Active' FROM TaiKhoan")
            records = cursor.fetchall()
            self.ui.tableWidget_3.setRowCount(0)
            for row_idx, row_data in enumerate(records):
                self.ui.tableWidget_3.insertRow(row_idx)
                for col_idx, data in enumerate(row_data):
                    self.ui.tableWidget_3.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))
            conn.close()
        except Exception as e: print("Staff err:", e)

    def load_services(self):
        try:
            conn = sqlite3.connect("hotel.db")
            cursor = conn.cursor()
            cursor.execute("SELECT Name, Price, 'VND', 'Active' FROM DichVu")
            records = cursor.fetchall()
            self.ui.tableWidget_4.setRowCount(0)
            for row_idx, row_data in enumerate(records):
                self.ui.tableWidget_4.insertRow(row_idx)
                for col_idx, data in enumerate(row_data):
                    self.ui.tableWidget_4.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))
            conn.close()
        except Exception as e: print("Service err:", e)

    def load_bookings(self):
        try:
            conn = sqlite3.connect("hotel.db")
            cursor = conn.cursor()
            cursor.execute('''
                SELECT KhachHang.Customer_ID, KhachHang.Name, DatPhong.Room_ID, DatPhong.CheckIn, DatPhong.Status 
                FROM DatPhong
                JOIN KhachHang ON DatPhong.Customer_ID = KhachHang.Customer_ID
            ''')
            records = cursor.fetchall()
            self.ui.tableWidget_5.setRowCount(0)
            for row_idx, row_data in enumerate(records):
                self.ui.tableWidget_5.insertRow(row_idx)
                for col_idx, data in enumerate(row_data):
                    self.ui.tableWidget_5.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))
            conn.close()
        except Exception as e: print("Book err:", e)

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