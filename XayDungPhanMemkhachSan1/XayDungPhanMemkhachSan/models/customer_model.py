"""
models/customer_model.py
"""
from database.database import get_connection


class CustomerModel:

    @staticmethod
    def get_all():
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, full_name, id_card, phone, email, address, created_at FROM customers ORDER BY id"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(customer_id: int):
        conn = get_connection()
        row = conn.execute("SELECT * FROM customers WHERE id=?", (customer_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def find_by_idcard(id_card: str):
        conn = get_connection()
        row = conn.execute("SELECT * FROM customers WHERE id_card=?", (id_card,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def add(full_name: str, id_card: str, phone: str, email: str, address: str):
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO customers (full_name, id_card, phone, email, address) VALUES (?,?,?,?,?)",
                (full_name, id_card, phone, email, address)
            )
            conn.commit()
            return True, "Thêm khách hàng thành công!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def update(customer_id: int, full_name: str, id_card: str, phone: str, email: str, address: str):
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE customers SET full_name=?, id_card=?, phone=?, email=?, address=? WHERE id=?",
                (full_name, id_card, phone, email, address, customer_id)
            )
            conn.commit()
            return True, "Cập nhật khách hàng thành công!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def delete(customer_id: int):
        conn = get_connection()
        try:
            active = conn.execute(
                "SELECT COUNT(*) FROM bookings WHERE customer_id=? AND status IN ('booked','checked_in')",
                (customer_id,)
            ).fetchone()[0]
            if active:
                return False, "Không thể xóa khách đang có đặt phòng!"
            conn.execute("DELETE FROM customers WHERE id=?", (customer_id,))
            conn.commit()
            return True, "Xóa khách hàng thành công!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def search(keyword: str):
        conn = get_connection()
        kw = f"%{keyword}%"
        rows = conn.execute(
            "SELECT id, full_name, id_card, phone, email, address, created_at FROM customers "
            "WHERE full_name LIKE ? OR id_card LIKE ? OR phone LIKE ?",
            (kw, kw, kw)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def count():
        conn = get_connection()
        n = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        conn.close()
        return n