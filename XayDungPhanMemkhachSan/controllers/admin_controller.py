from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QHeaderView, QSizePolicy
from views.Admin import Ui_MainWindow
from models.room_model import RoomModel
from models.customer_model import CustomerModel
from models.user_model import UserModel
from models.booking_model import BookingModel
from models.service_model import ServiceModel
from models.invoice_model import InvoiceModel
from utils.helpers import (msg_info, msg_warn, msg_error, msg_confirm,
                            fill_table, fmt_money, STATUS_VI)
from utils.export import export_excel, export_pdf


class AdminWindow(QtWidgets.QMainWindow):
    PAGE_DASHBOARD = 0
    PAGE_ROOM      = 1
    PAGE_CUSTOMER  = 2
    PAGE_STAFF     = 3
    PAGE_BOOKING   = 4
    PAGE_SERVICE   = 5
    PAGE_REPORT    = 6

    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.ui   = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Hotel Management – Admin")
        self._sel_room_id     = None
        self._sel_customer_id = None
        self._sel_staff_id    = None
        self._sel_service_id  = None
        self._sel_booking_id  = None
        self._report_data     = []

        self._setup_sidebar()
        self._setup_room_signals()
        self._setup_customer_signals()
        self._setup_staff_signals()
        self._setup_booking_signals()
        self._setup_service_signals()
        self._setup_report_signals()
        self._goto(self.PAGE_DASHBOARD)

        QtCore.QTimer.singleShot(0, self._setup_tables)

    # ── Setup tables ──────────────────────────────────────────────────────────
    def _setup_tables(self):
        self._all_tables = [
            self.ui.tbl_rooms,
            self.ui.tbl_customers,
            self.ui.tbl_staff,
            self.ui.tbl_bookings,
            self.ui.tbl_services,
            self.ui.tbl_dashboard_checkedin,
        ]
        for tbl in self._all_tables:
            h = tbl.horizontalHeader()
            h.setStretchLastSection(False)
            h.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            tbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            # ── FIX: ẩn vertical header (cột số thứ tự mặc định của Qt)
            #    để STT do fill_table tạo ra nằm ngang hàng với header cột ──
            tbl.verticalHeader().setVisible(False)

    def _refresh_table_columns(self):
        if not hasattr(self, '_all_tables'):
            return
        for tbl in self._all_tables:
            tbl.horizontalHeader().resizeSections(QHeaderView.ResizeMode.Stretch)
            tbl.updateGeometry()

    def _set_active_nav(self, index: int):
        nav_map = {
            self.PAGE_DASHBOARD: self.ui.btn_nav_dashboard,
            self.PAGE_ROOM:      self.ui.btn_nav_rooms,
            self.PAGE_CUSTOMER:  self.ui.btn_nav_customers,
            self.PAGE_STAFF:     self.ui.btn_nav_staff,
            self.PAGE_BOOKING:   self.ui.btn_nav_bookings,
            self.PAGE_SERVICE:   self.ui.btn_nav_services,
            self.PAGE_REPORT:    self.ui.btn_nav_report,
        }
        for page, btn in nav_map.items():
            btn.setChecked(page == index)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _setup_sidebar(self):
        self.ui.lbl_current_user.setText(f"👤 {self.user['full_name']}")
        self.ui.sidebar.setStyleSheet("""
QFrame {
    background-color: #1A2A4A;
    border-right: 2px solid #C9A84C;
}
QPushButton {
    background-color: transparent;
    color: #D0C9B8;
    font-size: 14px;
    text-align: left;
    padding: 13px 22px;
    border: none;
    border-left: 3px solid transparent;
}
QPushButton:hover:!checked {
    background-color: #223259;
    color: #FFFFFF;
    border-left: 3px solid #C9A84C;
}
QPushButton:checked {
    background-color: #2C4070;
    color: #FFFFFF;
    border-left: 4px solid #C9A84C;
    font-weight: bold;
}
""")
        self.ui.btn_logout.clicked.connect(self._logout)
        self.ui.btn_nav_dashboard.clicked.connect(lambda: self._goto(self.PAGE_DASHBOARD))
        self.ui.btn_nav_rooms.clicked.connect(lambda: self._goto(self.PAGE_ROOM))
        self.ui.btn_nav_customers.clicked.connect(lambda: self._goto(self.PAGE_CUSTOMER))
        self.ui.btn_nav_staff.clicked.connect(lambda: self._goto(self.PAGE_STAFF))
        self.ui.btn_nav_bookings.clicked.connect(lambda: self._goto(self.PAGE_BOOKING))
        self.ui.btn_nav_services.clicked.connect(lambda: self._goto(self.PAGE_SERVICE))
        self.ui.btn_nav_report.clicked.connect(lambda: self._goto(self.PAGE_REPORT))

    def _goto(self, index: int):
        self.ui.stackedWidget.setCurrentIndex(index)
        self._set_active_nav(index)
        {
            self.PAGE_DASHBOARD: self._load_dashboard,
            self.PAGE_ROOM:      self._load_rooms,
            self.PAGE_CUSTOMER:  self._load_customers,
            self.PAGE_STAFF:     self._load_staff,
            self.PAGE_BOOKING:   self._load_bookings,
            self.PAGE_SERVICE:   self._load_services,
            self.PAGE_REPORT:    self._load_report,
        }[index]()
        QtCore.QTimer.singleShot(0, self._refresh_table_columns)

    def _logout(self):
        if msg_confirm(self, "Bạn có muốn đăng xuất không?"):
            UserModel.log_activity(self.user["id"], "Đăng xuất hệ thống")
            self.close()
            from controllers.login_controller import LoginWindow
            self._login_win = LoginWindow()
            self._login_win.exec()

    # ══════════════════════════════════════════════════════════════════════════
    # DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    def _load_dashboard(self):
        from datetime import date, timedelta
        stats = RoomModel.stats()
        today     = date.today()
        today_str = today.isoformat()
        first_of_month = date(today.year, today.month, 1).isoformat()
        summ = InvoiceModel.summary(first_of_month, today_str)
        if summ["revenue"] == 0:
            summ = InvoiceModel.summary("2000-01-01", today_str)

        # ── Stat cards: hiển thị số lớn + nhãn nhỏ ──
        self._set_stat_card(
            self.ui.lbl_stat_total_rooms,
            "🏠", "Tổng Phòng", str(stats['total']), "#1565C0"
        )
        self._set_stat_card(
            self.ui.lbl_stat_occupied,
            "🔴", "Đang Thuê", str(stats['occupied']), "#C62828"
        )
        self._set_stat_card(
            self.ui.lbl_stat_customers,
            "👥", "Khách Hàng", str(CustomerModel.count()), "#E65100"
        )
        self._set_stat_card(
            self.ui.lbl_stat_revenue,
            "💰", "Doanh Thu", fmt_money(summ['revenue']), "#2E7D32"
        )

        # ── Phòng đang thuê hôm nay ──
        rows = BookingModel.get_active_today()
        if not rows:
            all_b = BookingModel.get_all()
            rows = [{"room_number": b["room"], "customer": b["customer"],
                     "check_out": b["check_out"]}
                    for b in all_b if b["status"] == "checked_in"]
        fill_table(self.ui.tbl_dashboard_checkedin, rows,
                   ["room_number", "customer", "check_out"])

        # ── Biểu đồ doanh thu 7 ngày ──
        d_from = (today - timedelta(days=6)).isoformat()
        chart_data = InvoiceModel.revenue_by_range(d_from, today_str)
        if not chart_data:
            chart_data = InvoiceModel.revenue_by_range("2000-01-01", today_str)
        self._draw_chart_into(self.ui.widget_5, chart_data, "Doanh Thu 7 Ngày Gần Nhất")

    def _set_stat_card(self, label: QtWidgets.QLabel,
                       icon: str, title: str, value: str, accent: str):
        """
        Render nội dung stat card với số lớn nổi bật.
        Dùng HTML rich-text để có 2 dòng: số (lớn, đậm) + tên (nhỏ, mờ).
        """
        html = (
            f'<div style="text-align:center; line-height:1.3;">'
            f'  <span style="font-size:11px; color:#6B7896;">{icon} {title}</span><br>'
            f'  <span style="font-size:22px; font-weight:bold; color:{accent};">{value}</span>'
            f'</div>'
        )
        label.setText(html)
        label.setTextFormat(QtCore.Qt.TextFormat.RichText)
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)

    # ══════════════════════════════════════════════════════════════════════════
    # QUẢN LÝ PHÒNG
    # ══════════════════════════════════════════════════════════════════════════
    def _setup_room_signals(self):
        self.ui.btn_room_add.clicked.connect(self._room_add)
        self.ui.btn_room_edit.clicked.connect(self._room_edit)
        self.ui.btn_room_delete.clicked.connect(self._room_delete)
        self.ui.inp_room_search.textChanged.connect(
            lambda t: self._load_rooms(t.replace("🔍 Tìm Phòng", "").strip()))
        self.ui.tbl_rooms.cellClicked.connect(self._room_select)

    def _load_rooms(self, keyword: str = ""):
        self._room_data = RoomModel.search(keyword) if keyword else RoomModel.get_all()
        fill_table(self.ui.tbl_rooms, self._room_data,
                   ["room_number", "type_name", "base_price", "status"],
                   stt=True,
                   money_keys=["base_price"], status_map=STATUS_VI)
        self._sel_room_id = None

    def _room_select(self, row: int, _col: int):
        if hasattr(self, "_room_data") and row < len(self._room_data):
            self._sel_room_id = self._room_data[row]["id"]

    def _room_add(self):
        dlg = RoomDialog(self)
        if dlg.exec():
            ok, msg = RoomModel.add(**dlg.get_data())
            (msg_info if ok else msg_error)(self, msg)
            if ok:
                UserModel.log_activity(self.user["id"], f"Thêm phòng {dlg.get_data()['room_number']}")
                self._load_rooms()

    def _room_edit(self):
        if not self._sel_room_id: msg_warn(self, "Chọn phòng cần sửa!"); return
        room = next((r for r in getattr(self, "_room_data", [])
                     if r["id"] == self._sel_room_id), None)
        if not room: return
        dlg = RoomDialog(self, room)
        if dlg.exec():
            ok, msg = RoomModel.update(self._sel_room_id, **dlg.get_data())
            (msg_info if ok else msg_error)(self, msg)
            if ok:
                UserModel.log_activity(self.user["id"], f"Sửa phòng {dlg.get_data()['room_number']}")
                self._load_rooms()

    def _room_delete(self):
        if not self._sel_room_id: msg_warn(self, "Chọn phòng cần xóa!"); return
        if msg_confirm(self, "Xóa phòng này?"):
            ok, msg = RoomModel.delete(self._sel_room_id)
            (msg_info if ok else msg_error)(self, msg)
            if ok:
                UserModel.log_activity(self.user["id"], f"Xóa phòng ID {self._sel_room_id}")
                self._load_rooms()

    # ══════════════════════════════════════════════════════════════════════════
    # KHÁCH HÀNG
    # ══════════════════════════════════════════════════════════════════════════
    def _setup_customer_signals(self):
        self.ui.btn_cust_add.clicked.connect(self._customer_add)
        self.ui.btn_cust_edit.clicked.connect(self._customer_edit)
        self.ui.btn_cust_delete.clicked.connect(self._customer_delete)
        self.ui.inp_cust_search.textChanged.connect(
            lambda t: self._load_customers(t.replace("🔍 Tìm Khách Hàng", "").strip()))
        self.ui.tbl_customers.cellClicked.connect(self._customer_select)

    def _load_customers(self, keyword: str = ""):
        self._cust_data = CustomerModel.search(keyword) if keyword else CustomerModel.get_all()
        fill_table(self.ui.tbl_customers, self._cust_data,
                   ["id", "full_name", "phone", "id_card", "email", "created_at"],
                   stt=True)
        self._sel_customer_id = None

    def _customer_select(self, row: int, _col: int):
        if hasattr(self, "_cust_data") and row < len(self._cust_data):
            self._sel_customer_id = self._cust_data[row]["id"]

    def _customer_add(self):
        dlg = CustomerDialog(self)
        if dlg.exec():
            ok, msg = CustomerModel.add(**dlg.get_data())
            (msg_info if ok else msg_error)(self, msg)
            if ok:
                UserModel.log_activity(self.user["id"], f"Thêm KH {dlg.get_data()['full_name']}")
                self._load_customers()

    def _customer_edit(self):
        if not self._sel_customer_id: msg_warn(self, "Chọn khách hàng cần sửa!"); return
        cust = CustomerModel.get_by_id(self._sel_customer_id)
        if not cust: return
        dlg = CustomerDialog(self, cust)
        if dlg.exec():
            ok, msg = CustomerModel.update(self._sel_customer_id, **dlg.get_data())
            (msg_info if ok else msg_error)(self, msg)
            if ok:
                UserModel.log_activity(self.user["id"], f"Sửa KH {dlg.get_data()['full_name']}")
                self._load_customers()

    def _customer_delete(self):
        if not self._sel_customer_id: msg_warn(self, "Chọn khách hàng cần xóa!"); return
        if msg_confirm(self, "Xóa khách hàng này?"):
            ok, msg = CustomerModel.delete(self._sel_customer_id)
            (msg_info if ok else msg_error)(self, msg)
            if ok:
                UserModel.log_activity(self.user["id"], f"Xóa KH ID {self._sel_customer_id}")
                self._load_customers()

    # ══════════════════════════════════════════════════════════════════════════
    # NHÂN VIÊN
    # ══════════════════════════════════════════════════════════════════════════
    def _setup_staff_signals(self):
        self.ui.btn_staff_add.clicked.connect(self._staff_add)
        self.ui.btn_staff_edit.clicked.connect(self._staff_edit)
        self.ui.btn_staff_delete.clicked.connect(self._staff_delete)
        self.ui.btn_staff_reset_pass.clicked.connect(self._staff_reset_pass)
        
        self.ui.btn_staff_history = QtWidgets.QPushButton("📜 Xem lịch sử", parent=self.ui.pg_staff)
        self.ui.btn_staff_history.setStyleSheet("QPushButton{background:#1A2B4A;color:#FFF;border:none;border-radius:5px;padding:7px 18px;font-size:13px;font-weight:bold;min-width:120px;}QPushButton:hover{background:#223259;}QPushButton:pressed{background:#0F1B30;}")
        self.ui.staffToolbar.insertWidget(4, self.ui.btn_staff_history)
        self.ui.btn_staff_history.clicked.connect(self._staff_history)
        
        self.ui.tbl_staff.cellClicked.connect(self._staff_select)

    def _staff_history(self):
        if not self._sel_staff_id: msg_warn(self, "Chọn nhân viên!"); return
        dlg = StaffHistoryDialog(self, self._sel_staff_id)
        dlg.exec()

    def _load_staff(self):
        self._staff_data = UserModel.get_all()
        fill_table(self.ui.tbl_staff, self._staff_data,
                   ["id", "full_name", "username", "phone", "role", "is_active"],
                   stt=True,
                   status_map=STATUS_VI)
        self._sel_staff_id = None

    def _staff_select(self, row: int, _col: int):
        if hasattr(self, "_staff_data") and row < len(self._staff_data):
            self._sel_staff_id = self._staff_data[row]["id"]

    def _staff_add(self):
        dlg = StaffDialog(self)
        if dlg.exec():
            d = dlg.get_data()
            ok, msg = UserModel.add(d["username"], d["password"], d["full_name"], d["role"])
            (msg_info if ok else msg_error)(self, msg)
            if ok:
                UserModel.log_activity(self.user["id"], f"Thêm nhân viên {d['username']}")
                self._load_staff()

    def _staff_edit(self):
        if not self._sel_staff_id: msg_warn(self, "Chọn nhân viên cần sửa!"); return
        staff = next((s for s in getattr(self, "_staff_data", [])
                      if s["id"] == self._sel_staff_id), None)
        if not staff: return
        dlg = StaffDialog(self, staff)
        if dlg.exec():
            d = dlg.get_data()
            ok, msg = UserModel.update(self._sel_staff_id, d["full_name"], d["role"], d["is_active"])
            (msg_info if ok else msg_error)(self, msg)
            if ok:
                UserModel.log_activity(self.user["id"], f"Sửa nhân viên ID {self._sel_staff_id}")
                self._load_staff()

    def _staff_delete(self):
        if not self._sel_staff_id: msg_warn(self, "Chọn nhân viên cần xóa!"); return
        if self._sel_staff_id == self.user["id"]:
            msg_warn(self, "Không thể xóa tài khoản đang đăng nhập!"); return
        if msg_confirm(self, "Vô hiệu hoá tài khoản này?"):
            ok, msg = UserModel.delete(self._sel_staff_id)
            (msg_info if ok else msg_error)(self, msg)
            if ok:
                UserModel.log_activity(self.user["id"], f"Vô hiệu hóa nv ID {self._sel_staff_id}")
                self._load_staff()

    def _staff_reset_pass(self):
        if not self._sel_staff_id: msg_warn(self, "Chọn nhân viên!"); return
        new_pass, ok = QtWidgets.QInputDialog.getText(
            self, "Đặt lại mật khẩu", "Mật khẩu mới:",
            QtWidgets.QLineEdit.EchoMode.Password)
        if ok and new_pass.strip():
            ok2, msg = UserModel.reset_password(self._sel_staff_id, new_pass.strip())
            (msg_info if ok2 else msg_error)(self, msg)
            if ok2:
                UserModel.log_activity(self.user["id"], f"Reset mật khẩu NV ID {self._sel_staff_id}")

    # ══════════════════════════════════════════════════════════════════════════
    # LỊCH SỬ ĐẶT PHÒNG
    # ══════════════════════════════════════════════════════════════════════════
    def _setup_booking_signals(self):
        self.ui.inp_booking_search.textChanged.connect(
            lambda t: self._load_bookings(t.replace("🔍 Tìm kiếm", "").strip()))
        self.ui.tbl_bookings.cellClicked.connect(self._booking_select)

    def _load_bookings(self, keyword: str = ""):
        self._booking_data = BookingModel.search(keyword) if keyword else BookingModel.get_all()
        fill_table(self.ui.tbl_bookings, self._booking_data,
                   ["id", "customer", "room", "check_in", "check_out", "status"],
                   stt=True,
                   status_map=STATUS_VI)
        self._sel_booking_id = None

    def _booking_select(self, row: int, _col: int):
        if hasattr(self, "_booking_data") and row < len(self._booking_data):
            self._sel_booking_id = self._booking_data[row]["id"]

    # ══════════════════════════════════════════════════════════════════════════
    # DỊCH VỤ
    # ══════════════════════════════════════════════════════════════════════════
    def _setup_service_signals(self):
        self.ui.btn_svc_add.clicked.connect(self._service_add)
        self.ui.btn_svc_edit.clicked.connect(self._service_edit)
        self.ui.btn_svc_delete.clicked.connect(self._service_delete)
        self.ui.inp_svc_search.textChanged.connect(
            lambda t: self._load_services(t.replace("🔍 Tìm dịch vụ", "").strip()))
        self.ui.tbl_services.cellClicked.connect(self._service_select)

    def _load_services(self, keyword: str = ""):
        self._svc_data = ServiceModel.search(keyword) if keyword else ServiceModel.get_all()
        fill_table(self.ui.tbl_services, self._svc_data,
                   ["name", "price", "unit", "is_active"],
                   stt=True,
                   money_keys=["price"], status_map=STATUS_VI)
        self._sel_service_id = None

    def _service_select(self, row: int, _col: int):
        if hasattr(self, "_svc_data") and row < len(self._svc_data):
            self._sel_service_id = self._svc_data[row]["id"]

    def _service_add(self):
        dlg = ServiceDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            data.pop("is_active", None)
            ok, msg = ServiceModel.add(**data)
            (msg_info if ok else msg_error)(self, msg)
            if ok:
                UserModel.log_activity(self.user["id"], f"Thêm dịch vụ {data['name']}")
                self._load_services()

    def _service_edit(self):
        if not self._sel_service_id: msg_warn(self, "Chọn dịch vụ cần sửa!"); return
        svc = next((s for s in getattr(self, "_svc_data", [])
                    if s["id"] == self._sel_service_id), None)
        if not svc: return
        dlg = ServiceDialog(self, svc)
        if dlg.exec():
            ok, msg = ServiceModel.update(self._sel_service_id, **dlg.get_data())
            (msg_info if ok else msg_error)(self, msg)
            if ok:
                UserModel.log_activity(self.user["id"], f"Sửa dịch vụ {dlg.get_data()['name']}")
                self._load_services()

    def _service_delete(self):
        if not self._sel_service_id: msg_warn(self, "Chọn dịch vụ cần xóa!"); return
        if msg_confirm(self, "Tắt dịch vụ này?"):
            ok, msg = ServiceModel.delete(self._sel_service_id)
            (msg_info if ok else msg_error)(self, msg)
            if ok:
                UserModel.log_activity(self.user["id"], f"Tắt dịch vụ ID {self._sel_service_id}")
                self._load_services()

   
    def _setup_report_signals(self):
        self.ui.cmb_rpt_type.clear()
        self.ui.cmb_rpt_type.addItems(["Ngày", "Tuần", "Tháng"])
        self.ui.btn_rpt_view.clicked.connect(self._report_view)
        self.ui.btn_rpt_export_excel.clicked.connect(self._report_excel)
        self.ui.btn_rpt_export_pdf.clicked.connect(self._report_pdf)

    def _load_report(self):
        from datetime import date
        today = date.today()
        self.ui.de_rpt_from.setDate(QtCore.QDate(today.year, 1, 1))
        self.ui.de_rpt_to.setDate(QtCore.QDate(today.year, today.month, today.day))
        self.ui.de_rpt_from.setCalendarPopup(True)
        self.ui.de_rpt_to.setCalendarPopup(True)
        self._report_view()

    def _report_view(self):
        d1 = self.ui.de_rpt_from.date().toString("yyyy-MM-dd")
        d2 = self.ui.de_rpt_to.date().toString("yyyy-MM-dd")
        summ = InvoiceModel.summary(d1, d2)

        if summ["revenue"] == 0 and summ["booked"] == 0:
            from datetime import date
            summ_all = InvoiceModel.summary("2000-01-01", date.today().isoformat())
            if summ_all["revenue"] > 0:
                summ = summ_all
                d1, d2 = "2000-01-01", date.today().isoformat()

        # ── Stat cards thống kê: số lớn + nhãn nhỏ ──
        self._set_stat_card_report(
            self.ui.lbl_rpt_revenue,
            "💰", "Doanh Thu", fmt_money(summ['revenue']), "#C62828"
        )
        self._set_stat_card_report(
            self.ui.lbl_rpt_rooms_rented,
            "🛏", "Phòng Đã Thuê", str(summ['booked']), "#E65100"
        )
        self._set_stat_card_report(
            self.ui.lbl_rpt_customers,
            "👥", "Khách Hàng", str(summ['customers']), "#2E7D32"
        )

        self._report_data = InvoiceModel.revenue_by_range(d1, d2)
        self._draw_chart(self._report_data)

    def _set_stat_card_report(self, label: QtWidgets.QLabel,
                               icon: str, title: str, value: str, accent: str):
        html = (
            f'<div style="text-align:center; line-height:1.4;">'
            f'  <span style="font-size:10px; color:#6B7896;">{icon} {title}</span><br>'
            f'  <span style="font-size:18px; font-weight:bold; color:{accent};">{value}</span>'
            f'</div>'
        )
        label.setText(html)
        label.setTextFormat(QtCore.Qt.TextFormat.RichText)
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)

    # ══════════════════════════════════════════════════════════════════════════
    # BIỂU ĐỒ (dùng chung cho Dashboard & Thống Kê)
    # ══════════════════════════════════════════════════════════════════════════
    def _draw_chart_into(self, container, rows: list, title: str = "Doanh Thu"):
        """Vẽ biểu đồ cột hiện đại vào bất kỳ QWidget/QFrame nào."""
        # Xóa nội dung cũ
        old_layout = container.layout()
        if old_layout:
            while old_layout.count():
                item = old_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
        else:
            old_layout = QtWidgets.QVBoxLayout(container)
            old_layout.setContentsMargins(4, 4, 4, 4)

        layout = container.layout()

        if not rows:
            lbl = QtWidgets.QLabel("📭  Không có dữ liệu trong khoảng thời gian này.")
            lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #9E9E9E; font-size: 13px;")
            layout.addWidget(lbl)
            return

        try:
            import matplotlib
            matplotlib.use("QtAgg")
            import matplotlib.pyplot as plt
            import matplotlib.ticker as mticker
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FC
            from matplotlib.figure import Figure

            # ── Màu sắc & style hiện đại ──
            BG       = "#FFFFFF"
            BAR_CLR  = "#1A2A4A"          # màu cột chính
            ACCENT   = "#C9A84C"           # màu vàng gold accent
            GRID_CLR = "#F0EDE6"
            TXT_CLR  = "#1A2A4A"

            fig = Figure(figsize=(6, 3.2), facecolor=BG, tight_layout=True)
            ax  = fig.add_subplot(111, facecolor=BG)

            labels   = [r["day"] for r in rows]
            revenues = [r["revenue"] for r in rows]
            x_pos    = range(len(labels))

            # ── Vẽ bar với gradient-like effect bằng 2 lớp ──
            bars = ax.bar(x_pos, revenues,
                          color=BAR_CLR, width=0.55,
                          zorder=3, linewidth=0)

            # Tô màu accent cho bar cao nhất
            if revenues:
                max_idx = revenues.index(max(revenues))
                bars[max_idx].set_color(ACCENT)
                bars[max_idx].set_edgecolor("#A07830")
                bars[max_idx].set_linewidth(1)

            # ── Label số trên mỗi cột ──
            for bar, val in zip(bars, revenues):
                if val > 0:
                    formatted = f"{int(val/1_000_000):.1f}M" if val >= 1_000_000 else \
                                f"{int(val/1_000)}K"         if val >= 1_000       else \
                                str(int(val))
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + max(revenues) * 0.01,
                        formatted,
                        ha="center", va="bottom",
                        fontsize=7.5, color=TXT_CLR, fontweight="bold"
                    )

            # ── Trục & grid ──
            ax.set_xticks(list(x_pos))
            ax.set_xticklabels(labels, rotation=35, ha="right",
                               fontsize=8, color=TXT_CLR)
            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(
                    lambda x, _: f"{int(x/1_000_000)}M" if x >= 1_000_000 else
                                 f"{int(x/1_000)}K"     if x >= 1_000       else
                                 str(int(x))
                )
            )
            ax.tick_params(axis="y", labelsize=8, colors=TXT_CLR)
            ax.tick_params(axis="x", colors=TXT_CLR)

            ax.yaxis.grid(True, color=GRID_CLR, linewidth=1, zorder=0)
            ax.set_axisbelow(True)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color(GRID_CLR)
            ax.spines["bottom"].set_color(GRID_CLR)

            # ── Tiêu đề ──
            ax.set_title(title, fontsize=11, fontweight="bold",
                         color=TXT_CLR, pad=10, loc="left")

            canvas = FC(fig)
            canvas.setStyleSheet("background: transparent;")
            layout.addWidget(canvas)

        except Exception as e:
            # Fallback text nếu matplotlib không có
            text = "\n".join(f"{r['day']}:  {fmt_money(r['revenue'])}" for r in rows)
            lbl = QtWidgets.QLabel(text)
            lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("font-size: 12px; color: #1A2A4A; padding: 8px;")
            layout.addWidget(lbl)

    def _draw_chart(self, rows: list):
        """Vẽ biểu đồ doanh thu vào fra_chart (trang Thống Kê)."""
        self._draw_chart_into(self.ui.fra_chart, rows, "Doanh Thu Theo Ngày")

    def _report_excel(self):
        if not self._report_data:
            msg_warn(self, "Không có dữ liệu!"); return
        try:
            path = export_excel(self._report_data,
                                ["Ngày", "Doanh Thu (đ)", "Số Booking"],
                                ["day", "revenue", "bookings"],
                                "BaoCaoDoanhThu")
            msg_info(self, f"Xuất Excel thành công!\n{path}")
        except Exception as e:
            msg_error(self, str(e))

    def _report_pdf(self):
        if not self._report_data:
            msg_warn(self, "Không có dữ liệu!"); return
        try:
            path = export_pdf(self._report_data,
                              ["Ngày", "Doanh Thu (đ)", "Số Booking"],
                              ["day", "revenue", "bookings"],
                              "BaoCaoDoanhThu")
            msg_info(self, f"Xuất PDF thành công!\n{path}")
        except Exception as e:
            msg_error(self, str(e))


