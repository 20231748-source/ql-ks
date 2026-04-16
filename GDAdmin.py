from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1050, 700)

        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setStyleSheet("background-color: #F5F5F5;")
        self.main_layout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ── TOP HEADER ──────────────────────────────────────────────────
        self.header = QtWidgets.QFrame(parent=self.centralwidget)
        self.header.setFixedHeight(52)
        self.header.setStyleSheet("background-color: #D8D8D8; border-bottom: 1px solid #BDBDBD;")
        self.header_layout = QtWidgets.QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(20, 0, 20, 0)

        self.lbl_header_title = QtWidgets.QLabel("PHẦN MỀM QUẢN LÝ PHÒNG KHÁCH SẠN")
        self.lbl_header_title.setStyleSheet(
            "color: #1A1A1A; font-size: 18px; font-weight: bold; background: transparent;"
        )
        self.header_layout.addWidget(self.lbl_header_title)
        self.header_layout.addStretch()

        self.lbl_admin = QtWidgets.QLabel("Admin")
        self.lbl_admin.setStyleSheet(
            "color: #1A1A1A; font-size: 15px; font-weight: bold; background: transparent;"
        )
        self.header_layout.addWidget(self.lbl_admin)

        self.main_layout.addWidget(self.header)

        # ── BODY (sidebar + content) ─────────────────────────────────────
        self.body_widget = QtWidgets.QWidget(parent=self.centralwidget)
        self.body_layout = QtWidgets.QHBoxLayout(self.body_widget)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(0)
        self.main_layout.addWidget(self.body_widget)

        # ── SIDEBAR ──────────────────────────────────────────────────────
        self.sidebar = QtWidgets.QFrame(parent=self.body_widget)
        self.sidebar.setFixedWidth(210)
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #1E2A3A;
            }
            QPushButton {
                background-color: transparent;
                color: #B0BAC9;
                font-size: 13px;
                font-weight: bold;
                padding: 14px 20px;
                text-align: left;
                border: none;
                border-left: 4px solid transparent;
            }
            QPushButton:hover {
                background-color: #253347;
                color: #FFFFFF;
            }
            QPushButton:checked {
                background-color: #253347;
                color: #FFFFFF;
                border-left: 4px solid #4FC3F7;
            }
        """)
        self.sidebar_layout = QtWidgets.QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(0, 30, 0, 0)
        self.sidebar_layout.setSpacing(2)

        # Menu items matching the image
        self.BtnDashBoard = QtWidgets.QPushButton("🏠 TRANG CHỦ", parent=self.sidebar)
        self.BtnDashBoard.setCheckable(True)

        self.BtnRoom = QtWidgets.QPushButton("🛏 PHÒNG", parent=self.sidebar)
        self.BtnRoom.setCheckable(True)

        self.BtnCustomer = QtWidgets.QPushButton("👤 KHÁCH", parent=self.sidebar)
        self.BtnCustomer.setCheckable(True)

        self.BtnAddRoom = QtWidgets.QPushButton("🔑 THUÊ PHÒNG", parent=self.sidebar)
        self.BtnAddRoom.setCheckable(True)

        self.BtnSerVice = QtWidgets.QPushButton("⚙ DỊCH VỤ", parent=self.sidebar)
        self.BtnSerVice.setCheckable(True)

        self.BtnInvoice = QtWidgets.QPushButton("🖨 HÓA ĐƠN", parent=self.sidebar)
        self.BtnInvoice.setCheckable(True)

        self.BtnReport = QtWidgets.QPushButton("📊 BÁO CÁO", parent=self.sidebar)
        self.BtnReport.setCheckable(True)

        self.sidebar_buttons = [
            self.BtnDashBoard, self.BtnRoom, self.BtnCustomer,
            self.BtnAddRoom, self.BtnSerVice, self.BtnInvoice, self.BtnReport
        ]
        for btn in self.sidebar_buttons:
            self.sidebar_layout.addWidget(btn)

        self.sidebar_layout.addStretch()

        self.Btnlog = QtWidgets.QPushButton("🚪 ĐĂNG XUẤT", parent=self.sidebar)
        self.Btnlog.setStyleSheet(
            "background-color: #C0392B; color: white; font-weight: bold; "
            "font-size: 13px; padding: 12px; margin: 12px; border-radius: 4px;"
        )
        self.sidebar_layout.addWidget(self.Btnlog)

        self.body_layout.addWidget(self.sidebar)

        # ── STACKED WIDGET (pages) ────────────────────────────────────────
        self.stackedWidget = QtWidgets.QStackedWidget(parent=self.body_widget)
        self.body_layout.addWidget(self.stackedWidget)

        # ── PAGE 0: DASHBOARD ─────────────────────────────────────────────
        self.page_dashboard = QtWidgets.QWidget()
        self.page_dashboard.setStyleSheet("background-color: #F5F5F5;")
        self.l_dash = QtWidgets.QVBoxLayout(self.page_dashboard)
        self.l_dash.setContentsMargins(40, 30, 40, 30)
        self.l_dash.setSpacing(20)

        lbl_dash_title = QtWidgets.QLabel("THỐNG KÊ TẠI KHÁCH SẠN")
        lbl_dash_title.setStyleSheet("font-size: 19px; font-weight: bold; color: #1A1A1A;")
        self.l_dash.addWidget(lbl_dash_title)

        # Row 1 – 3 cards
        row1 = QtWidgets.QHBoxLayout()
        row1.setSpacing(30)
        self.card_total   = self._make_stat_card("Tổng phòng",   "0")
        self.card_vacant  = self._make_stat_card("Phòng trống",  "0")
        self.card_rented  = self._make_stat_card("Đang thuê",    "0")
        row1.addWidget(self.card_total)
        row1.addWidget(self.card_vacant)
        row1.addWidget(self.card_rented)
        self.l_dash.addLayout(row1)

        # Row 2 – 2 cards (centred like image)
        row2_outer = QtWidgets.QHBoxLayout()
        row2_outer.setSpacing(0)
        row2_outer.addSpacing(130)          # left indent so cards start under Phòng trống
        row2_inner = QtWidgets.QHBoxLayout()
        row2_inner.setSpacing(30)
        self.card_booked  = self._make_stat_card("Đã đặt phòng", "0")
        self.card_revenue = self._make_stat_card("Doanh thu",    "0 VNĐ")
        row2_inner.addWidget(self.card_booked)
        row2_inner.addWidget(self.card_revenue)
        row2_outer.addLayout(row2_inner)
        row2_outer.addStretch()
        self.l_dash.addLayout(row2_outer)

        self.l_dash.addStretch()
        self.stackedWidget.addWidget(self.page_dashboard)

        # ── PAGE 1: PHÒNG ─────────────────────────────────────────────────
        self.page_rooms = QtWidgets.QWidget()
        self.page_rooms.setStyleSheet("background-color: #F5F5F5;")
        self.l_rooms = QtWidgets.QVBoxLayout(self.page_rooms)
        self.l_rooms.setContentsMargins(30, 30, 30, 30)
        self.l_rooms.setSpacing(15)

        lbl_rooms = QtWidgets.QLabel("QUẢN LÝ PHÒNG")
        lbl_rooms.setStyleSheet("font-size: 19px; font-weight: bold; color: #1A1A1A;")
        self.l_rooms.addWidget(lbl_rooms)

        self.tbl_rooms = QtWidgets.QTableWidget()
        self.tbl_rooms.setColumnCount(5)
        self.tbl_rooms.setHorizontalHeaderLabels(["ID", "Số phòng", "Loại phòng", "Giá (VNĐ)", "Trạng thái"])
        self.tbl_rooms.horizontalHeader().setStretchLastSection(True)
        self.tbl_rooms.setStyleSheet(
            "QTableWidget { background-color: white; border: 1px solid #D0D0D0; gridline-color: #E0E0E0; }"
            "QHeaderView::section { background-color: #2C3E50; color: white; padding: 8px; font-weight: bold; }"
        )
        self.l_rooms.addWidget(self.tbl_rooms)
        self.stackedWidget.addWidget(self.page_rooms)

        # ── PAGE 2: KHÁCH ─────────────────────────────────────────────────
        self.page_customers = QtWidgets.QWidget()
        self.page_customers.setStyleSheet("background-color: #F5F5F5;")
        self.l_customers = QtWidgets.QVBoxLayout(self.page_customers)
        self.l_customers.setContentsMargins(30, 30, 30, 30)
        self.l_customers.setSpacing(15)

        lbl_cus = QtWidgets.QLabel("QUẢN LÝ KHÁCH")
        lbl_cus.setStyleSheet("font-size: 19px; font-weight: bold; color: #1A1A1A;")
        self.l_customers.addWidget(lbl_cus)

        self.tbl_customers = QtWidgets.QTableWidget()
        self.tbl_customers.setColumnCount(4)
        self.tbl_customers.setHorizontalHeaderLabels(["ID", "Họ và tên", "CMND/CCCD", "Số điện thoại"])
        self.tbl_customers.horizontalHeader().setStretchLastSection(True)
        self.tbl_customers.setStyleSheet(
            "QTableWidget { background-color: white; border: 1px solid #D0D0D0; gridline-color: #E0E0E0; }"
            "QHeaderView::section { background-color: #2C3E50; color: white; padding: 8px; font-weight: bold; }"
        )
        self.l_customers.addWidget(self.tbl_customers)
        self.stackedWidget.addWidget(self.page_customers)

        # ── PAGE 3: THUÊ PHÒNG ────────────────────────────────────────────
        self.page_addroom = QtWidgets.QWidget()
        self.page_addroom.setStyleSheet("background-color: #F5F5F5;")
        self.l_addroom_main = QtWidgets.QVBoxLayout(self.page_addroom)
        self.l_addroom_main.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.l_addroom_main.setContentsMargins(30, 30, 30, 30)
        self.l_addroom_main.setSpacing(15)

        title_add = QtWidgets.QLabel("THUÊ PHÒNG")
        title_add.setStyleSheet("font-size: 19px; font-weight: bold; color: #1A1A1A;")
        self.l_addroom_main.addWidget(title_add)

        self.formWidget = QtWidgets.QWidget()
        self.formWidget.setStyleSheet(
            "background-color: white; border-radius: 6px; border: 1px solid #D0D0D0;"
        )
        self.l_addroom = QtWidgets.QFormLayout(self.formWidget)
        self.l_addroom.setContentsMargins(30, 30, 30, 30)
        self.l_addroom.setSpacing(18)
        self.l_addroom.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        field_style = "padding: 9px; border: 1px solid #BDBDBD; border-radius: 4px; font-size: 13px; background: white;"

        self.in_room_num = QtWidgets.QLineEdit()
        self.in_room_num.setPlaceholderText("VD: 101")
        self.in_room_num.setStyleSheet(field_style)

        self.in_room_type = QtWidgets.QComboBox()
        self.in_room_type.addItems(["Đơn", "Đôi", "VIP"])
        self.in_room_type.setStyleSheet(field_style)

        self.in_room_price = QtWidgets.QLineEdit()
        self.in_room_price.setPlaceholderText("VD: 500000")
        self.in_room_price.setStyleSheet(field_style)

        self.btn_submit_room = QtWidgets.QPushButton("Xác nhận thuê phòng")
        self.btn_submit_room.setStyleSheet(
            "background-color: #2C3E50; color: white; padding: 11px; "
            "border-radius: 4px; font-weight: bold; font-size: 13px;"
        )

        self.l_addroom.addRow("Số phòng:", self.in_room_num)
        self.l_addroom.addRow("Loại phòng:", self.in_room_type)
        self.l_addroom.addRow("Giá (VNĐ):", self.in_room_price)
        self.l_addroom.addRow("", self.btn_submit_room)

        self.l_addroom_main.addWidget(self.formWidget)
        self.l_addroom_main.addStretch()
        self.stackedWidget.addWidget(self.page_addroom)

        # ── PAGE 4: DỊCH VỤ ──────────────────────────────────────────────
        self.page_service = QtWidgets.QWidget()
        self.page_service.setStyleSheet("background-color: #F5F5F5;")
        lbl_sv = QtWidgets.QLabel("DỊCH VỤ", parent=self.page_service)
        lbl_sv.setStyleSheet("font-size: 19px; font-weight: bold; color: #1A1A1A; margin: 30px;")
        self.stackedWidget.addWidget(self.page_service)

        # ── PAGE 5: HÓA ĐƠN ──────────────────────────────────────────────
        self.page_invoice = QtWidgets.QWidget()
        self.page_invoice.setStyleSheet("background-color: #F5F5F5;")
        lbl_inv = QtWidgets.QLabel("HÓA ĐƠN", parent=self.page_invoice)
        lbl_inv.setStyleSheet("font-size: 19px; font-weight: bold; color: #1A1A1A; margin: 30px;")
        self.stackedWidget.addWidget(self.page_invoice)

        # ── PAGE 6: BÁO CÁO ──────────────────────────────────────────────
        self.page_report = QtWidgets.QWidget()
        self.page_report.setStyleSheet("background-color: #F5F5F5;")
        lbl_rpt = QtWidgets.QLabel("BÁO CÁO", parent=self.page_report)
        lbl_rpt.setStyleSheet("font-size: 19px; font-weight: bold; color: #1A1A1A; margin: 30px;")
        self.stackedWidget.addWidget(self.page_report)

        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    # ── Helper: stat card ────────────────────────────────────────────────
    def _make_stat_card(self, title: str, value: str) -> QtWidgets.QFrame:
        card = QtWidgets.QFrame()
        card.setMinimumSize(180, 110)
        card.setMaximumSize(260, 120)
        card.setStyleSheet(
            "QFrame { background-color: #D6D6D6; border-radius: 6px; }"
        )
        layout = QtWidgets.QVBoxLayout(card)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        lbl_val = QtWidgets.QLabel(value)
        lbl_val.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        lbl_val.setStyleSheet("font-size: 24px; font-weight: bold; color: #1A1A1A; background: transparent;")

        lbl_title = QtWidgets.QLabel(title)
        lbl_title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("font-size: 13px; color: #444; background: transparent;")

        layout.addWidget(lbl_val)
        layout.addWidget(lbl_title)
        return card

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Quản Lý Phòng Khách Sạn"))
