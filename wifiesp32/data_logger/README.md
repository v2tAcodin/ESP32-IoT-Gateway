# Backend Service & Data Logger v3.0 (Python Flask + MQTT + Supabase / SQLite)

Thư mục này chứa dịch vụ Backend hợp nhất (`service.py`) dùng để thu thập dữ liệu mực nước từ **ESP32-C3 / STM32** qua **MQTT (HiveMQ)**, lưu trữ vĩnh viễn vào **PostgreSQL (Supabase)** hoặc **SQLite (WAL)**, và cung cấp **REST API** cho Web Dashboard.

---

## 1. Thành phần chính

| Tệp | Chức năng |
| :--- | :--- |
| `service.py` | Dịch vụ chính gồm: MQTT Background Worker + DualDB Manager (Supabase PostgreSQL / SQLite WAL) + Flask REST API Server |
| `migrate_to_supabase.py` | Script nạp toàn bộ dữ liệu lịch sử từ `rainfall_data.db` (SQLite) lên Supabase PostgreSQL theo lô (*batch insert*), tự chống trùng lặp |
| `requirements.txt` | Danh sách thư viện Python cần thiết (`flask`, `gunicorn`, `paho-mqtt`, `psycopg2-binary`, `pandas`, `openpyxl`, `python-dotenv`) |
| `.env.example` | Mẫu biến môi trường — sao chép thành `.env` để cấu hình cục bộ (không đẩy `.env` lên Git) |
| `run_service.bat` | Script chạy nhanh `service.py` trên Windows |
| `test_sender.py` | Script phát gói tin MQTT giả lập để kiểm thử độc lập khi chưa cắm phần cứng |

---

## 2. Cơ chế hoạt động Dual-Mode Database

`service.py` sử dụng lớp bọc `DualDBConnection` giúp chạy mượt trên cả môi trường Cloud và máy cá nhân:

- **Chế độ Cloud (Supabase PostgreSQL):** Tự kích hoạt khi biến môi trường `DATABASE_URL` có tiền tố `postgresql://` (tự động bật `sslmode=require`). Dữ liệu được lưu vĩnh viễn, không bị mất khi Render ngủ hoặc deploy lại.
- **Chế độ Local (SQLite WAL):** Tự kích hoạt khi để trống `DATABASE_URL`. Lưu vào file `rainfall_data.db` với `PRAGMA journal_mode = WAL` giúp đọc/ghi đồng thời không bị khóa file.

---

## 3. Chạy cục bộ (Local PC)

```powershell
# 1. Tạo tệp cấu hình từ mẫu
Copy-Item .env.example .env

# 2. Cài đặt thư viện Python (khuyên dùng Python 3.11)
pip install -r requirements.txt

# 3. Khởi chạy Backend (hoặc double-click run_service.bat)
python service.py
```

Sau khi chạy, mở trình duyệt tại `http://localhost:5000` (Backend phục vụ sẵn cả giao diện Web Dashboard và toàn bộ REST API).

---

## 4. Triển khai trên Render Cloud + Supabase

1. Cấu hình start command (đã khai báo sẵn trong `render.yaml` ở thư mục gốc):
   ```bash
   gunicorn --workers 1 --threads 4 --bind 0.0.0.0:$PORT service:app
   ```
   > **Lưu ý:** Dùng `--workers 1` để tránh tạo nhiều tiến trình MQTT Worker ghi trùng gói tin vào CSDL, kết hợp `--threads 4` để xử lý đồng thời các yêu cầu HTTP.
2. Thêm biến môi trường trong **Render Dashboard → Environment**:
   - `DATABASE_URL`: chuỗi kết nối **Session Pooler** của Supabase (`postgresql://postgres.<ref>:<password>@aws-...pooler.supabase.com:5432/postgres`).
   - `ADMIN_API_KEY`: khóa bí mật dùng cho header `X-Admin-Token` khi gọi các API nhạy cảm (`/api/database/clear`, `/api/simulate`, `/api/import/indexeddb`).
   - `TIMEOUT_MINUTES`: `2.0` (ngưỡng báo mất dữ liệu nếu quá 2 phút không nhận gói mới).
3. *(Tùy chọn)* Di trú dữ liệu lịch sử từ máy tính lên Supabase:
   ```powershell
   $env:DATABASE_URL="postgresql://..."
   python migrate_to_supabase.py
   ```

---

## 5. Bảo mật & Tiện ích dữ liệu

- **Lọc trùng & Kiểm duyệt:** Tự động bỏ qua gói tin trùng trong `< 1.0s`, loại bỏ JSON thiếu trường, giá trị `NaN/Inf`, hoặc `raw_adc` ngoài dải `[0, 4095]`.
- **Xác thực quản trị:** Các endpoint xóa/nạp giả lập yêu cầu `X-Admin-Token` (chế độ **fail-closed** trên Render nếu chưa thiết lập `ADMIN_API_KEY`). Trước khi xóa dữ liệu, hệ thống bắt buộc xác nhận `"XOA"` và tự tạo bản sao lưu `.db`.
- **Xuất dữ liệu đa định dạng:**
  - `/api/export.xlsx`: File Excel gồm sheet thống kê tổng hợp và chi tiết mẫu đo (giờ Việt Nam UTC+7).
  - `/api/export.csv`: File CSV có gắn **UTF-8 BOM** mở thẳng trên Excel không lỗi font tiếng Việt.
  - `/api/database/download`: Tải trực tiếp file `.db` SQLite (tự động dựng snapshot từ Supabase nếu đang chạy Cloud).
