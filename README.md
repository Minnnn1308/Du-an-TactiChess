# ♟️ TactiChess - Python Chess Game 🔮

Một ứng dụng trò chơi Cờ vua toàn diện được xây dựng hoàn toàn bằng **Python** và Giao diện **PySide6** với phong cách đồ họa **Cyberpunk Neon**. Dự án này được thiết kế theo hướng Khoa học Máy tính (Đồ án / Bài Tập Lớn), tích hợp nhiều kiến trúc công nghệ mạnh mẽ như Đa luồng (Multi-threading), Cơ sở dữ liệu (SQLite) và Trí tuệ Nhân tạo (Stockfish).

---

## 🌟 Tính Năng Nổi Bật (Key Features)

- 🎨 **Giao Diện Đỉnh Cao (PySide6 UI):** Giao diện Cyberpunk 2D đẹp mắt, tự động bo góc, co dãn (Responsive). Hỗ trợ hiệu ứng Highlight và thiết kế Màn hình thông minh (QStackedWidget).
- 🧠 **Tích hợp Trí tuệ Nhân tạo (AI):** Gọi ngầm **Stockfish 16.1** qua `python-chess` để làm Đối thủ máy (PvE). Hỗ trợ đọc tệp thư viện Khai cuộc (`.bin`).
- 📊 **Phân Tích Bằng Centipawn (Game Review):** AI luồng phụ chấm điểm từng nước sau khi di chuyển. Đánh giá chất lượng nước đi chuẩn ván cờ quốc tế (Brilliant, Best Move, Inaccuracy, Blunder,...).
- 💾 **Cơ Sở Dữ Liệu Lịch Sử Đấu (SQLite):** Hệ thống Data tự động lưu trữ các ván cờ (Tên người chơi, Số nước, Chuỗi ký hiệu UCI) khi ván đấu kết thúc. Phát lại (Replay) và tự động gọi AI phân tích lại lịch sử.
- ⚡ **Luồng Xử Lý Song Song (Multi-threading):** Tách AI ra các nhánh `QThread` (AIWorker, AIMoveWorker), đảm bảo Giao diện ứng dụng hoàn toàn mượt mà, không bị "đơ" khi AI tính toán.
- 📐 **Lập Trình Hướng Đối Tượng (OOP) & Thuật Toán:** Xây dựng mọi cơ chế hoạt động của bàn cờ (Di chuyển, Nước đi hợp lệ, Nhập Thành, Ăn Qua Đường, Phong Cấp) bằng thuật toán trên Mảng 2 chiều mà không lệ thuộc Modules ngoài cho Vòng lặp ván cờ.

---

## 📂 Kiến Trúc Mã Nguồn (Project Structure)

Hệ thống mã nguồn được chia theo mô hình **MVC** (Model - View - Controller):

- `Code_GUI_Giaodien.py`: Main Entry. Xử lý toàn bộ UI, Events, chuyển cảnh và hiệu ứng.
- `Code_Logic_Xuly.py`: Engine cốt lõi của trò chơi. Thực hiện các thuật toán tính toán luật cờ vua.
- `Code_Database.py`: Quản lý Cơ sở dữ liệu SQLite cục bộ (File `DB_chess_history.db`).
- `Code_AI_Stockfish.py`: Lớp bao bọc (Wrapper) kết nối với Engine Stockfish (`.exe`) để lấy nước đi hoặc đánh giá thế cờ hiện tại dưới dạng Thread con.
- `images/`: Thư mục chứa tài nguyên đồ hoạ của từng quân cờ.
- Các tài nguyên ảnh nền (`Img_*.png|jpg`), file Logo (`Img_logo3.ico`).

*(Lưu ý: Tệp `Engine_stockfish.exe` rất nặng (hơn 100MB) nên không được upload trên Repo này. Xem phần Cài đặt ở dưới).*

---

## ⚙️ Hướng Dẫn Cài Đặt Khởi Chạy (Installation)

1. **Cài đặt Python**: Đảm bảo máy có Python 3.9+ 
2. **Cài đặt thư viện phụ thuộc**: Mở Terminal trong thư mục và gõ lệnh:
   ```bash
   pip install -r requirements.txt
   ```
3. **Cài đặt Stockfish (Bắt buộc)**:
   Do giới hạn dung lượng GitHub, tệp AI không có sẵn. 
   - Truy cập trang chủ [Stockfish](https://stockfishchess.org/download/) tải xuống tệp nhị phân cho Windows.
   - Giải nén tệp `.exe` và đổi tên nó thành `Engine_stockfish.exe`.
   - Bỏ tệp này vào thẳng thư mục gốc (Ngang hàng với file `Code_GUI_Giaodien.py`).
4. **Khởi chạy trò chơi**:
   ```bash
   python Code_GUI_Giaodien.py
   ```

---

## 👨‍💻 Tác Giả & Bản Quyền
- Vị trí: Bài tập lớn Khoa học máy tính / Thiết kế Giao diện.
- Phát triển bởi: Nguyen Quang Minh - B24DCVN069
- Ứng dụng là phần mềm mã nguồn mở dựa trên Stockfish Engine.

