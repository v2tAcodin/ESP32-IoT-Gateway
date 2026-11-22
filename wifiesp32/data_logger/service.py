"""
========================================================================================
HỆ THỐNG GIÁM SÁT MỰC NƯỚC IOT THỦY VĂN (BACKEND SERVICE CHUẨN V3.0)
========================================================================================
Bao gồm 3 thành phần chạy tích hợp:
1. MQTT Background Worker: Thu thập dữ liệu từ broker, kiểm duyệt tin, lưu vào SQLite.
2. SQLite Database Manager: WAL mode, migration v3.0, lưu trữ thời gian received_at (UTC).
3. Flask REST API Server: Cung cấp API cho Web Dashboard, Downsampling, Gap detection, Export.
========================================================================================
"""

import os
import sys
import time
import math
import json
import shutil
import sqlite3
import threading
import logging
from datetime import datetime, timezone, timedelta
import io

from dotenv import load_dotenv
import paho.mqtt.client as mqtt
import pandas as pd
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S'
)

# Nạp file cấu hình .env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "my_iot_project/stm32_sensor_data")
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "").strip() or None
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "").strip() or None
MQTT_USE_TLS = os.getenv("MQTT_USE_TLS", "false").lower() in ("true", "1", "yes")

TIMEOUT_MINUTES = float(os.getenv("TIMEOUT_MINUTES", 10.0))
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 5000))
DB_PATH = os.path.join(BASE_DIR, os.getenv("DB_PATH", "rainfall_data.db"))

# Múi giờ Việt Nam (UTC+7)
VN_TZ = timezone(timedelta(hours=7))

# Khóa luồng cho Database và Cache
g_db_lock = threading.Lock()
g_cache_lock = threading.Lock()
g_last_msg_cache = {"topic": None, "payload": None, "time": 0.0}
g_is_running = True

# ======================================================================================
# 1. QUẢN LÝ CƠ SỞ DỮ LIỆU SQLITE (WAL MODE & AUTO-MIGRATION V3.0)
# ======================================================================================

