"""
utils/helpers.py
Hàm tiện ích dùng chung cho toàn ứng dụng.
"""
from PyQt6 import QtWidgets, QtCore


def msg_info(parent, text: str, title: str = "Thông báo"):
    QtWidgets.QMessageBox.information(parent, title, text)


def msg_warn(parent, text: str, title: str = "Cảnh báo"):
    QtWidgets.QMessageBox.warning(parent, title, text)


def msg_error(parent, text: str, title: str = "Lỗi"):
    QtWidgets.QMessageBox.critical(parent, title, text)


def msg_confirm(parent, text: str, title: str = "Xác nhận") -> bool:
    reply = QtWidgets.QMessageBox.question(
        parent, title, text,
        QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
    )
    return reply == QtWidgets.QMessageBox.StandardButton.Yes


def fmt_money(value) -> str:
    try:
        return f"{float(value):,.0f} đ"
    except Exception:
        return str(value)


def fill_table(table: QtWidgets.QTableWidget, rows: list[dict], keys: list[str],
               money_keys: list[str] = None, status_map: dict = None,
               stt: bool = False):
    """
    Điền dữ liệu vào QTableWidget.
    - keys      : thứ tự cột tương ứng với key trong dict
    - money_keys: các key sẽ được format tiền tệ
    - status_map: dict dịch trạng thái sang tiếng Việt
    - stt       : True → vertical header hiện số 1,2,3...
                  KHÔNG thêm cột mới — số STT nằm ở cột hàng bên trái
    """
    money_keys = money_keys or []
    status_map = status_map or {}

    table.setRowCount(0)
    table.setRowCount(len(rows))

    for r_idx, row in enumerate(rows):
        # Đặt số thứ tự vào vertical header (cột hàng bên trái, không phải cột data)
        if stt:
            table.setVerticalHeaderItem(
                r_idx, QtWidgets.QTableWidgetItem(str(r_idx + 1)))

        # Các cột dữ liệu — index bắt đầu từ 0, không bị lệch
        for c_idx, key in enumerate(keys):
            val = row.get(key, "")
            if key in money_keys:
                display = fmt_money(val)
            elif key in ("status", "is_active"):
                display = status_map.get(str(val), str(val))
            else:
                display = str(val) if val is not None else ""
            item = QtWidgets.QTableWidgetItem(display)
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            table.setItem(r_idx, c_idx, item)

    # KHÔNG gọi setStretchLastSection hay resizeColumnsToContents ở đây —
    # controller đã set ResizeMode.Stretch rồi, gọi lại sẽ override và gây lỗi.


STATUS_VI = {
    "available":   "Trống",
    "occupied":    "Đang thuê",
    "maintenance": "Bảo trì",
    "booked":      "Đã đặt",
    "checked_in":  "Đang ở",
    "checked_out": "Đã trả",
    "cancelled":   "Huỷ",
    "1":           "Hoạt động",
    "0":           "Vô hiệu",
    "admin":       "Quản trị",
    "staff":       "Nhân viên",
    "paid":        "Đã thanh toán",
    "unpaid":      "Chưa TT",
    "cash":        "Tiền mặt",
    "card":        "Thẻ NH",
    "transfer":    "Chuyển khoản",
}