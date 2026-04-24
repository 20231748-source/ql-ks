import sys
import sqlite3
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox
from GDLogin import Ui_Dialog

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        # Configure password echo mode
        self.ui.lineEdit_2.setEchoMode(self.ui.lineEdit_2.EchoMode.Password)
        
        # Connect login button
        self.ui.BtnLogin.clicked.connect(self.handle_login)
        
    def handle_login(self):
        username = self.ui.lineEdit.text().strip()
        password = self.ui.lineEdit_2.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ thông tin!")
            return
            
        try:
            conn = sqlite3.connect("hotel.db")
            cursor = conn.cursor()
            cursor.execute("SELECT Role FROM TaiKhoan WHERE Username=? AND Password=?", (username, password))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                role = result[0]
                QMessageBox.information(self, "Thành công", f"Đăng nhập thành công với quyền {role}!")
                self.hide()
                if role == "Admin":
                    from main import MainWindow as AdminWindow
                    self.main_window = AdminWindow()
                    self.main_window.show()
                else:
                    from mainstaff import MainWindow as StaffWindow
                    self.main_window = StaffWindow()
                    self.main_window.show()
            else:
                QMessageBox.warning(self, "Thất bại", "Tên đăng nhập hoặc mật khẩu không đúng!")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi DB", f"Không thể kết nối cơ sở dữ liệu: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginDialog()
    window.show()
    sys.exit(app.exec())