# ══════════════════════════════════════════════════════════════════════════════
# DIALOGS
# ══════════════════════════════════════════════════════════════════════════════

class _Base(QtWidgets.QDialog):
    def __init__(self, parent, title):
        super().__init__(parent)
        self.setWindowTitle(title); self.setMinimumWidth(380)
        self._form = QtWidgets.QFormLayout()
        box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText("Lưu")
        box.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel).setText("Huỷ")
        box.accepted.connect(self._ok); box.rejected.connect(self.reject)
        root = QtWidgets.QVBoxLayout(self)
        root.addLayout(self._form); root.addWidget(box)
    def _ok(self):
        if self._validate(): self.accept()
    def _validate(self): return True


class RoomDialog(_Base):
    def __init__(self, parent=None, room=None):
        super().__init__(parent, "Thêm phòng" if room is None else "Sửa phòng")
        self.le_num  = QtWidgets.QLineEdit()
        self.sb_fl   = QtWidgets.QSpinBox(); self.sb_fl.setRange(1, 50)
        self.cb_type = QtWidgets.QComboBox()
        self.cb_stat = QtWidgets.QComboBox()
        self.cb_stat.addItems(["available", "occupied", "maintenance"])
        self.le_desc = QtWidgets.QLineEdit()
        self._types  = RoomModel.get_types()
        for t in self._types:
            self.cb_type.addItem(f"{t['name']} – {int(t['base_price']):,}đ", t["id"])
        self._form.addRow("Số phòng *",   self.le_num)
        self._form.addRow("Tầng *",       self.sb_fl)
        self._form.addRow("Loại phòng *", self.cb_type)
        self._form.addRow("Trạng thái",   self.cb_stat)
        self._form.addRow("Mô tả",        self.le_desc)
        if room:
            self.le_num.setText(room["room_number"]); self.sb_fl.setValue(room["floor"])
            for i in range(self.cb_type.count()):
                if self.cb_type.itemData(i) == room["type_id"]:
                    self.cb_type.setCurrentIndex(i)
            idx = self.cb_stat.findText(room["status"])
            if idx >= 0: self.cb_stat.setCurrentIndex(idx)
            self.le_desc.setText(room.get("description") or "")
    def _validate(self):
        if not self.le_num.text().strip():
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Nhập số phòng!"); return False
        return True
    def get_data(self):
        return {"room_number": self.le_num.text().strip(), "floor": self.sb_fl.value(),
                "type_id": self.cb_type.currentData(), "status": self.cb_stat.currentText(),
                "description": self.le_desc.text().strip()}


