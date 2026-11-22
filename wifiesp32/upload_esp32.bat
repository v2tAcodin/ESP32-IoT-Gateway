@echo off
chcp 65001 >nul
echo ===================================================
echo   TIẾN TRÌNH BIÊN DỊCH VÀ NẠP FIRMWARE ESP32-C3
echo ===================================================
echo Đang tìm kiếm PlatformIO CLI...

set PIO_EXE=%USERPROFILE%\.platformio\penv\Scripts\pio.exe

if not exist "%PIO_EXE%" (
    echo [LỖI] Không tìm thấy PlatformIO tại %PIO_EXE%
    pause
    exit /b 1
)

cd /d "%~dp0"

echo [1/2] Đang nạp firmware vào ESP32 (cổng COM7)...
"%PIO_EXE%" run -t upload

if %ERRORLEVEL% equ 0 (
    echo ===================================================
    echo [THÀNH CÔNG] ĐÃ NẠP CODE XONG VÀO ESP32-C3!
    echo ===================================================
    echo Đang mở Serial Monitor để xem log kết nối Wi-Fi...
    echo (Nhấn phím Ctrl + C để thoát khỏi Monitor)
    echo ---------------------------------------------------
    "%PIO_EXE%" device monitor -b 115200
) else (
    echo ===================================================
    echo [LỖI] Nạp code thất bại!
    echo Mẹo: Nhấn giữ nút BOOT trên ESP32, bấm nhả nút RESET,
    echo rồi chạy lại file này!
    echo ===================================================
    pause
)
