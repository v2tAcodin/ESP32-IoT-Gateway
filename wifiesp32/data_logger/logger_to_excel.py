"""
========================================================================================
HỆ THỐNG GHI DỮ LIỆU LƯỢNG MƯA & MỰC NƯỚC IOT RA EXCEL (CSDL TỐI GIẢN CHUẨN V2.0)
========================================================================================
Tác vụ:
1. Kết nối tự động tới HiveMQ Cloud Broker qua giao thức MQTT.
2. Lắng nghe bản tin JSON từ STM32 ➜ ESP32-C3 Gateway.
3. Lưu trữ bền vững vào CSDL SQLite theo schema tối giản (chỉ 5 trường):
   - timestamp (epoch ms UTC)
   - volt (điện áp V)
   - water_level_cm (mực nước cm)
   - is_simulated (0: thật, 1: giả lập)
   - calibration_version (chuỗi '1.0')
4. Tự động di trú (Migration) nếu phát hiện CSDL cũ để không mất dữ liệu.
5. Tự động tính toán động: Áp suất, Tỷ lệ cột nước, Tốc độ dâng/rút nước (cm/h).
6. Xuất file Excel đa tầng (Multi-sheet) chuẩn múi giờ UTC+7 (Việt Nam).
========================================================================================
"""

import sys
import os
import json
import time
import sqlite3
import argparse
from datetime import datetime, timezone, timedelta
import threading
import signal

import paho.mqtt.client as mqtt
import pandas as pd
import openpyxl

# Múi giờ UTC+7 (Việt Nam)
VN_TZ = timezone(timedelta(hours=7))

# --- CẤU HÌNH MẶC ĐỊNH ---
DEFAULT_BROKER = "broker.hivemq.com"
DEFAULT_PORT = 1883
DEFAULT_TOPIC = "my_iot_project/stm32_sensor_data"
DEFAULT_DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rainfall_data.db")
DEFAULT_EXCEL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Bao_Cao_Luong_Mua_Nghien_Cuu.xlsx")
DEFAULT_SAMPLE_INTERVAL = 2.0  # Giới hạn ghi 1 mẫu mỗi 2 giây
DEFAULT_EXCEL_FLUSH_INTERVAL = 30  # Cứ 30 giây tự động cập nhật file Excel một lần

# Biến toàn cục
g_last_saved_time = 0
g_packet_count = 0
g_saved_count = 0
g_is_running = True
g_db_lock = threading.Lock()
g_last_record_for_rate = None