class CustomerDialog(_Base):
    def __init__(self, parent=None, cust=None):
        super().__init__(parent, "Thêm khách hàng" if cust is None else "Sửa khách hàng")
        self.le_name = QtWidgets.QLineEdit()
        self.le_id   = QtWidgets.QLineEdit()
        self.le_ph   = QtWidgets.QLineEdit()
        self.le_em   = QtWidgets.QLineEdit()
        self.le_addr = QtWidgets.QLineEdit()
        self._form.addRow("Họ tên *",       self.le_name)
        self._form.addRow("CCCD *",         self.le_id)
        self._form.addRow("Điện thoại *",   self.le_ph)
        self._form.addRow("Email",          self.le_em)
        self._form.addRow("Địa chỉ",       self.le_addr)
        if cust:
            self.le_name.setText(cust.get("full_name",""))
            self.le_id.setText(cust.get("id_card",""))
            self.le_ph.setText(cust.get("phone",""))
            self.le_em.setText(cust.get("email","") or "")
            self.le_addr.setText(cust.get("address","") or "")
    def _validate(self):
        if not self.le_name.text().strip() or not self.le_id.text().strip() or not self.le_ph.text().strip():
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Điền đầy đủ thông tin (*)!"); return False
        return True
    def get_data(self):
        return {"full_name": self.le_name.text().strip(), "id_card": self.le_id.text().strip(),
                "phone": self.le_ph.text().strip(), "email": self.le_em.text().strip(),
                "address": self.le_addr.text().strip()}


