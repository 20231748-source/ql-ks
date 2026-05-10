from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QHeaderView, QSizePolicy
from views.Admin import Ui_MainWindow
from models.room_model import RoomModel
from models.customer_model import CustomerModel
from models.user_model import UserModel
from models.booking_model import BookingModel
from models.service_model import ServiceModel
from models.invoice_model import InvoiceModel
from models.activity_log_model import ActivityLogModel
from utils.helpers import (msg_info, msg_warn, msg_error, msg_confirm,
                            fill_table, fmt_money, STATUS_VI)
from utils.export import export_excel, export_pdf


class AdminWindow(QtWidgets.QMainWindow):
    PAGE_DASHBOARD  = 0
    PAGE_ROOM       = 1
    PAGE_CUSTOMER   = 2
    PAGE_STAFF      = 3
    PAGE_BOOKING    = 4
    PAGE_SERVICE    = 5
    PAGE_REPORT     = 6

    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.ui   = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Hotel Management – Admin")
        self._sel_room_id     = None
        self._sel_room_type_id = None   # NEW: selected room type
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
            tbl.verticalHeader().setVisible(False)

        # Tables được tạo động (không trong .ui) — setup riêng sau khi tạo
        for attr in ("tbl_room_types", "tbl_activity_log"):
            tbl = getattr(self, attr, None)
            if tbl:
                h = tbl.horizontalHeader()
                h.setStretchLastSection(False)
                h.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
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

        rows = BookingModel.get_active_today()
        if not rows:
            all_b = BookingModel.get_all()
            rows = [{"room_number": b["room"], "customer": b["customer"],
                     "check_out": b["check_out"]}
                    for b in all_b if b["status"] == "checked_in"]
        fill_table(self.ui.tbl_dashboard_checkedin, rows,
                   ["room_number", "customer", "check_out"])

        d_from = (today - timedelta(days=6)).isoformat()
        chart_data = InvoiceModel.revenue_by_range(d_from, today_str)
        if not chart_data:
            chart_data = InvoiceModel.revenue_by_range("2000-01-01", today_str)
        self._draw_chart_into(self.ui.widget_5, chart_data, "Doanh Thu 7 Ngày Gần Nhất")

    def _set_stat_card(self, label, icon, title, value, accent):
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
    # QUẢN LÝ PHÒNG  (tab: Danh sách phòng | Loại phòng)
    # ══════════════════════════════════════════════════════════════════════════
    def _setup_room_signals(self):
        # Sẽ connect sau khi tạo tab widget trong _inject_room_tabs()
        pass

    def _load_rooms(self, keyword: str = ""):
        # Lần đầu vào trang phòng → tạo tab layout nếu chưa có
        if not hasattr(self, "_room_tab_widget"):
            self._inject_room_tabs()

        # Load danh sách phòng
        self._room_data = RoomModel.search(keyword) if keyword else RoomModel.get_all()
        fill_table(self.ui.tbl_rooms, self._room_data,
                   ["room_number", "type_name", "base_price", "status"],
                   stt=True,
                   money_keys=["base_price"], status_map=STATUS_VI)
        self._sel_room_id = None

        # Load loại phòng
        self._load_room_types()

    def _inject_room_tabs(self):
        """
        Chèn QTabWidget vào pg_rooms để tách 'Danh Sách Phòng' và 'Loại Phòng'.
        Làm một lần duy nhất.
        """
        page_layout = self.ui.pg_rooms.layout()   # roomsLayout (QVBoxLayout)

        # ── Ẩn toolbar cũ trong .ui (btn_room_add, btn_room_edit, btn_room_delete,
        #    inp_room_search) — toolbar mới sẽ được tạo bên trong tab ──
        for attr in ("btn_room_add", "btn_room_edit", "btn_room_delete", "inp_room_search"):
            w = getattr(self.ui, attr, None)
            if w:
                w.hide()
        # Ẩn cả layout chứa các nút đó (roomsToolbar) bằng cách ẩn từng item
        rooms_layout = self.ui.pg_rooms.layout()
        for i in range(rooms_layout.count()):
            item = rooms_layout.itemAt(i)
            if item and isinstance(item, QtWidgets.QLayout if hasattr(QtWidgets, 'QLayout') else type(None)):
                # layout item — ẩn tất cả widget bên trong
                for j in range(item.count() if item else 0):
                    w2 = item.itemAt(j).widget() if item.itemAt(j) else None
                    if w2: w2.hide()

        # ── Tạo tab widget ──
        tab = QtWidgets.QTabWidget()
        tab.setStyleSheet("""
QTabWidget::pane { border: 1px solid #D3CECC; border-radius: 6px; background: #FAFAFA; }
QTabBar::tab {
    background: #E8E4DC; color: #1A2A4A; font-weight: bold;
    padding: 8px 22px; border-radius: 4px 4px 0 0; margin-right: 3px;
}
QTabBar::tab:selected { background: #1A2A4A; color: #C9A84C; }
QTabBar::tab:hover:!selected { background: #D4CFC4; }
""")
        self._room_tab_widget = tab

        # ── Tab 1: Danh sách phòng — lấy widget hiện có từ .ui ──
        # tbl_rooms đang nằm trong page layout → move vào tab1
        tab1 = QtWidgets.QWidget()
        t1l  = QtWidgets.QVBoxLayout(tab1)
        t1l.setContentsMargins(0, 8, 0, 0)
        t1l.setSpacing(8)

        # Toolbar (search + buttons) — clone từ cái đang có
        toolbar1 = QtWidgets.QHBoxLayout()
        toolbar1.setSpacing(8)
        self._inp_room_search = QtWidgets.QLineEdit()
        self._inp_room_search.setPlaceholderText("🔍 Tìm phòng...")
        self._inp_room_search.setStyleSheet(
            "QLineEdit{border:1.5px solid #D1D5DB;border-radius:6px;padding:7px 12px;"
            "font-size:13px;} QLineEdit:focus{border-color:#1A2A4A;}")
        self._inp_room_search.setMaximumWidth(260)

        def _make_btn(text, primary=True):
            btn = QtWidgets.QPushButton(text)
            if primary:
                btn.setStyleSheet(
                    "QPushButton{background:#1A2B4A;color:#FFF;border:none;border-radius:5px;"
                    "padding:7px 18px;font-size:13px;font-weight:bold;min-width:80px;}"
                    "QPushButton:hover{background:#223259;}")
            else:
                color = "#A32D2D" if "Xóa" in text else "#1A2B4A"
                bg2   = "#FDECEA" if "Xóa" in text else "#EAF2FB"
                btn.setStyleSheet(
                    f"QPushButton{{background:#FFF;color:{color};border:1.5px solid {color};"
                    f"border-radius:5px;padding:7px 18px;font-size:13px;min-width:80px;}}"
                    f"QPushButton:hover{{background:{bg2};}}")
            return btn

        self._btn_room_add    = _make_btn("➕ Thêm")
        self._btn_room_edit   = _make_btn("✏️ Sửa", False)
        self._btn_room_delete = _make_btn("🗑 Xóa", False)

        toolbar1.addWidget(self._inp_room_search)
        toolbar1.addWidget(self._btn_room_add)
        toolbar1.addWidget(self._btn_room_edit)
        toolbar1.addWidget(self._btn_room_delete)
        toolbar1.addStretch()
        t1l.addLayout(toolbar1)
        t1l.addWidget(self.ui.tbl_rooms)
        tab.addTab(tab1, "🛏  Danh Sách Phòng")

        # ── Tab 2: Loại phòng ──
        tab2 = QtWidgets.QWidget()
        t2l  = QtWidgets.QVBoxLayout(tab2)
        t2l.setContentsMargins(0, 8, 0, 0)
        t2l.setSpacing(8)

        toolbar2 = QtWidgets.QHBoxLayout()
        toolbar2.setSpacing(8)
        self._btn_rtype_add    = _make_btn("➕ Thêm loại")
        self._btn_rtype_edit   = _make_btn("✏️ Sửa", False)
        self._btn_rtype_delete = _make_btn("🗑 Xóa", False)
        toolbar2.addWidget(self._btn_rtype_add)
        toolbar2.addWidget(self._btn_rtype_edit)
        toolbar2.addWidget(self._btn_rtype_delete)
        toolbar2.addStretch()
        t2l.addLayout(toolbar2)

        self.tbl_room_types = QtWidgets.QTableWidget()
        self.tbl_room_types.setColumnCount(4)
        self.tbl_room_types.setHorizontalHeaderLabels(["ID", "Tên Loại", "Giá Cơ Bản", "Mô Tả"])
        self.tbl_room_types.setAlternatingRowColors(True)
        self.tbl_room_types.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_room_types.verticalHeader().setVisible(False)
        self.tbl_room_types.setStyleSheet(
            "QTableWidget{background:#FFF;alternate-background-color:#F0EDE6;"
            "border:1px solid #D3CECC;border-radius:6px;gridline-color:#E5E0D8;"
            "selection-background-color:#EAF2FB;selection-color:#1A2B4A;font-size:13px;}"
            "QTableWidget::item{padding:7px 10px;color:#1A2B4A;}"
            "QTableWidget::item:selected{background:#D6E8F7;}"
            "QHeaderView::section{background:#1A2B4A;color:#FFF;font-weight:bold;"
            "font-size:13px;padding:9px 10px;border:none;border-right:1px solid #223259;}"
        )
        h = self.tbl_room_types.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t2l.addWidget(self.tbl_room_types)
        tab.addTab(tab2, "📋  Loại Phòng")

        # ── Chèn tab widget vào page layout (thay thế tbl_rooms đã move sang tab1) ──
        page_layout.addWidget(tab)

        # ── Connect signals ──
        self._inp_room_search.textChanged.connect(
            lambda t: self._load_rooms(t.strip()))
        self._btn_room_add.clicked.connect(self._room_add)
        self._btn_room_edit.clicked.connect(self._room_edit)
        self._btn_room_delete.clicked.connect(self._room_delete)
        self.ui.tbl_rooms.cellClicked.connect(self._room_select)

        self._btn_rtype_add.clicked.connect(self._rtype_add)
        self._btn_rtype_edit.clicked.connect(self._rtype_edit)
        self._btn_rtype_delete.clicked.connect(self._rtype_delete)
        self.tbl_room_types.cellClicked.connect(self._rtype_select)

        # Cập nhật _all_tables nếu đã khởi tạo
        if hasattr(self, "_all_tables"):
            self._all_tables.append(self.tbl_room_types)
            h2 = self.tbl_room_types.horizontalHeader()
            h2.setStretchLastSection(False)
            h2.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    # ── Phòng (rooms) ─────────────────────────────────────────────────────────
    def _room_select(self, row: int, _col: int):
        if hasattr(self, "_room_data") and row < len(self._room_data):
            self._sel_room_id = self._room_data[row]["id"]

    def _room_add(self):
        dlg = RoomDialog(self)
        if dlg.exec():
            ok, msg = RoomModel.add(**dlg.get_data())
            (msg_info if ok else msg_error)(self, msg)
            if ok: self._load_rooms()

    def _room_edit(self):
        if not self._sel_room_id: msg_warn(self, "Chọn phòng cần sửa!"); return
        room = next((r for r in getattr(self, "_room_data", [])
                     if r["id"] == self._sel_room_id), None)
        if not room: return
        dlg = RoomDialog(self, room)
        if dlg.exec():
            ok, msg = RoomModel.update(self._sel_room_id, **dlg.get_data())
            (msg_info if ok else msg_error)(self, msg)
            if ok: self._load_rooms()

    def _room_delete(self):
        if not self._sel_room_id: msg_warn(self, "Chọn phòng cần xóa!"); return
        if msg_confirm(self, "Xóa phòng này?"):
            ok, msg = RoomModel.delete(self._sel_room_id)
            (msg_info if ok else msg_error)(self, msg)
            if ok: self._load_rooms()

    # ── Loại phòng (room types) ───────────────────────────────────────────────
    def _load_room_types(self):
        self._rtype_data = RoomModel.get_types()
        fill_table(
            self.tbl_room_types, self._rtype_data,
            ["id", "name", "base_price", "description"],
            money_keys=["base_price"]
        )
        self._sel_room_type_id = None

    def _rtype_select(self, row: int, _col: int):
        if hasattr(self, "_rtype_data") and row < len(self._rtype_data):
            self._sel_room_type_id = self._rtype_data[row]["id"]

    def _rtype_add(self):
        dlg = RoomTypeDialog(self)
        if dlg.exec():
            ok, msg = RoomModel.add_type(**dlg.get_data())
            (msg_info if ok else msg_error)(self, msg)
            if ok:
                self._load_room_types()
                ActivityLogModel.log(
                    self.user["id"], self.user["username"], self.user["full_name"],
                    "Thêm loại phòng", dlg.get_data().get("name", "")
                )

    def _rtype_edit(self):
        if not self._sel_room_type_id:
            msg_warn(self, "Chọn loại phòng cần sửa!"); return
        rtype = next((r for r in getattr(self, "_rtype_data", [])
                      if r["id"] == self._sel_room_type_id), None)
        if not rtype: return
        dlg = RoomTypeDialog(self, rtype)
        if dlg.exec():
            ok, msg = RoomModel.update_type(self._sel_room_type_id, **dlg.get_data())
            (msg_info if ok else msg_error)(self, msg)
            if ok:
                self._load_room_types()
                # Reload combo phòng nếu đang hiển thị
                ActivityLogModel.log(
                    self.user["id"], self.user["username"], self.user["full_name"],
                    "Sửa loại phòng", f"ID {self._sel_room_type_id} → {dlg.get_data().get('name','')}"
                )

    def _rtype_delete(self):
        if not self._sel_room_type_id:
            msg_warn(self, "Chọn loại phòng cần xóa!"); return
        if msg_confirm(self, "Xóa loại phòng này? (Chỉ xóa được nếu không có phòng nào dùng)"):
            ok, msg = RoomModel.delete_type(self._sel_room_type_id)
            (msg_info if ok else msg_error)(self, msg)
            if ok: self._load_room_types()

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
            if ok: self._load_customers()

    def _customer_edit(self):
        if not self._sel_customer_id: msg_warn(self, "Chọn khách hàng cần sửa!"); return
        cust = CustomerModel.get_by_id(self._sel_customer_id)
        if not cust: return
        dlg = CustomerDialog(self, cust)
        if dlg.exec():
            ok, msg = CustomerModel.update(self._sel_customer_id, **dlg.get_data())
            (msg_info if ok else msg_error)(self, msg)
            if ok: self._load_customers()

    def _customer_delete(self):
        if not self._sel_customer_id: msg_warn(self, "Chọn khách hàng cần xóa!"); return
        if msg_confirm(self, "Xóa khách hàng này?"):
            ok, msg = CustomerModel.delete(self._sel_customer_id)
            (msg_info if ok else msg_error)(self, msg)
            if ok: self._load_customers()

    # ══════════════════════════════════════════════════════════════════════════
    # NHÂN VIÊN  (tab: Danh sách | Nhật ký hoạt động)
    # ══════════════════════════════════════════════════════════════════════════
    def _setup_staff_signals(self):
        # Sẽ setup sau khi inject tabs
        pass

    def _load_staff(self):
        if not hasattr(self, "_staff_tab_widget"):
            self._inject_staff_tabs()

        self._staff_data = UserModel.get_all()
        fill_table(self.ui.tbl_staff, self._staff_data,
                   ["id", "full_name", "username", "phone", "role", "is_active"],
                   stt=True, status_map=STATUS_VI)
        self._sel_staff_id = None
        self._load_activity_log()

    def _inject_staff_tabs(self):
        for attr in ("btn_staff_add", "btn_staff_edit", "btn_staff_delete", "btn_staff_reset_pass"):
            w = getattr(self.ui, attr, None)
            if w: w.setVisible(False)

        page_layout = self.ui.pg_staff.layout() 

        tab = QtWidgets.QTabWidget()
        tab.setStyleSheet("""
QTabWidget::pane { border: 1px solid #D3CECC; border-radius: 6px; background: #FAFAFA; }
QTabBar::tab {
    background: #E8E4DC; color: #1A2A4A; font-weight: bold;
    padding: 8px 22px; border-radius: 4px 4px 0 0; margin-right: 3px;
}
QTabBar::tab:selected { background: #1A2A4A; color: #C9A84C; }
QTabBar::tab:hover:!selected { background: #D4CFC4; }
""")
        self._staff_tab_widget = tab

        tab1 = QtWidgets.QWidget()
        t1l  = QtWidgets.QVBoxLayout(tab1)
        t1l.setContentsMargins(0, 8, 0, 0)
        t1l.setSpacing(8)

        toolbar1 = QtWidgets.QHBoxLayout()
        toolbar1.setSpacing(8)

        def _btn(text, primary=True):
            b = QtWidgets.QPushButton(text)
            if primary:
                b.setStyleSheet(
                    "QPushButton{background:#1A2B4A;color:#FFF;border:none;border-radius:5px;"
                    "padding:7px 18px;font-size:13px;font-weight:bold;min-width:80px;}"
                    "QPushButton:hover{background:#223259;}")
            else:
                color = "#A32D2D" if "Xóa" in text else "#1A2B4A"
                bg2   = "#FDECEA" if "Xóa" in text else "#EAF2FB"
                b.setStyleSheet(
                    f"QPushButton{{background:#FFF;color:{color};border:1.5px solid {color};"
                    f"border-radius:5px;padding:7px 18px;font-size:13px;min-width:80px;}}"
                    f"QPushButton:hover{{background:{bg2};}}")
            return b

        self._btn_staff_add        = _btn("➕ Thêm")
        self._btn_staff_edit       = _btn("✏️ Sửa", False)
        self._btn_staff_delete     = _btn("🗑 Xóa", False)
        self._btn_staff_reset_pass = _btn("🔑 Đặt lại MK")
        for b in (self._btn_staff_add, self._btn_staff_edit,
                  self._btn_staff_delete, self._btn_staff_reset_pass):
            toolbar1.addWidget(b)
        toolbar1.addStretch()
        t1l.addLayout(toolbar1)
        t1l.addWidget(self.ui.tbl_staff)
        tab.addTab(tab1, "👨‍💼  Danh Sách Nhân Viên")

        # ── Tab 2: Nhật ký hoạt động ──
        tab2 = QtWidgets.QWidget()
        t2l  = QtWidgets.QVBoxLayout(tab2)
        t2l.setContentsMargins(0, 8, 0, 0)
        t2l.setSpacing(8)

        toolbar2 = QtWidgets.QHBoxLayout()
        toolbar2.setSpacing(8)
        self._inp_log_search = QtWidgets.QLineEdit()
        self._inp_log_search.setPlaceholderText("🔍 Tìm theo tên, hành động...")
        self._inp_log_search.setStyleSheet(
            "QLineEdit{border:1.5px solid #D1D5DB;border-radius:6px;padding:7px 12px;"
            "font-size:13px;} QLineEdit:focus{border-color:#1A2A4A;}")
        self._inp_log_search.setMaximumWidth(300)

        self._btn_log_refresh = _btn("🔄 Làm mới")
        self._btn_log_clear   = _btn("🗑 Xóa log cũ", False)

        # Lọc theo nhân viên
        self._cmb_log_staff = QtWidgets.QComboBox()
        self._cmb_log_staff.setMinimumWidth(180)
        self._cmb_log_staff.setStyleSheet(
            "QComboBox{border:1.5px solid #D1D5DB;border-radius:6px;padding:6px 10px;"
            "font-size:13px;color:#1A2A4A;background:#FFFFFF;}"
            "QComboBox:focus{border-color:#1A2A4A;}"
            "QComboBox QAbstractItemView{background:#FFF;color:#1A2A4A;"
            "selection-background-color:#1A2A4A;selection-color:#C9A84C;}"
        )
        self._cmb_log_staff.addItem("— Tất cả nhân viên —", None)
        for s in UserModel.get_all():
            self._cmb_log_staff.addItem(f"{s['full_name']} ({s['username']})", s["id"])

        toolbar2.addWidget(QtWidgets.QLabel("Nhân viên:"))
        toolbar2.addWidget(self._cmb_log_staff)
        toolbar2.addWidget(self._inp_log_search)
        toolbar2.addWidget(self._btn_log_refresh)
        toolbar2.addWidget(self._btn_log_clear)
        toolbar2.addStretch()
        t2l.addLayout(toolbar2)

        self.tbl_activity_log = QtWidgets.QTableWidget()
        self.tbl_activity_log.setColumnCount(5)
        self.tbl_activity_log.setHorizontalHeaderLabels(
            ["Nhân Viên", "Username", "Hành Động", "Chi Tiết", "Thời Gian"])
        self.tbl_activity_log.setAlternatingRowColors(True)
        self.tbl_activity_log.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_activity_log.verticalHeader().setVisible(False)
        self.tbl_activity_log.setStyleSheet(
            "QTableWidget{background:#FFF;alternate-background-color:#F0EDE6;"
            "border:1px solid #D3CECC;border-radius:6px;gridline-color:#E5E0D8;"
            "selection-background-color:#EAF2FB;font-size:13px;}"
            "QTableWidget::item{padding:7px 10px;color:#1A2B4A;}"
            "QHeaderView::section{background:#1A2B4A;color:#FFF;font-weight:bold;"
            "font-size:13px;padding:9px 10px;border:none;border-right:1px solid #223259;}"
        )
        h = self.tbl_activity_log.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t2l.addWidget(self.tbl_activity_log)
        tab.addTab(tab2, "📋  Nhật Ký Hoạt Động")

        # ── Thêm vào page ──
        page_layout.addWidget(tab)

        # ── Connect signals ──
        self._btn_staff_add.clicked.connect(self._staff_add)
        self._btn_staff_edit.clicked.connect(self._staff_edit)
        self._btn_staff_delete.clicked.connect(self._staff_delete)
        self._btn_staff_reset_pass.clicked.connect(self._staff_reset_pass)
        self.ui.tbl_staff.cellClicked.connect(self._staff_select)

        self._btn_log_refresh.clicked.connect(self._load_activity_log)
        self._btn_log_clear.clicked.connect(self._clear_old_logs)
        self._inp_log_search.textChanged.connect(self._load_activity_log)
        self._cmb_log_staff.currentIndexChanged.connect(self._load_activity_log)

        if hasattr(self, "_all_tables"):
            self._all_tables.append(self.tbl_activity_log)

    def _load_activity_log(self):
        if not hasattr(self, "tbl_activity_log"):
            return
        kw       = self._inp_log_search.text().strip() if hasattr(self, "_inp_log_search") else ""
        uid      = self._cmb_log_staff.currentData() if hasattr(self, "_cmb_log_staff") else None
        if uid:
            data = ActivityLogModel.get_by_user(uid)
            if kw:
                kl = kw.lower()
                data = [r for r in data
                        if kl in r["action"].lower() or kl in (r["detail"] or "").lower()]
        elif kw:
            data = ActivityLogModel.search(kw)
        else:
            data = ActivityLogModel.get_all()

        fill_table(
            self.tbl_activity_log, data,
            ["full_name", "username", "action", "detail", "created_at"]
        )

    def _clear_old_logs(self):
        days, ok = QtWidgets.QInputDialog.getInt(
            self, "Xóa log cũ", "Xóa log cũ hơn (ngày):", value=90, min=1, max=3650)
        if ok and msg_confirm(self, f"Xóa toàn bộ log cũ hơn {days} ngày?"):
            ActivityLogModel.clear_old(days)
            self._load_activity_log()
            msg_info(self, "Đã xóa log cũ!")

    # ── Staff CRUD ────────────────────────────────────────────────────────────
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
                self._load_staff()
                ActivityLogModel.log(
                    self.user["id"], self.user["username"], self.user["full_name"],
                    "Thêm nhân viên", f"{d['full_name']} ({d['username']})"
                )

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
                self._load_staff()
                ActivityLogModel.log(
                    self.user["id"], self.user["username"], self.user["full_name"],
                    "Sửa nhân viên", f"ID {self._sel_staff_id}: {d['full_name']}"
                )

    def _staff_delete(self):
        if not self._sel_staff_id: msg_warn(self, "Chọn nhân viên cần xóa!"); return
        if self._sel_staff_id == self.user["id"]:
            msg_warn(self, "Không thể xóa tài khoản đang đăng nhập!"); return
        if msg_confirm(self, "Vô hiệu hoá tài khoản này?"):
            ok, msg = UserModel.delete(self._sel_staff_id)
            (msg_info if ok else msg_error)(self, msg)
            if ok:
                self._load_staff()
                ActivityLogModel.log(
                    self.user["id"], self.user["username"], self.user["full_name"],
                    "Vô hiệu hoá tài khoản", f"User ID {self._sel_staff_id}"
                )

    def _staff_reset_pass(self):
        if not self._sel_staff_id: msg_warn(self, "Chọn nhân viên!"); return
        new_pass, ok = QtWidgets.QInputDialog.getText(
            self, "Đặt lại mật khẩu", "Mật khẩu mới:",
            QtWidgets.QLineEdit.EchoMode.Password)
        if ok and new_pass.strip():
            ok2, msg = UserModel.reset_password(self._sel_staff_id, new_pass.strip())
            (msg_info if ok2 else msg_error)(self, msg)
            if ok2:
                ActivityLogModel.log(
                    self.user["id"], self.user["username"], self.user["full_name"],
                    "Đặt lại mật khẩu", f"User ID {self._sel_staff_id}"
                )

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
                   stt=True, status_map=STATUS_VI)
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
                   stt=True, money_keys=["price"], status_map=STATUS_VI)
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
            if ok: self._load_services()

    def _service_edit(self):
        if not self._sel_service_id: msg_warn(self, "Chọn dịch vụ cần sửa!"); return
        svc = next((s for s in getattr(self, "_svc_data", [])
                    if s["id"] == self._sel_service_id), None)
        if not svc: return
        dlg = ServiceDialog(self, svc)
        if dlg.exec():
            ok, msg = ServiceModel.update(self._sel_service_id, **dlg.get_data())
            (msg_info if ok else msg_error)(self, msg)
            if ok: self._load_services()

    def _service_delete(self):
        if not self._sel_service_id: msg_warn(self, "Chọn dịch vụ cần xóa!"); return
        if msg_confirm(self, "Tắt dịch vụ này?"):
            ok, msg = ServiceModel.delete(self._sel_service_id)
            (msg_info if ok else msg_error)(self, msg)
            if ok: self._load_services()

    # ══════════════════════════════════════════════════════════════════════════
    # THỐNG KÊ
    # ══════════════════════════════════════════════════════════════════════════
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

    def _set_stat_card_report(self, label, icon, title, value, accent):
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
    # BIỂU ĐỒ
    # ══════════════════════════════════════════════════════════════════════════
    def _draw_chart_into(self, container, rows: list, title: str = "Doanh Thu"):
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
            import matplotlib.ticker as mticker
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FC
            from matplotlib.figure import Figure

            BG = "#FFFFFF"; BAR_CLR = "#1A2A4A"; ACCENT = "#C9A84C"
            GRID_CLR = "#F0EDE6"; TXT_CLR = "#1A2A4A"

            fig = Figure(figsize=(6, 3.2), facecolor=BG, tight_layout=True)
            ax  = fig.add_subplot(111, facecolor=BG)

            labels   = [r["day"] for r in rows]
            revenues = [r["revenue"] for r in rows]
            x_pos    = range(len(labels))

            bars = ax.bar(x_pos, revenues, color=BAR_CLR, width=0.55, zorder=3, linewidth=0)
            if revenues:
                max_idx = revenues.index(max(revenues))
                bars[max_idx].set_color(ACCENT)
                bars[max_idx].set_edgecolor("#A07830")
                bars[max_idx].set_linewidth(1)

            for bar, val in zip(bars, revenues):
                if val > 0:
                    formatted = (f"{int(val/1_000_000):.1f}M" if val >= 1_000_000 else
                                 f"{int(val/1_000)}K" if val >= 1_000 else str(int(val)))
                    ax.text(bar.get_x() + bar.get_width() / 2,
                            bar.get_height() + max(revenues) * 0.01,
                            formatted, ha="center", va="bottom",
                            fontsize=7.5, color=TXT_CLR, fontweight="bold")

            ax.set_xticks(list(x_pos))
            ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8, color=TXT_CLR)
            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(
                    lambda x, _: (f"{int(x/1_000_000)}M" if x >= 1_000_000 else
                                  f"{int(x/1_000)}K" if x >= 1_000 else str(int(x)))))
            ax.tick_params(axis="y", labelsize=8, colors=TXT_CLR)
            ax.tick_params(axis="x", colors=TXT_CLR)
            ax.yaxis.grid(True, color=GRID_CLR, linewidth=1, zorder=0)
            ax.set_axisbelow(True)
            for sp in ("top", "right"): ax.spines[sp].set_visible(False)
            ax.spines["left"].set_color(GRID_CLR)
            ax.spines["bottom"].set_color(GRID_CLR)
            ax.set_title(title, fontsize=11, fontweight="bold", color=TXT_CLR, pad=10, loc="left")

            canvas = FC(fig)
            canvas.setStyleSheet("background: transparent;")
            layout.addWidget(canvas)

        except Exception:
            text = "\n".join(f"{r['day']}:  {fmt_money(r['revenue'])}" for r in rows)
            lbl = QtWidgets.QLabel(text)
            lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("font-size: 12px; color: #1A2A4A; padding: 8px;")
            layout.addWidget(lbl)

    def _draw_chart(self, rows: list):
        self._draw_chart_into(self.ui.fra_chart, rows, "Doanh Thu Theo Ngày")

    def _report_excel(self):
        if not self._report_data: msg_warn(self, "Không có dữ liệu!"); return
        try:
            path = export_excel(self._report_data,
                                ["Ngày", "Doanh Thu (đ)", "Số Booking"],
                                ["day", "revenue", "bookings"], "BaoCaoDoanhThu")
            msg_info(self, f"Xuất Excel thành công!\n{path}")
        except Exception as e:
            msg_error(self, str(e))

    def _report_pdf(self):
        if not self._report_data: msg_warn(self, "Không có dữ liệu!"); return
        try:
            path = export_pdf(self._report_data,
                              ["Ngày", "Doanh Thu (đ)", "Số Booking"],
                              ["day", "revenue", "bookings"], "BaoCaoDoanhThu")
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


