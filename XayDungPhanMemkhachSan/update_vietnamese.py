"""
update_vietnamese.py
Chạy script này 1 lần để cập nhật toàn bộ dữ liệu sang tiếng Việt có dấu.
Đặt file này cùng thư mục với hotel.db rồi chạy: python update_vietnamese.py
"""
import sqlite3

DB_NAME = "hotel.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def update_all():
    conn = get_connection()
    cur = conn.cursor()
    total = 0

    # ── users: full_name ──────────────────────────────────────────────────────
    users = [
        ("Nguyễn Quản Trị",  "admin"),
        ("Trần Văn An",      "staff01"),
        ("Lê Thị Bình",      "staff02"),
    ]
    for full_name, username in users:
        cur.execute("UPDATE users SET full_name = ? WHERE username = ?", (full_name, username))
        total += cur.rowcount
    print(f"  ✔ users         : {len(users)} dòng")

    # ── room_types: name + description ───────────────────────────────────────
    room_types = [
        ("Phòng Đơn",   "1 giường đơn, tối đa 1 khách",           "Phong Don"),
        ("Phòng Đôi",   "1 giường đôi, tối đa 2 khách",           "Phong Doi"),
        ("Phòng VIP",   "Tiện nghi cao cấp, tối đa 2 khách",      "Phong VIP"),
        ("Phòng Suite", "Hạng sang, phòng khách riêng",           "Phong Suite"),
    ]
    for new_name, new_desc, old_name in room_types:
        cur.execute("""
            UPDATE room_types SET name = ?, description = ?
            WHERE name = ?
        """, (new_name, new_desc, old_name))
        total += cur.rowcount
    print(f"  ✔ room_types    : {len(room_types)} dòng")

    # ── services: name + unit + description ──────────────────────────────────
    services = [
        ("Ăn sáng",           "người", "Buffet sáng tại nhà hàng",           "An sang"),
        ("Ăn tối",            "người", "Set dinner tại nhà hàng",            "An toi"),
        ("Spa & Massage",     "lần",   "Dịch vụ spa thư giãn 60 phút",      "Spa & Massage"),
        ("Giặt ủi",           "kg",    "Giặt là quần áo, trả sau 4 giờ",    "Giat ui"),
        ("Đưa đón sân bay",   "lần",   "Xe 4 chỗ đưa đón sân bay",          "Dua don san bay"),
        ("Thuê xe máy",       "ngày",  "Xe tay ga, có mũ bảo hiểm",         "Thue xe may"),
        ("Minibar",           "món",   "Đồ uống & snack trong phòng",        "Minibar"),
        ("Phòng tập gym",     "lần",   "Sử dụng phòng tập trong 2 giờ",     "Phong tap gym"),
    ]
    for new_name, new_unit, new_desc, old_name in services:
        cur.execute("""
            UPDATE services SET name = ?, unit = ?, description = ?
            WHERE name = ?
        """, (new_name, new_unit, new_desc, old_name))
        total += cur.rowcount
    print(f"  ✔ services      : {len(services)} dòng")

    # ── customers: full_name + address ───────────────────────────────────────
    customers = [
        ("Phạm Minh Tuấn", "12 Lê Lợi, Hà Nội",       "001234567890"),
        ("Nguyễn Thị Mai",  "45 Trần Phú, TP.HCM",      "002345678901"),
        ("Lê Hoàng Nam",    "78 Nguyễn Huệ, Đà Nẵng",  "003456789012"),
    ]
    for full_name, address, id_card in customers:
        cur.execute("""
            UPDATE customers SET full_name = ?, address = ?
            WHERE id_card = ?
        """, (full_name, address, id_card))
        total += cur.rowcount
    print(f"  ✔ customers     : {len(customers)} dòng")

    conn.commit()
    conn.close()
    print(f"\n✅ Hoàn tất! Đã cập nhật {total} dòng sang tiếng Việt có dấu.")


if __name__ == "__main__":
    print("🔄 Đang cập nhật dữ liệu tiếng Việt...\n")
    update_all()
