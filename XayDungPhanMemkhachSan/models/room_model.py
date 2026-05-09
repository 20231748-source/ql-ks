"""
models/room_model.py
Tầng truy cập dữ liệu cho bảng rooms và room_types.
"""
from database.database import get_connection


class RoomModel:

    @staticmethod
    def get_all():
        conn = get_connection()
        rows = conn.execute("""
            SELECT r.id, r.room_number, rt.name AS type_name, rt.base_price,
                   r.floor, r.status, r.description, r.type_id
            FROM rooms r
            JOIN room_types rt ON r.type_id = rt.id
            ORDER BY r.room_number
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_available():
        conn = get_connection()
        rows = conn.execute("""
            SELECT r.id, r.room_number, rt.name AS type_name, rt.base_price,
                   r.floor, r.status
            FROM rooms r
            JOIN room_types rt ON r.type_id = rt.id
            WHERE r.status = 'available'
            ORDER BY r.room_number
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_types():
        conn = get_connection()
        rows = conn.execute("SELECT id, name, base_price FROM room_types ORDER BY id").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def add(room_number: str, floor: int, type_id: int, status: str, description: str):
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO rooms (room_number, floor, type_id, status, description) VALUES (?,?,?,?,?)",
                (room_number, floor, type_id, status, description)
            )
            conn.commit()
            return True, "Thêm phòng thành công!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def update(room_id: int, room_number: str, floor: int, type_id: int, status: str, description: str):
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE rooms SET room_number=?, floor=?, type_id=?, status=?, description=? WHERE id=?",
                (room_number, floor, type_id, status, description, room_id)
            )
            conn.commit()
            return True, "Cập nhật phòng thành công!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def delete(room_id: int):
        conn = get_connection()
        try:
            active = conn.execute(
                "SELECT COUNT(*) FROM bookings WHERE room_id=? AND status IN ('booked','checked_in')",
                (room_id,)
            ).fetchone()[0]
            if active:
                return False, "Không thể xóa phòng đang có khách!"
            conn.execute("DELETE FROM rooms WHERE id=?", (room_id,))
            conn.commit()
            return True, "Xóa phòng thành công!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def search(keyword: str):
        conn = get_connection()
        kw = f"%{keyword}%"
        rows = conn.execute("""
            SELECT r.id, r.room_number, rt.name AS type_name, rt.base_price,
                   r.floor, r.status, r.description, r.type_id
            FROM rooms r
            JOIN room_types rt ON r.type_id = rt.id
            WHERE r.room_number LIKE ? OR rt.name LIKE ? OR r.status LIKE ?
        """, (kw, kw, kw)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def set_status(room_id: int, status: str):
        conn = get_connection()
        conn.execute("UPDATE rooms SET status=? WHERE id=?", (status, room_id))
        conn.commit()
        conn.close()

    # ── Stats ──
    @staticmethod
    def stats():
        conn = get_connection()
        total    = conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
        occupied = conn.execute("SELECT COUNT(*) FROM rooms WHERE status='occupied'").fetchone()[0]
        avail    = conn.execute("SELECT COUNT(*) FROM rooms WHERE status='available'").fetchone()[0]
        maint    = conn.execute("SELECT COUNT(*) FROM rooms WHERE status='maintenance'").fetchone()[0]
        conn.close()
        return {"total": total, "occupied": occupied, "available": avail, "maintenance": maint}