class RoomTypeDialog(_Base):
    """Dialog thêm / sửa loại phòng."""
    def __init__(self, parent=None, rtype=None):
        super().__init__(parent, "Thêm loại phòng" if rtype is None else "Sửa loại phòng")
        self.le_name  = QtWidgets.QLineEdit()
        self.sb_price = QtWidgets.QDoubleSpinBox()
        self.sb_price.setRange(0, 100_000_000)
        self.sb_price.setSingleStep(50_000)
        self.sb_price.setSuffix(" đ")
        self.sb_price.setGroupSeparatorShown(True)
        self.le_desc  = QtWidgets.QLineEdit()
        self._form.addRow("Tên loại phòng *", self.le_name)
        self._form.addRow("Giá cơ bản / đêm *", self.sb_price)
        self._form.addRow("Mô tả", self.le_desc)
        if rtype:
            self.le_name.setText(rtype.get("name", ""))
            self.sb_price.setValue(float(rtype.get("base_price", 0)))
            self.le_desc.setText(rtype.get("description", "") or "")

    def _validate(self):
        if not self.le_name.text().strip():
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Nhập tên loại phòng!"); return False
        if self.sb_price.value() <= 0:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Giá phải lớn hơn 0!"); return False
        return True

    def get_data(self):
        return {
            "name":        self.le_name.text().strip(),
            "base_price":  self.sb_price.value(),
            "description": self.le_desc.text().strip(),
        }


