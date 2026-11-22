@echo off
chcp 65001 > nul
title CHƯƠNG TRÌNH GHI DỮ LIỆU LƯỢNG MƯA & MỰC NƯỚC IOT RA EXCEL
color 0A

echo ==============================================================================
echo    CHƯƠNG TRÌNH GHI DỮ LIỆU LƯỢNG MƯA & MỰC NƯỚC IOT RA EXCEL (DATABASE)
echo ==============================================================================
echo.
echo Đang kiểm tra môi trường Python...
python --version
if errorlevel 1 (
    echo.
    echo [LỖI] Máy tính chưa cài đặt Python hoặc chưa tick chọn "Add Python to PATH"!
    echo Vui lòng cài Python từ https://www.python.org/
    pause
    exit /b
)

echo.
echo Đang khởi chạy service.py (Backend Service v3.0)...
echo Dữ liệu sẽ được tự động lưu bền vững vào SQLite: rainfall_data.db
echo Cung cấp REST API tại http://localhost:5000 cho Web Dashboard
echo Nhấn Ctrl + C khi muốn dừng chương trình.
echo ==============================================================================
echo.

python "%~dp0service.py"

pause