class StaffDialog(_Base):
    def __init__(self, parent=None, staff=None):
        super().__init__(parent, "Thêm nhân viên" if staff is None else "Sửa nhân viên")
        self._edit = staff is not None
        self.le_name = QtWidgets.QLineEdit()
        self.le_user = QtWidgets.QLineEdit()
        self.le_pass = QtWidgets.QLineEdit(); self.le_pass.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.cb_role = QtWidgets.QComboBox(); self.cb_role.addItems(["staff", "admin"])
        self.cb_act  = QtWidgets.QComboBox(); self.cb_act.addItems(["1 – Hoạt động", "0 – Vô hiệu"])
        self._form.addRow("Họ tên *",   self.le_name)
        self._form.addRow("Username *", self.le_user)
        if not self._edit: self._form.addRow("Mật khẩu *", self.le_pass)
        self._form.addRow("Vai trò",    self.cb_role)
        if self._edit: self._form.addRow("Trạng thái", self.cb_act)
        if staff:
            self.le_name.setText(staff.get("full_name",""))
            self.le_user.setText(staff.get("username",""))
            self.le_user.setEnabled(False)
            idx = self.cb_role.findText(staff.get("role","staff"))
            if idx >= 0: self.cb_role.setCurrentIndex(idx)
            self.cb_act.setCurrentIndex(0 if staff.get("is_active",1) == 1 else 1)
    def _validate(self):
        if not self.le_name.text().strip() or not self.le_user.text().strip():
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Điền đầy đủ!"); return False
        if not self._edit and not self.le_pass.text().strip():
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Nhập mật khẩu!"); return False
        return True
    def get_data(self):
        return {"full_name": self.le_name.text().strip(), "username": self.le_user.text().strip(),
                "password": self.le_pass.text().strip(), "role": self.cb_role.currentText(),
                "is_active": 1 if self.cb_act.currentIndex() == 0 else 1}


