"""
controllers/login_controller.py
"""
from PyQt6 import QtWidgets
from views.Login import Ui_Dialog
from models.user_model import UserModel
from utils.helpers import msg_error, msg_warn


class LoginWindow(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self._main_window = None

        self.ui.BtnLogin.clicked.connect(self._login)
        self.ui.inp_password.returnPressed.connect(self._login)
        self.ui.inp_username.returnPressed.connect(self.ui.inp_password.setFocus)

    def _login(self):
        username = self.ui.inp_username.text().strip()
        password = self.ui.inp_password.text().strip()

        if not username or not password:
            msg_warn(self, "Vui lòng nhập đầy đủ thông tin đăng nhập!")
            return

        user = UserModel.login(username, password)
        if user is None:
            msg_error(self, "Tên đăng nhập hoặc mật khẩu không chính xác!")
            self.ui.inp_password.clear()
            self.ui.inp_password.setFocus()
            return

        UserModel.log_activity(user["id"], "Đăng nhập")
        self._open_main(user)

    def _open_main(self, user: dict):
        if user["role"] == "admin":
            from controllers.admin_controller import AdminWindow
            self._main_window = AdminWindow(user)
        else:
            from controllers.staff_controller import StaffWindow
            self._main_window = StaffWindow(user)

        self._main_window.show()

        # Đóng login SAU khi cửa sổ chính đã hiển thị
        self.close()