# HƯỚNG DẪN LƯU TRỮ VÀ TRÍCH XUẤT DỮ LIỆU LƯỢNG MƯA & MỰC NƯỚC RA EXCEL

Thư mục này cung cấp hệ thống hoàn chỉnh giúp lưu trữ, lọc và trích xuất dữ liệu đo được từ **STM32 & ESP32-C3** vào **Excel (.xlsx)** làm cơ sở dữ liệu nghiên cứu khoa học.

---

## 1. Cấu Trúc File Excel Chuẩn Nghiên Cứu

Khi xuất ra file `Bao_Cao_Luong_Mua_Nghien_Cuu.xlsx`, dữ liệu sẽ được phân tách thành 4 Sheet độc lập:

1. **Sheet 1: `Du_Lieu_Chi_Tiet` (Raw Data)**:
   - Lưu trữ toàn bộ các mốc thời gian đo: `STT`, `Thời Gian Đo (YYYY-MM-DD HH:mm:ss)`, `Năm`, `Tháng`, `Ngày`, `Giờ`, `Phút`, `Giây`, `Mực Nước (cm)`, `Lượng Mưa Quy Đổi (mm)`, `Điện Áp Cảm Biến (V)`, `Áp Suất Thủy Tĩnh (Bar)`, `Tỷ Lệ (%)`, `ADC Raw`.
2. **Sheet 2: `Tong_Hop_Theo_Gio` (Hourly Summary)**:
   - Tự động gom nhóm theo từng khung giờ trong ngày (`00:00 - 00:59`, `01:00 - 01:59`, ...).
   - Thống kê: `Số Lượng Mẫu`, `Mực Nước TB (cm)`, `Lượng Mưa TB (mm)`, `Đỉnh Cao Nhất (Max cm)`, `Thấp Nhất (Min cm)`, `Biến Thiên Dâng (cm)`.
3. **Sheet 3: `Tong_Hop_Theo_Ngay` (Daily Summary)**:
   - Tự động gom nhóm theo từng ngày: `Tổng Mẫu Ngày`, `Mực Nước TB Ngày (cm)`, `Lượng Mưa TB Ngày (mm)`, `Đỉnh Nước Ngày (Max cm)`, `Mực Nước Đáy Ngày (Min cm)`, `Biên Độ Biến Động (cm)`.
4. **Sheet 4: `Tong_Hop_Theo_Nam` (Yearly / Monthly Summary)**:
   - Tự động gom nhóm 12 tháng trong năm để phục vụ phân tích quy luật theo mùa.

---

## 2. Cách 1: Sử Dụng Trực Tiếp Trên Web Dashboard (Tiện lợi nhất)

1. Mở file [web_dashboard/index.html](file:///d:/Embedded/esp32/wifiesp32/web_dashboard/index.html) bằng bất kỳ trình duyệt nào (Chrome, Edge, Firefox, Cốc Cốc).
2. Trang web sẽ tự động kết nối tới MQTT Broker và lưu dữ liệu vào cơ sở dữ liệu cục bộ **IndexedDB** của trình duyệt.
3. Ở khu vực **"Cơ Sở Dữ Liệu Nghiên Cứu & Trích Xuất Excel"**:
   - Chọn bộ lọc: **Năm**, **Tháng**, **Ngày cụ thể**, hoặc **Từ giờ ... Đến giờ**.
   - Bấm **"Tra Cứu / Lọc Dữ Liệu"** để xem thống kê nhanh (Số mẫu, TB, Max, Min) và bảng xem trước 15 dòng.
   - Bấm nút xanh **📗 Xuất Báo Cáo Excel (.xlsx)** để tải ngay file Excel đa tầng về máy tính.
   - Hoặc bấm **🧪 Thử nghiệm (+50 mẫu)** để tạo dữ liệu test giả lập và kiểm tra ngay.

---

## 3. Cách 2: Sử Dụng Script Python Chạy Ngầm (Thu Thập Dài Hạn)

Phương án này cực kỳ thích hợp khi bạn muốn cắm máy tính để thu thập dữ liệu liên tục nhiều ngày, nhiều tháng:

### Bước 1: Khởi chạy
- **Cách đơn giản nhất:** Double-click chuột trái vào file `run_logger.bat`.
- Hoặc mở Command Prompt / PowerShell trong thư mục này và gõ:
  ```bash
  python logger_to_excel.py
  ```

### Bước 2: Theo dõi
- Chương trình sẽ in ra màn hình mỗi khi nhận và ghi một mẫu dữ liệu:
  ```
  [08:15:30] #0045 | Mực nước:  85.2 cm | Mưa: 852.0 mm | Volt: 0.65 V | Áp suất: 0.084 Bar
  ```
- Cứ mỗi 30 giây (hoặc khi bạn nhấn `Ctrl + C` để dừng), chương trình sẽ tự động cập nhật và đóng gói toàn bộ dữ liệu vào file `Bao_Cao_Luong_Mua_Nghien_Cuu.xlsx`.

### Bước 3: Kiểm thử độc lập (Khi chưa cắm phần cứng)
Nếu bạn muốn kiểm tra xem Python logger có ghi đúng vào Excel không trước khi đấu nối STM32, hãy mở một cửa sổ terminal khác và chạy:
```bash
python test_sender.py
```
Script `test_sender.py` sẽ tự động đóng vai cảm biến, phát các bản tin MQTT giả lập để bạn xem quá trình ghi Excel diễn ra trực tiếp!