class ServiceDialog(_Base):
    def __init__(self, parent=None, svc=None):
        super().__init__(parent, "Thêm dịch vụ" if svc is None else "Sửa dịch vụ")
        self.le_name = QtWidgets.QLineEdit()
        self.sb_pr   = QtWidgets.QDoubleSpinBox(); self.sb_pr.setRange(0, 100_000_000); self.sb_pr.setSuffix(" đ")
        self.le_unit = QtWidgets.QLineEdit()
        self.le_desc = QtWidgets.QLineEdit()
        self.cb_act  = QtWidgets.QComboBox(); self.cb_act.addItems(["1 – Hoạt động", "0 – Vô hiệu"])
        self._form.addRow("Tên dịch vụ *", self.le_name)
        self._form.addRow("Giá *",         self.sb_pr)
        self._form.addRow("Đơn vị *",      self.le_unit)
        self._form.addRow("Mô tả",         self.le_desc)
        self._form.addRow("Trạng thái",    self.cb_act)
        if svc:
            self.le_name.setText(svc.get("name",""))
            self.sb_pr.setValue(float(svc.get("price",0)))
            self.le_unit.setText(svc.get("unit",""))
            self.le_desc.setText(svc.get("description","") or "")
            self.cb_act.setCurrentIndex(0 if svc.get("is_active",1) == 1 else 1)
    def _validate(self):
        if not self.le_name.text().strip() or not self.le_unit.text().strip():
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Điền tên và đơn vị!"); return False
        return True
    def get_data(self):
        return {"name": self.le_name.text().strip(), "price": self.sb_pr.value(),
                "unit": self.le_unit.text().strip(), "description": self.le_desc.text().strip(),
                "is_active": 1 if self.cb_act.currentIndex() == 0 else 0}

class StaffHistoryDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, user_id=None):
        super().__init__(parent)
        self.setWindowTitle("📜 Lịch sử hoạt động")
        self.setMinimumSize(480, 400)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        self.tbl_history = QtWidgets.QTableWidget()
        self.tbl_history.setColumnCount(2)
        self.tbl_history.setHorizontalHeaderLabels(["Hành động", "Thời gian"])
        self.tbl_history.horizontalHeader().setStretchLastSection(True)
        self.tbl_history.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tbl_history.verticalHeader().setVisible(False)
        self.tbl_history.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_history.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_history.setAlternatingRowColors(True)
        self.tbl_history.setStyleSheet("QTableWidget{background:#FFF;alternate-background-color:#F0EDE6;border:1px solid #D3CECC;border-radius:6px;gridline-color:#E5E0D8;selection-background-color:#EAF2FB;selection-color:#1A2B4A;font-size:13px;}QTableWidget::item{padding:7px 10px;color:#1A2B4A;}QTableWidget::item:selected{background:#D6E8F7;}QHeaderView::section{background:#1A2B4A;color:#FFF;font-weight:bold;font-size:13px;padding:9px 10px;border:none;border-right:1px solid #223259;}QHeaderView::section:first{border-top-left-radius:6px;}QHeaderView::section:last{border-top-right-radius:6px;border-right:none;}")
        
        layout.addWidget(self.tbl_history)
        
        btn_close = QtWidgets.QPushButton("Đóng")
        btn_close.setStyleSheet("QPushButton{background:#FFF;color:#1A2B4A;border:1.5px solid #1A2B4A;border-radius:5px;padding:7px 18px;font-size:13px;min-width:80px;}QPushButton:hover{background:#EAF2FB;border-color:#C9A84C;color:#C9A84C;}")
        btn_close.clicked.connect(self.accept)
        
        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_close)
        layout.addLayout(bottom_layout)
        
        if user_id:
            from models.user_model import UserModel
            rows = UserModel.get_activity_history(user_id)
            fill_table(self.tbl_history, rows, ["action", "created_at"])