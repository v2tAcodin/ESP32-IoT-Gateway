"""
========================================================================================
HỆ THỐNG GHI DỮ LIỆU LƯỢNG MƯA & MỰC NƯỚC IOT RA FILE EXCEL (DATABASE NGHIÊN CỨU)
========================================================================================
Tác vụ:
1. Kết nối tự động tới HiveMQ Cloud Broker qua giao thức MQTT.
2. Lắng nghe bản tin JSON từ STM32 ➜ ESP32-C3 Gateway.
3. Lưu trữ bền vững vào CSDL SQLite (không sợ mất dữ liệu khi mất điện/tắt máy).
4. Tự động tổng hợp và ghi ra file Excel đa tầng (Multi-sheet):
   - Sheet 1: Dữ liệu chi tiết từng giây/phút (Raw Data)
   - Sheet 2: Tổng hợp thống kê theo từng Giờ (Hourly Summary)
   - Sheet 3: Tổng hợp thống kê theo từng Ngày (Daily Summary)
   - Sheet 4: Tổng hợp thống kê theo từng Năm / Tháng (Yearly Summary)
========================================================================================
"""

import sys
import os
import json
import time
import sqlite3
import argparse
from datetime import datetime
import threading
import signal

import paho.mqtt.client as mqtt
import pandas as pd
import openpyxl

# --- CẤU HÌNH MẶC ĐỊNH ---
DEFAULT_BROKER = "broker.hivemq.com"
DEFAULT_PORT = 1883
DEFAULT_TOPIC = "my_iot_project/stm32_sensor_data"
DEFAULT_DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rainfall_data.db")
DEFAULT_EXCEL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Bao_Cao_Luong_Mua_Nghien_Cuu.xlsx")
DEFAULT_SAMPLE_INTERVAL = 2.0  # Giới hạn ghi 1 mẫu mỗi 2 giây để tránh phình dữ liệu
DEFAULT_EXCEL_FLUSH_INTERVAL = 30  # Cứ 30 giây tự động cập nhật file Excel một lần

# Biến toàn cục
g_last_saved_time = 0
g_packet_count = 0
g_saved_count = 0
g_is_running = True
g_db_lock = threading.Lock()


def init_sqlite_db(db_path):
    """Khởi tạo bảng cơ sở dữ liệu SQLite nếu chưa tồn tại"""
    with g_db_lock:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                datetime_str TEXT,
                year INTEGER,
                month INTEGER,
                day INTEGER,
                hour INTEGER,
                minute INTEGER,
                second INTEGER,
                date TEXT,
                level REAL,
                rain_mm REAL,
                volt REAL,
                percent REAL,
                press REAL,
                raw INTEGER
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_datetime ON measurements(datetime_str)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ymd ON measurements(year, month, day, hour)')
        conn.commit()
        conn.close()


def save_to_sqlite(db_path, record):
    """Lưu 1 bản ghi vào CSDL SQLite"""
    with g_db_lock:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO measurements (
                timestamp, datetime_str, year, month, day, hour, minute, second,
                date, level, rain_mm, volt, percent, press, raw
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record['timestamp'], record['datetime_str'], record['year'], record['month'],
            record['day'], record['hour'], record['minute'], record['second'],
            record['date'], record['level'], record['rain_mm'], record['volt'],
            record['percent'], record['press'], record['raw']
        ))
        conn.commit()
        conn.close()


