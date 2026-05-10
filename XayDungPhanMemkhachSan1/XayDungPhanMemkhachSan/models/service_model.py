"""
models/service_model.py
"""
from database.database import get_connection


class ServiceModel:

    @staticmethod
    def get_all():
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, name, price, unit, description, is_active FROM services ORDER BY id"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_active():
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, name, price, unit FROM services WHERE is_active=1 ORDER BY name"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def add(name: str, price: float, unit: str, description: str):
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO services (name, price, unit, description) VALUES (?,?,?,?)",
                (name, price, unit, description)
            )
            conn.commit()
            return True, "Thêm dịch vụ thành công!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def update(service_id: int, name: str, price: float, unit: str, description: str, is_active: int):
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE services SET name=?, price=?, unit=?, description=?, is_active=? WHERE id=?",
                (name, price, unit, description, is_active, service_id)
            )
            conn.commit()
            return True, "Cập nhật dịch vụ thành công!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def delete(service_id: int):
        conn = get_connection()
        try:
            conn.execute("UPDATE services SET is_active=0 WHERE id=?", (service_id,))
            conn.commit()
            return True, "Đã tắt dịch vụ!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def search(keyword: str):
        conn = get_connection()
        kw = f"%{keyword}%"
        rows = conn.execute(
            "SELECT id, name, price, unit, description, is_active FROM services "
            "WHERE name LIKE ? OR unit LIKE ?", (kw, kw)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ── Booking services ──────────────────────────────────────────────────────
    @staticmethod
    def add_to_booking(booking_id: int, service_id: int, quantity: int, price: float, note: str = ""):
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO booking_services (booking_id, service_id, quantity, price, note) VALUES (?,?,?,?,?)",
                (booking_id, service_id, quantity, price, note)
            )
            conn.commit()
            return True, "Thêm dịch vụ vào booking thành công!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def get_by_booking(booking_id: int):
        conn = get_connection()
        rows = conn.execute("""
            SELECT bs.id, s.name, bs.quantity, bs.price,
                   (bs.quantity * bs.price) AS total, bs.used_at, bs.note
            FROM booking_services bs
            JOIN services s ON bs.service_id = s.id
            WHERE bs.booking_id=?
        """, (booking_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]