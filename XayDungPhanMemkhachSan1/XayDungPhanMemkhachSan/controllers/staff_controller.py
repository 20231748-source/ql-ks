from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QHeaderView, QSizePolicy
from views.Staff import Ui_StaffWindow
from models.room_model import RoomModel
from models.customer_model import CustomerModel
from models.booking_model import BookingModel
from models.service_model import ServiceModel
from models.invoice_model import InvoiceModel
from models.user_model import UserModel
from models.activity_log_model import ActivityLogModel
from utils.helpers import (msg_info, msg_warn, msg_error, msg_confirm,
                            fill_table, fmt_money, STATUS_VI)
from datetime import date, timedelta


class StaffWindow(QtWidgets.QMainWindow):
    PAGE_CHECKIN  = 0
    PAGE_CHECKOUT = 1
    PAGE_ROOMS    = 2
    PAGE_SERVICE  = 3
    PAGE_INVOICE  = 4
    PAGE_PROFILE  = 5

    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.ui = Ui_StaffWindow()
        self.ui.setupUi(self)
        self.setWindowTitle(f"Hotel Staff – {user['full_name']}")

        self._checkout_booking_id = None
        self._invoice_booking_id  = None
        self._invoice_calc        = None

        # Ghi log đăng nhập
        ActivityLogModel.log(
            user["id"], user["username"], user["full_name"],
            "Đăng nhập", "Giao diện nhân viên"
        )

        self._connect_sidebar()
        self._connect_checkin()
        self._connect_checkout()
        self._connect_rooms()
        self._connect_service()
        self._connect_invoice()
        self._connect_profile()
        self._goto(self.PAGE_CHECKIN)

        QtCore.QTimer.singleShot(0, self._post_show_setup)

    def _post_show_setup(self):
        self._setup_tables()
        self._setup_profile_center()

    def _setup_tables(self):
        self._all_tables = [
            self.ui.tbl_checkout_list,
            self.ui.tbl_rooms,
            self.ui.tbl_services_used,
            self.ui.tbl_inv_services,
        ]
        for tbl in self._all_tables:
            h = tbl.horizontalHeader()
            h.setStretchLastSection(False)
            h.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            tbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def _refresh_table_columns(self):
        if not hasattr(self, '_all_tables'):
            return
        for tbl in self._all_tables:
            tbl.horizontalHeader().resizeSections(QHeaderView.ResizeMode.Stretch)
            tbl.updateGeometry()

    def _setup_profile_center(self):
        pg_layout = self.ui.pg_profile.layout()
        target_frame = None
        for i in range(pg_layout.count()):
            item = pg_layout.itemAt(i)
            w = item.widget() if item else None
            if w and isinstance(w, QtWidgets.QFrame):
                if isinstance(w.layout(), QtWidgets.QFormLayout):
                    target_frame = w
                    frame_index = i
                    break
        if target_frame is None:
            return
        if target_frame.parent() is not self.ui.pg_profile:
            return
        target_frame.setMaximumWidth(16777215)
        target_frame.setFixedWidth(560)
        wrapper = QtWidgets.QWidget()
        wl = QtWidgets.QHBoxLayout(wrapper)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(0)
        pg_layout.removeWidget(target_frame)
        wl.addStretch()
        wl.addWidget(target_frame)
        wl.addStretch()
        pg_layout.insertWidget(frame_index, wrapper)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _connect_sidebar(self):
        self._nav_buttons = [
            self.ui.btn_nav_checkin,
            self.ui.btn_nav_checkout,
            self.ui.btn_nav_rooms,
            self.ui.btn_nav_service,
            self.ui.btn_nav_invoice,
            self.ui.btn_nav_profile,
        ]

        self.ui.sidebar.setStyleSheet("""
QFrame#sidebar {
    background-color: #1A2A4A;
    border: none;
    border-right: 2px solid #C9A84C;
}
QLabel#lbl_app_title {
    background-color: #12213A;
    color: #C9A84C;
    font-size: 15px;
    font-weight: bold;
    padding: 18px 12px;
    border-bottom: 2px solid #C9A84C;
    border-right: none;
}
QFrame#sidebar QPushButton {
    background-color: transparent;
    color: #B8C4D8;
    font-size: 13px;
    font-weight: 500;
    text-align: left;
    padding: 12px 18px;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0px;
}
QFrame#sidebar QPushButton:hover {
    background-color: #243558;
    color: #FFFFFF;
    border-left: 3px solid #C9A84C;
}
QFrame#sidebar QPushButton[active=true] {
    background-color: #2C4070;
    color: #FFFFFF;
    border-left: 4px solid #C9A84C;
    font-weight: bold;
}
QFrame#sidebar QPushButton[active=true]:hover {
    background-color: #2C4070;
    color: #FFFFFF;
    border-left: 4px solid #C9A84C;
}
QPushButton#btn_logout {
    background-color: transparent;
    color: #E8A0A0;
    font-size: 13px;
    text-align: left;
    padding: 12px 18px;
    border: none;
    border-top: 1px solid #2A3D5E;
    border-left: 3px solid transparent;
    border-radius: 0px;
}
QPushButton#btn_logout:hover {
    background-color: #4A1818;
    color: #FFFFFF;
    border-left: 3px solid #E8A0A0;
}
""")
        self.ui.btn_logout.clicked.connect(self._logout)
        self.ui.btn_nav_checkin.clicked.connect(lambda: self._goto(self.PAGE_CHECKIN))
        self.ui.btn_nav_checkout.clicked.connect(lambda: self._goto(self.PAGE_CHECKOUT))
        self.ui.btn_nav_rooms.clicked.connect(lambda: self._goto(self.PAGE_ROOMS))
        self.ui.btn_nav_invoice.clicked.connect(lambda: self._goto(self.PAGE_INVOICE))
        self.ui.btn_nav_service.clicked.connect(lambda: self._goto(self.PAGE_SERVICE))
        self.ui.btn_nav_profile.clicked.connect(lambda: self._goto(self.PAGE_PROFILE))

    def _set_active_nav(self, index: int):
        for i, btn in enumerate(self._nav_buttons):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _goto(self, index: int):
        self.ui.stackedWidget.setCurrentIndex(index)
        self._set_active_nav(index)
        {
            self.PAGE_CHECKIN:  self._load_checkin,
            self.PAGE_CHECKOUT: self._load_checkout,
            self.PAGE_ROOMS:    self._load_rooms,
            self.PAGE_SERVICE:  self._load_service,
            self.PAGE_INVOICE:  self._reset_invoice_ui,
            self.PAGE_PROFILE:  self._load_profile,
        }[index]()
        QtCore.QTimer.singleShot(0, self._refresh_table_columns)

    def _logout(self):
        if msg_confirm(self, "Bạn có muốn đăng xuất không?"):
            ActivityLogModel.log(
                self.user["id"], self.user["username"], self.user["full_name"],
                "Đăng xuất", ""
            )
            self.close()
            from controllers.login_controller import LoginWindow
            self._login_win = LoginWindow()
            self._login_win.exec()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 0: CHECK-IN — Đặt nhiều phòng, tìm khách cũ
    # ══════════════════════════════════════════════════════════════════════════
    def _connect_checkin(self):
        # Các nút sẽ được inject sau khi _inject_checkin_ui() chạy
        pass

    def _load_checkin(self):
        if not hasattr(self, "_checkin_injected"):
            self._inject_checkin_ui()
        self._checkin_reset()

    def _inject_checkin_ui(self):
        """
        Thay thế form check-in cũ bằng form mới hỗ trợ:
        - Tìm khách cũ theo CCCD / tên (tự điền thông tin)
        - Chọn nhiều phòng (QListWidget với multi-select)
        - Hiển thị lịch sử đặt phòng của khách đó
        """
        self._checkin_injected = True
        page_layout = self.ui.pg_checkin.layout()  # checkinPageLayout

        # Xóa fra_checkin_form cũ
        for i in range(page_layout.count() - 1, -1, -1):
            item = page_layout.itemAt(i)
            w = item.widget() if item else None
            if w and w.objectName() == "fra_checkin_form":
                page_layout.removeWidget(w)
                w.deleteLater()
                break

        # ── Container chính: splitter trái/phải ──
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background: #D3CECC; width: 2px; }")

        # ══ PANEL TRÁI: Form đặt phòng ══════════════════════════════════════
        left = QtWidgets.QFrame()
        left.setStyleSheet(
            "QFrame{background:#FFFFFF;border:1px solid #D3CECC;border-radius:8px;}"
            "QLabel{border:none;color:#1A2A4A;font-size:13px;font-weight:bold;}"
            "QLineEdit,QComboBox,QDateEdit{border:1.5px solid #D1D5DB;border-radius:6px;"
            "padding:7px 10px;font-size:13px;color:#1A2A4A;background:#FAFAFA;}"
            "QLineEdit:focus,QComboBox:focus,QDateEdit:focus{border-color:#1A2A4A;background:#FFF;}"
        )
        ll = QtWidgets.QVBoxLayout(left)
        ll.setContentsMargins(20, 16, 20, 16)
        ll.setSpacing(12)

        # -- Tiêu đề --
        hdr = QtWidgets.QLabel("📝  Thông Tin Đặt Phòng")
        hdr.setStyleSheet("font-size:15px;font-weight:bold;color:#1A2A4A;border:none;padding-bottom:4px;")
        ll.addWidget(hdr)

        # -- Tìm khách cũ --
        search_row = QtWidgets.QHBoxLayout()
        self._inp_ci_search = QtWidgets.QLineEdit()
        self._inp_ci_search.setPlaceholderText("🔍  Nhập CCCD hoặc tên khách để tìm khách cũ...")
        self._btn_ci_find = QtWidgets.QPushButton("Tìm")
        self._btn_ci_find.setStyleSheet(
            "QPushButton{background:#1A2A4A;color:#FFF;border:none;border-radius:6px;"
            "padding:8px 16px;font-size:13px;font-weight:bold;}"
            "QPushButton:hover{background:#C9A84C;color:#1A2A4A;}")
        search_row.addWidget(self._inp_ci_search)
        search_row.addWidget(self._btn_ci_find)
        ll.addLayout(search_row)

        # Nhãn thông báo khách cũ/mới
        self._lbl_ci_status = QtWidgets.QLabel("")
        self._lbl_ci_status.setStyleSheet(
            "border:none;font-size:12px;font-weight:normal;color:#2E7D32;padding:2px 0;")
        ll.addWidget(self._lbl_ci_status)

        # -- Form grid --
        form = QtWidgets.QGridLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)

        def lbl(t): return QtWidgets.QLabel(t)

        self._inp_ci_name   = QtWidgets.QLineEdit()
        self._inp_ci_idcard = QtWidgets.QLineEdit()
        self._inp_ci_phone  = QtWidgets.QLineEdit()
        self._inp_ci_name.setPlaceholderText("Họ và Tên *")
        self._inp_ci_idcard.setPlaceholderText("Số CCCD *")
        self._inp_ci_phone.setPlaceholderText("Số điện thoại *")

        form.addWidget(lbl("Họ và Tên *"),   0, 0); form.addWidget(self._inp_ci_name,   0, 1)
        form.addWidget(lbl("CCCD *"),         0, 2); form.addWidget(self._inp_ci_idcard, 0, 3)
        form.addWidget(lbl("Điện thoại *"),   1, 0); form.addWidget(self._inp_ci_phone,  1, 1)

        # Ngày check-in / check-out
        today    = date.today()
        tomorrow = today + timedelta(days=1)

        self._de_ci_checkin  = QtWidgets.QDateEdit()
        self._de_ci_checkout = QtWidgets.QDateEdit()
        self._de_ci_checkin.setCalendarPopup(True)
        self._de_ci_checkout.setCalendarPopup(True)
        self._de_ci_checkin.setDate(QtCore.QDate(today.year, today.month, today.day))
        self._de_ci_checkout.setDate(QtCore.QDate(tomorrow.year, tomorrow.month, tomorrow.day))

        # ── Style cho QDateEdit + calendar popup ──────────────────────────────
        # Phải style đầy đủ QCalendarWidget ở đây vì frame cha có nền tối
        # sẽ kế thừa xuống popup và làm ẩn chữ ngày.
        _date_style = (
            # ── Input field ──
            "QDateEdit {"
            "  border: 1.5px solid #D1D5DB; border-radius: 6px;"
            "  padding: 7px 10px; font-size: 13px;"
            "  color: #1A2A4A; background: #FFFFFF;"
            "}"
            "QDateEdit:focus { border-color: #1A2A4A; background: #FFFFFF; }"
            # ── Spin buttons ──
            "QDateEdit::up-button { subcontrol-origin: border; subcontrol-position: top right;"
            "  width: 20px; border-left: 1px solid #D1D5DB; border-bottom: 1px solid #D1D5DB;"
            "  background: #F5F5F5; border-radius: 0 6px 0 0; }"
            "QDateEdit::down-button { subcontrol-origin: border; subcontrol-position: bottom right;"
            "  width: 20px; border-left: 1px solid #D1D5DB; border-top: 1px solid #D1D5DB;"
            "  background: #F5F5F5; border-radius: 0 0 6px 0; }"
            "QDateEdit::up-arrow   { width:7px; height:7px;"
            "  border-left:4px solid transparent; border-right:4px solid transparent;"
            "  border-bottom:6px solid #1A2A4A; }"
            "QDateEdit::down-arrow { width:7px; height:7px;"
            "  border-left:4px solid transparent; border-right:4px solid transparent;"
            "  border-top:6px solid #1A2A4A; }"

            # ── Calendar popup — reset hoàn toàn về nền trắng chữ đen ──
            "QCalendarWidget {"
            "  background-color: #FFFFFF; color: #1A2A4A;"
            "}"
            # Navigation bar (Tháng Năm / mũi tên)
            "QCalendarWidget QWidget#qt_calendar_navigationbar {"
            "  background-color: #1A2A4A;"
            "}"
            "QCalendarWidget QToolButton {"
            "  color: #FFFFFF; background: transparent;"
            "  font-size: 13px; font-weight: bold; border: none; padding: 4px 8px;"
            "}"
            "QCalendarWidget QToolButton:hover { background: #2C4070; border-radius: 4px; }"
            "QCalendarWidget QToolButton::menu-indicator { image: none; }"
            "QCalendarWidget QSpinBox {"
            "  color: #FFFFFF; background: transparent;"
            "  font-size: 13px; font-weight: bold; border: none;"
            "  selection-background-color: #C9A84C; selection-color: #1A2A4A;"
            "}"
            "QCalendarWidget QSpinBox::up-button, QCalendarWidget QSpinBox::down-button"
            "  { width: 0; }"

            # Header ngày trong tuần (T2–CN)
            "QCalendarWidget QWidget { alternate-background-color: #F7F5F0; }"
            "QCalendarWidget QAbstractItemView {"
            "  background-color: #FFFFFF; color: #1A2A4A;"
            "  selection-background-color: #1A2A4A; selection-color: #FFFFFF;"
            "  font-size: 13px;"
            "}"
            "QCalendarWidget QAbstractItemView:enabled {"
            "  color: #1A2A4A; background-color: #FFFFFF;"
            "}"
            "QCalendarWidget QAbstractItemView:disabled { color: #AAAAAA; }"
        )
        self._de_ci_checkin.setStyleSheet(_date_style)
        self._de_ci_checkout.setStyleSheet(_date_style)

        form.addWidget(lbl("Check-in *"),  2, 0); form.addWidget(self._de_ci_checkin,  2, 1)
        form.addWidget(lbl("Check-out *"), 2, 2); form.addWidget(self._de_ci_checkout, 2, 3)

        # Ghi chú
        self._inp_ci_notes = QtWidgets.QLineEdit()
        self._inp_ci_notes.setPlaceholderText("Ghi chú (không bắt buộc)")
        form.addWidget(lbl("Ghi chú"), 3, 0)
        form.addWidget(self._inp_ci_notes, 3, 1, 1, 3)

        ll.addLayout(form)

        # -- Chọn phòng (multi-select) --
        room_lbl = QtWidgets.QLabel("Chọn phòng (có thể chọn nhiều) *")
        room_lbl.setStyleSheet("font-size:13px;font-weight:bold;color:#1A2A4A;border:none;")
        ll.addWidget(room_lbl)

        self._lst_ci_rooms = QtWidgets.QListWidget()
        self._lst_ci_rooms.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
        self._lst_ci_rooms.setStyleSheet(
            "QListWidget{border:1.5px solid #D1D5DB;border-radius:6px;background:#FAFAFA;"
            "font-size:13px;color:#1A2A4A;}"
            "QListWidget::item{padding:8px 12px;border-bottom:1px solid #EEEBE5;}"
            "QListWidget::item:selected{background:#1A2A4A;color:#C9A84C;font-weight:bold;}"
            "QListWidget::item:hover:!selected{background:#F0EDE6;}"
        )
        self._lst_ci_rooms.setMinimumHeight(130)
        self._lst_ci_rooms.setMaximumHeight(180)
        ll.addWidget(self._lst_ci_rooms)

        # Nhãn số phòng đã chọn + giá ước tính
        self._lbl_ci_room_info = QtWidgets.QLabel("Chưa chọn phòng nào.")
        self._lbl_ci_room_info.setStyleSheet(
            "border:none;font-size:12px;font-weight:normal;color:#6B7896;")
        ll.addWidget(self._lbl_ci_room_info)

        # -- Nút hành động --
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setSpacing(10)
        self._btn_ci_confirm = QtWidgets.QPushButton("✅  Xác Nhận Check-in")
        self._btn_ci_cancel  = QtWidgets.QPushButton("🗑  Hủy Booking")
        self._btn_ci_confirm.setStyleSheet(
            "QPushButton{background:#1A2A4A;color:#FFF;border:none;border-radius:7px;"
            "padding:10px 22px;font-size:13px;font-weight:bold;}"
            "QPushButton:hover{background:#C9A84C;color:#1A2A4A;}")
        self._btn_ci_cancel.setStyleSheet(
            "QPushButton{background:#FFF;color:#A32D2D;border:1.5px solid #A32D2D;"
            "border-radius:7px;padding:10px 22px;font-size:13px;}"
            "QPushButton:hover{background:#FDECEA;}")
        btn_row.addStretch()
        btn_row.addWidget(self._btn_ci_confirm)
        btn_row.addWidget(self._btn_ci_cancel)
        ll.addLayout(btn_row)
        ll.addStretch()

        # ══ PANEL PHẢI: Lịch sử khách ════════════════════════════════════════
        right = QtWidgets.QFrame()
        right.setStyleSheet(
            "QFrame{background:#FFFFFF;border:1px solid #D3CECC;border-radius:8px;}"
            "QLabel{border:none;}")
        rl = QtWidgets.QVBoxLayout(right)
        rl.setContentsMargins(16, 16, 16, 16)
        rl.setSpacing(10)

        rh = QtWidgets.QLabel("📖  Lịch Sử Đặt Phòng Của Khách")
        rh.setStyleSheet("font-size:14px;font-weight:bold;color:#1A2A4A;border:none;")
        rl.addWidget(rh)

        self._tbl_ci_history = QtWidgets.QTableWidget()
        self._tbl_ci_history.setColumnCount(5)
        self._tbl_ci_history.setHorizontalHeaderLabels(
            ["Phòng", "Check-in", "Check-out", "Trạng Thái", "Ngày Tạo"])
        self._tbl_ci_history.setAlternatingRowColors(True)
        self._tbl_ci_history.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self._tbl_ci_history.verticalHeader().setVisible(False)
        self._tbl_ci_history.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tbl_ci_history.setStyleSheet(
            "QTableWidget{background:#FFF;alternate-background-color:#F0EDE6;"
            "border:1px solid #D3CECC;border-radius:6px;gridline-color:#E5E0D8;"
            "font-size:12px;}"
            "QTableWidget::item{padding:6px 8px;color:#1A2A4A;}"
            "QTableWidget::item:selected{background:#D6E8F7;}"
            "QHeaderView::section{background:#1A2A4A;color:#FFF;font-weight:bold;"
            "font-size:12px;padding:8px 8px;border:none;border-right:1px solid #223259;}"
        )
        h = self._tbl_ci_history.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        rl.addWidget(self._tbl_ci_history)

        self._lbl_ci_hist_empty = QtWidgets.QLabel(
            "💡  Nhập CCCD và bấm Tìm để xem lịch sử.")
        self._lbl_ci_hist_empty.setStyleSheet(
            "border:none;font-size:12px;color:#9E9E9E;padding:8px 0;")
        self._lbl_ci_hist_empty.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        rl.addWidget(self._lbl_ci_hist_empty)

        # -- Nút đặt lại phòng từ booking cũ --
        self._btn_ci_rebook = QtWidgets.QPushButton("🔄  Đặt Lại Phòng Này")
        self._btn_ci_rebook.setStyleSheet(
            "QPushButton{background:#2E7D32;color:#FFF;border:none;border-radius:6px;"
            "padding:8px 16px;font-size:13px;font-weight:bold;}"
            "QPushButton:hover{background:#1B5E20;}"
            "QPushButton:disabled{background:#BDBDBD;color:#757575;}")
        self._btn_ci_rebook.setEnabled(False)
        rl.addWidget(self._btn_ci_rebook)

        # ── Ghép 2 panel vào splitter ──
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 6)
        splitter.setStretchFactor(1, 4)
        # Đặt kích thước ban đầu (pixels) để splitter không bị collapse
        splitter.setSizes([600, 400])

        page_layout.addWidget(splitter)

        # ── Connect signals ──
        self._btn_ci_find.clicked.connect(self._ci_find_customer)
        self._inp_ci_search.returnPressed.connect(self._ci_find_customer)
        self._inp_ci_idcard.editingFinished.connect(self._ci_autofill_by_idcard)
        self._btn_ci_confirm.clicked.connect(self._do_checkin)
        self._btn_ci_cancel.clicked.connect(self._do_cancel_booking)
        self._btn_ci_rebook.clicked.connect(self._ci_rebook)
        self._lst_ci_rooms.itemSelectionChanged.connect(self._ci_update_room_info)
        self._de_ci_checkin.dateChanged.connect(self._ci_update_room_info)
        self._de_ci_checkout.dateChanged.connect(self._ci_update_room_info)
        self._tbl_ci_history.cellClicked.connect(self._ci_history_select)

        self._ci_selected_booking = None   # booking row đang chọn từ history

    def _checkin_reset(self):
        """Reset toàn bộ form check-in."""
        self._inp_ci_name.clear()
        self._inp_ci_idcard.clear()
        self._inp_ci_phone.clear()
        self._inp_ci_notes.clear()
        self._inp_ci_search.clear()
        self._lbl_ci_status.setText("")
        self._lbl_ci_room_info.setText("Chưa chọn phòng nào.")
        today    = date.today()
        tomorrow = today + timedelta(days=1)
        self._de_ci_checkin.setDate(QtCore.QDate(today.year, today.month, today.day))
        self._de_ci_checkout.setDate(QtCore.QDate(tomorrow.year, tomorrow.month, tomorrow.day))
        self._reload_room_list()
        self._tbl_ci_history.setRowCount(0)
        self._lbl_ci_hist_empty.setText("💡  Nhập CCCD và bấm Tìm để xem lịch sử.")
        self._lbl_ci_hist_empty.show()
        self._btn_ci_rebook.setEnabled(False)
        self._ci_selected_booking = None
        self._ci_customer = None   # khách đang làm việc

    def _reload_room_list(self):
        self._lst_ci_rooms.clear()
        self._available_rooms = RoomModel.get_available()
        for r in self._available_rooms:
            item = QtWidgets.QListWidgetItem(
                f"Phòng {r['room_number']}  |  {r['type_name']}  |  "
                f"{int(r['base_price']):,} đ/đêm  |  Tầng {r['floor']}"
            )
            item.setData(QtCore.Qt.ItemDataRole.UserRole, r["id"])
            self._lst_ci_rooms.addItem(item)

    def _ci_find_customer(self):
        """Tìm khách theo CCCD hoặc tên."""
        kw = self._inp_ci_search.text().strip()
        if not kw:
            msg_warn(self, "Nhập CCCD hoặc tên để tìm!"); return

        # Thử tìm chính xác theo CCCD trước
        cust = CustomerModel.find_by_idcard(kw)
        if not cust:
            # Tìm theo tên (lấy đầu tiên)
            results = CustomerModel.search(kw)
            if results:
                if len(results) > 1:
                    # Nhiều kết quả → cho chọn
                    names = [f"{r['full_name']} | {r['id_card']} | {r['phone']}"
                             for r in results]
                    chosen, ok = QtWidgets.QInputDialog.getItem(
                        self, "Chọn khách hàng",
                        f"Tìm thấy {len(results)} khách — chọn một:",
                        names, 0, False)
                    if not ok: return
                    idx = names.index(chosen)
                    cust = results[idx]
                else:
                    cust = results[0]

        if cust:
            self._ci_fill_customer(cust)
            self._ci_load_history(cust["id"])
        else:
            self._lbl_ci_status.setText("⚠  Không tìm thấy — khách mới, điền thông tin bên dưới.")
            self._lbl_ci_status.setStyleSheet(
                "border:none;font-size:12px;color:#E65100;")
            self._tbl_ci_history.setRowCount(0)
            self._lbl_ci_hist_empty.setText("Không có lịch sử — đây là khách mới.")
            self._btn_ci_rebook.setEnabled(False)
            self._ci_customer = None

    def _ci_autofill_by_idcard(self):
        """Tự động điền nếu CCCD đã có trong DB (không hiển thị dialog)."""
        id_card = self._inp_ci_idcard.text().strip()
        if not id_card:
            return
        cust = CustomerModel.find_by_idcard(id_card)
        if cust:
            self._ci_fill_customer(cust)
            self._ci_load_history(cust["id"])

    def _ci_fill_customer(self, cust: dict):
        self._ci_customer = cust
        self._inp_ci_name.setText(cust.get("full_name", ""))
        self._inp_ci_idcard.setText(cust.get("id_card", ""))
        self._inp_ci_phone.setText(cust.get("phone", ""))
        self._lbl_ci_status.setText(
            f"✅  Khách cũ: {cust['full_name']} | CCCD: {cust['id_card']}")
        self._lbl_ci_status.setStyleSheet(
            "border:none;font-size:12px;color:#2E7D32;font-weight:bold;")

    def _ci_load_history(self, customer_id: int):
        """Hiển thị lịch sử booking của khách."""
        all_bookings = BookingModel.get_all()
        history = [b for b in all_bookings if b.get("customer_id") == customer_id]
        if history:
            fill_table(
                self._tbl_ci_history, history,
                ["room", "check_in", "check_out", "status", "created_at"],
                status_map=STATUS_VI
            )
            self._lbl_ci_hist_empty.hide()
        else:
            self._tbl_ci_history.setRowCount(0)
            self._lbl_ci_hist_empty.setText("Chưa có lịch sử đặt phòng.")
            self._lbl_ci_hist_empty.show()
        self._booking_history = history
        self._btn_ci_rebook.setEnabled(False)
        self._ci_selected_booking = None

    def _ci_history_select(self, row: int, _col: int):
        """Chọn một booking trong lịch sử."""
        if hasattr(self, "_booking_history") and row < len(self._booking_history):
            self._ci_selected_booking = self._booking_history[row]
            self._btn_ci_rebook.setEnabled(True)

    def _ci_rebook(self):
        """Chọn lại phòng giống booking cũ (nếu phòng còn trống)."""
        if not self._ci_selected_booking:
            msg_warn(self, "Chọn một lần đặt phòng cũ ở bảng lịch sử!"); return
        old_room_id = self._ci_selected_booking.get("room_id")
        # Tìm item trong danh sách phòng trống
        found = False
        for i in range(self._lst_ci_rooms.count()):
            item = self._lst_ci_rooms.item(i)
            if item.data(QtCore.Qt.ItemDataRole.UserRole) == old_room_id:
                self._lst_ci_rooms.clearSelection()
                item.setSelected(True)
                self._lst_ci_rooms.scrollToItem(item)
                found = True
                break
        if not found:
            msg_warn(self, f"Phòng {self._ci_selected_booking.get('room', '?')} "
                          f"hiện không trống — chọn phòng khác.")

    def _ci_update_room_info(self):
        """Cập nhật nhãn thông tin phòng đã chọn + ước tính giá."""
        selected = self._lst_ci_rooms.selectedItems()
        if not selected:
            self._lbl_ci_room_info.setText("Chưa chọn phòng nào.")
            return

        ci = self._de_ci_checkin.date().toPyDate()
        co = self._de_ci_checkout.date().toPyDate()
        nights = max((co - ci).days, 1)

        total_est = 0.0
        room_labels = []
        for item in selected:
            rid = item.data(QtCore.Qt.ItemDataRole.UserRole)
            r = next((x for x in self._available_rooms if x["id"] == rid), None)
            if r:
                room_labels.append(f"Phòng {r['room_number']}")
                total_est += r["base_price"] * nights

        rooms_str = ", ".join(room_labels)
        self._lbl_ci_room_info.setText(
            f"✔ {len(selected)} phòng: {rooms_str}  |  "
            f"{nights} đêm  |  Ước tính: {fmt_money(total_est)} (chưa VAT)"
        )
        self._lbl_ci_room_info.setStyleSheet(
            "border:none;font-size:12px;font-weight:normal;color:#1565C0;")

    def _do_checkin(self):
        full_name = self._inp_ci_name.text().strip()
        id_card   = self._inp_ci_idcard.text().strip()
        phone     = self._inp_ci_phone.text().strip()
        notes     = self._inp_ci_notes.text().strip()
        check_in  = self._de_ci_checkin.date().toString("yyyy-MM-dd")
        check_out = self._de_ci_checkout.date().toString("yyyy-MM-dd")

        if not full_name: msg_warn(self, "Vui lòng nhập Họ và Tên khách!"); return
        if not id_card:   msg_warn(self, "Vui lòng nhập số CCCD!"); return
        if not phone:     msg_warn(self, "Vui lòng nhập số điện thoại!"); return

        selected_items = self._lst_ci_rooms.selectedItems()
        if not selected_items:
            msg_warn(self, "Vui lòng chọn ít nhất một phòng!"); return

        ci_date = self._de_ci_checkin.date().toPyDate()
        co_date = self._de_ci_checkout.date().toPyDate()
        if ci_date >= co_date:
            msg_warn(self, "Ngày trả phòng phải sau ngày nhận!"); return

        room_ids = [item.data(QtCore.Qt.ItemDataRole.UserRole) for item in selected_items]

        # Tìm / tạo khách hàng
        cust = CustomerModel.find_by_idcard(id_card)
        if cust is None:
            ok, err = CustomerModel.add(full_name, id_card, phone, "", "")
            if not ok:
                msg_error(self, f"Lỗi tạo khách hàng: {err}"); return
            cust = CustomerModel.find_by_idcard(id_card)
        else:
            # Cập nhật tên/phone nếu khác
            if cust["full_name"] != full_name or cust["phone"] != phone:
                CustomerModel.update(cust["id"], full_name, id_card, phone,
                                     cust.get("email", ""), cust.get("address", ""))

        # Đặt từng phòng
        booked_rooms = []
        errors = []
        for rid in room_ids:
            ok, msg, booking_id = BookingModel.create(
                cust["id"], rid, self.user["id"], check_in, check_out, notes
            )
            if ok:
                booked_rooms.append(booking_id)
            else:
                errors.append(msg)

        if booked_rooms:
            room_nums = [item.text().split("|")[0].strip() for item in selected_items
                         if item.data(QtCore.Qt.ItemDataRole.UserRole) in room_ids]
            success_msg = (
                f"Đặt phòng thành công!\n"
                f"Khách: {full_name}\n"
                f"Mã booking: {', '.join(f'#{b}' for b in booked_rooms)}"
            )
            if errors:
                success_msg += f"\n\n⚠ Lỗi một số phòng:\n" + "\n".join(errors)
            msg_info(self, success_msg)
            ActivityLogModel.log(
                self.user["id"], self.user["username"], self.user["full_name"],
                "Check-in",
                f"Khách: {full_name} | Phòng: {', '.join(room_nums)} | "
                f"{check_in} → {check_out}"
            )
            self._checkin_reset()
        else:
            msg_error(self, "Không đặt được phòng nào!\n" + "\n".join(errors))

    def _do_cancel_booking(self):
        bid, ok = QtWidgets.QInputDialog.getInt(
            self, "Hủy Đặt Phòng", "Nhập mã booking (ID) cần hủy:", min=1)
        if not ok:
            return
        booking = BookingModel.get_by_id(bid)
        if not booking:
            msg_warn(self, f"Không tìm thấy booking #{bid}!"); return
        if booking["status"] not in ("booked", "checked_in"):
            msg_warn(self, f"Booking #{bid} không thể hủy (trạng thái: {booking['status']})"); return
        if msg_confirm(self, f"Hủy booking #{bid} – Phòng {booking['room_number']}?"):
            ok2, msg = BookingModel.cancel(bid)
            (msg_info if ok2 else msg_error)(self, msg)
            if ok2:
                ActivityLogModel.log(
                    self.user["id"], self.user["username"], self.user["full_name"],
                    "Hủy booking", f"Booking #{bid}"
                )
                self._checkin_reset()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 1: CHECK-OUT
    # ══════════════════════════════════════════════════════════════════════════
    def _connect_checkout(self):
        self.ui.btn_co_confirm.clicked.connect(self._do_checkout)
        self.ui.tbl_checkout_list.cellClicked.connect(self._on_checkout_row)

    def _load_checkout(self):
        self._checkout_booking_id = None
        data = BookingModel.get_all()
        self._checkout_data = [d for d in data if d["status"] == "checked_in"]
        for b in self._checkout_data:
            calc = InvoiceModel.calculate(b["id"])
            b["svc"]       = str(len(ServiceModel.get_by_booking(b["id"]))) + " dịch vụ"
            b["est_total"] = fmt_money(calc["total_amount"]) if calc else "—"
        fill_table(
            self.ui.tbl_checkout_list, self._checkout_data,
            ["room", "customer", "check_in", "check_out", "svc", "est_total", "status"],
            status_map=STATUS_VI
        )

    def _on_checkout_row(self, row: int, _col: int):
        if hasattr(self, "_checkout_data") and row < len(self._checkout_data):
            self._checkout_booking_id = self._checkout_data[row]["id"]

    def _do_checkout(self):
        if not self._checkout_booking_id:
            msg_warn(self, "Vui lòng chọn phòng cần trả!"); return
        booking = BookingModel.get_by_id(self._checkout_booking_id)
        room_num = booking.get("room_number", "") if booking else ""
        if not msg_confirm(self,
                f"Xác nhận khách rời phòng {room_num}?\n\n"
                f"Sau khi xác nhận, hệ thống sẽ chuyển sang\n"
                f"trang Hóa Đơn để hoàn tất thanh toán."):
            return
        pending_id = self._checkout_booking_id
        self._checkout_booking_id = None
        ActivityLogModel.log(
            self.user["id"], self.user["username"], self.user["full_name"],
            "Check-out", f"Phòng {room_num} | Booking #{pending_id}"
        )
        self._goto(self.PAGE_INVOICE)
        self._invoice_load_by_booking_id(pending_id)

    def _invoice_load_by_booking_id(self, booking_id: int):
        self._invoice_booking_id = booking_id
        booking = BookingModel.get_by_id(booking_id)
        if not booking:
            return
        self.ui.inp_inv_search.setText(str(booking.get("room_number", "")))
        self.ui.lbl_inv_room.setText(f"Phòng:   {booking['room_number']}")
        self.ui.lbl_inv_cust_name.setText(f"Họ Tên:  {booking['customer_name']}")
        self.ui.lbl_inv_checkin.setText(f"Check-in:  {booking['check_in']}")
        self.ui.lbl_inv_checkout.setText(f"Check-out: {booking['check_out']}")
        fill_table(self.ui.tbl_inv_services,
                   ServiceModel.get_by_booking(booking_id),
                   ["name", "quantity", "price", "total"],
                   money_keys=["price", "total"])
        self._invoice_calc = InvoiceModel.calculate(booking_id)
        if self._invoice_calc:
            c = self._invoice_calc
            self.ui.lbl_inv_room_charge.setText(f"Tiền Phòng:  {fmt_money(c['room_charge'])}")
            self.ui.lbl_inv_svc_charge.setText(f"Dịch Vụ:  {fmt_money(c['service_charge'])}")
            self.ui.lbl_inv_vat.setText(f"VAT(10%):  {fmt_money(c['vat_amount'])}")
            self.ui.lbl_inv_total.setText(f"Tổng Cộng:  {fmt_money(c['total_amount'])}")

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 2: Danh sách phòng
    # ══════════════════════════════════════════════════════════════════════════
    def _connect_rooms(self):
        self.ui.inp_room_search.textChanged.connect(
            lambda t: self._load_rooms(t.replace("🔍  Tìm kiếm...", "").strip()))

    def _load_rooms(self, keyword: str = ""):
        data = RoomModel.search(keyword) if keyword else RoomModel.get_all()
        fill_table(
            self.ui.tbl_rooms, data,
            ["room_number", "type_name", "floor", "base_price", "status"],
            money_keys=["base_price"], status_map=STATUS_VI
        )

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 3: Dịch vụ
    # ══════════════════════════════════════════════════════════════════════════
    def _connect_service(self):
        self.ui.btn_svc_add.clicked.connect(self._add_service)

    def _load_service(self):
        data    = BookingModel.get_all()
        checked = [d for d in data if d["status"] == "checked_in"]
        rows = []
        for b in checked:
            for s in ServiceModel.get_by_booking(b["id"]):
                rows.append({"room": b["room"], "name": s["name"],
                             "quantity": s["quantity"], "price": s["price"], "total": s["total"]})
        fill_table(self.ui.tbl_services_used, rows,
                   ["room", "name", "quantity", "price", "total"],
                   money_keys=["price", "total"])

    def _add_service(self):
        dlg = AddServiceDialog(self)
        if dlg.exec():
            ok, msg = ServiceModel.add_to_booking(**dlg.get_data())
            (msg_info if ok else msg_error)(self, msg)
            if ok:
                ActivityLogModel.log(
                    self.user["id"], self.user["username"], self.user["full_name"],
                    "Thêm dịch vụ", dlg.get_data().get("note", "")
                )
            self._load_service()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 4: Hóa đơn
    # ══════════════════════════════════════════════════════════════════════════
    def _connect_invoice(self):
        self.ui.btn_inv_find.clicked.connect(self._invoice_search)
        self.ui.inp_inv_search.returnPressed.connect(self._invoice_search)
        self.ui.rb_pay_cash.setChecked(True)
        for rb in (self.ui.rb_pay_cash, self.ui.rb_pay_card, self.ui.rb_pay_transfer):
            rb.toggled.connect(self._on_pttt_changed)
        self.ui.inp_inv_cash_given.textChanged.connect(self._update_change)
        self.ui.btn_inv_pay.clicked.connect(self._do_payment)
        self.ui.btn_inv_print.clicked.connect(self._print_invoice)

    def _reset_invoice_ui(self):
        self._invoice_booking_id = None
        self._invoice_calc       = None
        self.ui.inp_inv_search.clear()
        self.ui.inp_inv_cash_given.clear()
        for lbl, txt in [
            (self.ui.lbl_inv_room,        "Phòng:"),
            (self.ui.lbl_inv_cust_name,   "Họ Tên:"),
            (self.ui.lbl_inv_checkin,     "CheckIn:"),
            (self.ui.lbl_inv_checkout,    "CheckOut:"),
            (self.ui.lbl_inv_room_charge, "Tiền Phòng:  —"),
            (self.ui.lbl_inv_svc_charge,  "Dịch Vụ:  —"),
            (self.ui.lbl_inv_vat,         "VAT(10%):  —"),
            (self.ui.lbl_inv_total,       "Tổng Cộng:  —"),
            (self.ui.lbl_inv_change,      "Tiền Thừa:"),
        ]:
            lbl.setText(txt)
        self.ui.tbl_inv_services.setRowCount(0)

    def _invoice_search(self):
        kw = self.ui.inp_inv_search.text().strip()
        if not kw: msg_warn(self, "Nhập số phòng hoặc tên khách!"); return
        results = BookingModel.find_by_name_or_room(kw)
        if not results: msg_warn(self, f"Không tìm thấy booking với '{kw}'!"); return

        b = results[0]
        self._invoice_booking_id = b["id"]
        booking = BookingModel.get_by_id(b["id"])
        if not booking: return

        self.ui.lbl_inv_room.setText(f"Phòng:   {booking['room_number']}")
        self.ui.lbl_inv_cust_name.setText(f"Họ Tên:  {booking['customer_name']}")
        self.ui.lbl_inv_checkin.setText(f"Check-in:  {booking['check_in']}")
        self.ui.lbl_inv_checkout.setText(f"Check-out: {booking['check_out']}")
        fill_table(self.ui.tbl_inv_services,
                   ServiceModel.get_by_booking(b["id"]),
                   ["name", "quantity", "price", "total"],
                   money_keys=["price", "total"])
        self._invoice_calc = InvoiceModel.calculate(b["id"])
        if self._invoice_calc:
            c = self._invoice_calc
            self.ui.lbl_inv_room_charge.setText(f"Tiền Phòng:  {fmt_money(c['room_charge'])}")
            self.ui.lbl_inv_svc_charge.setText(f"Dịch Vụ:  {fmt_money(c['service_charge'])}")
            self.ui.lbl_inv_vat.setText(f"VAT(10%):  {fmt_money(c['vat_amount'])}")
            self.ui.lbl_inv_total.setText(f"Tổng Cộng:  {fmt_money(c['total_amount'])}")

    def _on_pttt_changed(self):
        self.ui.stk_payment_detail.setCurrentIndex(
            0 if self.ui.rb_pay_cash.isChecked() else 1)

    def _update_change(self, text: str):
        if not self._invoice_calc: return
        try:
            paid   = float(text.replace(",", "").replace("đ", "").replace(" ", ""))
            change = paid - self._invoice_calc["total_amount"]
            self.ui.lbl_inv_change.setText(
                f"Tiền Thừa:  {fmt_money(max(change, 0))}"
                + (" ⚠ Thiếu!" if change < 0 else ""))
        except ValueError:
            self.ui.lbl_inv_change.setText("Tiền Thừa:  —")

    def _get_pay_method(self) -> str:
        if self.ui.rb_pay_transfer.isChecked(): return "transfer"
        if self.ui.rb_pay_card.isChecked(): return "card"
        return "cash"

    def _do_payment(self):
        if not self._invoice_booking_id:
            msg_warn(self, "Vui lòng tìm hóa đơn trước!"); return
        if not self._invoice_calc:
            msg_warn(self, "Không tính được tiền, thử tìm lại hóa đơn!"); return
        if self.ui.rb_pay_cash.isChecked():
            try:
                paid = float(self.ui.inp_inv_cash_given.text().replace(",","").replace("đ","").replace(" ",""))
                if paid < self._invoice_calc["total_amount"]:
                    msg_warn(self, "Số tiền khách đưa chưa đủ!"); return
            except ValueError:
                pass
        if not msg_confirm(self, f"Xác nhận thanh toán?\nTổng: {fmt_money(self._invoice_calc['total_amount'])}"):
            return
        ok, result = InvoiceModel.create_or_update(self._invoice_booking_id, self._get_pay_method())
        if ok:
            BookingModel.checkout(self._invoice_booking_id)
            ActivityLogModel.log(
                self.user["id"], self.user["username"], self.user["full_name"],
                "Thanh toán",
                f"Booking #{self._invoice_booking_id} | "
                f"{fmt_money(result['total_amount'])} | {self._get_pay_method()}"
            )
            msg_info(self, f"Thanh toán & trả phòng thành công!\nTổng tiền: {fmt_money(result['total_amount'])}")
            self._reset_invoice_ui()
        else:
            msg_error(self, f"Lỗi: {result}")

    def _print_invoice(self):
        if not self._invoice_booking_id:
            msg_warn(self, "Vui lòng tìm hóa đơn trước!"); return
        inv     = InvoiceModel.get_by_booking(self._invoice_booking_id)
        booking = BookingModel.get_by_id(self._invoice_booking_id)
        svcs    = ServiceModel.get_by_booking(self._invoice_booking_id)
        if not booking: return
        if not inv and self._invoice_calc:
            inv = dict(self._invoice_calc)
            inv["pay_method"] = self._get_pay_method()
            inv["pay_status"] = "unpaid"
        days = self._invoice_calc.get("days", "—") if self._invoice_calc else inv.get("days", "—")
        svc_lines = "".join(
            f"  {s['name']:<22}{s['quantity']:>3} x {fmt_money(s['price']):>12} = {fmt_money(s['total']):>12}\n"
            for s in svcs
        ) or "  (Không có dịch vụ phát sinh)\n"
        body = (
            f"╔══════════════════════════════════════╗\n"
            f"║       HÓA ĐƠN THANH TOÁN            ║\n"
            f"╚══════════════════════════════════════╝\n\n"
            f"  Phòng      : {booking.get('room_number','')}\n"
            f"  Khách hàng : {booking.get('customer_name','')}\n"
            f"  Check-in   : {booking.get('check_in','')}\n"
            f"  Check-out  : {booking.get('check_out','')}\n"
            f"  Số đêm     : {days}\n\n"
            f"  ──────── Chi tiết dịch vụ ────────\n"
            f"{svc_lines}\n"
            f"  ──────────── Tổng kết ────────────\n"
            f"  Tiền phòng  : {fmt_money(inv.get('room_charge',0)):>14}\n"
            f"  Dịch vụ    : {fmt_money(inv.get('service_charge',0)):>14}\n"
            f"  VAT (10%)  : {fmt_money(inv.get('vat_amount',0)):>14}\n"
            f"  {'─'*36}\n"
            f"  TỔNG CỘNG  : {fmt_money(inv.get('total_amount',0)):>14}\n\n"
            f"  Thanh toán : {STATUS_VI.get(inv.get('pay_method','cash'),'Tiền mặt')}\n"
            f"  Trạng thái : {STATUS_VI.get(inv.get('pay_status','unpaid'),'Chưa TT')}\n\n"
            f"       Cảm ơn quý khách!\n"
        )
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("🧾 Hóa Đơn")
        dlg.setMinimumSize(500, 540)
        vl = QtWidgets.QVBoxLayout(dlg)
        te = QtWidgets.QTextEdit()
        te.setReadOnly(True)
        te.setPlainText(body)
        te.setFontFamily("Courier New")
        te.setFontPointSize(10)
        vl.addWidget(te)
        btn = QtWidgets.QPushButton("✕  Đóng")
        btn.clicked.connect(dlg.accept)
        vl.addWidget(btn)
        dlg.exec()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 5: Profile
    # ══════════════════════════════════════════════════════════════════════════
    def _connect_profile(self):
        self.ui.btn_pf_save.clicked.connect(self._save_profile)

    def _load_profile(self):
        self.ui.inp_pf_fullname.setText(self.user.get("full_name", ""))
        self.ui.inp_pf_phone.clear()
        self.ui.inp_pf_new_pass.clear()
        self.ui.inp_pf_confirm_pass.clear()
        self.ui.inp_pf_old_pass.clear()

    def _save_profile(self):
        full_name    = self.ui.inp_pf_fullname.text().strip()
        old_pass     = self.ui.inp_pf_old_pass.text().strip()
        new_pass     = self.ui.inp_pf_new_pass.text().strip()
        confirm_pass = self.ui.inp_pf_confirm_pass.text().strip()

        if full_name and full_name != self.user.get("full_name", ""):
            ok, msg = UserModel.update_profile(self.user["id"], full_name)
            if ok:
                self.user["full_name"] = full_name
                self.setWindowTitle(f"Hotel Staff – {full_name}")
                ActivityLogModel.log(
                    self.user["id"], self.user["username"], self.user["full_name"],
                    "Cập nhật hồ sơ", f"Tên mới: {full_name}"
                )
            (msg_info if ok else msg_error)(self, msg)

        if old_pass or new_pass or confirm_pass:
            if not old_pass: msg_warn(self, "Vui lòng nhập mật khẩu cũ!"); return
            if not new_pass: msg_warn(self, "Vui lòng nhập mật khẩu mới!"); return
            if new_pass != confirm_pass: msg_warn(self, "Mật khẩu mới và xác nhận không khớp!"); return
            if len(new_pass) < 6: msg_warn(self, "Mật khẩu mới phải có ít nhất 6 ký tự!"); return
            ok, msg = UserModel.change_password(self.user["id"], old_pass, new_pass)
            (msg_info if ok else msg_error)(self, msg)
            if ok:
                ActivityLogModel.log(
                    self.user["id"], self.user["username"], self.user["full_name"],
                    "Đổi mật khẩu", ""
                )
                self.ui.inp_pf_new_pass.clear()
                self.ui.inp_pf_confirm_pass.clear()
                self.ui.inp_pf_old_pass.clear()