def export_sqlite_to_excel(db_path, excel_path):
    """Đọc dữ liệu từ SQLite và xuất ra file Excel chuẩn nghiên cứu gồm 4 Sheet"""
    with g_db_lock:
        conn = sqlite3.connect(db_path)
        df_raw = pd.read_sql_query('SELECT * FROM measurements ORDER BY id ASC', conn)
        conn.close()

    if df_raw.empty:
        print("  [Excel] Chưa có dữ liệu trong CSDL để xuất file Excel.")
        return False

    try:
        # Chuẩn bị Sheet 1: Dữ liệu chi tiết
        df_sheet1 = pd.DataFrame({
            "STT": df_raw["id"],
            "Thời Gian Đo": df_raw["datetime_str"],
            "Năm": df_raw["year"],
            "Tháng": df_raw["month"],
            "Ngày": df_raw["day"],
            "Giờ": df_raw["hour"],
            "Phút": df_raw["minute"],
            "Giây": df_raw["second"],
            "Mực Nước (cm)": df_raw["level"].round(2),
            "Lượng Mưa Quy Đổi (mm)": df_raw["rain_mm"].round(2),
            "Điện Áp Cảm Biến (V)": df_raw["volt"].round(2),
            "Áp Suất Thủy Tĩnh (Bar)": df_raw["press"].round(3),
            "Tỷ Lệ Cột Nước (%)": df_raw["percent"].round(1),
            "ADC Raw (12-bit)": df_raw["raw"]
        })

        # Chuẩn bị Sheet 2: Tổng hợp theo từng Giờ (Hourly Summary)
        df_hourly = df_raw.groupby(["date", "hour"]).agg(
            Số_Mẫu_Đo=("level", "count"),
            Mực_Nước_TB_cm=("level", "mean"),
            Lượng_Mưa_TB_mm=("rain_mm", "mean"),
            Đỉnh_Nước_Max_cm=("level", "max"),
            Đáy_Nước_Min_cm=("level", "min")
        ).reset_index()

        df_hourly["Biến_Thiên_Dâng_cm"] = (df_hourly["Đỉnh_Nước_Max_cm"] - df_hourly["Đáy_Nước_Min_cm"]).round(2)
        df_hourly["Mực_Nước_TB_cm"] = df_hourly["Mực_Nước_TB_cm"].round(2)
        df_hourly["Lượng_Mưa_TB_mm"] = df_hourly["Lượng_Mưa_TB_mm"].round(2)
        df_hourly["Đỉnh_Nước_Max_cm"] = df_hourly["Đỉnh_Nước_Max_cm"].round(2)
        df_hourly["Đáy_Nước_Min_cm"] = df_hourly["Đáy_Nước_Min_cm"].round(2)

        df_sheet2 = pd.DataFrame({
            "Ngày Đo": df_hourly["date"],
            "Khung Giờ": df_hourly["hour"].apply(lambda h: f"{h:02d}:00 - {h:02d}:59"),
            "Số Lượng Mẫu": df_hourly["Số_Mẫu_Đo"],
            "Mực Nước TB (cm)": df_hourly["Mực_Nước_TB_cm"],
            "Lượng Mưa TB (mm)": df_hourly["Lượng_Mưa_TB_mm"],
            "Đỉnh Cao Nhất (Max cm)": df_hourly["Đỉnh_Nước_Max_cm"],
            "Thấp Nhất (Min cm)": df_hourly["Đáy_Nước_Min_cm"],
            "Biến Thiên Dâng (cm)": df_hourly["Biến_Thiên_Dâng_cm"]
        })

        # Chuẩn bị Sheet 3: Tổng hợp theo từng Ngày (Daily Summary)
        df_daily = df_raw.groupby(["date", "year", "month", "day"]).agg(
            Số_Mẫu_Ngày=("level", "count"),
            Mực_Nước_TB_Ngày_cm=("level", "mean"),
            Lượng_Mưa_TB_Ngày_mm=("rain_mm", "mean"),
            Đỉnh_Nước_Ngày_Max_cm=("level", "max"),
            Đáy_Nước_Ngày_Min_cm=("level", "min")
        ).reset_index()

        df_daily["Biên_Độ_Ngày_cm"] = (df_daily["Đỉnh_Nước_Ngày_Max_cm"] - df_daily["Đáy_Nước_Ngày_Min_cm"]).round(2)
        df_daily["Mực_Nước_TB_Ngày_cm"] = df_daily["Mực_Nước_TB_Ngày_cm"].round(2)
        df_daily["Lượng_Mưa_TB_Ngày_mm"] = df_daily["Lượng_Mưa_TB_Ngày_mm"].round(2)
        df_daily["Đỉnh_Nước_Ngày_Max_cm"] = df_daily["Đỉnh_Nước_Ngày_Max_cm"].round(2)
        df_daily["Đáy_Nước_Ngày_Min_cm"] = df_daily["Đáy_Nước_Ngày_Min_cm"].round(2)

        df_sheet3 = pd.DataFrame({
            "Ngày Đo": df_daily["date"],
            "Năm": df_daily["year"],
            "Tháng": df_daily["month"],
            "Ngày": df_daily["day"],
            "Tổng Mẫu Thu Thập": df_daily["Số_Mẫu_Ngày"],
            "Mực Nước TB Ngày (cm)": df_daily["Mực_Nước_TB_Ngày_cm"],
            "Lượng Mưa TB Ngày (mm)": df_daily["Lượng_Mưa_TB_Ngày_mm"],
            "Đỉnh Nước Ngày (Max cm)": df_daily["Đỉnh_Nước_Ngày_Max_cm"],
            "Đáy Nước Ngày (Min cm)": df_daily["Đáy_Nước_Ngày_Min_cm"],
            "Biên Độ Biến Động (cm)": df_daily["Biên_Độ_Ngày_cm"]
        })

        # Chuẩn bị Sheet 4: Tổng hợp theo Tháng & Năm (Yearly / Monthly)
        df_monthly = df_raw.groupby(["year", "month"]).agg(
            Số_Mẫu_Tháng=("level", "count"),
            Mực_Nước_TB_Tháng_cm=("level", "mean"),
            Lượng_Mưa_TB_Tháng_mm=("rain_mm", "mean"),
            Đỉnh_Nước_Tháng_Max_cm=("level", "max")
        ).reset_index()

        df_sheet4 = pd.DataFrame({
            "Năm": df_monthly["year"],
            "Tháng": df_monthly["month"],
            "Tổng Mẫu Tháng": df_monthly["Số_Mẫu_Tháng"],
            "Mực Nước TB Tháng (cm)": df_monthly["Mực_Nước_TB_Tháng_cm"].round(2),
            "Lượng Mưa TB Tháng (mm)": df_monthly["Lượng_Mưa_TB_Tháng_mm"].round(2),
            "Đỉnh Cao Nhất Tháng (cm)": df_monthly["Đỉnh_Nước_Tháng_Max_cm"].round(2)
        })

        # Ghi vào file Excel bằng ExcelWriter (openpyxl engine)
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            df_sheet1.to_excel(writer, sheet_name="Du_Lieu_Chi_Tiet", index=False)
            df_sheet2.to_excel(writer, sheet_name="Tong_Hop_Theo_Gio", index=False)
            df_sheet3.to_excel(writer, sheet_name="Tong_Hop_Theo_Ngay", index=False)
            df_sheet4.to_excel(writer, sheet_name="Tong_Hop_Theo_Nam", index=False)

        print(f"  [Excel] Cập nhật thành công: {os.path.basename(excel_path)} ({len(df_sheet1)} dòng, 4 sheets)")
        return True

    except Exception as e:
        print(f"  [LỖI EXCEL] Không thể ghi file Excel: {e}")
        return False