class RoomDialog(_Base):
    def __init__(self, parent=None, room=None):
        super().__init__(parent, "Thêm phòng" if room is None else "Sửa phòng")
        self.le_num  = QtWidgets.QLineEdit()
        self.sb_fl   = QtWidgets.QSpinBox(); self.sb_fl.setRange(1, 50)
        self.cb_type = QtWidgets.QComboBox()
        self.cb_stat = QtWidgets.QComboBox()
        # Hiển thị tiếng Việt, lưu giá trị DB trong itemData
        for label, val in [
            ("🟢  Còn trống",  "available"),
            ("🔴  Đang thuê",  "occupied"),
            ("🔧  Bảo trì",    "maintenance"),
        ]:
            self.cb_stat.addItem(label, val)
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
            idx = self.cb_stat.findData(room["status"])
            if idx >= 0: self.cb_stat.setCurrentIndex(idx)
            self.le_desc.setText(room.get("description") or "")

    def _validate(self):
        if not self.le_num.text().strip():
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Nhập số phòng!"); return False
        return True

    def get_data(self):
        return {"room_number": self.le_num.text().strip(), "floor": self.sb_fl.value(),
                "type_id": self.cb_type.currentData(), "status": self.cb_stat.currentData(),
                "description": self.le_desc.text().strip()}


