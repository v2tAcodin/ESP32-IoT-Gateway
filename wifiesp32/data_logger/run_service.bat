@echo off
chcp 65001 >nul
title IoT Water Level Backend Service v3.0

echo =====================================================================
echo    KHỞI CHẠY BACKEND SERVICE GIÁM SÁT MỰC NƯỚC IOT THỦY VĂN
echo =====================================================================
echo.

cd /d "%~dp0"

echo [*] Kiểm tra các thư viện Python cần thiết...
python -m pip install -r requirements.txt --quiet

echo.
echo [*] Bắt đầu khởi chạy Backend Service (MQTT Logger + REST API Port 5000)...
echo [*] Nhấn Ctrl + C để dừng dịch vụ bất cứ lúc nào.
echo.
python service.py

pause
