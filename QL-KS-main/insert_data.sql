-- Insert users
INSERT INTO User (username, password, full_name, role, is_active) VALUES ('admin', '123456', 'Nguyễn Quản Trị', 'admin', 1);
INSERT INTO User (username, password, full_name, role, is_active) VALUES ('nhanvien', '123456', 'Trần Nhân Viên', 'staff', 1);

-- Insert room types
INSERT INTO RoomType (id, name, description, base_price) VALUES (1, 'Phòng Đơn', 'Phòng 1 giường', 300000);
INSERT INTO RoomType (id, name, description, base_price) VALUES (2, 'Phòng Đôi', 'Phòng 2 giường', 500000);
INSERT INTO RoomType (id, name, description, base_price) VALUES (3, 'Phòng VIP', 'Phòng siêu sang trọng', 1000000);

-- Insert rooms
INSERT INTO Room (room_number, floor, room_type_id, status, description) VALUES ('101', 1, 1, 'Trống', 'Tầng 1');
INSERT INTO Room (room_number, floor, room_type_id, status, description) VALUES ('102', 1, 1, 'Trống', 'Tầng 1');
INSERT INTO Room (room_number, floor, room_type_id, status, description) VALUES ('201', 2, 2, 'Trống', 'Tầng 2');
INSERT INTO Room (room_number, floor, room_type_id, status, description) VALUES ('301', 3, 3, 'Trống', 'Tầng 3 VIP');

-- Insert customers
INSERT INTO Customers (id, full_name, cccd, phone, email, address, create_at) VALUES (1, 'Nguyễn Khách Hàng', '012345678912', '0901234567', 'khachhang@gmail.com', 'Hà Nội', CURRENT_TIMESTAMP);
INSERT INTO Customers (id, full_name, cccd, phone, email, address, create_at) VALUES (2, 'Trần Văn B', '012345678913', '0911234567', 'tranvanb@gmail.com', 'Hồ Chí Minh', CURRENT_TIMESTAMP);

-- Insert services
INSERT INTO Service (id, name, price, unit, description, is_active) VALUES (1, 'Giặt ủi', 50000, 'Lần', 'Dịch vụ giặt ủi lấy ngay', 1);
INSERT INTO Service (id, name, price, unit, description, is_active) VALUES (2, 'Nước suối', 10000, 'Chai', 'Nước suối Aquafina', 1);

-- Insert booking
INSERT INTO Booking (id, customer_id, room_id, staff_id, check_in_date, check_out_date, status, notes, create_at) VALUES (1, 1, 1, 2, '2026-04-20 14:00:00', '2026-04-22 12:00:00', 'Đã đặt', 'Khách VIP', CURRENT_TIMESTAMP);

-- Insert BookingService
INSERT INTO BookingService (booking_id, service_id, quantity, price, used_at, note) VALUES (1, 1, 1, 50000, CURRENT_TIMESTAMP, '');
INSERT INTO BookingService (booking_id, service_id, quantity, price, used_at, note) VALUES (1, 2, 2, 10000, CURRENT_TIMESTAMP, '2 chai nước suối');

-- Insert Invoices
INSERT INTO Invoices (booking_id, room_charge, service_charge, vat_amount, total_amount, payment_method, payment_status, created_at) VALUES (1, 600000, 70000, 67000, 737000, 'Tiền mặt', 'Chưa thanh toán', CURRENT_TIMESTAMP);