class CustomerDialog(_Base):
    def __init__(self, parent=None, cust=None):
        super().__init__(parent, "Thêm khách hàng" if cust is None else "Sửa khách hàng")
        self.le_name = QtWidgets.QLineEdit()
        self.le_id   = QtWidgets.QLineEdit()
        self.le_ph   = QtWidgets.QLineEdit()
        self.le_em   = QtWidgets.QLineEdit()
        self.le_addr = QtWidgets.QLineEdit()
        self._form.addRow("Họ tên *",     self.le_name)
        self._form.addRow("CCCD *",       self.le_id)
        self._form.addRow("Điện thoại *", self.le_ph)
        self._form.addRow("Email",        self.le_em)
        self._form.addRow("Địa chỉ",     self.le_addr)
        if cust:
            self.le_name.setText(cust.get("full_name", ""))
            self.le_id.setText(cust.get("id_card", ""))
            self.le_ph.setText(cust.get("phone", ""))
            self.le_em.setText(cust.get("email", "") or "")
            self.le_addr.setText(cust.get("address", "") or "")

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
        self.le_pass = QtWidgets.QLineEdit()
        self.le_pass.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.cb_role = QtWidgets.QComboBox(); self.cb_role.addItems(["staff", "admin"])
        self.cb_act  = QtWidgets.QComboBox(); self.cb_act.addItems(["1 – Hoạt động", "0 – Vô hiệu"])
        self._form.addRow("Họ tên *",   self.le_name)
        self._form.addRow("Username *", self.le_user)
        if not self._edit: self._form.addRow("Mật khẩu *", self.le_pass)
        self._form.addRow("Vai trò",    self.cb_role)
        if self._edit: self._form.addRow("Trạng thái", self.cb_act)
        if staff:
            self.le_name.setText(staff.get("full_name", ""))
            self.le_user.setText(staff.get("username", ""))
            self.le_user.setEnabled(False)
            idx = self.cb_role.findText(staff.get("role", "staff"))
            if idx >= 0: self.cb_role.setCurrentIndex(idx)
            self.cb_act.setCurrentIndex(0 if staff.get("is_active", 1) == 1 else 1)

    def _validate(self):
        if not self.le_name.text().strip() or not self.le_user.text().strip():
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Điền đầy đủ!"); return False
        if not self._edit and not self.le_pass.text().strip():
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Nhập mật khẩu!"); return False
        return True

    def get_data(self):
        return {"full_name": self.le_name.text().strip(), "username": self.le_user.text().strip(),
                "password": self.le_pass.text().strip(), "role": self.cb_role.currentText(),
                "is_active": 1 if self.cb_act.currentIndex() == 0 else 0}


