import sys
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox
from GDLogin import Ui_Dialog
import database

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.BtnLogin.clicked.connect(self.check_login)

    def check_login(self):
        username = self.ui.lineEdit.text()
        password = self.ui.lineEdit_2.text()
        
        users = database.fetch_query("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        if len(users) > 0:
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Sai tài khoản hoặc mật khẩu!")

if __name__ == "__main__":
    database.init_db()
    app = QApplication(sys.argv)
    window = LoginDialog()
    if window.exec() == QDialog.DialogCode.Accepted:
        print("Login successful")
    sys.exit()