def get_db_connection():
    """Khởi tạo kết nối SQLite kích hoạt WAL mode và chế độ Row-factory"""
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """
    Khởi tạo bảng measurements chuẩn v3.0 và chạy di trú an toàn từ schema cũ (v1/v2).
    Schema mới gồm: id, received_at, level_cm, volt, percent, press_bar, raw_adc, is_simulated, created_at
    """
    with g_db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='measurements'")
        table_exists = cursor.fetchone() is not None

        if table_exists:
            cursor.execute("PRAGMA table_info(measurements)")
            cols = [col[1] for col in cursor.fetchall()]

            # Nếu bảng cũ thiếu received_at hoặc level_cm -> Chạy di trú
            if "received_at" not in cols or "level_cm" not in cols:
                logging.info("[MIGRATION] Phát hiện CSDL cũ. Đang tự động di trú sang schema v3.0...")
                cursor.execute('''
                    CREATE TABLE measurements_v3 (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        received_at INTEGER NOT NULL,
                        level_cm REAL NOT NULL,
                        volt REAL NOT NULL,
                        percent REAL NOT NULL,
                        press_bar REAL NOT NULL,
                        raw_adc INTEGER NOT NULL,
                        is_simulated INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                level_col = "water_level_cm" if "water_level_cm" in cols else ("level" if "level" in cols else "0.0")
                ts_col = "timestamp" if "timestamp" in cols else "(strftime('%s', datetime_str) * 1000)"
                sim_col = "is_simulated" if "is_simulated" in cols else "0"

                cursor.execute(f'''
                    INSERT INTO measurements_v3 (id, received_at, level_cm, volt, percent, press_bar, raw_adc, is_simulated, created_at)
                    SELECT 
                        id,
                        CAST({ts_col} AS INTEGER),
                        CAST({level_col} AS REAL),
                        CAST(volt AS REAL),
                        ROUND((CAST({level_col} AS REAL) / 500.0) * 100.0, 1),
                        ROUND(CAST({level_col} AS REAL) / 1019.72, 3),
                        CAST((CAST(volt AS REAL) / 3.3) * 4095 AS INTEGER),
                        {sim_col},
                        CURRENT_TIMESTAMP
                    FROM measurements
                ''')

                cursor.execute("DROP TABLE measurements")
                cursor.execute("ALTER TABLE measurements_v3 RENAME TO measurements")
                logging.info("[MIGRATION] Hoàn tất di trú! Toàn bộ số liệu lịch sử đã được bảo toàn an toàn.")
        else:
            cursor.execute('''
                CREATE TABLE measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    received_at INTEGER NOT NULL,
                    level_cm REAL NOT NULL,
                    volt REAL NOT NULL,
                    percent REAL NOT NULL,
                    press_bar REAL NOT NULL,
                    raw_adc INTEGER NOT NULL,
                    is_simulated INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            logging.info("[CSDL] Khởi tạo bảng measurements v3.0 thành công.")

        # Tạo Index phục vụ tối ưu hóa truy vấn thời gian và nguồn dữ liệu
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_received_at ON measurements(received_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_simulated ON measurements(is_simulated);")

        conn.commit()
        conn.close()


# ======================================================================================
# 2. TIẾN TRÌNH MQTT NGẦM (DEDUPLICATION, VALIDATION, RETRY VỚI EXPONENTIAL BACKOFF)
# ======================================================================================

def process_mqtt_message(topic, payload_str):
    """Kiểm duyệt bản tin, parse JSON, lọc trùng 1s và lưu vào SQLite"""
    now_epoch_ms = int(time.time() * 1000)

    # 1. Lọc trùng nhẹ (Deduplication): Bỏ qua bản tin cùng topic, cùng payload trong < 1.0 giây
    with g_cache_lock:
        now_sec = time.time()
        if (g_last_msg_cache["topic"] == topic and 
            g_last_msg_cache["payload"] == payload_str and 
            (now_sec - g_last_msg_cache["time"]) < 1.0):
            logging.debug(f"[DEDUP] Bỏ qua gói tin trùng lặp trong < 1.0s trên topic: '{topic}'")
            return
        g_last_msg_cache["topic"] = topic
        g_last_msg_cache["payload"] = payload_str
        g_last_msg_cache["time"] = now_sec

    # 2. Parse JSON & Xác thực tính toàn vẹn của dữ liệu trong try/except
    try:
        data = json.loads(payload_str)
        if not isinstance(data, dict):
            raise ValueError("Payload không phải là đối tượng JSON")

        # Kiểm tra 5 trường bắt buộc nhận từ cảm biến
        required_fields = ["level", "volt", "percent", "press", "raw"]
        for f in required_fields:
            if f not in data or data[f] is None:
                raise ValueError(f"Thiếu trường bắt buộc '{f}' trong payload")

        level = float(data["level"])
        volt = float(data["volt"])
        percent = float(data["percent"])
        press = float(data["press"])
        raw = int(data["raw"])

        # Kiểm tra NaN / Inf
        for val, name in [(level, "level"), (volt, "volt"), (percent, "percent"), (press, "press")]:
            if math.isnan(val) or math.isinf(val):
                raise ValueError(f"Giá trị của '{name}' là NaN hoặc Infinity")

        # Kiểm tra giá trị raw ADC (phải trong dải 0 - 4095)
        if not (0 <= raw <= 4095):
            raise ValueError(f"Giá trị raw ADC ({raw}) ngoài dải hợp lệ [0, 4095]")

        is_simulated = 1 if bool(data.get("is_simulated", False)) else 0

        # Lưu chính xác giá trị firmware gửi vào SQLite (received_at = giờ server lúc nhận)
        with g_db_lock:
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO measurements (
                    received_at, level_cm, volt, percent, press_bar, raw_adc, is_simulated
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (now_epoch_ms, level, volt, percent, press, raw, is_simulated))
            conn.commit()
            conn.close()

        dt_vn = datetime.fromtimestamp(now_epoch_ms / 1000.0, tz=VN_TZ)
        tag = "[TEST]" if is_simulated else "[THẬT]"
        logging.info(f"[{dt_vn.strftime('%d/%m/%Y %H:%M:%S')}] {tag} Mực nước: {level:5.1f}cm | Volt: {volt:4.2f}V | ADC: {raw:4d}")

    except Exception as e:
        logging.warning(f"[DROP BẢN TIN LỖI] {e} | Payload thô: '{payload_str}'")


def mqtt_worker_loop():
    """Vòng lặp MQTT client chạy ngầm, tự động kết nối lại với Exponential Backoff (1s -> 60s)"""
    global g_is_running
    backoff = 1
    max_backoff = 60

    while g_is_running:
        client = None
        try:
            client_id = f"backend_logger_{int(time.time())}"
            try:
                client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
            except AttributeError:
                client = mqtt.Client(client_id=client_id)

            if MQTT_USERNAME:
                client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
            if MQTT_USE_TLS:
                client.tls_set()

            def on_connect(c, userdata, flags, rc, props=None):
                nonlocal backoff
                if rc == 0:
                    logging.info(f"✔ ĐÃ KẾT NỐI TỚI MQTT BROKER: {MQTT_BROKER}:{MQTT_PORT}")
                    c.subscribe(MQTT_TOPIC)
                    logging.info(f"✔ Đang lắng nghe dữ liệu liên tục trên topic: '{MQTT_TOPIC}'")
                    backoff = 1 # Reset backoff khi kết nối thành công
                else:
                    logging.error(f"✘ Kết nối MQTT Broker thất bại, mã lỗi: {rc}")

            def on_message(c, userdata, msg):
                payload_str = msg.payload.decode('utf-8', errors='ignore')
                process_mqtt_message(msg.topic, payload_str)

            client.on_connect = on_connect
            client.on_message = on_message

            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            client.loop_forever()

        except Exception as e:
            if not g_is_running:
                break
            logging.error(f"[MQTT ERROR] Mất kết nối ({e}). Thử lại sau {backoff} giây...")
            time.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
        finally:
            if client:
                try:
                    client.disconnect()
                except Exception:
                    pass


# ======================================================================================
# 3. FLASK REST API SERVER (PHỤC VỤ DASHBOARD, THỐNG KÊ, BIỂU ĐỒ & XUẤT BÁO CÁO)
# ======================================================================================

app = Flask(__name__)
CORS(app)  # Bật CORS cho phép Dashboard gọi API từ bất kỳ nguồn nào

@app.route('/api/status', methods=['GET'])
def get_status():
    """
    Kiểm tra trạng thái hệ thống:
    Trả về Online hoặc Mất dữ liệu nếu quá timeout_minutes (mặc định 10 phút) không có mẫu mới.
    """
    timeout_min = request.args.get('timeout_min', default=TIMEOUT_MINUTES, type=float)
    now_ms = int(time.time() * 1000)

    with g_db_lock:
        conn = get_db_connection()
        # Lấy mẫu thật mới nhất
        row = conn.execute('SELECT * FROM measurements WHERE is_simulated = 0 ORDER BY received_at DESC LIMIT 1').fetchone()
        if not row:
            # Fallback nếu chưa có mẫu thật nào thì lấy mẫu mới nhất bất kỳ
            row = conn.execute('SELECT * FROM measurements ORDER BY received_at DESC LIMIT 1').fetchone()
        conn.close()

    if row:
        last_received_at = row['received_at']
        elapsed_sec = max(0.0, (now_ms - last_received_at) / 1000.0)
        is_online = (elapsed_sec <= (timeout_min * 60.0))
        dt_vn = datetime.fromtimestamp(last_received_at / 1000.0, tz=VN_TZ)
        last_received_str = dt_vn.strftime('%d/%m/%Y %H:%M:%S')

        latest_data = {
            "id": row['id'],
            "received_at": last_received_at,
            "datetime_str": last_received_str,
            "level_cm": round(row['level_cm'], 1),
            "volt": round(row['volt'], 2),
            "percent": round(row['percent'], 1),
            "press_bar": round(row['press_bar'], 3),
            "raw_adc": row['raw_adc'],
            "is_simulated": bool(row['is_simulated'])
        }
    else:
        last_received_at = None
        elapsed_sec = None
        is_online = False
        last_received_str = "Chưa có dữ liệu"
        latest_data = None

    status_text = "Online" if is_online else "Mất dữ liệu"

    return jsonify({
        "status": status_text,
        "is_online": is_online,
        "timeout_minutes": timeout_min,
        "elapsed_seconds": round(elapsed_sec, 1) if elapsed_sec is not None else None,
        "last_received_at": last_received_at,
        "last_received_str": last_received_str,
        "server_time_utc": now_ms,
        "latest_measurement": latest_data
    })


@app.route('/api/measurements', methods=['GET'])
def get_measurements():
    """
    Truy vấn danh sách mẫu đo có phân trang, lọc theo thời gian và nguồn dữ liệu.
    Tự động tính tốc độ thay đổi mực nước (cm/h) giữa các mẫu liên tiếp.
    """
    from_ts = request.args.get('from', type=int)
    to_ts = request.args.get('to', type=int)
    limit = min(request.args.get('limit', default=50, type=int), 1000)
    offset = max(0, request.args.get('offset', default=0, type=int))
    include_sim = request.args.get('include_simulated', default=0, type=int)
    sort_order = request.args.get('sort', default='desc', type=str).lower()
    if sort_order not in ('asc', 'desc'):
        sort_order = 'desc'

    conditions = ["1=1"]
    params = []

    if not include_sim:
        conditions.append("is_simulated = 0")
    if from_ts is not None:
        conditions.append("received_at >= ?")
        params.append(from_ts)
    if to_ts is not None:
        conditions.append("received_at <= ?")
        params.append(to_ts)

    where_clause = " WHERE " + " AND ".join(conditions)

    with g_db_lock:
        conn = get_db_connection()
        total = conn.execute(f"SELECT COUNT(*) FROM measurements {where_clause}", params).fetchone()[0]
        query = f"SELECT * FROM measurements {where_clause} ORDER BY received_at {sort_order} LIMIT ? OFFSET ?"
        rows = conn.execute(query, params + [limit, offset]).fetchall()
        conn.close()

    data_list = []
    for r in rows:
        dt_vn = datetime.fromtimestamp(r['received_at'] / 1000.0, tz=VN_TZ)
        data_list.append({
            "id": r['id'],
            "received_at": r['received_at'],
            "datetime_str": dt_vn.strftime('%d/%m/%Y %H:%M:%S'),
            "level_cm": round(r['level_cm'], 1),
            "volt": round(r['volt'], 2),
            "percent": round(r['percent'], 1),
            "press_bar": round(r['press_bar'], 3),
            "raw_adc": r['raw_adc'],
            "is_simulated": bool(r['is_simulated']),
            "rate_cm_h": 0.0
        })

    # Tính tốc độ thay đổi mực nước (cm/h) giữa các bản ghi liên tiếp
    for i in range(len(data_list) - 1):
        curr = data_list[i]
        next_r = data_list[i + 1]
        dt_sec = abs(curr['received_at'] - next_r['received_at']) / 1000.0
        if dt_sec >= 1.0:
            if sort_order == 'desc':
                d_level = curr['level_cm'] - next_r['level_cm']
            else:
                d_level = next_r['level_cm'] - curr['level_cm']
            rate = (d_level / dt_sec) * 3600.0
            curr['rate_cm_h'] = round(rate, 1)

    return jsonify({
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": data_list
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Thống kê tổng số mẫu, mẫu hợp lệ, mẫu lỗi, giá trị trung bình, Max và Min kèm thời điểm UTC+7.
    Loại trừ hoàn toàn các mẫu nghi lỗi cảm biến (ngoài dải volt/level) ra khỏi Max/Min/Avg.
    """
    from_ts = request.args.get('from', type=int)
    to_ts = request.args.get('to', type=int)
    include_sim = request.args.get('include_simulated', default=0, type=int)
    volt_min = request.args.get('volt_min', default=0.08, type=float)
    volt_max = request.args.get('volt_max', default=3.35, type=float)
    level_min = request.args.get('level_min', default=0.0, type=float)
    level_max = request.args.get('level_max', default=500.0, type=float)

    conditions = ["1=1"]
    params = []

    if not include_sim:
        conditions.append("is_simulated = 0")
    if from_ts is not None:
        conditions.append("received_at >= ?")
        params.append(from_ts)
    if to_ts is not None:
        conditions.append("received_at <= ?")
        params.append(to_ts)

    where_clause = " WHERE " + " AND ".join(conditions)

    with g_db_lock:
        conn = get_db_connection()
        rows = conn.execute(f"SELECT * FROM measurements {where_clause} ORDER BY received_at ASC", params).fetchall()
        conn.close()

    total_count = len(rows)
    if total_count == 0:
        return jsonify({
            "total_samples": 0, "valid_samples": 0, "error_samples": 0,
            "avg_level_cm": 0.0, "max_level_cm": 0.0, "max_time_str": "--/--/---- --:--:--",
            "min_level_cm": 0.0, "min_time_str": "--/--/---- --:--:--"
        })

    # Lọc mẫu hợp lệ
    valid_rows = [
        r for r in rows
        if (volt_min <= r['volt'] <= volt_max and level_min <= r['level_cm'] <= level_max)
    ]
    error_count = total_count - len(valid_rows)

    if not valid_rows:
        return jsonify({
            "total_samples": total_count, "valid_samples": 0, "error_samples": error_count,
            "avg_level_cm": 0.0, "max_level_cm": 0.0, "max_time_str": "--/--/---- --:--:--",
            "min_level_cm": 0.0, "min_time_str": "--/--/---- --:--:--"
        })

    sum_level = sum(r['level_cm'] for r in valid_rows)
    avg_level = round(sum_level / len(valid_rows), 1)

    max_rec = max(valid_rows, key=lambda r: r['level_cm'])
    min_rec = min(valid_rows, key=lambda r: r['level_cm'])

    max_dt = datetime.fromtimestamp(max_rec['received_at'] / 1000.0, tz=VN_TZ)
    min_dt = datetime.fromtimestamp(min_rec['received_at'] / 1000.0, tz=VN_TZ)

    return jsonify({
        "total_samples": total_count,
        "valid_samples": len(valid_rows),
        "error_samples": error_count,
        "avg_level_cm": avg_level,
        "max_level_cm": round(max_rec['level_cm'], 1),
        "max_time_str": max_dt.strftime('%d/%m/%Y %H:%M:%S'),
        "max_timestamp": max_rec['received_at'],
        "min_level_cm": round(min_rec['level_cm'], 1),
        "min_time_str": min_dt.strftime('%d/%m/%Y %H:%M:%S'),
        "min_timestamp": min_rec['received_at']
    })


@app.route('/api/series', methods=['GET'])
def get_series():
    """
    Downsample dữ liệu cho biểu đồ (min, max, avg).
    Tự động phát hiện gap (> 2 lần chu kỳ trung bình) và chèn điểm null để ngắt đường vẽ.
    """
    from_ts = request.args.get('from', type=int)
    to_ts = request.args.get('to', type=int)
    include_sim = request.args.get('include_simulated', default=0, type=int)

    conditions = ["1=1"]
    params = []
    if not include_sim:
        conditions.append("is_simulated = 0")
    if from_ts is not None:
        conditions.append("received_at >= ?")
        params.append(from_ts)
    if to_ts is not None:
        conditions.append("received_at <= ?")
        params.append(to_ts)

    where_clause = " WHERE " + " AND ".join(conditions)

    with g_db_lock:
        conn = get_db_connection()
        rows = conn.execute(f"SELECT received_at, level_cm, volt FROM measurements {where_clause} ORDER BY received_at ASC", params).fetchall()
        conn.close()

    if not rows:
        return jsonify({"labels": [], "levels": [], "volts": [], "total_points": 0})

    n = len(rows)
    timestamps = [r['received_at'] for r in rows]
    levels = [r['level_cm'] for r in rows]
    volts = [r['volt'] for r in rows]

    # Tính chu kỳ trung bình T_avg giữa các mẫu
    if n > 1:
        total_span_sec = (timestamps[-1] - timestamps[0]) / 1000.0
        t_avg_sec = total_span_sec / (n - 1)
        gap_threshold_sec = max(10.0, t_avg_sec * 2.0)
    else:
        gap_threshold_sec = 60.0

    # Downsample nếu số điểm > 1500 để biểu đồ không bị lag
    target_points = 800
    if n > 1500:
        bucket_size = math.ceil(n / target_points)
        downsampled_ts = []
        downsampled_levels = []
        downsampled_volts = []

        for i in range(0, n, bucket_size):
            chunk_ts = timestamps[i:i + bucket_size]
            chunk_lvl = levels[i:i + bucket_size]
            chunk_v = volts[i:i + bucket_size]

            avg_ts = int(sum(chunk_ts) / len(chunk_ts))
            avg_lvl = round(sum(chunk_lvl) / len(chunk_lvl), 1)
            avg_v = round(sum(chunk_v) / len(chunk_v), 2)

            downsampled_ts.append(avg_ts)
            downsampled_levels.append(avg_lvl)
            downsampled_volts.append(avg_v)

        pts_ts = downsampled_ts
        pts_lvl = downsampled_levels
        pts_v = downsampled_volts
    else:
        pts_ts = timestamps
        pts_lvl = levels
        pts_v = volts

    # Chèn điểm null khi phát hiện GAP (> gap_threshold_sec) để Chart.js ngắt đường vẽ
    final_labels = []
    final_levels = []
    final_volts = []

    for i in range(len(pts_ts)):
        if i > 0:
            dt_sec = (pts_ts[i] - pts_ts[i - 1]) / 1000.0
            if dt_sec > gap_threshold_sec:
                # Chèn null làm gap
                mid_ts = pts_ts[i - 1] + int(dt_sec * 500)
                mid_dt = datetime.fromtimestamp(mid_ts / 1000.0, tz=VN_TZ)
                final_labels.append(mid_dt.strftime('%H:%M:%S\n%d/%m'))
                final_levels.append(None)
                final_volts.append(None)

        dt_vn = datetime.fromtimestamp(pts_ts[i] / 1000.0, tz=VN_TZ)
        final_labels.append(dt_vn.strftime('%H:%M:%S\n%d/%m'))
        final_levels.append(pts_lvl[i])
        final_volts.append(pts_v[i])

    return jsonify({
        "labels": final_labels,
        "levels": final_levels,
        "volts": final_volts,
        "total_points": n
    })


@app.route('/api/simulate', methods=['POST'])
def create_simulated_samples():
    """Tạo nhanh 50 mẫu thử nghiệm giả lập (is_simulated = 1) vào CSDL SQLite"""
    body = request.get_json(silent=True) or {}
    count = int(body.get('count', 50))
    count = max(1, min(count, 500))

    now_ms = int(time.time() * 1000)
    samples = []

    for i in range(count):
        # Mẫu cách nhau 2 giây lùi dần về quá khứ
        sample_ts = now_ms - ((count - i) * 2000)
        # Giả lập mức nước dao động sin từ 50cm đến 140cm
        sim_level = 90.0 + math.sin(i * 0.2) * 45.0
        sim_level = max(0.0, min(500.0, sim_level))
        sim_volt = 0.12 + (sim_level / 500.0) * (3.30 - 0.12)
        sim_percent = (sim_level / 500.0) * 100.0
        sim_press = sim_level / 1019.72
        sim_raw = int((sim_volt / 3.3) * 4095)

        samples.append((
            sample_ts,
            round(sim_level, 1),
            round(sim_volt, 2),
            round(sim_percent, 1),
            round(sim_press, 3),
            sim_raw,
            1  # is_simulated = 1
        ))

    with g_db_lock:
        conn = get_db_connection()
        conn.executemany('''
            INSERT INTO measurements (
                received_at, level_cm, volt, percent, press_bar, raw_adc, is_simulated
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', samples)
        conn.commit()
        conn.close()

    logging.info(f"[SIMULATE] Đã nạp thành công {count} mẫu giả lập vào SQLite.")
    return jsonify({"success": True, "inserted": count})


@app.route('/api/import/indexeddb', methods=['POST'])
def import_from_indexeddb():
    """Nhập một lần toàn bộ bản ghi cũ từ IndexedDB vào backend SQLite"""
    body = request.get_json(silent=True) or {}
    records = body.get('records', [])

    if not records:
        return jsonify({"success": False, "message": "Không có bản ghi nào để nhập"}), 400

    imported = 0
    with g_db_lock:
        conn = get_db_connection()
        for r in records:
            ts = int(r.get('timestamp') or r.get('received_at') or int(time.time()*1000))
            lvl = float(r.get('water_level_cm') or r.get('level') or 0.0)
            v = float(r.get('volt') or 0.0)
            pct = float(r.get('percent') or ((lvl / 500.0) * 100.0))
            press = float(r.get('press_bar') or (lvl / 1019.72))
            raw = int(r.get('raw_adc') or r.get('raw') or int((v / 3.3) * 4095))
            is_sim = 1 if bool(r.get('is_simulated', False)) else 0

            conn.execute('''
                INSERT INTO measurements (
                    received_at, level_cm, volt, percent, press_bar, raw_adc, is_simulated
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ts, round(lvl, 1), round(v, 2), round(pct, 1), round(press, 3), raw, is_sim))
            imported += 1

        conn.commit()
        conn.close()

    logging.info(f"[IMPORT] Đã nhập {imported} bản ghi từ IndexedDB vào backend SQLite thành công.")
    return jsonify({"success": True, "imported": imported})


@app.route('/api/database/clear', methods=['POST'])
def clear_database():
    """
    Xóa toàn bộ CSDL SQLite:
    Yêu cầu gửi body {"confirm": "XOA"}.
    Tự động tạo file backup trước khi xóa để phòng mất dữ liệu.
    """
    body = request.get_json(silent=True) or {}
    confirm_text = body.get('confirm', '').strip().upper()

    if confirm_text != "XOA":
        return jsonify({"success": False, "message": "Xác nhận không hợp lệ. Phải nhập đúng 'XOA'!"}), 400

    # 1. Tạo file backup SQLite trước khi xóa
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"rainfall_data_backup_{timestamp_str}.db"
    backup_path = os.path.join(BASE_DIR, backup_filename)

    with g_db_lock:
        if os.path.exists(DB_PATH):
            shutil.copy2(DB_PATH, backup_path)
            logging.info(f"[BACKUP] Đã tự động tạo bản sao lưu CSDL trước khi xóa: {backup_filename}")

        # 2. Xóa toàn bộ dữ liệu trong bảng measurements
        conn = get_db_connection()
        conn.execute("DELETE FROM measurements")
        conn.commit()
        conn.close()

        # Thu gọn file CSDL (VACUUM ở chế độ autocommit)
        try:
            vac_conn = sqlite3.connect(DB_PATH, isolation_level=None)
            vac_conn.execute("VACUUM")
            vac_conn.close()
        except Exception as e:
            logging.debug(f"[VACUUM] {e}")

    logging.info("[CSDL] Đã xóa sạch dữ liệu bảng measurements thành công!")
    return jsonify({
        "success": True,
        "message": "Đã tạo bản sao lưu và xóa sạch cơ sở dữ liệu thành công!",
        "backup_filename": backup_filename,
        "backup_download_url": f"/api/backup/download/{backup_filename}"
    })


@app.route('/api/backup/download/<filename>', methods=['GET'])
def download_backup_file(filename):
    """Tải về bản sao lưu CSDL SQLite"""
    file_path = os.path.join(BASE_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    return jsonify({"error": "File backup không tồn tại"}), 404


@app.route('/api/export.csv', methods=['GET'])
def export_csv():
    """Xuất CSV kèm UTF-8 BOM để Excel đọc đúng tiếng Việt không bị lỗi font"""
    include_sim = request.args.get('include_simulated', default=0, type=int)
    from_ts = request.args.get('from', type=int)
    to_ts = request.args.get('to', type=int)

    conditions = ["1=1"]
    params = []
    if not include_sim:
        conditions.append("is_simulated = 0")
    if from_ts is not None:
        conditions.append("received_at >= ?")
        params.append(from_ts)
    if to_ts is not None:
        conditions.append("received_at <= ?")
        params.append(to_ts)

    where_clause = " WHERE " + " AND ".join(conditions)

    with g_db_lock:
        conn = get_db_connection()
        query = f"SELECT * FROM measurements{where_clause} ORDER BY received_at ASC"
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

    if df.empty:
        df = pd.DataFrame(columns=["Thông Báo"])
        df.loc[0] = ["Không có dữ liệu phù hợp để xuất"]
    else:
        # Chuyển đổi timestamp sang chuỗi giờ Việt Nam (UTC+7)
        dt_vns = [datetime.fromtimestamp(ts / 1000.0, tz=VN_TZ) for ts in df['received_at']]
        df.insert(1, "Thời Gian Nhận (UTC+7)", [dt.strftime('%d/%m/%Y %H:%M:%S') for dt in dt_vns])

        # Tính tốc độ thay đổi mực nước (cm/h)
        rates = [0.0]
        ts_vals = df['received_at'].values
        lvl_vals = df['level_cm'].values
        for i in range(1, len(ts_vals)):
            dt_sec = (ts_vals[i] - ts_vals[i - 1]) / 1000.0
            if dt_sec >= 1.0:
                rate = ((lvl_vals[i] - lvl_vals[i - 1]) / dt_sec) * 3600.0
                rates.append(round(rate, 1))
            else:
                rates.append(0.0)
        df.insert(3, "Tốc Độ Thay Đổi (cm/h)", rates)

        df['Nguồn Dữ Liệu'] = df['is_simulated'].apply(lambda s: "Giả lập (Test)" if s == 1 else "Thật (Cảm biến)")
        df.rename(columns={
            "received_at": "Timestamp UTC (ms)",
            "level_cm": "Mực Nước (cm)",
            "volt": "Điện Áp Cảm Biến (V)",
            "percent": "Tỷ Lệ Cột Nước (%)",
            "press_bar": "Áp Suất Thủy Tĩnh (Bar)",
            "raw_adc": "ADC Raw (12-bit)"
        }, inplace=True)
        df.drop(columns=["is_simulated", "created_at"], errors='ignore', inplace=True)

    csv_buffer = io.BytesIO()
    # Ghi với utf-8-sig để tự động gắn UTF-8 BOM
    csv_text = df.to_csv(index=False)
    csv_buffer.write(csv_text.encode('utf-8-sig'))
    csv_buffer.seek(0)

    return send_file(
        csv_buffer,
        mimetype="text/csv",
        as_attachment=True,
        download_name="Bao_Cao_Muc_Nuoc_Thuy_Van.csv"
    )


@app.route('/api/export.xlsx', methods=['GET'])
def export_excel():
    """Xuất file Excel chuẩn nghiên cứu gồm 3 Sheet: Dữ liệu chi tiết, Tổng hợp theo Giờ, Tổng hợp theo Ngày"""
    include_sim = request.args.get('include_simulated', default=0, type=int)
    from_ts = request.args.get('from', type=int)
    to_ts = request.args.get('to', type=int)

    conditions = ["1=1"]
    params = []
    if not include_sim:
        conditions.append("is_simulated = 0")
    if from_ts is not None:
        conditions.append("received_at >= ?")
        params.append(from_ts)
    if to_ts is not None:
        conditions.append("received_at <= ?")
        params.append(to_ts)

    where_clause = " WHERE " + " AND ".join(conditions)

    with g_db_lock:
        conn = get_db_connection()
        query = f"SELECT * FROM measurements{where_clause} ORDER BY received_at ASC"
        df_raw = pd.read_sql_query(query, conn, params=params)
        conn.close()

    excel_buffer = io.BytesIO()

    if df_raw.empty:
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            pd.DataFrame({"Thông Báo": ["Chưa có dữ liệu"]}).to_excel(writer, sheet_name="Du_Lieu", index=False)
    else:
        # 1. Tính toán cột ngày giờ UTC+7 và tốc độ dâng rút nước
        timestamps = df_raw['received_at'].values
        levels = df_raw['level_cm'].values

        rates = [0.0]
        for i in range(1, len(levels)):
            dt_sec = (timestamps[i] - timestamps[i - 1]) / 1000.0
            if dt_sec >= 1.0:
                rate = ((levels[i] - levels[i - 1]) / dt_sec) * 3600.0
                rates.append(round(rate, 1))
            else:
                rates.append(0.0)

        df_raw['rate_cm_h'] = rates

        dts = [datetime.fromtimestamp(ts / 1000.0, tz=VN_TZ) for ts in timestamps]
        df_raw['datetime_str'] = [d.strftime('%d/%m/%Y %H:%M:%S') for d in dts]
        df_raw['date_str'] = [d.strftime('%d/%m/%Y') for d in dts]
        df_raw['hour'] = [d.hour for d in dts]
        df_raw['year'] = [d.year for d in dts]
        df_raw['month'] = [d.month for d in dts]
        df_raw['day'] = [d.day for d in dts]

        # Sheet 1: Dữ liệu chi tiết
        df_sheet1 = pd.DataFrame({
            "STT": range(1, len(df_raw) + 1),
            "Thời Gian Nhận (dd/mm/yyyy HH:mm:ss UTC+7)": df_raw['datetime_str'],
            "Mực Nước (cm)": df_raw['level_cm'].round(1),
            "Tốc Độ Thay Đổi (cm/h)": df_raw['rate_cm_h'],
            "Điện Áp Cảm Biến (V)": df_raw['volt'].round(2),
            "Áp Suất Thủy Tĩnh (Bar)": df_raw['press_bar'].round(3),
            "Tỷ Lệ Cột Nước (%)": df_raw['percent'].round(1),
            "Giá Trị ADC Raw (12-bit)": df_raw['raw_adc'],
            "Nguồn Dữ Liệu": df_raw['is_simulated'].apply(lambda s: "Giả lập (Test)" if s == 1 else "Thật (Cảm biến)")
        })

        # Sheet 2: Tổng hợp theo từng Giờ
        df_hourly = df_raw.groupby(["date_str", "hour"]).agg(
            Số_Lượng_Mẫu=("level_cm", "count"),
            Mực_Nước_TB_cm=("level_cm", "mean"),
            Đỉnh_Nước_Max_cm=("level_cm", "max"),
            Đáy_Nước_Min_cm=("level_cm", "min"),
            Tốc_Độ_Dâng_Max=("rate_cm_h", "max"),
            Tốc_Độ_Rút_Max=("rate_cm_h", "min")
        ).reset_index()

        df_hourly["Biến_Thiên_Dâng_cm"] = (df_hourly["Đỉnh_Nước_Max_cm"] - df_hourly["Đáy_Nước_Min_cm"]).round(2)
        df_hourly["Mực_Nước_TB_cm"] = df_hourly["Mực_Nước_TB_cm"].round(2)

        df_sheet2 = pd.DataFrame({
            "Ngày Đo (dd/mm/yyyy)": df_hourly["date_str"],
            "Khung Giờ": df_hourly["hour"].apply(lambda h: f"{h:02d}:00 - {h:02d}:59"),
            "Số Lượng Mẫu": df_hourly["Số_Lượng_Mẫu"],
            "Mực Nước TB (cm)": df_hourly["Mực_Nước_TB_cm"],
            "Đỉnh Cao Nhất (Max cm)": df_hourly["Đỉnh_Nước_Max_cm"].round(1),
            "Thấp Nhất (Min cm)": df_hourly["Đáy_Nước_Min_cm"].round(1),
            "Biến Thiên Dâng (cm)": df_hourly["Biến_Thiên_Dâng_cm"],
            "Tốc Độ Dâng Max (cm/h)": df_hourly["Tốc_Độ_Dâng_Max"].round(1),
            "Tốc Độ Rút Max (cm/h)": df_hourly["Tốc_Độ_Rút_Max"].round(1)
        })

        # Sheet 3: Tổng hợp theo từng Ngày
        df_daily = df_raw.groupby(["date_str", "year", "month", "day"]).agg(
            Tổng_Mẫu_Ngày=("level_cm", "count"),
            Mực_Nước_TB_Ngày_cm=("level_cm", "mean"),
            Đỉnh_Nước_Ngày_Max_cm=("level_cm", "max"),
            Đáy_Nước_Ngày_Min_cm=("level_cm", "min")
        ).reset_index()

        df_daily["Biên_Độ_Ngày_cm"] = (df_daily["Đỉnh_Nước_Ngày_Max_cm"] - df_daily["Đáy_Nước_Ngày_Min_cm"]).round(2)
        df_daily["Mực_Nước_TB_Ngày_cm"] = df_daily["Mực_Nước_TB_Ngày_cm"].round(2)

        df_sheet3 = pd.DataFrame({
            "Ngày Đo (dd/mm/yyyy)": df_daily["date_str"],
            "Năm": df_daily["year"],
            "Tháng": df_daily["month"],
            "Ngày": df_daily["day"],
            "Tổng Mẫu Thu Thập": df_daily["Tổng_Mẫu_Ngày"],
            "Mực Nước TB Ngày (cm)": df_daily["Mực_Nước_TB_Ngày_cm"],
            "Đỉnh Nước Ngày (Max cm)": df_daily["Đỉnh_Nước_Ngày_Max_cm"].round(1),
            "Đáy Nước Ngày (Min cm)": df_daily["Đáy_Nước_Ngày_Min_cm"].round(1),
            "Biên Độ Biến Động (cm)": df_daily["Biên_Độ_Ngày_cm"]
        })

        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            df_sheet1.to_excel(writer, sheet_name="Du_Lieu_Chi_Tiet", index=False)
            df_sheet2.to_excel(writer, sheet_name="Tong_Hop_Theo_Gio", index=False)
            df_sheet3.to_excel(writer, sheet_name="Tong_Hop_Theo_Ngay", index=False)

    excel_buffer.seek(0)
    return send_file(
        excel_buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="Bao_Cao_Muc_Nuoc_Thuy_Van.xlsx"
    )


# ======================================================================================
# 4. ĐIỂM KHỞI CHẠY HỆ THỐNG
# ======================================================================================

def main():
    global g_is_running

    print("=" * 80)
    print("   HỆ THỐNG GIÁM SÁT MỰC NƯỚC IOT THỦY VĂN (BACKEND SERVICE V3.0)")
    print("=" * 80)
    print(f" • MQTT Broker     : {MQTT_BROKER}:{MQTT_PORT} (TLS: {MQTT_USE_TLS})")
    print(f" • Lắng nghe Topic : {MQTT_TOPIC}")
    print(f" • Timeout Mất Tin : {TIMEOUT_MINUTES} phút")
    print(f" • CSDL SQLite     : {DB_PATH} (WAL mode)")
    print(f" • REST API Server : http://localhost:{API_PORT}")
    print("=" * 80)

    # 1. Khởi tạo CSDL SQLite & Migration
    init_database()

    # 2. Khởi chạy MQTT Background Worker Thread
    mqtt_thread = threading.Thread(target=mqtt_worker_loop, daemon=True)
    mqtt_thread.start()

    # 3. Khởi chạy Flask API Server
    try:
        app.run(host=API_HOST, port=API_PORT, debug=False, use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        logging.info("\n[DỪNG HỆ THỐNG] Đang tắt các tiến trình...")
        g_is_running = False
        sys.exit(0)


if __name__ == "__main__":
    main()
