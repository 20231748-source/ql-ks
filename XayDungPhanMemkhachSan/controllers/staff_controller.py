from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QHeaderView, QSizePolicy
from views.Staff import Ui_StaffWindow
from models.room_model import RoomModel
from models.customer_model import CustomerModel
from models.booking_model import BookingModel
from models.service_model import ServiceModel
from models.invoice_model import InvoiceModel
from models.user_model import UserModel
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
        if hasattr(self.ui, 'btn_header_logout'):
            self.ui.btn_header_logout.clicked.connect(self._logout)
        self.ui.btn_nav_checkin.clicked.connect(lambda: self._goto(self.PAGE_CHECKIN))
        self.ui.btn_nav_checkout.clicked.connect(lambda: self._goto(self.PAGE_CHECKOUT))
        self.ui.btn_nav_rooms.clicked.connect(lambda: self._goto(self.PAGE_ROOMS))
        self.ui.btn_nav_invoice.clicked.connect(lambda: self._goto(self.PAGE_INVOICE))
        self.ui.btn_nav_service.clicked.connect(lambda: self._goto(self.PAGE_SERVICE))
        self.ui.btn_nav_profile.clicked.connect(lambda: self._goto(self.PAGE_PROFILE))

    def _set_active_nav(self, index: int):
        """Highlight đúng nút sidebar, bỏ highlight tất cả nút khác."""
        for i, btn in enumerate(self._nav_buttons):
            btn.setProperty("active", i == index)
            # Buộc Qt re-apply stylesheet
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
        # Force bảng re-fit sau khi stacked widget đổi trang
        QtCore.QTimer.singleShot(0, self._refresh_table_columns)

    def _logout(self):
        if msg_confirm(self, "Bạn có muốn đăng xuất không?"):
            UserModel.log_activity(self.user["id"], "Đăng xuất hệ thống")
            self.close()
            from controllers.login_controller import LoginWindow
            self._login_win = LoginWindow()
            self._login_win.exec()

    # ── Page 0: Check-in ─────────────────────────────────────────────────────
    def _connect_checkin(self):
        self.ui.btn_ci_confirm.clicked.connect(self._do_checkin)
        self.ui.btn_ci_cancel.clicked.connect(self._do_cancel_booking)

    def _load_checkin(self):
        self.ui.inp_ci_name.clear()
        self.ui.inp_ci_idcard.clear()
        self.ui.inp_ci_phone.clear()
        today    = date.today()
        tomorrow = today + timedelta(days=1)
        self.ui.de_ci_checkin.setDate(QtCore.QDate(today.year, today.month, today.day))
        self.ui.de_ci_checkout.setDate(QtCore.QDate(tomorrow.year, tomorrow.month, tomorrow.day))
        self._reload_room_combo()

    def _reload_room_combo(self):
        self.ui.cmb_ci_room.clear()
        rooms = RoomModel.get_available()
        if not rooms:
            self.ui.cmb_ci_room.addItem("— Không có phòng trống —", None)
            return
        for r in rooms:
            self.ui.cmb_ci_room.addItem(
                f"Phòng {r['room_number']}  |  {r['type_name']}  |  {int(r['base_price']):,} đ/đêm",
                r["id"]
            )

    def _do_checkin(self):
        full_name = self.ui.inp_ci_name.text().strip()
        id_card   = self.ui.inp_ci_idcard.text().strip()
        phone     = self.ui.inp_ci_phone.text().strip()
        check_in  = self.ui.de_ci_checkin.date().toString("yyyy-MM-dd")
        check_out = self.ui.de_ci_checkout.date().toString("yyyy-MM-dd")
        room_id   = self.ui.cmb_ci_room.currentData()

        if not full_name: msg_warn(self, "Vui lòng nhập Họ và Tên khách!"); return
        if not id_card:   msg_warn(self, "Vui lòng nhập số CCCD!"); return
        if not phone:     msg_warn(self, "Vui lòng nhập số điện thoại!"); return
        if not room_id:   msg_warn(self, "Vui lòng chọn phòng!"); return
        if check_in >= check_out:
            msg_warn(self, "Ngày trả phòng phải sau ngày nhận!"); return

        cust = CustomerModel.find_by_idcard(id_card)
        if cust is None:
            ok, err = CustomerModel.add(full_name, id_card, phone, "", "")
            if not ok:
                msg_error(self, f"Lỗi tạo khách hàng: {err}"); return
            cust = CustomerModel.find_by_idcard(id_card)

        ok, msg, booking_id = BookingModel.create(
            cust["id"], room_id, self.user["id"], check_in, check_out
        )
        (msg_info if ok else msg_error)(self, msg if not ok else f"Đặt phòng thành công!\nMã: #{booking_id}")
        if ok:
            UserModel.log_activity(self.user["id"], f"Nhận phòng ID #{booking_id}")
            self._load_checkin()

    def _do_cancel_booking(self):
        # Page checkin không có bảng → hỏi mã booking
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
                UserModel.log_activity(self.user["id"], f"Hủy phòng ID #{bid}")
                self._load_checkin()

    # ── Page 1: Check-out ────────────────────────────────────────────────────
    def _connect_checkout(self):
        self.ui.btn_co_confirm.clicked.connect(self._do_checkout)
        self.ui.tbl_checkout_list.cellClicked.connect(self._on_checkout_row)

    def _load_checkout(self):
        self._checkout_booking_id = None
        data      = BookingModel.get_all()
        self._checkout_data = [d for d in data if d["status"] == "checked_in"]
        for b in self._checkout_data:
            calc          = InvoiceModel.calculate(b["id"])
            b["svc"]      = str(len(ServiceModel.get_by_booking(b["id"]))) + " dịch vụ"
            b["est_total"]= fmt_money(calc["total_amount"]) if calc else "—"
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

    # ── Page 2: Danh sách phòng ──────────────────────────────────────────────
    def _connect_rooms(self):
        self.ui.inp_room_search.textChanged.connect(
            lambda t: self._load_rooms(t.replace("🔍  Tìm kiếm...", "").strip())
        )

    def _load_rooms(self, keyword: str = ""):
        data = RoomModel.search(keyword) if keyword else RoomModel.get_all()
        fill_table(
            self.ui.tbl_rooms, data,
            ["room_number", "type_name", "floor", "base_price", "status"],
            money_keys=["base_price"], status_map=STATUS_VI
        )

    def _connect_service(self):
        self.ui.btn_svc_add.clicked.connect(self._add_service)

    def _load_service(self):
        data      = BookingModel.get_all()
        checked   = [d for d in data if d["status"] == "checked_in"]
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
                UserModel.log_activity(self.user["id"], f"Thêm dịch vụ cho phòng thuê #{dlg.get_data()['booking_id']}")
            self._load_service()

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
            (self.ui.lbl_inv_room,     "Phòng:"),
            (self.ui.lbl_inv_cust_name,     "Họ Tên:"),
            (self.ui.lbl_inv_checkin,  "CheckIn:"),
            (self.ui.lbl_inv_checkout, "CheckOut:"),
            (self.ui.lbl_inv_room_charge, "Tiền Phòng:  —"),
            (self.ui.lbl_inv_svc_charge, "Dịch Vụ:  —"),
            (self.ui.lbl_inv_vat, "VAT(8%):  —"),
            (self.ui.lbl_inv_total, "Tổng Cộng:  —"),
            (self.ui.lbl_inv_change, "Tiền Thừa:"),
        ]:
            lbl.setText(txt)
        self.ui.tbl_inv_services.setRowCount(0)

    def _invoice_search(self):
        kw = self.ui.inp_inv_search.text().strip()
        if not kw:
            msg_warn(self, "Nhập số phòng hoặc tên khách!"); return
        results = BookingModel.find_by_name_or_room(kw)
        if not results:
            msg_warn(self, f"Không tìm thấy booking với '{kw}'!"); return

        b       = results[0]
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
            0 if self.ui.rb_pay_cash.isChecked() else 1
        )

    def _update_change(self, text: str):
        if not self._invoice_calc: return
        try:
            paid   = float(text.replace(",", "").replace("đ", "").replace(" ", ""))
            change = paid - self._invoice_calc["total_amount"]
            self.ui.lbl_inv_change.setText(
                f"Tiền Thừa:  {fmt_money(max(change, 0))}"
                + (" ⚠ Thiếu!" if change < 0 else "")
            )
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
            UserModel.log_activity(self.user["id"], f"Thanh toán & trả phòng #{self._invoice_booking_id} ({result['total_amount']})")
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
            (msg_info if ok else msg_error)(self, msg)

        if old_pass or new_pass or confirm_pass:
            if not old_pass:
                msg_warn(self, "Vui lòng nhập mật khẩu cũ!"); return
            if not new_pass:
                msg_warn(self, "Vui lòng nhập mật khẩu mới!"); return
            if new_pass != confirm_pass:
                msg_warn(self, "Mật khẩu mới và xác nhận không khớp!"); return
            if len(new_pass) < 6:
                msg_warn(self, "Mật khẩu mới phải có ít nhất 6 ký tự!"); return
            ok, msg = UserModel.change_password(self.user["id"], old_pass, new_pass)
            (msg_info if ok else msg_error)(self, msg)
            if ok:
                self.ui.inp_pf_new_pass.clear()
                self.ui.inp_pf_confirm_pass.clear()
                self.ui.inp_pf_old_pass.clear()


# ── Dialog: Thêm dịch vụ vào booking ─────────────────────────────────────────

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
                f"{s['name']}  ({int(s['price']):,} đ / {s['unit']})", s["id"]
            )

        self.cb_service.currentIndexChanged.connect(self._refresh_price)
        self._refresh_price()

        layout.addRow("Booking *",  self.cb_booking)
        layout.addRow("Dịch vụ *",  self.cb_service)
        layout.addRow("Đơn giá:",   self.lbl_price)
        layout.addRow("Số lượng *", self.sb_quantity)
        layout.addRow("Ghi chú:",   self.le_note)

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
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
        sid  = self.cb_service.currentData()
        svc  = next((s for s in self._services if s["id"] == sid), None)
        return {
            "booking_id": self.cb_booking.currentData(),
            "service_id": sid,
            "quantity":   self.sb_quantity.value(),
            "price":      svc["price"] if svc else 0,
            "note":       self.le_note.text().strip(),
        }