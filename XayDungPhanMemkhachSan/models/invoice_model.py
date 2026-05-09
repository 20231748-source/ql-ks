"""
models/invoice_model.py
"""
from database.database import get_connection
from datetime import datetime, date


VAT_RATE = 0.10


class InvoiceModel:

    @staticmethod
    def calculate(booking_id: int):
        conn = get_connection()
        booking = conn.execute("""
            SELECT b.check_in, b.check_out, rt.base_price
            FROM bookings b
            JOIN rooms r ON b.room_id = r.id
            JOIN room_types rt ON r.type_id = rt.id
            WHERE b.id=?
        """, (booking_id,)).fetchone()

        if not booking:
            conn.close()
            return None

        from datetime import date as dt
        ci = dt.fromisoformat(booking["check_in"])
        co = dt.fromisoformat(booking["check_out"])
        days = max((co - ci).days, 1)
        room_charge = days * booking["base_price"]

        svc_rows = conn.execute(
            "SELECT SUM(quantity * price) AS total FROM booking_services WHERE booking_id=?",
            (booking_id,)
        ).fetchone()
        conn.close()

        service_charge = svc_rows["total"] or 0
        vat = (room_charge + service_charge) * VAT_RATE
        total = room_charge + service_charge + vat
        return {
            "booking_id": booking_id,
            "room_charge": room_charge,
            "service_charge": service_charge,
            "vat_amount": vat,
            "total_amount": total,
            "days": days,
        }

    @staticmethod
    def create_or_update(booking_id: int, pay_method: str):
        data = InvoiceModel.calculate(booking_id)
        if not data:
            return False, "Không tìm thấy booking!"
        conn = get_connection()
        try:
            existing = conn.execute(
                "SELECT id FROM invoices WHERE booking_id=?", (booking_id,)
            ).fetchone()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if existing:
                conn.execute("""
                    UPDATE invoices SET room_charge=?, service_charge=?, vat_amount=?,
                    total_amount=?, pay_method=?, pay_status='paid', paid_at=?
                    WHERE booking_id=?
                """, (data["room_charge"], data["service_charge"], data["vat_amount"],
                      data["total_amount"], pay_method, now, booking_id))
            else:
                conn.execute("""
                    INSERT INTO invoices (booking_id, room_charge, service_charge,
                        vat_amount, total_amount, pay_method, pay_status, paid_at)
                    VALUES (?,?,?,?,?,?,'paid',?)
                """, (booking_id, data["room_charge"], data["service_charge"],
                      data["vat_amount"], data["total_amount"], pay_method, now))
            conn.commit()
            return True, data
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def get_by_booking(booking_id: int):
        conn = get_connection()
        row = conn.execute("SELECT * FROM invoices WHERE booking_id=?", (booking_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def revenue_by_range(date_from: str, date_to: str):
        conn = get_connection()
        rows = conn.execute("""
            SELECT DATE(i.paid_at) AS day, SUM(i.total_amount) AS revenue,
                   COUNT(*) AS bookings
            FROM invoices i
            WHERE i.pay_status='paid' AND DATE(i.paid_at) BETWEEN ? AND ?
            GROUP BY day ORDER BY day
        """, (date_from, date_to)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def revenue_by_range_all(date_from: str, date_to: str):
        """Doanh thu ước tính theo ngày — bao gồm cả booking chưa thanh toán.
        Dùng cho Dashboard và Thống Kê khi chưa có nhiều invoice paid.
        Ưu tiên dùng paid_at của invoice nếu đã paid, ngược lại dùng check_out."""
        conn = get_connection()
        rows = conn.execute("""
            SELECT
                COALESCE(DATE(i.paid_at), b.check_out) AS day,
                SUM(COALESCE(i.total_amount,
                    (julianday(b.check_out) - julianday(b.check_in))
                    * rt.base_price * 1.10
                )) AS revenue,
                COUNT(*) AS bookings
            FROM bookings b
            JOIN rooms r  ON b.room_id  = r.id
            JOIN room_types rt ON r.type_id = rt.id
            LEFT JOIN invoices i ON i.booking_id = b.id
            WHERE b.status IN ('checked_in', 'checked_out', 'booked')
              AND COALESCE(DATE(i.paid_at), b.check_out) BETWEEN ? AND ?
            GROUP BY day
            ORDER BY day
        """, (date_from, date_to)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def summary(date_from: str, date_to: str):
        conn = get_connection()
        rev = conn.execute("""
            SELECT COALESCE(SUM(total_amount),0) AS total
            FROM invoices WHERE pay_status='paid'
            AND DATE(paid_at) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()["total"]

        booked = conn.execute("""
            SELECT COUNT(*) FROM bookings
            WHERE status IN ('checked_in','checked_out')
            AND check_in BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()[0]

        customers = conn.execute("""
            SELECT COUNT(DISTINCT customer_id) FROM bookings
            WHERE check_in BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()[0]
        conn.close()
        return {"revenue": rev, "booked": booked, "customers": customers}