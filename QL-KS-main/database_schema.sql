-- Tạo CSDL
CREATE DATABASE IF NOT EXISTS qlks;
USE qlks

-- Tạo csdl

-- 1. Bảng User (Nhân viên / Quản trị viên)

CREATE TABLE User (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    is_active TINYINT(1) DEFAULT 1
);


-- 2. Bảng RoomType (Loại phòng)
CREATE TABLE RoomType (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    base_price DECIMAL(10, 2) NOT NULL
);


-- 3. Bảng Room (Phòng)
CREATE TABLE Room (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_number VARCHAR(20) NOT NULL UNIQUE,
    floor INT NOT NULL,
    room_type_id INT NOT NULL,
    status VARCHAR(50) NOT NULL,
    description TEXT,
    FOREIGN KEY (room_type_id) REFERENCES RoomType(id) ON DELETE RESTRICT
);

-- 4. Bảng Customers (Khách hàng)
CREATE TABLE Customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    cccd VARCHAR(20) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    address TEXT,
    create_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 5. Bảng Service (Dịch vụ)
CREATE TABLE Service (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    description TEXT,
    is_active TINYINT(1) DEFAULT 1
);

-- 6. Bảng Booking (Đặt phòng)
CREATE TABLE Booking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    room_id INT NOT NULL,
    staff_id INT NOT NULL,
    check_in_date DATETIME NOT NULL,
    check_out_date DATETIME NOT NULL,
    actual_checkout DATETIME,
    status VARCHAR(50) NOT NULL,
    notes TEXT,
    create_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES Customers(id) ON DELETE RESTRICT,
    FOREIGN KEY (room_id) REFERENCES Room(id) ON DELETE RESTRICT,
    FOREIGN KEY (staff_id) REFERENCES User(id) ON DELETE RESTRICT
);

-- 7. Bảng BookingService (Dịch vụ đã đặt)
CREATE TABLE BookingService (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    service_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    used_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    note TEXT,
    FOREIGN KEY (booking_id) REFERENCES Booking(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES Service(id) ON DELETE RESTRICT
);

-- 8. Bảng Invoices (Hóa đơn)
CREATE TABLE Invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    room_charge DECIMAL(10, 2) NOT NULL,
    service_charge DECIMAL(10, 2) NOT NULL,
    vat_amount DECIMAL(10, 2) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50),
    payment_status VARCHAR(50),
    paid_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES Booking(id) ON DELETE CASCADE
);