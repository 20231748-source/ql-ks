
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
        rows = conn.execute(
            "SELECT id, name, base_price, description FROM room_types ORDER BY id"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ── Room CRUD ─────────────────────────────────────────────────────────────

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

    # ── Room Type CRUD (MỚI) ─────────────────────────────────────────────────

    @staticmethod
    def add_type(name: str, base_price: float, description: str = ""):
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO room_types (name, base_price, description) VALUES (?,?,?)",
                (name, base_price, description)
            )
            conn.commit()
            return True, "Thêm loại phòng thành công!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def update_type(type_id: int, name: str, base_price: float, description: str = ""):
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE room_types SET name=?, base_price=?, description=? WHERE id=?",
                (name, base_price, description, type_id)
            )
            conn.commit()
            return True, "Cập nhật loại phòng thành công!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def delete_type(type_id: int):
        conn = get_connection()
        try:
            used = conn.execute(
                "SELECT COUNT(*) FROM rooms WHERE type_id=?", (type_id,)
            ).fetchone()[0]
            if used:
                return False, f"Không thể xóa — có {used} phòng đang dùng loại này!"
            conn.execute("DELETE FROM room_types WHERE id=?", (type_id,))
            conn.commit()
            return True, "Xóa loại phòng thành công!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    # ── Stats ─────────────────────────────────────────────────────────────────

    @staticmethod
    def stats():
        conn = get_connection()
        total    = conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
        occupied = conn.execute("SELECT COUNT(*) FROM rooms WHERE status='occupied'").fetchone()[0]
        avail    = conn.execute("SELECT COUNT(*) FROM rooms WHERE status='available'").fetchone()[0]
        maint    = conn.execute("SELECT COUNT(*) FROM rooms WHERE status='maintenance'").fetchone()[0]
        conn.close()
        return {"total": total, "occupied": occupied, "available": avail, "maintenance": maint}