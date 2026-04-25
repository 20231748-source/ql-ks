import sqlite3

db_path = r"c:\Users\Administrator\Downloads\QL-KS-main\QL-KS-main\ThietKeClassAndDatabase\qlks.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Insert users
    cursor.execute("INSERT OR IGNORE INTO User (username, password, full_name, role, is_active) VALUES ('admin', '123456', 'Nguyễn Quản Trị', 'admin', 1)")
    cursor.execute("INSERT OR IGNORE INTO User (username, password, full_name, role, is_active) VALUES ('nhanvien', '123456', 'Trần Nhân Viên', 'staff', 1)")
    
    # Insert room types
    cursor.execute("INSERT OR IGNORE INTO RoomType (id, name, description, base_price) VALUES (1, 'Phòng Đơn', 'Phòng 1 giường', 300000)")
    cursor.execute("INSERT OR IGNORE INTO RoomType (id, name, description, base_price) VALUES (2, 'Phòng Đôi', 'Phòng 2 giường', 500000)")
    cursor.execute("INSERT OR IGNORE INTO RoomType (id, name, description, base_price) VALUES (3, 'Phòng VIP', 'Phòng siêu sang trọng', 1000000)")

    # Insert rooms
    cursor.execute("INSERT OR IGNORE INTO Room (room_number, floor, room_type_id, status, description) VALUES ('101', 1, 1, 'Trống', 'Tầng 1')")
    cursor.execute("INSERT OR IGNORE INTO Room (room_number, floor, room_type_id, status, description) VALUES ('102', 1, 1, 'Trống', 'Tầng 1')")
    cursor.execute("INSERT OR IGNORE INTO Room (room_number, floor, room_type_id, status, description) VALUES ('201', 2, 2, 'Trống', 'Tầng 2')")
    cursor.execute("INSERT OR IGNORE INTO Room (room_number, floor, room_type_id, status, description) VALUES ('301', 3, 3, 'Trống', 'Tầng 3 VIP')")

    # Insert customers
    cursor.execute("INSERT OR IGNORE INTO Customers (id, full_name, cccd, phone, email, address, create_at) VALUES (1, 'Nguyễn Khách Hàng', '012345678912', '0901234567', 'khachhang@gmail.com', 'Hà Nội', datetime('now'))")
    cursor.execute("INSERT OR IGNORE INTO Customers (id, full_name, cccd, phone, email, address, create_at) VALUES (2, 'Trần Văn B', '012345678913', '0911234567', 'tranvanb@gmail.com', 'Hồ Chí Minh', datetime('now'))")

    # Insert services
    cursor.execute("INSERT OR IGNORE INTO Service (id, name, price, unit, description, is_active) VALUES (1, 'Giặt ủi', 50000, 'Lần', 'Dịch vụ giặt ủi lấy ngay', 1)")
    cursor.execute("INSERT OR IGNORE INTO Service (id, name, price, unit, description, is_active) VALUES (2, 'Nước suối', 10000, 'Chai', 'Nước suối Aquafina', 1)")

    # Insert booking
    cursor.execute("INSERT OR IGNORE INTO Booking (id, customer_id, room_id, staff_id, check_in_date, check_out_date, status, notes, create_at) VALUES (1, 1, 1, 2, '2026-04-20 14:00:00', '2026-04-22 12:00:00', 'Đã đặt', 'Khách VIP', datetime('now'))")

    # Insert BookingService
    cursor.execute("INSERT OR IGNORE INTO BookingService (booking_id, service_id, quantity, price, used_at, note) VALUES (1, 1, 1, 50000, datetime('now'), '')")
    cursor.execute("INSERT OR IGNORE INTO BookingService (booking_id, service_id, quantity, price, used_at, note) VALUES (1, 2, 2, 10000, datetime('now'), '2 chai nước suối')")

    # Insert Invoices
    cursor.execute("INSERT OR IGNORE INTO Invoices (booking_id, room_charge, service_charge, vat_amount, total_amount, payment_method, payment_status, created_at) VALUES (1, 600000, 70000, 67000, 737000, 'Tiền mặt', 'Chưa thanh toán', datetime('now'))")

    conn.commit()
    print("Success")
except Exception as e:
    print("Error:", repr(e))
    conn.rollback()
finally:
    conn.close()
