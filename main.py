import sys
from PyQt6 import QtWidgets
from GDAdmin import Ui_MainWindow
from mainLogin import LoginDialog
import database


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Sidebar buttons in page order
        # 0=Dashboard, 1=Phòng, 2=Khách, 3=Thuê phòng, 4=Dịch vụ, 5=Hóa đơn, 6=Báo cáo
        self.buttons = [
            self.ui.BtnDashBoard,
            self.ui.BtnRoom,
            self.ui.BtnCustomer,
            self.ui.BtnAddRoom,
            self.ui.BtnSerVice,
            self.ui.BtnInvoice,
            self.ui.BtnReport,
        ]

        for i, btn in enumerate(self.buttons):
            btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))

        self.ui.Btnlog.clicked.connect(self.logout)
        self.ui.btn_submit_room.clicked.connect(self.add_room)

        self.switch_page(0)
        self.load_dashboard_stats()

    # ── Page switching ──────────────────────────────────────────────────
    def switch_page(self, index):
        self.ui.stackedWidget.setCurrentIndex(index)
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == index)

        if index == 1:
            self.load_rooms()
        elif index == 2:
            self.load_customers()

    # ── Dashboard stats ─────────────────────────────────────────────────
    def load_dashboard_stats(self):
        try:
            total   = database.fetch_query("SELECT COUNT(*) FROM rooms")[0][0]
            vacant  = database.fetch_query("SELECT COUNT(*) FROM rooms WHERE status='Trống'")[0][0]
            rented  = database.fetch_query("SELECT COUNT(*) FROM rooms WHERE status='Đang thuê'")[0][0]
            booked  = database.fetch_query("SELECT COUNT(*) FROM rooms WHERE status='Đã đặt'")[0][0]
            revenue_row = database.fetch_query("SELECT SUM(total_amount) FROM invoices")
            revenue = revenue_row[0][0] if revenue_row and revenue_row[0][0] else 0
        except Exception:
            total = vacant = rented = booked = revenue = 0

        def set_val(card, val):
            # The value label is the first label in the card's layout
            lbl = card.layout().itemAt(0).widget()
            lbl.setText(str(val))

        set_val(self.ui.card_total,   f"{total}")
        set_val(self.ui.card_vacant,  f"{vacant}")
        set_val(self.ui.card_rented,  f"{rented}")
        set_val(self.ui.card_booked,  f"{booked}")
        set_val(self.ui.card_revenue, f"{int(revenue):,} VNĐ")

    # ── Room list ───────────────────────────────────────────────────────
    def load_rooms(self):
        rooms = database.fetch_query(
            "SELECT id, room_number, type, price, status FROM rooms"
        )
        self.ui.tbl_rooms.setRowCount(len(rooms))
        for row_idx, row_data in enumerate(rooms):
            for col_idx, item in enumerate(row_data):
                self.ui.tbl_rooms.setItem(
                    row_idx, col_idx, QtWidgets.QTableWidgetItem(str(item))
                )

    # ── Customer list ───────────────────────────────────────────────────
    def load_customers(self):
        customers = database.fetch_query(
            "SELECT id, name, identity_card, phone FROM customers"
        )
        self.ui.tbl_customers.setRowCount(len(customers))
        for row_idx, row_data in enumerate(customers):
            for col_idx, item in enumerate(row_data):
                self.ui.tbl_customers.setItem(
                    row_idx, col_idx, QtWidgets.QTableWidgetItem(str(item))
                )

    # ── Add / rent room ─────────────────────────────────────────────────
    def add_room(self):
        room_num  = self.ui.in_room_num.text().strip()
        room_type = self.ui.in_room_type.currentText()
        price     = self.ui.in_room_price.text().strip()

        if not room_num or not price:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đủ thông tin!")
            return

        try:
            database.execute_query(
                "INSERT INTO rooms (room_number, type, price) VALUES (?, ?, ?)",
                (room_num, room_type, float(price))
            )
            QtWidgets.QMessageBox.information(self, "Thành công", "Thêm phòng thành công!")
            self.ui.in_room_num.clear()
            self.ui.in_room_price.clear()
            self.load_dashboard_stats()
            self.switch_page(1)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Lỗi", f"Không thể thêm (phòng đã tồn tại?): {e}")

    # ── Logout ──────────────────────────────────────────────────────────
    def logout(self):
        self.close()
        login = LoginDialog()
        if login.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.__init__()
            self.show()


# ════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    database.init_db()
    app = QtWidgets.QApplication(sys.argv)

    login = LoginDialog()
    if login.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        window = MainWindow()
        window.show()
        sys.exit(app.exec())