"""
Script di trú dữ liệu từ SQLite cục bộ (rainfall_data.db) lên Supabase PostgreSQL.
Cách chạy:
  1. Cài psycopg2-binary: pip install psycopg2-binary python-dotenv
  2. Đặt biến môi trường DATABASE_URL (chuỗi Session Pooler của Supabase) hoặc lưu vào wifiesp32/data_logger/.env
  3. Chạy: python wifiesp32/data_logger/migrate_to_supabase.py
     (Mặc định chỉ chuyển dữ liệu thật is_simulated = 0; thêm --include-simulated nếu muốn chuyển cả mẫu thử)
"""
import os
import sys
import sqlite3
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]

DB_PATH = os.path.join(BASE_DIR, "rainfall_data.db")


def main():
    if not DATABASE_URL.startswith("postgresql://"):
        print("LỖI: Chưa tìm thấy biến môi trường DATABASE_URL (PostgreSQL / Supabase Session Pooler)!")
        print("Hãy đặt $env:DATABASE_URL='postgresql://...' hoặc thêm vào file wifiesp32/data_logger/.env")
        sys.exit(1)

    try:
        import psycopg2
        from psycopg2.extras import execute_values
    except ImportError:
        print("LỖI: Chưa cài psycopg2-binary. Chạy: pip install psycopg2-binary")
        sys.exit(1)

    include_sim = "--include-simulated" in sys.argv
    if not os.path.exists(DB_PATH):
        print(f"LỖI: Không tìm thấy file nguồn {DB_PATH}")
        sys.exit(1)

    sq_conn = sqlite3.connect(DB_PATH)
    where = "" if include_sim else "WHERE is_simulated = 0"
    rows = sq_conn.execute(
        f"SELECT received_at, level_cm, volt, percent, press_bar, raw_adc, is_simulated FROM measurements {where} ORDER BY received_at ASC"
    ).fetchall()
    sq_conn.close()

    print(f"Đọc được {len(rows):,} bản ghi từ SQLite ({'tất cả' if include_sim else 'chỉ dữ liệu thật'}).")
    if not rows:
        print("Không có bản ghi nào để chuyển.")
        return

    dsn = DATABASE_URL
    if "sslmode=" not in dsn:
        sep = "&" if "?" in dsn else "?"
        dsn = f"{dsn}{sep}sslmode=require"

    pg_conn = psycopg2.connect(dsn, connect_timeout=15)
    cur = pg_conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS measurements (
            id BIGSERIAL PRIMARY KEY,
            received_at BIGINT NOT NULL,
            level_cm DOUBLE PRECISION NOT NULL,
            volt DOUBLE PRECISION NOT NULL,
            percent DOUBLE PRECISION NOT NULL,
            press_bar DOUBLE PRECISION NOT NULL,
            raw_adc INTEGER NOT NULL,
            is_simulated INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cur.execute("CREATE INDEX IF NOT EXISTS idx_received_at ON measurements(received_at);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_simulated ON measurements(is_simulated);")

    # Tránh chèn trùng theo mốc received_at đã có trên Supabase
    cur.execute("SELECT received_at FROM measurements")
    existing_ts = {r[0] for r in cur.fetchall()}
    new_rows = [r for r in rows if r[0] not in existing_ts]

    print(f"Bỏ qua {len(rows) - len(new_rows):,} bản ghi đã tồn tại trên Supabase; chuẩn bị nạp {len(new_rows):,} bản ghi mới...")

    batch_size = 1000
    for i in range(0, len(new_rows), batch_size):
        batch = new_rows[i:i + batch_size]
        execute_values(
            cur,
            "INSERT INTO measurements (received_at, level_cm, volt, percent, press_bar, raw_adc, is_simulated) VALUES %s",
            batch
        )
        pg_conn.commit()
        print(f"  Đã nạp {min(i + batch_size, len(new_rows)):,} / {len(new_rows):,} bản ghi...")

    cur.execute("SELECT COUNT(*) FROM measurements")
    total_pg = cur.fetchone()[0]
    cur.close()
    pg_conn.close()
    print(f"HOÀN TẤT! Tổng số bản ghi hiện có trên Supabase PostgreSQL: {total_pg:,}")


if __name__ == "__main__":
    main()
