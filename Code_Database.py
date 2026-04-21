# ==========================================
# FILE: Database.py
# CHỨC NĂNG: Quản lý Cơ sở dữ liệu SQLite cho Game Cờ Vua, lưu trữ lịch sử các ván đấu.
# ĐIỂM NHẤN THUYẾT TRÌNH: Thể hiện thao tác CRUD (Create, Read, Update, Delete) cơ bản lên cơ sở dữ liệu quan hệ cục bộ (SQLite). Lịch sử ván kết nối trực tiếp đến giao diện.
# ==========================================

import sqlite3
from datetime import datetime
import os

class ChessDatabase:
    def __init__(self, db_name="DB_chess_history.db"):
        """
        Khởi tạo kết nối. Nếu file .db chưa tồn tại, SQLite sẽ tự động tạo ra nó.
        """
        # Đảm bảo file db được lưu cùng thư mục với code
        db_path = os.path.join(os.path.abspath("."), db_name)
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        """
        Tạo cấu trúc Bảng (Table).
        Tư duy DSA: Bảng này giống hệt một Mảng 2 chiều (2D Array), mỗi cột là 1 thuộc tính.
        """
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS MatchHistory (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                player_white TEXT,
                player_black TEXT,
                result TEXT,
                total_moves INTEGER,
                moves_list TEXT, 
                play_time TEXT
            )
        ''')
        self.conn.commit()

    # ==========================================
    # 1. CREATE (Tạo/Lưu ván đấu mới)
    # ==========================================
    def save_match(self, player_white, player_black, result, total_moves, moves_list):
        """Lưu toàn bộ "xác" ván cờ vào Database"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.cursor.execute('''
            INSERT INTO MatchHistory (player_white, player_black, result, total_moves, moves_list, play_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (player_white, player_black, result, total_moves, moves_list, now))
        
        self.conn.commit()

    # ==========================================
    # 2. READ (Đọc/Lấy danh sách lịch sử)
    # ==========================================
    def get_all_matches(self):
        """Lấy toàn bộ lịch sử đấu, sắp xếp từ mới nhất đến cũ nhất"""
        self.cursor.execute('SELECT * FROM MatchHistory ORDER BY id DESC')
        return self.cursor.fetchall() # Trả về một danh sách (List) các Tuples

    def get_match_by_id(self, match_id):
        """Truy xuất chính xác 1 ván đấu để xem lại (Replay)"""
        self.cursor.execute('SELECT * FROM MatchHistory WHERE id = ?', (match_id,))
        return self.cursor.fetchone()

    # ==========================================
    # 3. UPDATE (Cập nhật/Sửa dữ liệu)
    # ==========================================
    def update_match_result(self, match_id, new_result):
        """Sửa kết quả ván đấu (Ví dụ: Đổi từ Thua thành Thắng)"""
        self.cursor.execute('''
            UPDATE MatchHistory 
            SET result = ? 
            WHERE id = ?
        ''', (new_result, match_id))
        self.conn.commit()

    # ==========================================
    # 4. DELETE (Xóa dữ liệu)
    # ==========================================
    def delete_match(self, match_id):
        """Xóa một ván đấu khỏi lịch sử"""
        self.cursor.execute('DELETE FROM MatchHistory WHERE id = ?', (match_id,))
        self.conn.commit()

    def clear_all_history(self):
        """Xóa trắng toàn bộ lịch sử"""
        self.cursor.execute('DELETE FROM MatchHistory')
        self.conn.commit()

    def close(self):
        """Đóng kết nối cơ sở dữ liệu để giải phóng RAM"""
        self.conn.close()


# ==========================================
# KHỐI LỆNH TEST CHẠY ĐỘC LẬP
# ==========================================
if __name__ == "__main__":
    print("Đang khởi tạo Cơ sở dữ liệu SQLite...")
    db = ChessDatabase()

    print("\n--- TEST CHỨC NĂNG CREATE ---")
    # Giả lập ván 1: Mình đánh với Máy
    db.save_match(
        player_white="Người Chơi", 
        player_black="Alpha Thần Thánh", 
        result="ĐEN THẮNG", 
        total_moves=15, 
        moves_list="e2e4, e7e5, g1f3, b8c6, f1c4"
    )
    
    # Giả lập ván 2: Mình đánh với Bạn
    db.save_match(
        player_white="Minh", 
        player_black="Hoàng", 
        result="TRẮNG THẮNG", 
        total_moves=32, 
        moves_list="d2d4, d7d5, c2c4, c7c6"
    )
    print("Đã chèn 2 ván đấu giả lập vào Database thành công!")

    print("\n--- TEST CHỨC NĂNG READ ---")
    matches = db.get_all_matches()
    for match in matches:
        print(f"ID: {match[0]} | {match[1]} vs {match[2]} | KQ: {match[3]} | Thời gian: {match[6]}")
        print(f"   => Nước đi: {match[5]}")

    db.close()
    print("\nKiểm tra thư mục dự án của bạn đi, sẽ thấy một file 'chess_history.db' vừa xuất hiện!")