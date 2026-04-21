# ==========================================
# CLASS 1: Trạng thái Ván Cờ (GameState)
# Vai trò: Quản lý mảng 2 chiều đại diện cho bàn cờ, theo dõi lượt đi, và lưu trữ lịch sử nước đi.
# DSA áp dụng: 2D Array (Bàn cờ), Stack (Lịch sử undo) - các cấu trúc dữ liệu cơ bản để quản lý state trò chơi.
# ==========================================
class GameState:
    def __init__(self):
        # b_co: Bàn cờ (board)
        self.b_co = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"], 
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"], 
            ["--", "--", "--", "--", "--", "--", "--", "--"], 
            ["--", "--", "--", "--", "--", "--", "--", "--"], 
            ["--", "--", "--", "--", "--", "--", "--", "--"], 
            ["--", "--", "--", "--", "--", "--", "--", "--"], 
            ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"], 
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]  
        ]
        
        # l_trang: Lượt trắng (white_to_move)
        self.l_trang = True 
        
        # ls_di: Lịch sử đi (move_log)
        self.ls_di = [] 

        # vt_v_t, vt_v_d: Vị trí vua trắng/đen
        self.vt_v_t = (7, 4) 
        self.vt_v_d = (0, 4) 
        
        # c_bi, h_co: Chiếu bí, hòa cờ
        self.c_bi = False 
        self.h_co = False 

        # o_ep: Ô en passant, ls_ep: Lịch sử en passant
        self.o_ep = () 
        self.ls_ep = [self.o_ep] 
        
        # q_nt: Quyền nhập thành, ls_q_nt: Lịch sử quyền nhập thành
        self.q_nt = {'wks': True, 'wqs': True, 'bks': True, 'bqs': True}
        self.ls_q_nt = [dict(self.q_nt)]

    # ==========================================
    # CÁC PROPERTY (GETTER/SETTER) GIAO TIẾP VỚI CA MÔ-ĐUN BÊN NGOÀI
    # Giữ nguyên tương thích với code cũ chạy giao diện mà không bị lỗi
    # ==========================================
    @property
    def board(self): return self.b_co
    @board.setter
    def board(self, val): self.b_co = val

    @property
    def white_to_move(self): return self.l_trang
    @white_to_move.setter
    def white_to_move(self, val): self.l_trang = val

    @property
    def move_log(self): return self.ls_di
    
    @property
    def checkmate(self): return self.c_bi
    @checkmate.setter
    def checkmate(self, val): self.c_bi = val

    @property
    def stalemate(self): return self.h_co
    @stalemate.setter
    def stalemate(self, val): self.h_co = val

    def make_move(self, nuoc_di): 
        # Bỏ quân cờ ở ô cũ
        self.b_co[nuoc_di.h_dau][nuoc_di.c_dau] = "--"
        # Đặt quân ở ô mới
        self.b_co[nuoc_di.h_cuoi][nuoc_di.c_cuoi] = nuoc_di.q_di
        # Lưu lịch sử
        self.ls_di.append(nuoc_di)
        # Đổi lượt
        self.l_trang = not self.l_trang

        # Cập nhật vị trí Vua
        if nuoc_di.q_di == "wK":
            self.vt_v_t = (nuoc_di.h_cuoi, nuoc_di.c_cuoi)
        elif nuoc_di.q_di == "bK":
            self.vt_v_d = (nuoc_di.h_cuoi, nuoc_di.c_cuoi)

        # Xử lý phong cấp (Pawn Promotion)
        if nuoc_di.la_pc:
            self.b_co[nuoc_di.h_cuoi][nuoc_di.c_cuoi] = nuoc_di.q_di[0] + nuoc_di.chon_pc

        # Xử lý ăn qua đường (En Passant)
        if nuoc_di.la_ep:
            self.b_co[nuoc_di.h_dau][nuoc_di.c_cuoi] = "--"
            
        if nuoc_di.q_di[1] == 'P' and abs(nuoc_di.h_dau - nuoc_di.h_cuoi) == 2:
            self.o_ep = ((nuoc_di.h_dau + nuoc_di.h_cuoi) // 2, nuoc_di.c_dau)
        else:
            self.o_ep = ()
            
        self.ls_ep.append(self.o_ep)
        
        # Xử lý nhập thành (Castling)
        if nuoc_di.la_nt:
            if nuoc_di.c_cuoi - nuoc_di.c_dau == 2: # Nhập thành gần
                self.b_co[nuoc_di.h_cuoi][nuoc_di.c_cuoi - 1] = self.b_co[nuoc_di.h_cuoi][nuoc_di.c_cuoi + 1] 
                self.b_co[nuoc_di.h_cuoi][nuoc_di.c_cuoi + 1] = "--" 
            else: # Nhập thành xa
                self.b_co[nuoc_di.h_cuoi][nuoc_di.c_cuoi + 1] = self.b_co[nuoc_di.h_cuoi][nuoc_di.c_cuoi - 2]
                self.b_co[nuoc_di.h_cuoi][nuoc_di.c_cuoi - 2] = "--"
                
        self.update_castle_rights(nuoc_di)
        self.ls_q_nt.append(dict(self.q_nt))

    def update_castle_rights(self, nuoc_di):
        if nuoc_di.q_di == 'wK':
            self.q_nt['wks'] = self.q_nt['wqs'] = False 
        elif nuoc_di.q_di == 'bK':
            self.q_nt['bks'] = self.q_nt['bqs'] = False
        elif nuoc_di.q_di == 'wR':
            if nuoc_di.h_dau == 7: 
                if nuoc_di.c_dau == 0: self.q_nt['wqs'] = False 
                elif nuoc_di.c_dau == 7: self.q_nt['wks'] = False 
        elif nuoc_di.q_di == 'bR':
            if nuoc_di.h_dau == 0: 
                if nuoc_di.c_dau == 0: self.q_nt['bqs'] = False 
                elif nuoc_di.c_dau == 7: self.q_nt['bks'] = False 

    def undo_move(self):
        if len(self.ls_di) != 0: 
            nuoc_di = self.ls_di.pop()
            
            self.b_co[nuoc_di.h_dau][nuoc_di.c_dau] = nuoc_di.q_di
            self.b_co[nuoc_di.h_cuoi][nuoc_di.c_cuoi] = nuoc_di.q_an
            self.l_trang = not self.l_trang

            if nuoc_di.q_di == "wK":
                self.vt_v_t = (nuoc_di.h_dau, nuoc_di.c_dau)
            elif nuoc_di.q_di == "bK":
                self.vt_v_d = (nuoc_di.h_dau, nuoc_di.c_dau)
                
            if nuoc_di.la_ep:
                self.b_co[nuoc_di.h_cuoi][nuoc_di.c_cuoi] = "--" 
                self.b_co[nuoc_di.h_dau][nuoc_di.c_cuoi] = nuoc_di.q_an 
                
            self.ls_ep.pop()
            self.o_ep = self.ls_ep[-1]
            
            self.ls_q_nt.pop()
            self.q_nt = dict(self.ls_q_nt[-1])
            
            if nuoc_di.la_nt:
                if nuoc_di.c_cuoi - nuoc_di.c_dau == 2: 
                    self.b_co[nuoc_di.h_cuoi][nuoc_di.c_cuoi + 1] = self.b_co[nuoc_di.h_cuoi][nuoc_di.c_cuoi - 1]
                    self.b_co[nuoc_di.h_cuoi][nuoc_di.c_cuoi - 1] = "--"
                else: 
                    self.b_co[nuoc_di.h_cuoi][nuoc_di.c_cuoi - 2] = self.b_co[nuoc_di.h_cuoi][nuoc_di.c_cuoi + 1]
                    self.b_co[nuoc_di.h_cuoi][nuoc_di.c_cuoi + 1] = "--"

    def get_valid_moves(self):
        ds_n = self.get_all_possible_moves()
        
        if self.l_trang:
            self.get_castle_moves(self.vt_v_t[0], self.vt_v_t[1], ds_n)
        else:
            self.get_castle_moves(self.vt_v_d[0], self.vt_v_d[1], ds_n)
            
        for i in range(len(ds_n) - 1, -1, -1):
            self.make_move(ds_n[i])
            self.l_trang = not self.l_trang
            if self.in_check():
                ds_n.remove(ds_n[i])
            self.l_trang = not self.l_trang
            self.undo_move()
            
        if len(ds_n) == 0:
            if self.in_check():
                self.c_bi = True
                print("CHIẾU BÍ!")
            else:
                self.h_co = True
                print("HÒA CỜ!")
        else:
            self.c_bi = False
            self.h_co = False
            
        return ds_n

    def in_check(self):
        if self.l_trang:
            return self.square_under_attack(self.vt_v_t[0], self.vt_v_t[1])
        else:
            return self.square_under_attack(self.vt_v_d[0], self.vt_v_d[1])

    def square_under_attack(self, h, c):
        self.l_trang = not self.l_trang
        ds_n_dich = self.get_all_possible_moves()
        self.l_trang = not self.l_trang
        
        for n in ds_n_dich:
            if n.h_cuoi == h and n.c_cuoi == c:
                return True 
        return False
    
    def get_fen(self):
        chuoi_fen = ""
        for h in range(8):
            o_trong = 0
            for c in range(8):
                quan = self.b_co[h][c]
                if quan == "--":
                    o_trong += 1
                else:
                    if o_trong > 0:
                        chuoi_fen += str(o_trong)
                        o_trong = 0
                    ky_tu = quan[1]
                    if quan[0] == 'b':
                        ky_tu = ky_tu.lower()
                    chuoi_fen += ky_tu
                    
            if o_trong > 0:
                chuoi_fen += str(o_trong)
            if h < 7:
                chuoi_fen += "/" 
                
        luot = "w" if self.l_trang else "b"
        chuoi_fen += f" {luot} "
        
        qnt_str = ""
        if self.q_nt['wks']: qnt_str += "K"
        if self.q_nt['wqs']: qnt_str += "Q"
        if self.q_nt['bks']: qnt_str += "k"
        if self.q_nt['bqs']: qnt_str += "q"
        if qnt_str == "": qnt_str = "-" 
        chuoi_fen += f"{qnt_str} "

        if self.o_ep != ():
            c_ep = chr(self.o_ep[1] + 97) 
            h_ep = str(8 - self.o_ep[0]) 
            chuoi_fen += f"{c_ep}{h_ep}"
        else:
            chuoi_fen += "-"
            
        chuoi_fen += " 0 1" 
        return chuoi_fen

    def get_all_possible_moves(self):
        ds_n = [] 
        for h in range(len(self.b_co)):       
            for c in range(len(self.b_co[h])):    
                mau_q = self.b_co[h][c][0]  
                if (mau_q == 'w' and self.l_trang) or (mau_q == 'b' and not self.l_trang):
                    quan = self.b_co[h][c][1] 
                    if quan == 'P': self.get_pawn_moves(h, c, ds_n)
                    elif quan == 'N': self.get_knight_moves(h, c, ds_n)
                    elif quan == 'R': self.get_rook_moves(h, c, ds_n)
                    elif quan == 'B': self.get_bishop_moves(h, c, ds_n)
                    elif quan == 'Q': self.get_queen_moves(h, c, ds_n)
                    elif quan == 'K': self.get_king_moves(h, c, ds_n)
        return ds_n

    def get_pawn_moves(self, h, c, ds_n):
        if self.l_trang: 
            if self.b_co[h - 1][c] == "--": 
                ds_n.append(Move((h, c), (h - 1, c), self.b_co))
                if h == 6 and self.b_co[h - 2][c] == "--":
                    ds_n.append(Move((h, c), (h - 2, c), self.b_co))
            if c - 1 >= 0: 
                if self.b_co[h - 1][c - 1][0] == 'b': 
                    ds_n.append(Move((h, c), (h - 1, c - 1), self.b_co))
                elif (h - 1, c - 1) == self.o_ep:
                    n = Move((h, c), (h - 1, c - 1), self.b_co)
                    n.la_ep = True
                    ds_n.append(n)
            if c + 1 <= 7: 
                if self.b_co[h - 1][c + 1][0] == 'b': 
                    ds_n.append(Move((h, c), (h - 1, c + 1), self.b_co))
                elif (h - 1, c + 1) == self.o_ep:
                    n = Move((h, c), (h - 1, c + 1), self.b_co)
                    n.la_ep = True
                    ds_n.append(n)
        else: 
            if self.b_co[h + 1][c] == "--":
                ds_n.append(Move((h, c), (h + 1, c), self.b_co))
                if h == 1 and self.b_co[h + 2][c] == "--": 
                    ds_n.append(Move((h, c), (h + 2, c), self.b_co))
            if c - 1 >= 0:
                if self.b_co[h + 1][c - 1][0] == 'w':
                    ds_n.append(Move((h, c), (h + 1, c - 1), self.b_co))
                elif (h + 1, c - 1) == self.o_ep:
                    n = Move((h, c), (h + 1, c - 1), self.b_co)
                    n.la_ep = True
                    ds_n.append(n)
            if c + 1 <= 7:
                if self.b_co[h + 1][c + 1][0] == 'w':
                    ds_n.append(Move((h, c), (h + 1, c + 1), self.b_co))
                elif (h + 1, c + 1) == self.o_ep:
                    n = Move((h, c), (h + 1, c + 1), self.b_co)
                    n.la_ep = True
                    ds_n.append(n)

    def get_knight_moves(self, h, c, ds_n):
        v_ma = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        mau_ta = "w" if self.l_trang else "b"
        for m in v_ma:
            h_cuoi = h + m[0]
            c_cuoi = c + m[1]
            if 0 <= h_cuoi < 8 and 0 <= c_cuoi < 8:
                q_cuoi = self.b_co[h_cuoi][c_cuoi]
                if q_cuoi[0] != mau_ta: 
                    ds_n.append(Move((h, c), (h_cuoi, c_cuoi), self.b_co))

    def get_castle_moves(self, h, c, ds_n):
        if self.square_under_attack(h, c):
            return 
        if (self.l_trang and self.q_nt['wks']) or (not self.l_trang and self.q_nt['bks']):
            self.get_kingside_castle_moves(h, c, ds_n)
        if (self.l_trang and self.q_nt['wqs']) or (not self.l_trang and self.q_nt['bqs']):
            self.get_queenside_castle_moves(h, c, ds_n)

    def get_kingside_castle_moves(self, h, c, ds_n):
        if self.b_co[h][c + 1] == '--' and self.b_co[h][c + 2] == '--':
            if not self.square_under_attack(h, c + 1) and not self.square_under_attack(h, c + 2):
                n = Move((h, c), (h, c + 2), self.b_co)
                n.la_nt = True 
                ds_n.append(n)

    def get_queenside_castle_moves(self, h, c, ds_n):
        if self.b_co[h][c - 1] == '--' and self.b_co[h][c - 2] == '--' and self.b_co[h][c - 3] == '--':
            if not self.square_under_attack(h, c - 1) and not self.square_under_attack(h, c - 2):
                n = Move((h, c), (h, c - 2), self.b_co)
                n.la_nt = True
                ds_n.append(n)

    def get_king_moves(self, h, c, ds_n):
        v_vua = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
        mau_ta = "w" if self.l_trang else "b"
        for i in range(8):
            h_cuoi = h + v_vua[i][0]
            c_cuoi = c + v_vua[i][1]
            if 0 <= h_cuoi < 8 and 0 <= c_cuoi < 8:
                q_cuoi = self.b_co[h_cuoi][c_cuoi]
                if q_cuoi[0] != mau_ta:
                    ds_n.append(Move((h, c), (h_cuoi, c_cuoi), self.b_co))

    def get_rook_moves(self, h, c, ds_n):
        huong = ((-1, 0), (1, 0), (0, -1), (0, 1)) 
        mau_dich = "b" if self.l_trang else "w"
        for d in huong:
            for i in range(1, 8): 
                h_cuoi = h + d[0] * i
                c_cuoi = c + d[1] * i
                if 0 <= h_cuoi < 8 and 0 <= c_cuoi < 8:
                    q_cuoi = self.b_co[h_cuoi][c_cuoi]
                    if q_cuoi == "--": 
                        ds_n.append(Move((h, c), (h_cuoi, c_cuoi), self.b_co))
                    elif q_cuoi[0] == mau_dich: 
                        ds_n.append(Move((h, c), (h_cuoi, c_cuoi), self.b_co))
                        break
                    else: 
                        break
                else: 
                    break

    def get_bishop_moves(self, h, c, ds_n):
        huong = ((-1, -1), (-1, 1), (1, -1), (1, 1)) 
        mau_dich = "b" if self.l_trang else "w"
        for d in huong:
            for i in range(1, 8):
                h_cuoi = h + d[0] * i
                c_cuoi = c + d[1] * i
                if 0 <= h_cuoi < 8 and 0 <= c_cuoi < 8:
                    q_cuoi = self.b_co[h_cuoi][c_cuoi]
                    if q_cuoi == "--": 
                        ds_n.append(Move((h, c), (h_cuoi, c_cuoi), self.b_co))
                    elif q_cuoi[0] == mau_dich: 
                        ds_n.append(Move((h, c), (h_cuoi, c_cuoi), self.b_co))
                        break
                    else: 
                        break
                else: 
                    break

    def get_queen_moves(self, h, c, ds_n):
        self.get_rook_moves(h, c, ds_n)
        self.get_bishop_moves(h, c, ds_n)

# ==========================================
# CLASS 2: Nước Đi (Move)
# ==========================================
class Move:
    hang_sang_so = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    so_sang_hang = {v: k for k, v in hang_sang_so.items()} 
    cot_sang_chu = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    chu_sang_cot = {v: k for k, v in cot_sang_chu.items()}

    def __init__(self, d_dau, d_cuoi, b_co):
        self.h_dau = d_dau[0]
        self.c_dau = d_dau[1]
        self.h_cuoi = d_cuoi[0]
        self.c_cuoi = d_cuoi[1]
        
        self.q_di = b_co[self.h_dau][self.c_dau]
        self.q_an = b_co[self.h_cuoi][self.c_cuoi]
        
        self.m_id = self.h_dau * 1000 + self.c_dau * 100 + self.h_cuoi * 10 + self.c_cuoi
        
        self.la_pc = False
        if (self.q_di == 'wP' and self.h_cuoi == 0) or (self.q_di == 'bP' and self.h_cuoi == 7):
            self.la_pc = True
            
        self.chon_pc = 'Q'
        
        self.la_ep = False
        if self.q_di[1] == 'P' and abs(self.c_dau - self.c_cuoi) == 1 and self.q_an == "--":
            self.la_ep = True
            self.q_an = b_co[self.h_dau][self.c_cuoi]
            
        self.la_nt = getattr(self, 'la_nt', False)
        
    # ==========================================
    # CÁC PROPERTY TƯƠNG THÍCH VỚI TÊN BIẾN CŨ (API INTERFACE)
    # Giúp GUI_Giaodien lấy thuộc tính mà không cần sửa file ở đó
    # ==========================================
    @property
    def start_row(self): return self.h_dau
    @property
    def start_col(self): return self.c_dau
    @property
    def end_row(self): return self.h_cuoi
    @property
    def end_col(self): return self.c_cuoi
    @property
    def piece_moved(self): return self.q_di
    @property
    def piece_captured(self): return self.q_an
    @property
    def is_pawn_promotion(self): return self.la_pc
    @property
    def promotion_choice(self): return self.chon_pc
    @promotion_choice.setter
    def promotion_choice(self, val): self.chon_pc = val
    @property
    def is_castle_move(self): return self.la_nt
    @is_castle_move.setter
    def is_castle_move(self, val): self.la_nt = val
    @property
    def is_enpassant_move(self): return self.la_ep
    @is_enpassant_move.setter
    def is_enpassant_move(self, val): self.la_ep = val

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.m_id == other.m_id
        return False

    def get_chess_notation(self):
        q_str = "" if self.q_di[1] == 'P' else self.q_di[1] 
        d_tt = self.get_rank_file(self.h_dau, self.c_dau)
        c_tt = self.get_rank_file(self.h_cuoi, self.c_cuoi)
        
        chuoi = f"{q_str}{d_tt} -> {c_tt}"
        if self.la_pc:
            chuoi += f"={self.chon_pc}"
        return chuoi

    def get_rank_file(self, h, c):
        return self.chu_sang_cot[c] + self.so_sang_hang[h]
