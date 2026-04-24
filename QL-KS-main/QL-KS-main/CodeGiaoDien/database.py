import sqlite3
import datetime

DB_NAME = "hotel.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Accounts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS TaiKhoan (
            Username TEXT PRIMARY KEY,
            Password TEXT NOT NULL,
            Role TEXT NOT NULL
        )
    ''')
    
    # 2. Rooms
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Phong (
            Room_ID TEXT PRIMARY KEY,
            Name TEXT NOT NULL,
            Type TEXT NOT NULL,
            Status TEXT NOT NULL,
            Price REAL NOT NULL
        )
    ''')
    
    # 3. Customers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS KhachHang (
            Customer_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            CCCD TEXT UNIQUE NOT NULL,
            Phone TEXT NOT NULL
        )
    ''')
    
    # 4. Bookings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS DatPhong (
            Booking_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Room_ID TEXT,
            Customer_ID INTEGER,
            CheckIn TEXT,
            CheckOut TEXT,
            Status TEXT,
            FOREIGN KEY(Room_ID) REFERENCES Phong(Room_ID),
            FOREIGN KEY(Customer_ID) REFERENCES KhachHang(Customer_ID)
        )
    ''')
    
    # 5. Services
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS DichVu (
            Service_ID TEXT PRIMARY KEY,
            Name TEXT NOT NULL,
            Price REAL NOT NULL
        )
    ''')
    
    # 6. Service Usage
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SuDungDichVu (
            Usage_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Booking_ID INTEGER,
            Service_ID TEXT,
            Quantity INTEGER,
            FOREIGN KEY(Booking_ID) REFERENCES DatPhong(Booking_ID),
            FOREIGN KEY(Service_ID) REFERENCES DichVu(Service_ID)
        )
    ''')
    
    # 7. Bills
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS HoaDon (
            Bill_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Booking_ID INTEGER,
            TotalRoom REAL,
            TotalService REAL,
            TotalAmount REAL,
            Date TEXT,
            FOREIGN KEY(Booking_ID) REFERENCES DatPhong(Booking_ID)
        )
    ''')
    
    # Insert default admin and staff accounts if they don't exist
    cursor.execute("SELECT COUNT(*) FROM TaiKhoan")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO TaiKhoan (Username, Password, Role) VALUES ('admin', 'admin', 'Admin')")
        cursor.execute("INSERT INTO TaiKhoan (Username, Password, Role) VALUES ('staff', 'staff', 'Staff')")
    
    # Insert default rooms if they don't exist
    cursor.execute("SELECT COUNT(*) FROM Phong")
    if cursor.fetchone()[0] == 0:
        rooms = [
            ("P101", "Phòng 101", "Phòng Thường", "Trống", 300000),
            ("P102", "Phòng 102", "Phòng Thường", "Trống", 300000),
            ("P201", "Phòng 201", "Phòng Đôi", "Trống", 500000),
            ("P202", "Phòng 202", "Phòng Đôi", "Trống", 500000),
            ("P301", "Phòng 301", "VIP", "Trống", 1000000)
        ]
        cursor.executemany("INSERT INTO Phong VALUES (?,?,?,?,?)", rooms)

    # Insert default services if they don't exist
    cursor.execute("SELECT COUNT(*) FROM DichVu")
    if cursor.fetchone()[0] == 0:
        services = [
            ("DV01", "Giặt ủi", 50000),
            ("DV02", "Dọn phòng", 30000),
            ("DV03", "Ăn sáng", 100000),
            ("DV04", "Gửi xe", 10000)
        ]
        cursor.executemany("INSERT INTO DichVu VALUES (?,?,?)", services)
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