def excel_flusher_task(db_path, excel_path, interval_sec):
    """Tiến trình chạy ngầm tự động ghi file Excel định kỳ"""
    global g_is_running
    while g_is_running:
        time.sleep(interval_sec)
        if not g_is_running:
            break
        export_sqlite_to_excel(db_path, excel_path)


def main():
    parser = argparse.ArgumentParser(description="IoT Rainfall & Water Level Data Logger to Excel")
    parser.add_argument("--broker", default=DEFAULT_BROKER, help="MQTT Broker host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="MQTT Broker port")
    parser.add_argument("--topic", default=DEFAULT_TOPIC, help="MQTT Topic")
    parser.add_argument("--interval", type=float, default=DEFAULT_SAMPLE_INTERVAL, help="Sample interval (seconds)")
    parser.add_argument("--flush", type=int, default=DEFAULT_EXCEL_FLUSH_INTERVAL, help="Excel flush interval (seconds)")
    parser.add_argument("--excel", default=DEFAULT_EXCEL_FILE, help="Path to output Excel file")
    parser.add_argument("--db", default=DEFAULT_DB_FILE, help="Path to SQLite DB file")
    parser.add_argument("--export-now", action="store_true", help="Chỉ xuất dữ liệu từ DB ra Excel rồi thoát")
    args = parser.parse_args()

    # Nếu chỉ muốn xuất file Excel từ CSDL có sẵn
    if args.export_now:
        print("Đang xuất dữ liệu từ CSDL SQLite sang Excel...")
        export_sqlite_to_excel(args.db, args.excel)
        print("Hoàn tất!")
        return

    # Khởi tạo CSDL SQLite
    init_sqlite_db(args.db)

    print("=" * 72)
    print("   HỆ THỐNG GHI DỮ LIỆU LƯỢNG MƯA & MỰC NƯỚC IOT RA EXCEL")
    print("=" * 72)
    print(f" • MQTT Broker     : {args.broker}:{args.port}")
    print(f" • Lắng nghe Topic : {args.topic}")
    print(f" • Chu kỳ lấy mẫu  : {args.interval} giây/mẫu")
    print(f" • Tự động ghi Excel: Cứ mỗi {args.flush} giây")
    print(f" • CSDL SQLite     : {args.db}")
    print(f" • File Excel      : {args.excel}")
    print("=" * 72)
    print(" [INFO] Nhấn Ctrl + C để dừng chương trình bất cứ lúc nào.")
    print("=" * 72)

    # Callback khi kết nối MQTT
    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f" ✔ ĐÃ KẾT NỐI TỚI BROKER '{args.broker}' THÀNH CÔNG!")
            client.subscribe(args.topic)
            print(f" ✔ Đã đăng ký lắng nghe dữ liệu từ kênh: '{args.topic}'\n")
        else:
            print(f" ✘ Kết nối Broker thất bại, mã lỗi: {rc}")

    # Callback khi nhận message từ MQTT
    def on_message(client, userdata, msg):
        global g_last_saved_time, g_packet_count, g_saved_count
        now_ts = time.time()
        now_dt = datetime.now()
        g_packet_count += 1

        payload_str = msg.payload.decode('utf-8', errors='ignore')

        # Throttling: Kiểm tra chu kỳ lấy mẫu
        if (now_ts - g_last_saved_time) < args.interval:
            return

        g_last_saved_time = now_ts
        g_saved_count += 1

        try:
            data = json.loads(payload_str)
            level = float(data.get("level", 0.0))
            volt = float(data.get("volt", 0.0))
            percent = float(data.get("percent", (level / 500.0) * 100.0))
            press = float(data.get("press", level / 1019.72))
            raw_adc = int(data.get("raw", 0))
            rain_mm = round(level * 10.0, 1)  # Quy đổi 1 cm nước = 10 mm mưa

            record = {
                "timestamp": now_dt.isoformat(),
                "datetime_str": now_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "year": now_dt.year,
                "month": now_dt.month,
                "day": now_dt.day,
                "hour": now_dt.hour,
                "minute": now_dt.minute,
                "second": now_dt.second,
                "date": now_dt.strftime("%Y-%m-%d"),
                "level": level,
                "rain_mm": rain_mm,
                "volt": volt,
                "percent": percent,
                "press": press,
                "raw": raw_adc
            }

            save_to_sqlite(args.db, record)

            print(f" [{now_dt.strftime('%H:%M:%S')}] #{g_saved_count:04d} | "
                  f"Mực nước: {level:5.1f} cm | "
                  f"Mưa: {rain_mm:5.1f} mm | "
                  f"Volt: {volt:4.2f} V | "
                  f"Áp suất: {press:5.3f} Bar")

        except Exception as e:
            print(f" [LỖI JSON] Không đọc được gói tin: {payload_str} ({e})")

    # Khởi tạo MQTT Client (hỗ trợ cả paho-mqtt v1 và v2)
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"excel_logger_{int(time.time())}")
    except AttributeError:
        client = mqtt.Client(client_id=f"excel_logger_{int(time.time())}")

    client.on_connect = on_connect
    client.on_message = on_message

    # Bật task chạy ngầm ghi Excel định kỳ
    flusher_thread = threading.Thread(
        target=excel_flusher_task,
        args=(args.db, args.excel, args.flush),
        daemon=True
    )
    flusher_thread.start()

    # Xử lý ngắt tín hiệu Ctrl + C
    def handle_exit(sig, frame):
        global g_is_running
        print("\n\n [DỪNG TIẾN TRÌNH] Đang hoàn tất ghi dữ liệu cuối cùng vào Excel...")
        g_is_running = False
        client.loop_stop()
        client.disconnect()
        export_sqlite_to_excel(args.db, args.excel)
        print(" ✔ Toàn bộ dữ liệu đã được bảo lưu an toàn trong file Excel!")
        print(" Tạm biệt!\n")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # Kết nối và bắt đầu lắng nghe
    try:
        client.connect(args.broker, args.port, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        handle_exit(None, None)
    except Exception as e:
        print(f"\n [LỖI KẾT NỐI] {e}")
        handle_exit(None, None)


if __name__ == "__main__":
    main()
