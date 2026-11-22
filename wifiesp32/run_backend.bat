@echo off
chcp 65001 >nul
title IoT Water Level Backend Service v3.0

echo =====================================================================
echo    KHỞI CHẠY BACKEND SERVICE GIÁM SÁT MỰC NƯỚC IOT THỦY VĂN
echo =====================================================================
echo.

cd /d "%~dp0data_logger"

echo [*] Đang khởi chạy service.py (MQTT Logger + REST API Port 5000)...
echo [*] Dữ liệu tự động lưu vào SQLite: rainfall_data.db
echo [*] Web Dashboard sẽ đọc dữ liệu từ http://localhost:5000
echo [*] Nhấn Ctrl + C để dừng dịch vụ bất cứ lúc nào.
echo ---------------------------------------------------------------------
echo.
python service.py

pause
