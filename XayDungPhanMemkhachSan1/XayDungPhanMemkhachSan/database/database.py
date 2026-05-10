import sqlite3
import hashlib

DB_NAME = "hotel.db"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            full_name   TEXT    NOT NULL,
            role        TEXT    NOT NULL CHECK(role IN ('admin', 'staff')),
            is_active   INTEGER NOT NULL DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS room_types (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL UNIQUE,
            description TEXT,
            base_price  REAL    NOT NULL DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number  TEXT    NOT NULL UNIQUE,
            floor        INTEGER NOT NULL DEFAULT 1,
            type_id      INTEGER NOT NULL,
            status       TEXT    NOT NULL DEFAULT 'available'
                         CHECK(status IN ('available', 'occupied', 'maintenance')),
            description  TEXT,
            FOREIGN KEY (type_id) REFERENCES room_types(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name   TEXT    NOT NULL,
            id_card     TEXT    NOT NULL UNIQUE,
            phone       TEXT    NOT NULL,
            email       TEXT,
            address     TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL UNIQUE,
            price       REAL    NOT NULL DEFAULT 0,
            unit        TEXT    NOT NULL DEFAULT 'lan',
            description TEXT,
            is_active   INTEGER NOT NULL DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id     INTEGER NOT NULL,
            room_id         INTEGER NOT NULL,
            staff_id        INTEGER NOT NULL,
            check_in        TEXT    NOT NULL,
            check_out       TEXT    NOT NULL,
            actual_checkout TEXT,
            status          TEXT    NOT NULL DEFAULT 'booked'
                            CHECK(status IN ('booked', 'checked_in', 'checked_out', 'cancelled')),
            notes           TEXT,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (room_id)     REFERENCES rooms(id),
            FOREIGN KEY (staff_id)    REFERENCES users(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS booking_services (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id  INTEGER NOT NULL,
            service_id  INTEGER NOT NULL,
            quantity    INTEGER NOT NULL DEFAULT 1,
            price       REAL    NOT NULL,
            used_at     TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
            note        TEXT,
            FOREIGN KEY (booking_id) REFERENCES bookings(id),
            FOREIGN KEY (service_id) REFERENCES services(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id      INTEGER NOT NULL UNIQUE,
            room_charge     REAL    NOT NULL DEFAULT 0,
            service_charge  REAL    NOT NULL DEFAULT 0,
            vat_amount      REAL    NOT NULL DEFAULT 0,
            total_amount    REAL    NOT NULL DEFAULT 0,
            pay_method      TEXT    NOT NULL DEFAULT 'cash'
                            CHECK(pay_method IN ('cash', 'card', 'transfer')),
            pay_status      TEXT    NOT NULL DEFAULT 'unpaid'
                            CHECK(pay_status IN ('unpaid', 'paid')),
            paid_at         TEXT,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (booking_id) REFERENCES bookings(id)
        )
    """)

    conn.commit()
    conn.close()
    print(" Tao bang thanh cong!")


def seed_data():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO users (username, password, full_name, role)
            VALUES (?, ?, ?, ?)
        """, [
            ("admin",   hash_password("admin123"), "Nguyen Quan Tri", "admin"),
            ("staff01", hash_password("staff123"), "Tran Van An",     "staff"),
            ("staff02", hash_password("staff123"), "Le Thi Binh",     "staff"),
        ])
        print("  -> Da them 3 tai khoan (1 admin, 2 staff)")

    cur.execute("SELECT COUNT(*) FROM room_types")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO room_types (name, description, base_price)
            VALUES (?, ?, ?)
        """, [
            ("Phong Don",   "1 giuong don, toi da 1 khach",        300_000),
            ("Phong Doi",   "1 giuong doi, toi da 2 khach",        500_000),
            ("Phong VIP",   "Tien nghi cao cap, toi da 2 khach", 1_200_000),
            ("Phong Suite", "Hang sang, phong khach rieng",      2_500_000),
        ])
        print("  -> Da them 4 loai phong")

    # ── ROOMS ──────────────────────────────────────────────────────────────
    cur.execute("SELECT COUNT(*) FROM rooms")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO rooms (room_number, floor, type_id, status)
            VALUES (?, ?, ?, ?)
        """, [
            ("101", 1, 1, "available"),
            ("102", 1, 1, "available"),
            ("103", 1, 1, "maintenance"),
            ("104", 1, 2, "available"),
            ("105", 1, 2, "occupied"),
            ("201", 2, 1, "available"),
            ("202", 2, 1, "available"),
            ("203", 2, 2, "available"),
            ("204", 2, 2, "occupied"),
            ("301", 3, 3, "available"),
            ("302", 3, 3, "available"),
            ("401", 4, 4, "available"),
            ("402", 4, 4, "available"),
        ])
        print("  -> Da them 13 phong (tang 1-4)")

    cur.execute("SELECT COUNT(*) FROM services")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO services (name, price, unit, description)
            VALUES (?, ?, ?, ?)
        """, [
            ("An sang",          50_000, "nguoi", "Buffet sang tai nha hang"),
            ("An toi",          120_000, "nguoi", "Set dinner tai nha hang"),
            ("Spa & Massage",   200_000, "lan",   "Dich vu spa thu gian 60 phut"),
            ("Giat ui",          30_000, "kg",    "Giat la quan ao, tra sau 4 gio"),
            ("Dua don san bay", 250_000, "lan",   "Xe 4 cho dua don san bay"),
            ("Thue xe may",     150_000, "ngay",  "Xe tay ga, co mu bao hiem"),
            ("Minibar",          50_000, "mon",   "Do uong & snack trong phong"),
            ("Phong tap gym",    80_000, "lan",   "Su dung phong tap trong 2 gio"),
        ])
        print("  -> Da them 8 dich vu")

    cur.execute("SELECT COUNT(*) FROM customers")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO customers (full_name, id_card, phone, email, address)
            VALUES (?, ?, ?, ?, ?)
        """, [
            ("Pham Minh Tuan", "001234567890", "0931111111", "tuan@gmail.com", "12 Le Loi, Ha Noi"),
            ("Nguyen Thi Mai",  "002345678901", "0942222222", "mai@gmail.com",  "45 Tran Phu, TP.HCM"),
            ("Le Hoang Nam",    "003456789012", "0953333333", "nam@gmail.com",  "78 Nguyen Hue, Da Nang"),
        ])
        print("  -> Da them 3 khach hang mau")

    cur.execute("SELECT COUNT(*) FROM bookings")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO bookings
                (customer_id, room_id, staff_id, check_in, check_out, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            (1, 5, 2, "2025-04-18", "2025-04-21", "checked_in"),   
            (2, 9, 3, "2025-04-19", "2025-04-23", "checked_in"),   
            (3, 10, 2, "2025-04-10", "2025-04-12", "checked_out"), 
        ])
        print("  -> Da them 3 booking mau")

    cur.execute("SELECT COUNT(*) FROM booking_services")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO booking_services (booking_id, service_id, quantity, price)
            VALUES (?, ?, ?, ?)
        """, [
            (1, 1, 2,  50_000),   
            (1, 3, 1, 200_000),   
            (2, 1, 1,  50_000),  
            (3, 5, 1, 250_000),  
        ])
        print("  -> Da them dich vu cho cac booking")

    cur.execute("SELECT COUNT(*) FROM invoices")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO invoices (
                booking_id, room_charge, service_charge,
                vat_amount, total_amount, pay_method, pay_status, paid_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (3, 2_400_000, 250_000, 265_000, 2_915_000, "cash", "paid", "2025-04-12 10:30:00"),
        ])
        print("  -> Da them 1 hoa don")

    conn.commit()
    conn.close()
    print("\n Seed du lieu hoan tat!")


if __name__ == "__main__":
    create_tables()
    seed_data()