def init_sqlite_db(db_path):
    """
    Khởi tạo bảng cơ sở dữ liệu SQLite theo schema tối giản v2.0
    Tự động chạy Migration nếu phát hiện bảng cũ để bảo toàn dữ liệu 100%.
    """
    with g_db_lock:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Kiểm tra xem bảng measurements đã tồn tại chưa
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='measurements'")
        table_exists = cursor.fetchone() is not None

        if table_exists:
            # Kiểm tra các cột hiện tại trong bảng
            cursor.execute("PRAGMA table_info(measurements)")
            columns = [col[1] for col in cursor.fetchall()]

            # Nếu bảng cũ có cột thừa như 'rain_mm' hoặc thiếu 'water_level_cm'
            if "water_level_cm" not in columns or "rain_mm" in columns:
                print("  [MIGRATION] Phát hiện CSDL cũ. Đang tự động di trú sang schema tối giản v2.0...")
                cursor.execute('''
                    CREATE TABLE measurements_v2 (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp INTEGER,
                        volt REAL,
                        water_level_cm REAL,
                        is_simulated INTEGER DEFAULT 0,
                        is_error INTEGER DEFAULT 0,
                        is_aggregated INTEGER DEFAULT 0,
                        sample_count INTEGER DEFAULT 1,
                        max_level_cm REAL,
                        min_level_cm REAL,
                        calibration_version TEXT DEFAULT '1.0'
                    )
                ''')

                # Sao chép dữ liệu từ bảng cũ sang bảng mới
                level_col = "level" if "level" in columns else "water_level_cm"
                cursor.execute(f'''
                    INSERT INTO measurements_v2 (id, timestamp, volt, water_level_cm, is_simulated, calibration_version)
                    SELECT 
                        id,
                        CASE 
                            WHEN typeof(timestamp) = 'integer' THEN timestamp
                            ELSE CAST(strftime('%s', datetime_str) AS INTEGER) * 1000
                        END,
                        volt,
                        {level_col},
                        0,
                        '1.0'
                    FROM measurements
                ''')

                cursor.execute("DROP TABLE measurements")
                cursor.execute("ALTER TABLE measurements_v2 RENAME TO measurements")
                print("  [MIGRATION] Hoàn tất di trú! Toàn bộ số liệu cũ đã được bảo toàn an toàn.")
        else:
            # Tạo bảng mới tối giản
            cursor.execute('''
                CREATE TABLE measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER,
                    volt REAL,
                    water_level_cm REAL,
                    is_simulated INTEGER DEFAULT 0,
                    is_error INTEGER DEFAULT 0,
                    is_aggregated INTEGER DEFAULT 0,
                    sample_count INTEGER DEFAULT 1,
                    max_level_cm REAL,
                    min_level_cm REAL,
                    calibration_version TEXT DEFAULT '1.0'
                )
            ''')

        # Đảm bảo các cột mới phục vụ Lỗi cảm biến & Chính sách lưu trữ (Rollup) luôn tồn tại
        cursor.execute("PRAGMA table_info(measurements)")
        existing_cols = [col[1] for col in cursor.fetchall()]
        new_cols = [
            ("is_error", "INTEGER DEFAULT 0"),
            ("is_aggregated", "INTEGER DEFAULT 0"),
            ("sample_count", "INTEGER DEFAULT 1"),
            ("max_level_cm", "REAL"),
            ("min_level_cm", "REAL")
        ]
        for col_name, col_def in new_cols:
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE measurements ADD COLUMN {col_name} {col_def}")

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ts ON measurements(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sim ON measurements(is_simulated)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_err ON measurements(is_error)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agg ON measurements(is_aggregated)")

        conn.commit()
        conn.close()


def save_to_sqlite(db_path, record):
    """Lưu 1 bản ghi tối giản vào CSDL SQLite"""
    with g_db_lock:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO measurements (
                timestamp, volt, water_level_cm, is_simulated, is_error,
                is_aggregated, sample_count, max_level_cm, min_level_cm, calibration_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record['timestamp'],
            record['volt'],
            record['water_level_cm'],
            1 if record.get('is_simulated', False) else 0,
            1 if record.get('is_error', False) else 0,
            1 if record.get('is_aggregated', False) else 0,
            record.get('sample_count', 1),
            record.get('max_level_cm', record['water_level_cm']),
            record.get('min_level_cm', record['water_level_cm']),
            record.get('calibration_version', '1.0')
        ))
        conn.commit()
        conn.close()


