"""
models/user_model.py
Tầng truy cập dữ liệu cho bảng users.
"""
from database.database import get_connection, hash_password


class UserModel:

    @staticmethod
    def login(username: str, password: str):
        """Xác thực đăng nhập, trả về dict user hoặc None."""
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=? AND is_active=1",
            (username, hash_password(password))
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_all():
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, full_name, username, '' AS phone, role, is_active FROM users ORDER BY id"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def add(username: str, password: str, full_name: str, role: str):
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO users (username, password, full_name, role) VALUES (?,?,?,?)",
                (username, hash_password(password), full_name, role)
            )
            conn.commit()
            return True, "Thêm nhân viên thành công!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def update(user_id: int, full_name: str, role: str, is_active: int):
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE users SET full_name=?, role=?, is_active=? WHERE id=?",
                (full_name, role, is_active, user_id)
            )
            conn.commit()
            return True, "Cập nhật thành công!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def delete(user_id: int):
        conn = get_connection()
        try:
            # Không xóa cứng, chỉ vô hiệu hoá
            conn.execute("UPDATE users SET is_active=0 WHERE id=?", (user_id,))
            conn.commit()
            return True, "Đã vô hiệu hoá tài khoản!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def reset_password(user_id: int, new_password: str):
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE users SET password=? WHERE id=?",
                (hash_password(new_password), user_id)
            )
            conn.commit()
            return True, "Đặt lại mật khẩu thành công!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def change_password(user_id: int, old_password: str, new_password: str):
        conn = get_connection()
        row = conn.execute(
            "SELECT id FROM users WHERE id=? AND password=?",
            (user_id, hash_password(old_password))
        ).fetchone()
        conn.close()
        if not row:
            return False, "Mật khẩu cũ không đúng!"
        return UserModel.reset_password(user_id, new_password)

    @staticmethod
    def update_profile(user_id: int, full_name: str):
        conn = get_connection()
        try:
            conn.execute("UPDATE users SET full_name=? WHERE id=?", (full_name, user_id))
            conn.commit()
            return True, "Cập nhật thông tin thành công!"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def search(keyword: str):
        conn = get_connection()
        kw = f"%{keyword}%"
        rows = conn.execute(
            "SELECT id, full_name, username, '' AS phone, role, is_active FROM users "
            "WHERE full_name LIKE ? OR username LIKE ?",
            (kw, kw)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def log_activity(user_id: int, action: str):
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO user_logs (user_id, action) VALUES (?, ?)",
                (user_id, action)
            )
            conn.commit()
        except Exception as e:
            print(f"Error logging activity: {e}")
        finally:
            conn.close()

    @staticmethod
    def get_activity_history(user_id: int):
        conn = get_connection()
        rows = conn.execute(
            "SELECT action, created_at FROM user_logs WHERE user_id=? ORDER BY created_at DESC", 
            (user_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]