# ══════════════════════════════════════════════════════════════════════════════
# DIALOG: Thêm dịch vụ vào booking
# ══════════════════════════════════════════════════════════════════════════════

class AddServiceDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("➕ Thêm dịch vụ cho khách")
        self.setMinimumWidth(400)
        layout = QtWidgets.QFormLayout(self)
        layout.setSpacing(12)

        self.cb_booking  = QtWidgets.QComboBox()
        self.cb_service  = QtWidgets.QComboBox()
        self.sb_quantity = QtWidgets.QSpinBox()
        self.sb_quantity.setRange(1, 999)
        self.lbl_price   = QtWidgets.QLabel("—")
        self.le_note     = QtWidgets.QLineEdit()

        data = BookingModel.get_all()
        self._bookings = [d for d in data if d["status"] == "checked_in"]
        if not self._bookings:
            self.cb_booking.addItem("— Không có phòng đang thuê —", None)
        for b in self._bookings:
            self.cb_booking.addItem(f"Phòng {b['room']}  –  {b['customer']}", b["id"])

        self._services = ServiceModel.get_active()
        if not self._services:
            self.cb_service.addItem("— Không có dịch vụ —", None)
        for s in self._services:
            self.cb_service.addItem(
                f"{s['name']}  ({int(s['price']):,} đ / {s['unit']})", s["id"])

        self.cb_service.currentIndexChanged.connect(self._refresh_price)
        self._refresh_price()

        layout.addRow("Booking *",  self.cb_booking)
        layout.addRow("Dịch vụ *",  self.cb_service)
        layout.addRow("Đơn giá:",   self.lbl_price)
        layout.addRow("Số lượng *", self.sb_quantity)
        layout.addRow("Ghi chú:",   self.le_note)

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._ok)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _refresh_price(self):
        sid = self.cb_service.currentData()
        svc = next((s for s in self._services if s["id"] == sid), None)
        self.lbl_price.setText(f"{int(svc['price']):,} đ / {svc['unit']}" if svc else "—")

    def _ok(self):
        if not self.cb_booking.currentData():
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Không có phòng đang thuê!"); return
        if not self.cb_service.currentData():
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng chọn dịch vụ!"); return
        self.accept()

    def get_data(self) -> dict:
        sid = self.cb_service.currentData()
        svc = next((s for s in self._services if s["id"] == sid), None)
        return {
            "booking_id": self.cb_booking.currentData(),
            "service_id": sid,
            "quantity":   self.sb_quantity.value(),
            "price":      svc["price"] if svc else 0,
            "note":       self.le_note.text().strip(),
        }