def rollup_old_records_sqlite(db_path, cutoff_days=30):
    """
    Chính sách lưu trữ (Retention Policy):
    Gộp các mẫu thô cũ hơn `cutoff_days` ngày thành 1 bản ghi/giờ (avg/min/max)
    giúp CSDL SQLite không bị phình to khi hệ thống chạy liên tục nhiều tháng.
    """
    cutoff_epoch_ms = int((time.time() - cutoff_days * 86400) * 1000)
    with g_db_lock:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, timestamp, volt, water_level_cm, is_simulated, is_error 
            FROM measurements 
            WHERE timestamp < ? AND is_aggregated = 0
            ORDER BY timestamp ASC
        ''', (cutoff_epoch_ms,))
        rows = cursor.fetchall()

        if not rows:
            conn.close()
            return 0

        # Gom nhóm theo từng mốc giờ (1 giờ = 3,600,000 ms)
        hourly_map = {}
        for row in rows:
            r_id, ts, volt, level, is_sim, is_err = row
            hour_bucket = (ts // 3600000) * 3600000
            key = (hour_bucket, is_sim)
            if key not in hourly_map:
                hourly_map[key] = {
                    "hour_ts": hour_bucket,
                    "is_sim": is_sim,
                    "ids": [],
                    "valid_levels": [],
                    "volts": []
                }
            h = hourly_map[key]
            h["ids"].append(r_id)
            if not is_err:
                h["valid_levels"].append(level)
            h["volts"].append(volt)

        # Lưu bản ghi gộp và xóa các mẫu thô tương ứng
        for group in hourly_map.values():
            avg_level = 0.0
            max_level = 0.0
            min_level = 0.0
            if group["valid_levels"]:
                avg_level = sum(group["valid_levels"]) / len(group["valid_levels"])
                max_level = max(group["valid_levels"])
                min_level = min(group["valid_levels"])
            avg_volt = sum(group["volts"]) / len(group["volts"]) if group["volts"] else 0.0
            sample_cnt = len(group["ids"])

            cursor.execute('''
                INSERT INTO measurements (
                    timestamp, volt, water_level_cm, is_simulated, is_error,
                    is_aggregated, sample_count, max_level_cm, min_level_cm, calibration_version
                ) VALUES (?, ?, ?, ?, 0, 1, ?, ?, ?, '1.0')
            ''', (
                group["hour_ts"], round(avg_volt, 2), round(avg_level, 1),
                group["is_sim"], sample_cnt, round(max_level, 1), round(min_level, 1)
            ))

            cursor.executemany("DELETE FROM measurements WHERE id = ?", [(i,) for i in group["ids"]])

        conn.commit()
        conn.close()
        print(f"  [RETENTION] Đã gộp thành công {len(rows)} mẫu cũ (> {cutoff_days} ngày) thành {len(hourly_map)} bản ghi giờ!")
        return len(rows)


def export_sqlite_to_excel(db_path, excel_path, include_simulated=False):
    """
    Đọc dữ liệu từ SQLite, TÍNH TOÁN ĐỘNG các trường vật lý,
    và xuất ra file Excel chuẩn nghiên cứu gồm 4 Sheet theo múi giờ UTC+7.
    """
    with g_db_lock:
        conn = sqlite3.connect(db_path)
        query = 'SELECT * FROM measurements'
        if not include_simulated:
            query += ' WHERE is_simulated = 0'
        query += ' ORDER BY timestamp ASC'
        df_raw = pd.read_sql_query(query, conn)
        conn.close()

    if df_raw.empty:
        print("  [Excel] Chưa có dữ liệu phù hợp trong CSDL để xuất file Excel.")
        return False

    try:
        # 1. TÍNH TOÁN CÁC TRƯỜNG ĐỘNG (COMPUTED ON-THE-FLY)
        timestamps = df_raw["timestamp"].values
        levels = df_raw["water_level_cm"].values

        # Tính tốc độ dâng/rút nước (cm/h) giữa các mẫu liên tiếp
        rates = [0.0]
        for i in range(1, len(levels)):
            dt_sec = (timestamps[i] - timestamps[i - 1]) / 1000.0
            if dt_sec >= 1.0:
                rate = ((levels[i] - levels[i - 1]) / dt_sec) * 3600.0
                rates.append(round(rate, 1))
            else:
                rates.append(0.0)

        df_raw["rate_cm_h"] = rates

        # Tính ngày giờ theo múi giờ UTC+7
        def parse_vn_time(ts_ms):
            dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=VN_TZ)
            return (
                dt.strftime("%d/%m/%Y %H:%M:%S"),
                dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second,
                dt.strftime("%d/%m/%Y")
            )

        parsed_times = [parse_vn_time(ts) for ts in timestamps]
        df_raw["datetime_str"] = [p[0] for p in parsed_times]
        df_raw["year"] = [p[1] for p in parsed_times]
        df_raw["month"] = [p[2] for p in parsed_times]
        df_raw["day"] = [p[3] for p in parsed_times]
        df_raw["hour"] = [p[4] for p in parsed_times]
        df_raw["minute"] = [p[5] for p in parsed_times]
        df_raw["second"] = [p[6] for p in parsed_times]
        df_raw["date_str"] = [p[7] for p in parsed_times]

        # Áp suất và % cột nước
        df_raw["press_bar"] = (df_raw["water_level_cm"] / 1019.72).round(3)
        df_raw["percent"] = ((df_raw["water_level_cm"] / 500.0) * 100.0).clip(0, 100).round(1)
        df_raw["level_mm"] = (df_raw["water_level_cm"] * 10.0).round(0)

        # Chuẩn bị Sheet 1: Dữ liệu chi tiết
        df_sheet1 = pd.DataFrame({
            "STT": range(1, len(df_raw) + 1),
            "Thời Gian Đo (dd/mm/yyyy HH:mm:ss UTC+7)": df_raw["datetime_str"],
            "Năm": df_raw["year"],
            "Tháng": df_raw["month"],
            "Ngày": df_raw["day"],
            "Giờ": df_raw["hour"],
            "Phút": df_raw["minute"],
            "Giây": df_raw["second"],
            "Mực Nước (cm)": df_raw["water_level_cm"].round(1),
            "Mực Nước Quy Đổi (mm)": df_raw["level_mm"],
            "Tốc Độ Thay Đổi (cm/h)": df_raw["rate_cm_h"],
            "Điện Áp Cảm Biến (V)": df_raw["volt"].round(2),
            "Trạng Thái Cảm Biến": df_raw["is_error"].apply(lambda e: "⚠️ Lỗi điện áp" if e == 1 else "✔ Hợp lệ"),
            "Áp Suất Thủy Tĩnh (Bar)": df_raw["press_bar"],
            "Tỷ Lệ Cột Nước (%)": df_raw["percent"],
            "Loại Bản Ghi": df_raw["is_aggregated"].apply(lambda a: "Đã gộp theo giờ" if a == 1 else "Mẫu thô tức thời"),
            "Nguồn Dữ Liệu": df_raw["is_simulated"].apply(lambda s: "Giả lập (Test)" if s == 1 else "Thật (Cảm biến)"),
            "Phiên Bản Hiệu Chuẩn": df_raw["calibration_version"]
        })

        # LỌC BỎ CÁC MẪU LỖI ĐỂ TÍNH THỐNG KÊ (BẢO ĐẢM TÍNH TOÀN VẸN KHOA HỌC)
        df_valid = df_raw[df_raw["is_error"] == 0]

        if not df_valid.empty:
            # Chuẩn bị Sheet 2: Tổng hợp theo từng Giờ (Hourly Summary)
            df_hourly = df_valid.groupby(["date_str", "hour"]).agg(
                Số_Mẫu_Hợp_Lệ=("water_level_cm", "count"),
                Mực_Nước_TB_cm=("water_level_cm", "mean"),
                Đỉnh_Nước_Max_cm=("water_level_cm", "max"),
                Đáy_Nước_Min_cm=("water_level_cm", "min"),
                Tốc_Độ_Dâng_Max=("rate_cm_h", "max"),
                Tốc_Độ_Rút_Max=("rate_cm_h", "min")
            ).reset_index()

            df_hourly["Biến_Thiên_Dâng_cm"] = (df_hourly["Đỉnh_Nước_Max_cm"] - df_hourly["Đáy_Nước_Min_cm"]).round(2)
            df_hourly["Mực_Nước_TB_cm"] = df_hourly["Mực_Nước_TB_cm"].round(2)

            df_sheet2 = pd.DataFrame({
                "Ngày Đo (dd/mm/yyyy)": df_hourly["date_str"],
                "Khung Giờ": df_hourly["hour"].apply(lambda h: f"{h:02d}:00 - {h:02d}:59"),
                "Số Lượng Mẫu Hợp Lệ": df_hourly["Số_Mẫu_Hợp_Lệ"],
                "Mực Nước TB (cm)": df_hourly["Mực_Nước_TB_cm"],
                "Đỉnh Cao Nhất (Max cm)": df_hourly["Đỉnh_Nước_Max_cm"].round(1),
                "Thấp Nhất (Min cm)": df_hourly["Đáy_Nước_Min_cm"].round(1),
                "Biến Thiên Dâng (cm)": df_hourly["Biến_Thiên_Dâng_cm"],
                "Tốc Độ Dâng Max (cm/h)": df_hourly["Tốc_Độ_Dâng_Max"].round(1),
                "Tốc Độ Rút Max (cm/h)": df_hourly["Tốc_Độ_Rút_Max"].round(1)
            })

            # Chuẩn bị Sheet 3: Tổng hợp theo từng Ngày (Daily Summary)
            df_daily = df_valid.groupby(["date_str", "year", "month", "day"]).agg(
                Số_Mẫu_Hợp_Lệ=("water_level_cm", "count"),
                Mực_Nước_TB_Ngày_cm=("water_level_cm", "mean"),
                Đỉnh_Nước_Ngày_Max_cm=("water_level_cm", "max"),
                Đáy_Nước_Ngày_Min_cm=("water_level_cm", "min")
            ).reset_index()

            df_daily["Biên_Độ_Ngày_cm"] = (df_daily["Đỉnh_Nước_Ngày_Max_cm"] - df_daily["Đáy_Nước_Ngày_Min_cm"]).round(2)
            df_daily["Mực_Nước_TB_Ngày_cm"] = df_daily["Mực_Nước_TB_Ngày_cm"].round(2)

            df_sheet3 = pd.DataFrame({
                "Ngày Đo (dd/mm/yyyy)": df_daily["date_str"],
                "Năm": df_daily["year"],
                "Tháng": df_daily["month"],
                "Ngày": df_daily["day"],
                "Tổng Mẫu Hợp Lệ": df_daily["Số_Mẫu_Hợp_Lệ"],
                "Mực Nước TB Ngày (cm)": df_daily["Mực_Nước_TB_Ngày_cm"],
                "Đỉnh Nước Ngày (Max cm)": df_daily["Đỉnh_Nước_Ngày_Max_cm"].round(1),
                "Đáy Nước Ngày (Min cm)": df_daily["Đáy_Nước_Ngày_Min_cm"].round(1),
                "Biên Độ Biến Động (cm)": df_daily["Biên_Độ_Ngày_cm"]
            })
        else:
            df_sheet2 = pd.DataFrame({"Thông Báo": ["Tất cả các mẫu trong khoảng lọc đều là mẫu lỗi cảm biến"]})
            df_sheet3 = pd.DataFrame({"Thông Báo": ["Tất cả các mẫu trong khoảng lọc đều là mẫu lỗi cảm biến"]})

        # Ghi vào file Excel đa Sheet
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            df_sheet1.to_excel(writer, sheet_name="Du_Lieu_Chi_Tiet", index=False)
            df_sheet2.to_excel(writer, sheet_name="Tong_Hop_Theo_Gio", index=False)
            df_sheet3.to_excel(writer, sheet_name="Tong_Hop_Theo_Ngay", index=False)

        print(f"  [Excel] Cập nhật thành công: {os.path.basename(excel_path)} ({len(df_sheet1)} dòng, 3 sheets, UTC+7)")
        return True

    except Exception as e:
        print(f"  [LỖI EXCEL] Không thể xuất file Excel: {e}")
        return False


def export_sqlite_to_csv_with_bom(db_path, csv_path):
    """Xuất CSV kèm UTF-8 BOM để Excel đọc đúng tiếng Việt không bị lỗi font"""
    with g_db_lock:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query('SELECT * FROM measurements ORDER BY timestamp ASC', conn)
        conn.close()

    if not df.empty:
        # Ghi với encoding utf-8-sig (tự động gắn UTF-8 BOM \xef\xbb\xbf)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"  [CSV] Đã xuất file CSV chuẩn UTF-8 BOM: {csv_path}")


def excel_flusher_task(db_path, excel_path, interval_sec, include_simulated):
    """Tiến trình ngầm tự động flush ra Excel định kỳ"""
    global g_is_running
    while g_is_running:
        time.sleep(interval_sec)
        if not g_is_running:
            break
        export_sqlite_to_excel(db_path, excel_path, include_simulated)


def main():
    parser = argparse.ArgumentParser(description="IoT Rainfall & Water Level Data Logger v2.0")
    parser.add_argument("--broker", default=DEFAULT_BROKER, help="MQTT Broker host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="MQTT Broker port")
    parser.add_argument("--topic", default=DEFAULT_TOPIC, help="MQTT Topic")
    parser.add_argument("--interval", type=float, default=DEFAULT_SAMPLE_INTERVAL, help="Sample interval (seconds)")
    parser.add_argument("--flush", type=int, default=DEFAULT_EXCEL_FLUSH_INTERVAL, help="Excel flush interval (seconds)")
    parser.add_argument("--excel", default=DEFAULT_EXCEL_FILE, help="Path to output Excel file")
    parser.add_argument("--db", default=DEFAULT_DB_FILE, help="Path to SQLite DB file")
    parser.add_argument("--include-simulated", action="store_true", help="Bao gồm cả dữ liệu giả lập trong file Excel")
    parser.add_argument("--export-now", action="store_true", help="Chỉ xuất dữ liệu từ DB ra Excel rồi thoát")
    parser.add_argument("--volt-min", type=float, default=0.08, help="Ngưỡng điện áp dưới hợp lệ (V)")
    parser.add_argument("--volt-max", type=float, default=3.35, help="Ngưỡng điện áp trên hợp lệ (V)")
    parser.add_argument("--retention-days", type=int, default=30, help="Số ngày lưu trữ mẫu thô trước khi tự động gộp theo giờ")
    parser.add_argument("--rollup-now", action="store_true", help="Chạy ngay chính sách gộp dữ liệu cũ > 30 ngày rồi thoát")
    args = parser.parse_args()

    # Khởi tạo CSDL SQLite & Migration nếu cần
    init_sqlite_db(args.db)

    # Chạy chính sách gộp dữ liệu cũ > 30 ngày (nếu người dùng yêu cầu hoặc tự động kiểm tra)
    if args.rollup_now:
        print(f"Đang thực hiện chính sách gộp dữ liệu cũ hơn {args.retention_days} ngày trong SQLite...")
        count = rollup_old_records_sqlite(args.db, args.retention_days)
        print(f"Hoàn tất gộp dữ liệu! ({count} bản ghi thô đã được xử lý)")
        return

    # Tự động dọn dẹp / gộp dữ liệu cũ > retention_days ngày khi khởi động
    rollup_old_records_sqlite(args.db, args.retention_days)

    if args.export_now:
        print("Đang xuất dữ liệu từ CSDL SQLite sang Excel...")
        export_sqlite_to_excel(args.db, args.excel, args.include_simulated)
        print("Hoàn tất!")
        return

    print("=" * 75)
    print("   HỆ THỐNG GHI DỮ LIỆU MỰC NƯỚC IOT RA EXCEL (CSDL TỐI GIẢN V2.0)")
    print("=" * 75)
    print(f" • MQTT Broker     : {args.broker}:{args.port}")
    print(f" • Lắng nghe Topic : {args.topic}")
    print(f" • Chu kỳ lấy mẫu  : {args.interval} giây/mẫu")
    print(f" • Dải điện áp hợp lệ: {args.volt_min}V - {args.volt_max}V")
    print(f" • Chính sách gộp  : Dữ liệu cũ > {args.retention_days} ngày gộp theo giờ")
    print(f" • Múi giờ chuẩn   : UTC+7 (Việt Nam)")
    print(f" • CSDL SQLite     : {args.db}")
    print(f" • File Excel      : {args.excel}")
    print("=" * 75)
    print(" [INFO] Nhấn Ctrl + C để dừng chương trình bất cứ lúc nào.")
    print("=" * 75)

    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f" ✔ ĐÃ KẾT NỐI TỚI BROKER '{args.broker}' THÀNH CÔNG!")
            client.subscribe(args.topic)
            print(f" ✔ Đã đăng ký lắng nghe dữ liệu từ kênh: '{args.topic}'\n")
        else:
            print(f" ✘ Kết nối Broker thất bại, mã lỗi: {rc}")

    def on_message(client, userdata, msg):
        global g_last_saved_time, g_packet_count, g_saved_count, g_last_record_for_rate
        now_epoch_ms = int(time.time() * 1000)
        now_dt = datetime.fromtimestamp(now_epoch_ms / 1000.0, tz=VN_TZ)
        g_packet_count += 1

        payload_str = msg.payload.decode('utf-8', errors='ignore')

        # Throttling
        if (time.time() - g_last_saved_time) < args.interval:
            return

        g_last_saved_time = time.time()
        g_saved_count += 1

        try:
            data = json.loads(payload_str)
            level = float(data.get("level", 0.0))
            volt = float(data.get("volt", 0.0))
            is_sim = bool(data.get("is_simulated", False))

            # Kiểm tra lỗi cảm biến dựa trên dải điện áp hợp lệ
            is_voltage_err = bool(volt < args.volt_min or volt > args.volt_max)

            # Tính tốc độ dâng/rút nước tức thời (chỉ tính khi mẫu trước và nay không bị lỗi)
            rate_cm_h = 0.0
            if g_last_record_for_rate and not is_voltage_err:
                dt_sec = (now_epoch_ms - g_last_record_for_rate['timestamp']) / 1000.0
                if dt_sec >= 1.0:
                    rate_cm_h = ((level - g_last_record_for_rate['level']) / dt_sec) * 3600.0
            if not is_voltage_err:
                g_last_record_for_rate = {'timestamp': now_epoch_ms, 'level': level}

            # LƯU VÀO CSDL TỐI GIẢN (KÈM CỜ IS_ERROR)
            record = {
                "timestamp": now_epoch_ms,
                "volt": volt,
                "water_level_cm": level,
                "is_simulated": is_sim,
                "is_error": is_voltage_err,
                "is_aggregated": False,
                "sample_count": 1,
                "calibration_version": "1.0"
            }

            save_to_sqlite(args.db, record)

            sim_label = "[TEST]" if is_sim else "[THẬT]"
            err_label = " ⚠️ [LỖI CẢM BIẾN]" if is_voltage_err else ""
            rate_str = f"{rate_cm_h:+5.1f} cm/h"
            print(f" [{now_dt.strftime('%d/%m/%Y %H:%M:%S')}] #{g_saved_count:04d} {sim_label}{err_label} | "
                  f"Mực nước: {level:5.1f} cm | "
                  f"Tốc độ: {rate_str} | "
                  f"Volt: {volt:4.2f} V")

        except Exception as e:
            print(f" [LỖI JSON] Không phân tích được: {payload_str} ({e})")

    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"logger_v2_{int(time.time())}")
    except AttributeError:
        client = mqtt.Client(client_id=f"logger_v2_{int(time.time())}")

    client.on_connect = on_connect
    client.on_message = on_message

    flusher_thread = threading.Thread(
        target=excel_flusher_task,
        args=(args.db, args.excel, args.flush, args.include_simulated),
        daemon=True
    )
    flusher_thread.start()

    def handle_exit(sig, frame):
        global g_is_running
        print("\n\n [DỪNG TIẾN TRÌNH] Đang hoàn tất ghi dữ liệu cuối cùng vào Excel...")
        g_is_running = False
        client.loop_stop()
        client.disconnect()
        export_sqlite_to_excel(args.db, args.excel, args.include_simulated)
        print(" ✔ Toàn bộ dữ liệu đã được bảo lưu an toàn!")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

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