class ServiceDialog(_Base):
    def __init__(self, parent=None, svc=None):
        super().__init__(parent, "Thêm dịch vụ" if svc is None else "Sửa dịch vụ")
        self.le_name = QtWidgets.QLineEdit()
        self.sb_pr   = QtWidgets.QDoubleSpinBox()
        self.sb_pr.setRange(0, 100_000_000); self.sb_pr.setSuffix(" đ")
        self.le_unit = QtWidgets.QLineEdit()
        self.le_desc = QtWidgets.QLineEdit()
        self.cb_act  = QtWidgets.QComboBox(); self.cb_act.addItems(["1 – Hoạt động", "0 – Vô hiệu"])
        self._form.addRow("Tên dịch vụ *", self.le_name)
        self._form.addRow("Giá *",         self.sb_pr)
        self._form.addRow("Đơn vị *",      self.le_unit)
        self._form.addRow("Mô tả",         self.le_desc)
        self._form.addRow("Trạng thái",    self.cb_act)
        if svc:
            self.le_name.setText(svc.get("name", ""))
            self.sb_pr.setValue(float(svc.get("price", 0)))
            self.le_unit.setText(svc.get("unit", ""))
            self.le_desc.setText(svc.get("description", "") or "")
            self.cb_act.setCurrentIndex(0 if svc.get("is_active", 1) == 1 else 1)

    def _validate(self):
        if not self.le_name.text().strip() or not self.le_unit.text().strip():
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Điền tên và đơn vị!"); return False
        return True

    def get_data(self):
        return {"name": self.le_name.text().strip(), "price": self.sb_pr.value(),
                "unit": self.le_unit.text().strip(), "description": self.le_desc.text().strip(),
                "is_active": 1 if self.cb_act.currentIndex() == 0 else 0}