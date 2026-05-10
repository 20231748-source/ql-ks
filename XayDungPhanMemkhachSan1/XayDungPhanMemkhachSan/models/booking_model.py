"""
models/booking_model.py
"""
from database.database import get_connection
from datetime import date


class BookingModel:

    @staticmethod
    def get_all():
        conn = get_connection()
        rows = conn.execute("""
            SELECT b.id, c.full_name AS customer, r.room_number AS room,
                   b.check_in, b.check_out, b.status, b.actual_checkout,
                   b.customer_id, b.room_id, b.staff_id, b.notes
            FROM bookings b
            JOIN customers c ON b.customer_id = c.id
            JOIN rooms r ON b.room_id = r.id
            ORDER BY b.id DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_active_today():
        today = date.today().isoformat()
        conn = get_connection()
        rows = conn.execute("""
            SELECT r.room_number, c.full_name AS customer, b.check_out
            FROM bookings b
            JOIN customers c ON b.customer_id = c.id
            JOIN rooms r ON b.room_id = r.id
            WHERE b.status IN ('booked','checked_in')
              AND b.check_in <= ? AND b.check_out >= ?
        """, (today, today)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(booking_id: int):
        conn = get_connection()
        row = conn.execute("""
            SELECT b.*, c.full_name AS customer_name, r.room_number,
                   rt.base_price, r.type_id
            FROM bookings b
            JOIN customers c ON b.customer_id = c.id
            JOIN rooms r ON b.room_id = r.id
            JOIN room_types rt ON r.type_id = rt.id
            WHERE b.id=?
        """, (booking_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def find_checkedin_by_room(room_number: str):
        conn = get_connection()
        row = conn.execute("""
            SELECT b.id, b.customer_id, b.room_id, b.check_in, b.check_out,
                   c.full_name AS customer_name, r.room_number
            FROM bookings b
            JOIN customers c ON b.customer_id = c.id
            JOIN rooms r ON b.room_id = r.id
            WHERE r.room_number=? AND b.status='checked_in'
        """, (room_number,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def find_by_name_or_room(keyword: str):
        conn = get_connection()
        kw = f"%{keyword}%"
        rows = conn.execute("""
            SELECT b.id, c.full_name AS customer_name, r.room_number,
                   b.check_in, b.check_out, b.status
            FROM bookings b
            JOIN customers c ON b.customer_id = c.id
            JOIN rooms r ON b.room_id = r.id
            WHERE (c.full_name LIKE ? OR r.room_number LIKE ?)
              AND b.status IN ('booked','checked_in')
        """, (kw, kw)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def create(customer_id: int, room_id: int, staff_id: int,
               check_in: str, check_out: str, notes: str = ""):
        conn = get_connection()
        try:
            status = conn.execute("SELECT status FROM rooms WHERE id=?", (room_id,)).fetchone()
            if status and status[0] != "available":
                return False, "Phòng đã được đặt hoặc đang bảo trì!", None

            cur = conn.execute(
                """INSERT INTO bookings (customer_id, room_id, staff_id, check_in, check_out, status, notes)
                   VALUES (?,?,?,?,?,'checked_in',?)""",
                (customer_id, room_id, staff_id, check_in, check_out, notes)
            )
            booking_id = cur.lastrowid
            conn.execute("UPDATE rooms SET status='occupied' WHERE id=?", (room_id,))
            conn.commit()
            return True, "Đặt phòng thành công!", booking_id
        except Exception as e:
            return False, str(e), None
        finally:
            conn.close()

    @staticmethod
    def checkout(booking_id: int):
        from datetime import datetime
        conn = get_connection()
        try:
            row = conn.execute("SELECT room_id FROM bookings WHERE id=?", (booking_id,)).fetchone()
            if not row:
                return False, "Không tìm thấy booking!"
            conn.execute(
                "UPDATE bookings SET status='checked_out', actual_checkout=? WHERE id=?",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), booking_id)
            )
            conn.execute("UPDATE rooms SET status='available' WHERE id=?", (row["room_id"],))
            conn.commit()
            return True, "Trả phòng thành công!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def cancel(booking_id: int):
        conn = get_connection()
        try:
            row = conn.execute("SELECT room_id FROM bookings WHERE id=?", (booking_id,)).fetchone()
            conn.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (booking_id,))
            if row:
                conn.execute("UPDATE rooms SET status='available' WHERE id=?", (row["room_id"],))
            conn.commit()
            return True, "Huỷ đặt phòng thành công!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def search(keyword: str):
        conn = get_connection()
        kw = f"%{keyword}%"
        rows = conn.execute("""
            SELECT b.id, c.full_name AS customer, r.room_number AS room,
                   b.check_in, b.check_out, b.status
            FROM bookings b
            JOIN customers c ON b.customer_id = c.id
            JOIN rooms r ON b.room_id = r.id
            WHERE c.full_name LIKE ? OR r.room_number LIKE ? OR b.status LIKE ?
            ORDER BY b.id DESC
        """, (kw, kw, kw)).fetchall()
        conn.close()
        return [dict(r) for r in rows]