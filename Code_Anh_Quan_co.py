import os
import urllib.request

def download_chess_pieces():
    # 1. Tạo thư mục 'images' nếu chưa có
    os.makedirs("images", exist_ok=True)
    
    # 2. Danh sách 12 loại quân cờ theo đúng tên ta đã cấu hình trong file GUI
    pieces = ["wP", "wR", "wN", "wB", "wQ", "wK", "bP", "bR", "bN", "bB", "bQ", "bK"]
    
    print("Bắt đầu tải bộ ảnh quân cờ (Nền trong suốt, chuẩn HD)...\n")
    
    for piece in pieces:
        # Lấy trực tiếp từ server assets công khai của Chess.com (Theme: Alpha)
        # Bọn họ dùng tên viết thường (vd: wp.png) nên ta dùng .lower() để khớp URL
        url = f"https://images.chesscomfiles.com/chess-themes/pieces/alpha/150/{piece.lower()}.png"
        filepath = f"images/{piece}.png"
        
        try:
            # Tải ảnh từ URL và lưu vào máy
            urllib.request.urlretrieve(url, filepath)
            print(f"[+] Đã tải thành công: {piece}.png")
        except Exception as e:
            print(f"[-] Lỗi khi tải {piece}.png: {e}")
            
    print("\nHoàn tất! Bạn hãy mở thư mục 'images' ra để kiểm tra thành quả.")

if __name__ == "__main__":
    download_chess_pieces()
