# ==========================================
# FILE: AI_Stockfish.py
# CHỨC NĂNG: Lớp bao bọc (Wrapper) engine Stockfish để tính toán nước đi và phân tích chất lượng nước đi.
# ĐIỂM NHẤN THUYẾT TRÌNH: Sử dụng Threading (Đa luồng) để không làm đơ giao diện chính, kết hợp với thư viện python-chess để giao tiếp UCI với engine.
# ==========================================
import chess
import chess.engine
import chess.polyglot
import os
import sys
import subprocess # THÊM THƯ VIỆN NÀY ĐỂ GIẤU CONSOLE
import threading

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class StockfishCoach:
    def __init__(self, engine_path="Engine_stockfish.exe", book_path="Engine_human.bin"):
        self.lock = threading.RLock() # Khóa đồng bộ chống crash asyncio trên thread
        self.engine_path = get_resource_path(engine_path)
        self.book_path = get_resource_path(book_path)

        if not os.path.exists(self.engine_path):
            raise FileNotFoundError(f"Không tìm thấy file AI tại: {self.engine_path}")
            
        try:
            if sys.platform == "win32":
                self.engine = chess.engine.SimpleEngine.popen_uci(
                    self.engine_path, 
                    creationflags=subprocess.CREATE_NO_WINDOW # Giấu nhẹm đi
                )
            else:
                self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
        except Exception as e:
            print(f"Lỗi khi khởi chạy Stockfish: {e}")
            self.engine = None
            
        self.limit = chess.engine.Limit(time=0.1)

    def set_difficulty(self, skill_level, depth_limit):
        """Cấu hình lại độ khó của Stockfish tuỳ theo vị Tướng"""
        with self.lock:
            # Option 'Skill Level' của Stockfish dao động từ 0 (cực dốt) đến 20 (Max)
            if skill_level is not None:
                self.engine.configure({"Skill Level": skill_level})
            if depth_limit is not None:
                self.limit = chess.engine.Limit(depth=depth_limit)

    def get_board_score(self, fen_string):
        board = chess.Board(fen_string)
        with self.lock:
            if not self.engine: return 0
            try:
                info = self.engine.analyse(board, self.limit)
            except Exception as e:
                print(f"Lỗi phân tích: {e}")
                return 0
            
        score = info["score"].white()
        if score.is_mate():
            mate_in = score.mate()
            return 10000 if mate_in > 0 else -10000
        return score.score()

    def get_best_move(self, fen_string):
        board = chess.Board(fen_string)
        
        # --- TRA SÁCH TRƯỚC ---
        if os.path.exists(self.book_path):
            with chess.polyglot.open_reader(self.book_path) as reader:
                try:
                    entry = reader.find(board)
                    return str(entry.move)
                except IndexError:
                    pass 
                    
        # --- HẾT SÁCH THÌ STOCKFISH TÍNH ---
        with self.lock:
            if not self.engine: return "None"
            try:
                result = self.engine.play(board, self.limit) 
                return str(result.move)
            except Exception as e:
                print(f"Lỗi tính nước đi: {e}")
                return "None"

    def analyze_move_quality(self, fen_before, fen_after, is_white_turn, move_uci):
        """
        Thuật toán đánh giá Centipawn Loss (CPL) chuẩn Chess.com
        """
        board_before = chess.Board(fen_before)
        
        # 1. TRƯỜNG HỢP NƯỚC BẮT BUỘC (Forced Move)
        if len(list(board_before.legal_moves)) == 1:
            return "NƯỚC BẮT BUỘC", "#7f8c8d"  # Màu xám
            
        # 2. KHAI CUỘC (Book Move) - Nếu có thư viện Opening
        book_path = get_resource_path("Engine_human.bin")
        if os.path.exists(book_path):
            with chess.polyglot.open_reader(book_path) as reader:
                for entry in reader.find_all(board_before):
                    if str(entry.move) == move_uci:
                        return "BOOK MOVE (Sách)", "#a58e7a" # Màu nâu nhạt
                        
        # 3. LẤY ĐIỂM SỐ TỪ STOCKFISH (Quy về góc nhìn của Trắng)
        score_before = self.get_board_score(fen_before)
        score_after = self.get_board_score(fen_after)

        # 4. TÍNH TOÁN ĐỘ LỆCH ĐIỂM (CPL) DỰA TRÊN LƯỢT ĐI
        # Nếu là Trắng đi, ta muốn điểm tăng (cp_loss = trước - sau)
        # Nếu là Đen đi, ta muốn điểm giảm (cp_loss = sau - trước)
        if is_white_turn:
            cp_loss = score_before - score_after
        else:
            cp_loss = score_after - score_before

        # 5. XỬ LÝ TRƯỜNG HỢP BỎ LỠ CHIẾU BÍ (Missed Win)
        # Điểm > 5000 tức là Stockfish đã tìm ra đường Mate, nhưng sau khi đi lại mất Mate
        if is_white_turn:
            missed_mate = (score_before > 5000 and score_after < 5000)
        else:
            missed_mate = (score_before < -5000 and score_after > -5000)
            
        if missed_mate:
            return "MISSED WIN !! (Bỏ lỡ)", "#ff7769" # Màu hồng đỏ

        # 6. KHUNG ĐÁNH GIÁ CHUẨN CHESS.COM
        # Khi CPL âm rất sâu, tức là bạn tìm ra nước đi mà Stockfish ở độ sâu thấp không nhìn ra
        if cp_loss < -150:
            return "BRILLIANT!!", "#1baca6" # Xanh lam ngọc (Teal)
        elif cp_loss < -50:
            return "GREAT MOVE!", "#5c8bb0" # Xanh dương
            
        # CPL xấp xỉ 0 tức là bạn đi trùng với nước tốt nhất của máy tính
        elif cp_loss <= 10:
            return "BEST MOVE ★", "#95ba25" # Xanh lá mạ
        elif cp_loss <= 30:
            return "EXCELLENT", "#95ba30" 
        elif cp_loss <= 60:
            return "GOOD", "#95ba55"
            
        # Bắt đầu đi những nước ngáo ngơ làm tụt điểm
        elif cp_loss <= 150:
            return "INACCURACY !?", "#f6cd46" # Vàng
        elif cp_loss <= 300:
            return "MISTAKE ?", "#e58f2a" # Cam
        else:
            return "BLUNDER ??", "#ca3431" # Đỏ thẫm

    def analyze_move_quality_with_cp(self, fen_before, fen_after, is_white_turn, move_uci):
        """Dành riêng cho Game Review: Trả về Label, Color và chỉ số Centipawn dạng chuỗi (Vd: +1.2 hoặc -M3)"""
        label, color = self.analyze_move_quality(fen_before, fen_after, is_white_turn, move_uci)
        
        board_after = chess.Board(fen_after)
        with self.lock:
            if not self.engine: return label, color, "0.00"
            try:
                info = self.engine.analyse(board_after, self.limit)
            except Exception as e:
                print(f"Lỗi phân tích: {e}")
                return label, color, "0.00"
        score = info["score"].white()
        
        if score.is_mate():
            mate_in = score.mate()
            cp_str = f"+M{mate_in}" if mate_in > 0 else f"-M{abs(mate_in)}"
        else:
            val = score.score() / 100.0
            cp_str = f"+{val:.2f}" if val > 0 else f"{val:.2f}"
            if cp_str == "+0.00": cp_str = "0.00"
            
        return label, color, cp_str

    def close(self):
        with self.lock:
            if self.engine:
                try:
                    self.engine.quit()
                    self.engine = None
                except:
                    pass
