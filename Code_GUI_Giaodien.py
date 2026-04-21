# ==========================================
# FILE: GUI_Giaodien.py
# CHỨC NĂNG: Giao diện đồ họa người dùng (GUI) chính cho game, được thiết kế bằng PySide6.
# ĐIỂM NHẤN THUYẾT TRÌNH: Sử dụng QStackedWidget để chuyển đổi qua lại giữa Màn hình Menu, Game và Lịch sử đấu. Tích hợp Multithreading (Luồng song song) với QThread để không làm giật lag giao diện (non-blocking UI) khi AI đang tính toán nước đi.
# ==========================================
import sys
import os
import re
import ctypes
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                               QGridLayout, QVBoxLayout, QHBoxLayout, QLabel,
                               QInputDialog, QListWidget, QStackedWidget, QPushButton,
                               QGraphicsDropShadowEffect, QTableWidget, QTableWidgetItem,
                               QHeaderView, QListWidgetItem)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QPixmap, QCursor, QFont, QPainter, QPen, QColor, QIcon
from Code_Logic_Xuly import GameState, Move
from Code_AI_Stockfish import StockfishCoach
from Code_Database import ChessDatabase

def get_resource_path(relative_path):
    """Hàm giúp file .exe tìm đúng thư mục Tạm chứa ảnh"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# ==========================================
# CLASS 1: ChessSquare (Kế thừa từ QLabel)
# Mục đích: Đại diện cho 1 ô vuông duy nhất trên bàn cờ 8x8.
# Chịu trách nhiệm: Hiển thị màu nền, load ảnh quân cờ, bắt sự kiện click.
# ==========================================
class ChessSquare(QLabel):
    # Signal (Tín hiệu): Đây là cách các đối tượng trong PySide6 "nói chuyện" với nhau.
    # Khi ô cờ bị click, nó sẽ hét lên: "Tôi ở hàng [int], cột [int] vừa bị click!"
    square_clicked = Signal(int, int)

    def __init__(self, row, col, bg_color):
        super().__init__()
        self.row = row
        self.col = col
        self.default_color = bg_color
        self.piece_name = None # Trạng thái ban đầu: Ô trống, không có quân cờ
        self.is_valid_move = False
        
        # --- Thiết lập Giao diện cho Ô cờ ---
        self.setMinimumSize(60, 60) # Kích thước tối thiểu, cho phép co dãn to ra khi kéo cửa sổ
        self.setAlignment(Qt.AlignCenter) # Căn giữa hình ảnh quân cờ
        self.setScaledContents(True) # Ép hình ảnh tự động co dãn vừa khít với kích thước ô cờ
        self.setCursor(QCursor(Qt.PointingHandCursor)) # Đổi con trỏ thành hình "bàn tay" khi di chuột vào
        
        # Đổ màu nền khởi tạo
        self.reset_color()

    def set_piece(self, piece_name):
        """Hàm dùng để tải và hiển thị hình ảnh quân cờ (Ví dụ: 'wP', 'bK')"""
        self.piece_name = piece_name
        if self.piece_name:
            # BẮT BUỘC PHẢI BỌC ĐƯỜNG DẪN BẰNG HÀM get_resource_path
            image_path = get_resource_path(f"images/{self.piece_name}.png")
            
            if os.path.exists(image_path):
                self.setPixmap(QPixmap(image_path))
            else:
                self.setText("?") 
        else:
            self.clear()

    def reset_color(self):
        """Hàm trả ô cờ về màu sắc ban đầu"""
        self.setStyleSheet(f"background-color: {self.default_color}; border: 1px solid #333;")

    def highlight(self, color="rgba(0, 243, 255, 0.3)"):
        """Hàm bôi màu khi chọn ô cờ hoặc highlight nước đi"""
        self.setStyleSheet(f"background-color: {color}; border: 2px solid #00f3ff;")

    def highlight_last_move(self):
        """Highlight màu vàng nhạt cho nước đi vừa thực hiện"""
        self.setStyleSheet(f"background-color: #c9c922; border: 2px solid #f6f669;")

    def mousePressEvent(self, event):
        """Hàm ghi đè (Override) sự kiện click chuột mặc định của thư viện"""
        if event.button() == Qt.LeftButton: # Chỉ nhận diện chuột trái
            # Phát tín hiệu tọa độ ra ngoài để Class MainWindow xử lý
            self.square_clicked.emit(self.row, self.col)

    def set_valid_move(self, is_valid):
        """Bật/tắt trạng thái gợi ý nước đi"""
        self.is_valid_move = is_valid
        self.update() # Yêu cầu vẽ lại ô cờ

    def paintEvent(self, event):
        """Ghi đè hàm vẽ mặc định để chèn thêm chấm mờ"""
        super().paintEvent(event) # Vẫn giữ nguyên màu nền và ảnh quân cờ cũ
        
        if self.is_valid_move:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing) # Làm mịn, chống răng cưa
            center = self.rect().center()
            
            if self.piece_name:
                # Nếu ô có quân địch -> Vẽ vòng tròn rỗng bao quanh
                painter.setPen(QPen(QColor(0, 0, 0, 60), 6)) # Đen mờ, viền dày 6px
                painter.setBrush(Qt.NoBrush)
                radius = min(self.width(), self.height()) / 2 - 8
                painter.drawEllipse(center, radius, radius)
            else:
                # Nếu ô trống -> Vẽ chấm tròn đặc ở giữa
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(0, 0, 0, 60)) # Màu đen mờ (Alpha 60)
                radius = min(self.width(), self.height()) / 6
                painter.drawEllipse(center, radius, radius)
            painter.end()

# ==========================================
# CLASS: AIWorker (Đa luồng)
# Vai trò: Đem tác vụ nặng (Stockfish) ra chạy riêng để không làm đơ Giao diện
# ==========================================
class AIWorker(QThread):
    eval_done = Signal(str, str) 

    # Đã thêm tham số move_uci vào đây
    def __init__(self, coach, fen_before, fen_after, is_white_turn, move_uci):
        super().__init__()
        self.coach = coach
        self.fen_before = fen_before
        self.fen_after = fen_after
        self.is_white_turn = is_white_turn
        self.move_uci = move_uci # Lưu lại

    def run(self):
        try:
            # Truyền đủ 4 tham số cho Stockfish
            label, color = self.coach.analyze_move_quality(self.fen_before, self.fen_after, self.is_white_turn, self.move_uci)
            self.eval_done.emit(label, color)
        except Exception as e:
            print("Lỗi luồng AI Eval:", e) # In ra terminal để debug nếu lỗi
            self.eval_done.emit("Lỗi AI", "#555555")

# ==========================================
# CLASS: AIMoveWorker (Luồng tính toán nước đi của AI)
# ==========================================
class AIMoveWorker(QThread):
    move_calculated = Signal(str) # Tín hiệu phát ra chuỗi (VD: "e2e4")

    def __init__(self, coach, fen):
        super().__init__()
        self.coach = coach
        self.fen = fen

    def run(self):
        try:
            # Gọi hàm get_best_move từ file AI_Stockfish.py
            best_move = self.coach.get_best_move(self.fen)
            self.move_calculated.emit(best_move)
        except Exception as e:
            print(f"Lỗi AI Move: {e}")

# ==========================================
# CLASS: HistoryAnalysisWorker (Phân tích toàn bộ trận đấu)
# ==========================================
class HistoryAnalysisWorker(QThread):
    analysis_progress = Signal(int, str, str, str) # Index, Label, Color, CP

    def __init__(self, coach, moves_uci):
        super().__init__()
        self.coach = coach
        self.moves_uci = moves_uci
        self.is_running = True

    def run(self):
        try:
            from Code_Logic_Xuly import GameState, Move
            temp_game = GameState()
            
            for i, uci in enumerate(self.moves_uci):
                if not self.is_running: break
                
                # Dùng Regex để tìm các tọa độ ô cờ (vd: g1, f3) trong chuỗi
                coords = re.findall(r'[a-h][1-8]', uci.lower())
                if len(coords) < 2: continue
                
                # Trích xuất tọa độ từ kết quả Regex
                start_sq = coords[0]
                end_sq = coords[1]
                
                start_col = ord(start_sq[0]) - ord('a')
                start_row = 8 - int(start_sq[1])
                end_col = ord(end_sq[0]) - ord('a')
                end_row = 8 - int(end_sq[1])
                
                moves = temp_game.get_valid_moves()
                selected_move = None
                for m in moves:
                    if m.start_row == start_row and m.start_col == start_col and \
                       m.end_row == end_row and m.end_col == end_col:
                        selected_move = m
                        if len(uci) == 5:
                            selected_move.promotion_choice = uci[4].upper()
                        break
                
                if selected_move:
                    fen_before = temp_game.get_fen()
                    turn_before = temp_game.white_to_move
                    temp_game.make_move(selected_move)
                    fen_after = temp_game.get_fen()
                    
                    label, color, cp = self.coach.analyze_move_quality_with_cp(fen_before, fen_after, turn_before, uci)
                    self.analysis_progress.emit(i, label, color, cp)
                else:
                    break
        except Exception as e:
            print(f"Lỗi phân tích lịch sử: {e}")

    def stop(self):
        self.is_running = False

# ==========================================
# CLASS: MatchHistoryWidget (Màn hình Lịch sử đấu)
# ==========================================
class MatchHistoryWidget(QWidget):
    back_to_menu = Signal()

    def __init__(self, db, coach):
        super().__init__()
        self.db = db
        self.coach = coach
        self.analysis_thread = None
        self.init_ui()

    def init_ui(self):
        self.setObjectName("history_widget")
        bg_path = get_resource_path("Img_background4.jpg").replace("\\", "/")
        self.setStyleSheet(f"""
            #history_widget {{
                border-image: url("{bg_path}") 0 0 0 0 stretch stretch;
            }}
            QWidget {{ color: #00f3ff; }}
        """)
        layout = QHBoxLayout(self)
        
        # 1. Danh sách trận đấu (Bên trái)
        left_panel = QVBoxLayout()
        title = QLabel("LỊCH SỬ ĐẤU")
        title.setStyleSheet("font-size: 30px; font-weight: 800; color: #ff00ff; margin-bottom: 20px;")
        left_panel.addWidget(title)
        
        self.match_list = QListWidget()
        self.match_list.setStyleSheet("""
            QListWidget { background-color: #1a1b26; border: 1px solid #00f3ff; font-size: 14px; }
            QListWidget::item { padding: 15px; border-bottom: 1px solid #333; }
            QListWidget::item:selected { background-color: #00f3ff; color: #000; }
        """)
        self.match_list.itemClicked.connect(self.load_match_details)
        left_panel.addWidget(self.match_list)
        
        btn_back = QPushButton("QUAY LẠI MENU")
        btn_back.setStyleSheet("""
            QPushButton { font-size: 18px; font-weight: bold; padding: 10px; color: #fff; background: #c0392b; }
            QPushButton:hover { background: #e74c3c; }
        """)
        btn_back.clicked.connect(self.stop_and_back)
        left_panel.addWidget(btn_back)
        
        layout.addLayout(left_panel, stretch=1)
        
        # 2. Chi tiết ván đấu (Bên phải)
        right_panel = QVBoxLayout()
        detail_title = QLabel("CHI TIẾT NƯỚC ĐI & PHÂN TÍCH AI")
        detail_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #f8ff00;")
        right_panel.addWidget(detail_title)
        
        self.move_table = QTableWidget(0, 4)
        self.move_table.setHorizontalHeaderLabels(["Nước đi", "Đánh giá", "Điểm (CP)", "Chất lượng"])
        self.move_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.move_table.setStyleSheet("""
            QTableWidget { background-color: #050505; color: #fff; border: 1px solid #555; }
            QHeaderView::section { background-color: #222; color: #00f3ff; padding: 5px; }
        """)
        right_panel.addWidget(self.move_table)
        
        layout.addLayout(right_panel, stretch=2)
        
        self.refresh_matches()

    def refresh_matches(self):
        self.match_list.clear()
        matches = self.db.get_all_matches()
        for m in matches:
            display_text = f"ID: {m[0]} | {m[6]}\n{m[1]} vs {m[2]} | {m[3]} ({m[4]} nước)"
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, m[5]) # Store moves_list
            self.match_list.addItem(item)

    def load_match_details(self, item):
        moves_str = item.data(Qt.UserRole)
        moves_uci = [m.strip() for m in moves_str.split(",")] if moves_str else []
        
        self.move_table.setRowCount(0)
        for i, uci in enumerate(moves_uci):
            row = self.move_table.rowCount()
            self.move_table.insertRow(row)
            self.move_table.setItem(row, 0, QTableWidgetItem(f"{i//2 + 1}. {'Trắng' if i%2==0 else 'Đen'}: {uci}"))
            self.move_table.setItem(row, 1, QTableWidgetItem("Đang tính..."))
        
        if self.analysis_thread and self.analysis_thread.isRunning():
            self.analysis_thread.stop()
            self.analysis_thread.wait()
            
        self.analysis_thread = HistoryAnalysisWorker(self.coach, moves_uci)
        self.analysis_thread.analysis_progress.connect(self.update_move_analysis)
        self.analysis_thread.start()

    def update_move_analysis(self, index, label, color, cp):
        if index < self.move_table.rowCount():
            label_item = QTableWidgetItem(label)
            label_item.setForeground(QColor(color))
            label_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.move_table.setItem(index, 3, label_item)
            
            cp_item = QTableWidgetItem(cp)
            self.move_table.setItem(index, 2, cp_item)
            
            # Simple text evaluation based on CP for column 1
            self.move_table.setItem(index, 1, QTableWidgetItem("Phân tích xong"))

    def stop_and_back(self):
        if self.analysis_thread and self.analysis_thread.isRunning():
            self.analysis_thread.stop()
            self.analysis_thread.wait()
        self.back_to_menu.emit()

# ==========================================
# CLASS: SquareContainer
# Mục đích: Đảm bảo nội dung bên trong (Bàn cờ) luôn là hình vuông
# ==========================================
class SquareContainer(QWidget):
    def __init__(self, content_widget):
        super().__init__()
        self.content_widget = content_widget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(content_widget)

    def resizeEvent(self, event):
        # Lấy kích thước hiện tại của container
        size = self.size()
        side = min(size.width(), size.height())
        # Ép widget bên trong thành hình vuông
        self.content_widget.setFixedSize(side, side)
        super().resizeEvent(event)
        
# ==========================================
# CLASS 2: ChessMainWindow (Cửa sổ chính của ứng dụng)
# Mục đích: Chứa bàn cờ, thanh thông tin bên phải, quản lý layout tổng thể.
# ==========================================
class ChessMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TactiChess")
        icon_path = get_resource_path("Img_logo3.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.resize(1000, 800)
        self.setMinimumSize(850, 650)
        
        # --- THÊM MỚI: Trạng thái Game Mode ---
        self.player_one = True  # Trắng (True = Người, False = Máy)
        self.player_two = False # Đen 

        # Khởi tạo dữ liệu Logic
        self.game_state = GameState() 
        self.valid_moves = self.game_state.get_valid_moves()
        self.move_made = False 
        self.sq_selected = () 
        self.player_clicks = [] 
        self.ui_board = [[None for _ in range(8)] for _ in range(8)]
        self.last_move_squares = [] # Lưu 2 ô của nước đi cuối cùng để highlight
        
        # (Trong hàm __init__)
        # XÓA dòng cũ: self.ai_coach = StockfishCoach("stockfish")
        # THÊM 2 dòng mới:
        self.ai_coach_eval = StockfishCoach("Engine_stockfish.exe") # Chuyên chấm điểm
        self.ai_coach_play = StockfishCoach("Engine_stockfish.exe") # Chuyên tự đánh cờ
        self.db = ChessDatabase()
        self.ai_thread = None

        # ==========================================
        # QUẢN LÝ MÀN HÌNH BẰNG QStackedWidget
        # ==========================================
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # 1. Gọi hàm tạo Màn hình Menu (Lá bài 1)
        self.init_menu_ui()
        
        # 2. Gọi hàm tạo Màn hình Game (Lá bài 2) - Lưu ý: Đổi tên init_ui cũ thành init_game_ui
        self.init_game_ui() 
        
        # 3. MÀN HÌNH LỊCH SỬ ĐẤU
        self.history_widget = MatchHistoryWidget(self.db, self.ai_coach_eval)
        self.history_widget.back_to_menu.connect(self.return_to_menu)
        self.stacked_widget.addWidget(self.history_widget)
        
        # Hiển thị lá bài đầu tiên là Menu
        self.stacked_widget.setCurrentWidget(self.menu_widget)
        self.setup_starting_pieces()

    # ==========================================
    # MÀN HÌNH 1: MENU CHÍNH (START SCREEN)
    # ==========================================
    def init_menu_ui(self):
        self.menu_widget = QWidget()
        self.menu_widget.setObjectName("menu_widget")
        # NỀN ẢNH BACKGROUND CYBERPUNK
        bg_path = get_resource_path("Img_background4.jpg").replace("\\", "/")
        self.menu_widget.setStyleSheet(f"""
            #menu_widget {{
                border-image: url("{bg_path}") 0 0 0 0 stretch stretch;
            }}
            QLabel {{ background: transparent; border: none; }}
        """)
        layout = QVBoxLayout(self.menu_widget)
        layout.setAlignment(Qt.AlignCenter)

        # Tên Game Neon (Đóng khung đen để nổi bật)
        title = QLabel("TactiChess")
        title.setStyleSheet("""
            font-size: 110px; font-weight: 900; 
            color: #00f3ff; 
            font-family: 'Segoe UI Black', Arial;
            background-color: rgba(0, 0, 0, 0.85);
            padding: 0px 50px;
            border-radius: 20px;
            border: 3px solid #00f3ff;
        """)
        title.setAlignment(Qt.AlignCenter)
        
        # Bóng đổ đen cho toàn bộ khung chữ
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor("black"))
        shadow.setOffset(5, 5)
        title.setGraphicsEffect(shadow)

        # Chữ ký tác giả (thêm nền đen mờ để dễ đọc)
        author = QLabel("CREATED BY NGUYEN QUANG MINH - B24DCVN069")
        author.setStyleSheet("""
            font-size: 18px; font-weight: bold; color: #ff00ff; 
            background-color: rgba(0, 0, 0, 0.75);
            padding: 5px 15px; border-radius: 5px;
            letter-spacing: 5px; margin-bottom: 50px;
        """)
        author.setAlignment(Qt.AlignCenter)

        # Style chung cho nút bấm Cyberpunk (nền đen mờ 75%)
        btn_style = """
            QPushButton {
                font-size: 22px; font-weight: bold; color: #00f3ff;
                background-color: rgba(0, 0, 0, 0.75); 
                border: 2px solid #00f3ff;
                border-radius: 5px; 
                padding: 15px;
                min-width: 320px;
            }
            QPushButton:hover { 
                background-color: #00f3ff; 
                color: #000;
                border: 2px solid #fff;
            }
            QPushButton:pressed { background-color: #008888; }
        """

        btn_pvp = QPushButton("CHƠI 2 NGƯỜI - PVP")
        btn_pvp.setStyleSheet(btn_style)
        btn_pvp.setCursor(Qt.PointingHandCursor)
        btn_pvp.clicked.connect(self.start_pvp_game) 

        btn_pve = QPushButton("CHƠI VỚI MÁY - PVE")
        btn_pve.setStyleSheet(btn_style.replace("#00f3ff", "#ff00ff"))
        btn_pve.setCursor(Qt.PointingHandCursor)
        btn_pve.clicked.connect(self.start_pve_game)

        btn_history = QPushButton("LỊCH SỬ ĐẤU")
        btn_history.setStyleSheet(btn_style.replace("#00f3ff", "#f8ff00"))
        btn_history.setCursor(Qt.PointingHandCursor)
        btn_history.clicked.connect(self.show_history_screen)

        # Xếp các thành phần vào Layout
        layout.addStretch()

        # [NEW] LOGO TRÊN CÙNG MENU
        menu_logo_top = QLabel()
        menu_pix_top = QPixmap(get_resource_path("Img_logo3.ico"))
        if not menu_pix_top.isNull():
            menu_logo_top.setPixmap(menu_pix_top.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        menu_logo_top.setAlignment(Qt.AlignCenter)
        layout.addWidget(menu_logo_top)
        layout.addSpacing(20)

        layout.addWidget(title)
        layout.addWidget(author)
        layout.addSpacing(30)
        layout.addWidget(btn_pvp, alignment=Qt.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(btn_pve, alignment=Qt.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(btn_history, alignment=Qt.AlignCenter)
        
        # [NEW] LOGO DƯỚI CÙNG MENU
        layout.addSpacing(30)
        menu_logo_bottom = QLabel()
        menu_pix_bottom = QPixmap(get_resource_path("Img_logo3.ico"))
        if not menu_pix_bottom.isNull():
            menu_logo_bottom.setPixmap(menu_pix_bottom.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        menu_logo_bottom.setAlignment(Qt.AlignCenter)
        layout.addWidget(menu_logo_bottom)

        layout.addStretch()

        self.stacked_widget.addWidget(self.menu_widget)

    # ==========================================
    # CÁC HÀM XỬ LÝ CHUYỂN MÀN HÌNH VÀ RESET GAME
    # ==========================================
    def start_pvp_game(self):
        self.player_one = True
        self.player_two = True
        self.reset_game()
        self.stacked_widget.setCurrentWidget(self.game_widget) # Đổi sang màn hình Game

    def start_pve_game(self):
        self.player_one = True
        self.player_two = False
        self.reset_game()
        self.stacked_widget.setCurrentWidget(self.game_widget)
        # Gọi AI luôn phòng trường hợp bạn đổi ý cho AI cầm cờ Trắng đi trước
        self.check_and_trigger_ai()

    def return_to_menu(self):
        self.stacked_widget.setCurrentWidget(self.menu_widget) # Đổi về màn hình Menu

    def show_history_screen(self):
        self.history_widget.refresh_matches()
        self.stacked_widget.setCurrentWidget(self.history_widget)

    def save_game_to_db(self, manual_winner=None):
        """Lưu ván cờ hiện tại vào database"""
        if len(self.game_state.move_log) == 0:
            return
            
        # Chuẩn bị dữ liệu
        is_pve = (self.player_one and not self.player_two) or (not self.player_one and self.player_two)
        player_white = "Người chơi" if self.player_one else "Stockfish"
        player_black = "Người chơi" if self.player_two else "Stockfish"
        
        # Kết quả
        if manual_winner:
            winner = manual_winner
        elif self.game_state.checkmate:
            winner = "TRẮNG THẮNG" if not self.game_state.white_to_move else "ĐEN THẮNG"
        elif self.game_state.stalemate:
            winner = "HÒA CỜ"
        else:
            winner = "CHƯA KẾT THÚC"
            
        # Danh sách nước đi dạng UCI
        moves_uci = []
        for m in self.game_state.move_log:
            uci = m.get_rank_file(m.start_row, m.start_col) + m.get_rank_file(m.end_row, m.end_col)
            if m.is_pawn_promotion:
                uci += m.promotion_choice.lower()
            moves_uci.append(uci)
            
        moves_str = ", ".join(moves_uci)
        
        self.db.save_match(player_white, player_black, winner, len(moves_uci), moves_str)

    def handle_resign(self):
        from PySide6.QtWidgets import QMessageBox
        current_turn = "Trắng" if self.game_state.white_to_move else "Đen"
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("Xác nhận đầu hàng")
        msgBox.setText(f"Lượt của {current_turn}. Bạn có chắc chắn muốn đầu hàng không?")
        msgBox.setIcon(QMessageBox.Question)
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.No)
        
        # Style cho MessageBox giống Cyberpunk
        msgBox.setStyleSheet("QMessageBox { background-color: #0a0b10; color: #00f3ff; } QLabel { color: #00f3ff; font-size: 14px; } QPushButton { background-color: rgba(0, 0, 0, 0.75); color: #00f3ff; border: 1px solid #00f3ff; padding: 5px 15px; font-weight: bold; } QPushButton:hover { background-color: #00f3ff; color: #000; }")
        
        if msgBox.exec() == QMessageBox.Yes:
            winner = "ĐEN THẮNG" if self.game_state.white_to_move else "TRẮNG THẮNG"
            self.save_game_to_db(manual_winner=winner)
            self.reset_game()

    def handle_draw(self):
        from PySide6.QtWidgets import QMessageBox
        is_pve = (self.player_one and not self.player_two) or (not self.player_one and self.player_two)
        current_turn = "Trắng" if self.game_state.white_to_move else "Đen"
        other_turn = "Đen" if self.game_state.white_to_move else "Trắng"
        
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("Đề nghị cầu hòa")
        msgBox.setIcon(QMessageBox.Question)
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.No)
        
        # Style cho MessageBox giống Cyberpunk
        msgBox.setStyleSheet("QMessageBox { background-color: #0a0b10; color: #00f3ff; } QLabel { color: #00f3ff; font-size: 14px; } QPushButton { background-color: rgba(0, 0, 0, 0.75); color: #00f3ff; border: 1px solid #00f3ff; padding: 5px 15px; font-weight: bold; } QPushButton:hover { background-color: #00f3ff; color: #000; }")
        
        if is_pve:
             msgBox.setText("Bạn có chắc muốn kết thúc ván cờ với kết quả Hòa không?")
        else:
             msgBox.setText(f"Bên {current_turn} đề nghị hòa cờ.\nBên {other_turn} có đồng ý không?")
             
        if msgBox.exec() == QMessageBox.Yes:
            self.save_game_to_db(manual_winner="HÒA CỜ")
            self.reset_game()

    def reset_game(self):
        """Khởi tạo lại toàn bộ bàn cờ về trạng thái ban đầu"""
        self.game_state = GameState()
        self.valid_moves = self.game_state.get_valid_moves()
        self.sq_selected = ()
        self.player_clicks = []
        self.move_made = False
        self.last_move_squares = []
        
        # Xóa lịch sử và thông báo trên UI
        if hasattr(self, 'move_history_list'):
            self.move_history_list.clear()
        if hasattr(self, 'ai_score_label'):
            self.ai_score_label.setText("AI EVAL: WAITING...")
            self.ai_score_label.setStyleSheet("font-size: 13px; color: #7f8c8d; padding: 10px;")
            
        self.update_game_status()
        self.setup_starting_pieces()
        self.clear_highlights()
        self.fen_history = [self.game_state.get_fen()]

    def init_game_ui(self):
        """Layout Game Cyberpunk"""
        self.game_widget = QWidget()
        self.game_widget.setObjectName("game_widget")
        bg_path = get_resource_path("Img_background4.jpg").replace("\\", "/")
        self.game_widget.setStyleSheet(f"""
            #game_widget {{
                border-image: url("{bg_path}") 0 0 0 0 stretch stretch;
            }}
        """)
        
        main_layout = QHBoxLayout(self.game_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # --- BÀN CỜ (Bọc trong SquareContainer) ---
        self.board_inner = QWidget()
        self.board_layout = QGridLayout(self.board_inner)
        self.board_layout.setSpacing(0)
        self.board_layout.setContentsMargins(0, 0, 0, 0)
        
        self.draw_board_with_coordinates()
        
        for i in range(8):
            self.board_layout.setColumnStretch(i + 1, 1)
            self.board_layout.setRowStretch(i, 1)
            
        # SỬ DỤNG SQUARE_CONTAINER Ở ĐÂY
        self.board_wrapper = SquareContainer(self.board_inner)
        main_layout.addWidget(self.board_wrapper, stretch=4) 
        
        # --- SIDE PANEL CYBERPUNK ---
        self.side_panel = QWidget()
        self.side_panel.setObjectName("side_panel")
        self.side_panel.setMinimumWidth(320)
        self.side_panel.setStyleSheet("""
            #side_panel { 
                background-color: rgba(20, 25, 40, 0.8); 
                border: 1px solid #00f3ff;
            }
            QLabel { color: #00f3ff; border: none; background: transparent; }
        """)
        self.side_layout = QVBoxLayout(self.side_panel)
        self.side_layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel("SYSTEM STATUS")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: 800; color: #ff00ff; margin-bottom: 20px;")
        self.side_layout.addWidget(title_label)
        
        self.game_status_label = QLabel("STATUS: ONLINE")
        self.game_status_label.setAlignment(Qt.AlignCenter)
        self.game_status_label.setStyleSheet("""
            font-size: 14px; font-weight: bold; color: #00f3ff; 
            border: 1px solid #00f3ff; padding: 8px;
        """)
        
        history_title = QLabel("[ TRUY XUẤT LỊCH SỬ ]")
        history_title.setStyleSheet("font-weight: bold; color: #f8ff00; margin-top: 10px;")
        self.side_layout.addWidget(history_title)

        self.move_history_list = QListWidget()
        self.move_history_list.setStyleSheet("""
            QListWidget {
                font-size: 14px; background-color: #050505; color: #00f3ff; 
                border: 1px solid #333;
            }
            QListWidget::item { border-bottom: 1px solid #222; padding: 5px; }
            QListWidget::item:selected { background-color: #00f3ff; color: #000; }
        """)
        self.side_layout.addWidget(self.move_history_list)
        self.move_history_list.itemClicked.connect(self.on_history_item_clicked)
        
        self.side_layout.addWidget(self.game_status_label)
        
        self.selected_info_label = QLabel("COORDINATES: NULL\nUNIT: NONE")
        self.selected_info_label.setAlignment(Qt.AlignCenter)
        self.selected_info_label.setStyleSheet("""
            font-size: 14px; color: #fff; background-color: #1a1a1a; 
            border-top: 2px solid #ff00ff; padding: 10px;
        """)
        self.side_layout.addWidget(self.selected_info_label)
        
        self.ai_score_label = QLabel("AI EVAL: WAITING...")
        self.ai_score_label.setAlignment(Qt.AlignCenter)
        self.ai_score_label.setStyleSheet("font-size: 13px; color: #7f8c8d; padding: 10px;")
        self.side_layout.addWidget(self.ai_score_label)
        
        # --- BỘ NÚT ĐIỀU KHIỂN ---
        ctrl_grid = QGridLayout()
        btn_style = """
            QPushButton { 
                font-size: 12px; font-weight: bold; padding: 8px; 
                background-color: transparent; border: 1px solid #555; color: #fff;
            }
            QPushButton:hover { border: 1px solid #00f3ff; color: #00f3ff; }
        """
        self.btn_undo = QPushButton("HOÀN TÁC")
        btn_resign = QPushButton("ĐẦU HÀNG")
        btn_draw = QPushButton("CẦU HÒA")
        btn_menu = QPushButton("MENU")

        for b in [self.btn_undo, btn_resign, btn_draw, btn_menu]: b.setStyleSheet(btn_style)
        self.btn_undo.setStyleSheet(btn_style.replace("#00f3ff", "#f8ff00")) # Nút Hoàn tác màu Vàng neon

        self.btn_undo.clicked.connect(self.undo_last_move)
        btn_resign.clicked.connect(self.handle_resign)
        btn_draw.clicked.connect(self.handle_draw)
        btn_menu.clicked.connect(self.return_to_menu)

        ctrl_grid.addWidget(self.btn_undo, 0, 0)
        ctrl_grid.addWidget(btn_resign, 0, 1)
        ctrl_grid.addWidget(btn_draw, 1, 0)
        ctrl_grid.addWidget(btn_menu, 1, 1)
        self.side_layout.addLayout(ctrl_grid)
        
        # LOGO GÓC DƯỚI side_panel
        bottom_logo = QLabel()
        bottom_pix = QPixmap(get_resource_path("Img_logo3.ico"))
        if not bottom_pix.isNull():
            bottom_logo.setPixmap(bottom_pix.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        bottom_logo.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        bottom_logo.setStyleSheet("border: none; background: transparent; margin-top: 10px;")
        self.side_layout.addWidget(bottom_logo)
        
        main_layout.addWidget(self.side_panel, stretch=1)
        self.stacked_widget.addWidget(self.game_widget)
    
    
    # ==========================================
    # HÀM 1: Vẽ 64 ô cờ và trục tọa độ (A-H, 1-8)
    # Tư duy DSA: Sử dụng vòng lặp lồng nhau (Nested Loops) để duyệt ma trận 2D
    # ==========================================
    def draw_board_with_coordinates(self):
        # 1. Vẽ trục số
        for row in range(8):
            rank = str(8 - row)
            rank_label = QLabel(rank)
            rank_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            rank_label.setStyleSheet("font-weight: bold; font-size: 14px; padding-right: 5px; color: #00f3ff;")
            self.board_layout.addWidget(rank_label, row, 0)

        # 2. Vẽ 64 ô cờ CYBERPUNK
        # Màu ô tối: Đen huyền bí, Ô sáng: Xám xanh công nghệ
        colors = ["#4c566a", "#2e3440"] 
        for row in range(8):
            for col in range(8):
                color_index = (row + col) % 2 
                bg_color = colors[color_index]

                square = ChessSquare(row, col, bg_color)
                square.square_clicked.connect(self.on_square_clicked)
                self.ui_board[row][col] = square
                self.board_layout.addWidget(square, row, col + 1)

        # 3. Vẽ trục chữ
        for col in range(8):
            file_char = chr(col + 65)
            file_label = QLabel(file_char)
            file_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
            file_label.setStyleSheet("font-weight: bold; font-size: 14px; padding-top: 5px; color: #00f3ff;")
            self.board_layout.addWidget(file_label, 8, col + 1)

    # ==========================================
    # HÀM 2: Khởi tạo vị trí 32 quân cờ ban đầu
    # ==========================================
    def setup_starting_pieces(self):
        """Giờ đây GUI không tự hardcode mảng nữa, mà đọc trực tiếp từ GameState"""
        for row in range(8):
            for col in range(8):
                piece = self.game_state.board[row][col]
                # Nếu là ô trống "--" thì truyền None để clear ảnh, ngược lại truyền tên quân (vd: "wP")
                if piece == "--":
                    self.ui_board[row][col].set_piece(None)
                else:
                    self.ui_board[row][col].set_piece(piece)

    # ==========================================
    # HÀM 3: Phiên dịch Tọa độ (Mapping)
    # ==========================================
    def get_chess_notation(self, row, col):
        """Dịch từ index mảng (0, 0) sang tọa độ chuẩn (A8)"""
        file_char = chr(col + 65)  # A, B, C...
        rank_char = str(8 - row)   # 8, 7, 6...
        return f"{file_char}{rank_char}"

    # ==========================================
    # HÀM 4: Xử lý sự kiện khi click vào một ô cờ
    # ==========================================
    def on_square_clicked(self, row, col):
        # 1. Kiểm tra xem có phải lượt của con người không?
        is_human_turn = (self.game_state.white_to_move and self.player_one) or \
                        (not self.game_state.white_to_move and self.player_two)
        
        # Nếu đang là lượt của máy, bỏ qua mọi cú click chuột (tránh lỗi tẩu hỏa nhập ma)
        if not is_human_turn:
            return
        """Xử lý logic khi click chuột: Click 1 lần để chọn, click lần 2 để đi"""
        # Nếu người chơi click lại vào chính ô vừa chọn -> Hủy chọn (Deselect)
        if self.sq_selected == (row, col):
            self.sq_selected = ()
            self.player_clicks = []
            self.selected_info_label.setText("Đã hủy chọn")
            self.clear_highlights()
        else:
            self.sq_selected = (row, col)
            self.player_clicks.append(self.sq_selected)
            self.ui_board[row][col].highlight("#f6f669")

            for move in self.valid_moves:
                if move.start_row == row and move.start_col == col:
                    self.ui_board[move.end_row][move.end_col].set_valid_move(True)

        # Khi người chơi đã click đủ 2 ô (Ô bắt đầu và Ô kết thúc)
        if len(self.player_clicks) == 2:
            start_sq = self.player_clicks[0]
            end_sq = self.player_clicks[1]
            
            # Tạo một đối tượng Move từ 2 cú click
            move = Move(start_sq, end_sq, self.game_state.board)
            
            # Kiểm tra xem nước đi này có nằm trong danh sách hợp lệ không
            if move in self.valid_moves:
                valid_move = self.valid_moves[self.valid_moves.index(move)]
                
                # --- 1. Lấy FEN TRƯỚC khi đi ---
                fen_before = self.game_state.get_fen()
                turn_before = self.game_state.white_to_move
                
                # --- XỬ LÝ PHONG CẤP BẰNG POPUP ---
                if valid_move.is_pawn_promotion:
                    items = ["Hậu (Queen)", "Xe (Rook)", "Tượng (Bishop)", "Mã (Knight)"]
                    item, ok = QInputDialog.getItem(self, "Phong cấp Tốt", "Chúc mừng! Tốt của bạn đã đi đến cuối bàn.\nHãy chọn quân bạn muốn phong cấp:", items, 0, False)
                    if ok and item:
                        if "Hậu" in item: valid_move.promotion_choice = "Q"
                        elif "Xe" in item: valid_move.promotion_choice = "R"
                        elif "Tượng" in item: valid_move.promotion_choice = "B"
                        elif "Mã" in item: valid_move.promotion_choice = "N"
                # Thực hiện nước đi trên Logic
                self.game_state.make_move(valid_move) 
                self.move_made = True
                self.fen_history.append(self.game_state.get_fen()) # Lưu lại FEN sau mỗi nước đi thành công vào lịch sử
                
                # --- 2. Lấy FEN SAU khi đi ---
                fen_after = self.game_state.get_fen()
                
                # --- DỊCH NƯỚC ĐI THÀNH CHUỖI UCI (VD: e2e4) ĐỂ TRA SÁCH ---
                move_uci = valid_move.get_rank_file(valid_move.start_row, valid_move.start_col) + \
                           valid_move.get_rank_file(valid_move.end_row, valid_move.end_col)
                if valid_move.is_pawn_promotion:
                    move_uci += valid_move.promotion_choice.lower()
                
                # --- 3. Gọi AI chạy ngầm chấm điểm ---
                self.ai_score_label.setText("Đang phân tích...")
                self.ai_score_label.setStyleSheet("font-size: 16px; margin-top: 20px; color: #7f8c8d; border: 1px dashed #bdc3c7; padding: 10px;")
                
                # Khởi tạo và chạy luồng phụ (Đã bổ sung truyền biến move_uci)
                if self.ai_thread and self.ai_thread.isRunning():
                    self.ai_thread.terminate()
                    self.ai_thread.wait()
                
                self.ai_thread = AIWorker(self.ai_coach_eval, fen_before, fen_after, turn_before, move_uci)
                self.ai_thread.eval_done.connect(self.update_ai_score_ui)
                self.ai_thread.start()
                
                # Cập nhật GUI (Đoạn này giữ nguyên)
                self.sq_selected = ()
                self.player_clicks = []
                self.clear_highlights()
                self.setup_starting_pieces() 
                self.selected_info_label.setText(f"Vừa đi: {valid_move.get_chess_notation()}")
            else:
                self.player_clicks = [self.sq_selected] # Giữ lại ô bắt đầu để người chơi chọn ô đích khác
                
                # Phân tích nguyên nhân 1: Vua hiện tại đang bị chiếu
                if self.game_state.in_check():
                    self.selected_info_label.setText("Lỗi: Vua đang bị chiếu! Phải cứu Vua.")
                
                # Phân tích nguyên nhân 2 & 3
                else:
                    # Gọi lại mảng nước đi thô (Pseudo-legal) để đối chiếu
                    pseudo_moves = self.game_state.get_all_possible_moves()
                    
                    # Nếu nước đi đúng hình học, nhưng lại không có trong valid_moves
                    # Nghĩa là nó đã bị bộ lọc Checkmate loại bỏ -> Nước đi tự sát (Làm lộ Vua)
                    if move in pseudo_moves:
                        self.selected_info_label.setText("Lỗi: Nước đi này làm lộ Vua!")
                    else:
                        # Thậm chí không có trong mảng hình học -> Đi sai luật
                        self.selected_info_label.setText("Lỗi: Quân cờ không thể đi thế này!")

        # Cập nhật danh sách nước đi mới nếu vừa có người đi thành công
        if self.move_made:
            self.valid_moves = self.game_state.get_valid_moves()
            self.move_made = False
            
            # ==========================================
            # THÊM MỚI: Cập nhật chữ lên App
            # ==========================================
            self.update_game_status()
            # ==========================================
            # THÊM MỚI: Xử lý ký hiệu Chiếu/Chiếu bí và in ra GUI
            # ==========================================
            # 1. Lấy chuỗi ký hiệu cơ bản (VD: e2 -> e4, h7 -> h8=Q)
            move_text = valid_move.get_chess_notation()
        
            # 2. Kiểm tra trạng thái ván cờ hiện tại để nối thêm ký hiệu đặc biệt
            if self.game_state.checkmate:
                move_text += "#"  # Chiếu bí
            elif self.game_state.in_check():
                move_text += "+"  # Chiếu tướng
            
            # 3. Tạo dòng text hoàn chỉnh (Có đánh số thứ tự lượt đi)
            move_number = (len(self.game_state.move_log) - 1) // 2 + 1
            turn_color = "Trắng" if not self.game_state.white_to_move else "Đen"
        
            final_display_text = f"{move_number}. {turn_color}: {move_text}"
        
            # 4. Đẩy vào QListWidget trên giao diện và tự động cuộn xuống đáy
            self.move_history_list.addItem(final_display_text)
            self.move_history_list.scrollToBottom()
            # Kích hoạt AI nếu đang ở chế độ chơi với máy
            self.check_and_trigger_ai()
            
            # HIGHLIGHT NƯỚC VỪA ĐI
            self.highlight_move_squares(valid_move.start_row, valid_move.start_col, valid_move.end_row, valid_move.end_col)


    def highlight_move_squares(self, r1, c1, r2, c2):
        """Xóa highlight cũ và vẽ highlight cho nước đi mới"""
        # Xóa các highlight cũ (chỉ reset màu, không xóa gợi ý nước đi nếu đang chọn quân)
        for r, c in self.last_move_squares:
            self.ui_board[r][c].reset_color()
        
        # Lưu tọa độ mới
        self.last_move_squares = [(r1, c1), (r2, c2)]
        
        # Vẽ highlight mới
        for r, c in self.last_move_squares:
            self.ui_board[r][c].highlight_last_move()

    def clear_highlights(self, reset_last_move=False):
        """Hàm phụ trợ để xóa bôi vàng trên toàn bàn cờ"""
        for r in range(8):
            for c in range(8):
                # Nếu reset_last_move=True, xóa luôn cả highlight nước đi vừa thực hiện
                # Nếu không, chỉ xóa các highlight chọn quân và gợi ý
                is_last_move = (r, c) in self.last_move_squares
                if not is_last_move or reset_last_move:
                    self.ui_board[r][c].reset_color()
                self.ui_board[r][c].set_valid_move(False)
        
        if reset_last_move:
            self.last_move_squares = []

    def update_game_status(self):
        """Hàm đồng bộ trạng thái từ Logic (Model) lên Giao diện (View)"""
        if self.game_state.checkmate:
            # Nếu đến lượt Trắng mà bị chiếu bí -> Đen thắng và ngược lại
            winner = "ĐEN" if self.game_state.white_to_move else "TRẮNG"
            self.game_status_label.setText(f"CHIẾU BÍ!\n{winner} THẮNG CỜ")
            self.game_status_label.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background-color: #e74c3c; padding: 10px; border-radius: 5px;")
            
        elif self.game_state.stalemate:
            self.game_status_label.setText("HÒA CỜ!\n(Stalemate)")
            self.game_status_label.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background-color: #f39c12; padding: 10px; border-radius: 5px;")
        
        # TỰ ĐỘNG LƯU KHI KẾT THÚC
        if self.game_state.checkmate or self.game_state.stalemate:
            self.save_game_to_db()
            
        elif self.game_state.in_check():
            self.game_status_label.setText("CẢNH BÁO:\nĐANG BỊ CHIẾU TƯỚNG!")
            self.game_status_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #e74c3c; background-color: #fce4e4; padding: 10px; border-radius: 5px;")
            
        else:
            self.game_status_label.setText("Trạng thái: Đang chơi")
            self.game_status_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60; background-color: #ecf0f1; padding: 10px; border-radius: 5px;")

    def update_ai_score_ui(self, label, color):
        self.ai_score_label.setText(f"Đánh giá AI: {label}")
        
        # Bê nguyên xi bộ style của bạn xuống đây, chỉ thay mỗi cái biến {color} và thêm in đậm!
        self.ai_score_label.setStyleSheet(
            f"font-size: 16px; margin-top: 20px; color: {color}; "
            f"border: 1px dashed #bdc3c7; padding: 10px; font-weight: bold;"
        )

    # ==========================================
    # LOGIC AI TỰ ĐỘNG CHƠI
    # ==========================================
    def check_and_trigger_ai(self):
        """Kiểm tra xem có phải lượt của AI không, nếu phải thì kích hoạt AI"""
        # Nếu ván cờ đã kết thúc thì dừng lại
        if self.game_state.checkmate or self.game_state.stalemate:
            return
            
        # Xác định xem lượt hiện tại là của Người hay Máy
        is_human_turn = (self.game_state.white_to_move and self.player_one) or \
                        (not self.game_state.white_to_move and self.player_two)
                        
        if not is_human_turn:
            # self.ai_score_label.setText("AI đang suy nghĩ...")
            # self.ai_score_label.setStyleSheet("font-size: 16px; margin-top: 20px; color: #d35400; font-weight: bold; padding: 10px;")
            
            # Lấy trạng thái bàn cờ gửi cho AI
            fen = self.game_state.get_fen()
            
            # Khởi tạo luồng để AI suy nghĩ ngầm
            if hasattr(self, 'ai_move_thread') and self.ai_move_thread and self.ai_move_thread.isRunning():
                self.ai_move_thread.terminate()
                self.ai_move_thread.wait()
                
            self.ai_move_thread = AIMoveWorker(self.ai_coach_play, fen)
            self.ai_move_thread.move_calculated.connect(self.execute_ai_move)
            self.ai_move_thread.start()

    def execute_ai_move(self, move_str):
        """
        DSA: Dịch chuỗi "e2e4" của AI thành tọa độ mảng 2D.
        Sử dụng phép toán trên mã ASCII (ord).
        """
        # 1. Dịch chuỗi thành index mảng
        # Chữ 'a' có mã ASCII là 97. 'e' là 101 -> 101 - 97 = 4 (Cột 4)
        start_col = ord(move_str[0]) - ord('a') 
        start_row = 8 - int(move_str[1])
        end_col = ord(move_str[2]) - ord('a')
        end_row = 8 - int(move_str[3])

        # 2. Tìm Object Move tương ứng trong danh sách nước đi hợp lệ
        ai_move = None
        for move in self.valid_moves:
            if move.start_row == start_row and move.start_col == start_col \
               and move.end_row == end_row and move.end_col == end_col:
                ai_move = move
                
                # Xử lý ngoại lệ: Nếu AI quyết định Phong Cấp (chuỗi dài 5 ký tự, VD: e7e8q)
                if len(move_str) == 5: 
                    ai_move.promotion_choice = move_str[4].upper()
                break

        # 3. Thực thi nước đi và cập nhật Giao diện
        if ai_move:
            self.game_state.make_move(ai_move)
            self.fen_history.append(self.game_state.get_fen())
            
            # Cập nhật valid_moves cho lượt tiếp theo
            self.valid_moves = self.game_state.get_valid_moves()
            self.setup_starting_pieces() 
            self.update_game_status()
            
            # Cập nhật lịch sử
            move_text = ai_move.get_chess_notation()
            if self.game_state.checkmate: move_text += "#"
            elif self.game_state.in_check(): move_text += "*"
            
            move_num = (len(self.game_state.move_log) - 1) // 2 + 1
            turn_color = "Trắng" if not self.game_state.white_to_move else "Đen"
            
            # Thêm chữ (AI) vào cuối để dễ phân biệt
            self.move_history_list.addItem(f"{move_num}. {turn_color}: {move_text} (AI)")
            self.move_history_list.scrollToBottom()
            
            self.selected_info_label.setText(f"AI vừa đi: {ai_move.get_chess_notation()}")
            
            # HIGHLIGHT NƯỚC AI VỪA ĐI
            self.highlight_move_squares(ai_move.start_row, ai_move.start_col, ai_move.end_row, ai_move.end_col)
            # self.ai_score_label.setText("Đến lượt bạn!")
            # self.ai_score_label.setStyleSheet("font-size: 16px; margin-top: 20px; color: #27ae60; padding: 10px;")

    def on_history_item_clicked(self, item):
        """Hàm xử lý khi người dùng click vào một nước đi trong danh sách để xem lại đánh giá"""
        # Lấy vị trí (index) của nước đi vừa click
        idx = self.move_history_list.row(item)
        
        # Kiểm tra an toàn để tránh lỗi Out of Index
        if hasattr(self, 'fen_history') and 0 <= idx < len(self.game_state.move_log):
            # Lấy FEN trước và sau của nước đi đó trong quá khứ
            fen_before = self.fen_history[idx]
            fen_after = self.fen_history[idx + 1]
            
            # Chẵn là lượt Trắng, Lẻ là lượt Đen
            turn_before = True if idx % 2 == 0 else False
            
            # Tái tạo chuỗi UCI (VD: e2e4) để tra sách Book Move
            move = self.game_state.move_log[idx]
            move_uci = move.get_rank_file(move.start_row, move.start_col) + \
                       move.get_rank_file(move.end_row, move.end_col)
            if move.is_pawn_promotion:
                move_uci += move.promotion_choice.lower()
                
            # Đổi text báo hiệu đang phân tích
            self.ai_score_label.setText(f"Đang phân tích nước thứ {idx + 1}...")
            self.ai_score_label.setStyleSheet("font-size: 16px; margin-top: 20px; color: #7f8c8d; border: 1px dashed #bdc3c7; padding: 10px;")
            
            # Gọi luồng AI Worker chấm điểm lại đúng nước đi đó!
            if self.ai_thread and self.ai_thread.isRunning():
                self.ai_thread.terminate()
                self.ai_thread.wait()
                
            self.ai_thread = AIWorker(self.ai_coach_eval, fen_before, fen_after, turn_before, move_uci)
            self.ai_thread.eval_done.connect(self.update_ai_score_ui)
            self.ai_thread.start()

    def undo_last_move(self):
        """Hàm xử lý hoàn tác nước đi và cập nhật lại toàn bộ giao diện"""
        # 1. Gọi logic hoàn tác từ GameState
        self.game_state.undo_move()
        
        # 2. Cập nhật lại các biến trạng thái trong GUI
        self.valid_moves = self.game_state.get_valid_moves()
        self.sq_selected = ()
        self.player_clicks = []
        self.move_made = False
        
        # 3. Xóa nước đi cuối cùng trong danh sách lịch sử hiển thị
        if self.move_history_list.count() > 0:
            self.move_history_list.takeItem(self.move_history_list.count() - 1)
            
        # 4. Xóa FEN cuối cùng trong lịch sử FEN
        if hasattr(self, 'fen_history') and len(self.fen_history) > 1:
            self.fen_history.pop()
            
        # 5. Làm mới bàn cờ và trạng thái
        self.setup_starting_pieces()
        self.clear_highlights()
        self.update_game_status()
        self.selected_info_label.setText("Đã hoàn tác nước đi")
        
        # Xóa highlight nước đi cũ vì nó không còn đúng nữa
        self.clear_highlights(reset_last_move=True)
        
        # Nếu là chế độ đánh với máy, kiểm tra xem lượt hiện tại sau khi hoàn tác 1 nước đã là của mình chưa
        is_pve = (self.player_one and not self.player_two) or (not self.player_one and self.player_two)
        if is_pve:
             is_human_turn = (self.game_state.white_to_move and self.player_one) or \
                             (not self.game_state.white_to_move and self.player_two)
             if not is_human_turn:
                 if len(self.game_state.move_log) > 0:
                     self.undo_last_move() # Đệ quy hoàn tác thêm nước nữa (nước của mình) để lấy lại lượt
                 else:
                     self.check_and_trigger_ai() # Kích hoạt lại AI nếu đã tua về trạng thái lúc mới vào game (AI đi trước)
# ==========================================
# KHỐI LỆNH CHẠY CHƯƠNG TRÌNH CHÍNH
# ==========================================
if __name__ == "__main__":
    # --- FIX HIỂN THỊ LOGO TRÊN THANH TASKBAR WINDOWS ---
    try:
        myappid = 'nguyenquangminh.tactichess.game.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    window = ChessMainWindow()
    window.show()
    sys.exit(app.exec())

# ==========================================