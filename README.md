# ESP32-IoT-Gateway

> **Hệ thống IoT Gateway thu thập dữ liệu cảm biến từ STM32 truyền lên Cloud và giám sát thời gian thực qua Web Dashboard.**

---

## 🌟 Giới thiệu tổng quan

Dự án triển khai mô hình **IoT Gateway 3 tầng (3-Tier Hierarchical Architecture)**:
1. **Edge Sensing Node (STM32F103):** Lấy mẫu ADC 12-bit đọc điện áp biến trở (0.00V - 3.30V), lọc nhiễu trung bình 16 mẫu và đóng gói dữ liệu JSON.
2. **Wireless Gateway (ESP32-C3):** Nhận luồng UART qua FreeRTOS Task với kỹ thuật *Delimiter-based Framing* (`\n`), duy trì kết nối Wi-Fi Station và xuất bản dữ liệu lên Cloud Broker qua giao thức **MQTT**.
3. **Cloud & Presentation (HiveMQ + Web Dashboard):** Điều phối bản tin qua cơ chế Publish/Subscribe. Giao diện Web kết nối trực tiếp qua **WebSocket Secure (WSS Port 8884)**, hiển thị các thẻ thông số và vẽ đồ thị thời gian thực mượt mà bằng **Chart.js** mà không cần máy chủ Backend trung gian.

---

## 🏗️ Kiến trúc hệ thống & Luồng dữ liệu

```
[Biến Trở (PA0)] 
       │
       ▼
 ┌───────────┐      UART (115200 8N1)      ┌───────────┐      Wi-Fi (MQTT 1883)      ┌────────────────┐
 │   STM32   │ ──────────────────────────> │ ESP32-C3  │ ──────────────────────────> │  MQTT BROKER   │
 │ (Sensing) │    {"volt":2.45,"..."}\n    │ (Gateway) │    Pub/Sub JSON Payload     │ (broker.hivemq)│
 └───────────┘                             └───────────┘                             └───────┬────────┘
                                                                                             │
                                                                                    WSS 8884 │ (WebSocket)
                                                                                             ▼
                                                                                   ┌──────────────────┐
                                                                                   │  WEB DASHBOARD   │
                                                                                   │ (Real-time View) │
                                                                                   └──────────────────┘
```

---

## 🔌 Sơ đồ nối dây phần cứng (Wiring Pinout)

### 1. Biến trở ➔ STM32 Blue Pill
| Chân Biến trở | Chân STM32 | Chức năng |
| :--- | :--- | :--- |
| **Chân 1 (Bìa)** | **3.3V** | Cấp nguồn tham chiếu |
| **Chân 2 (Chân giữa - Wiper)** | **PA0** | Tín hiệu điện áp analog (ADC1_IN0) |
| **Chân 3 (Bìa)** | **GND** | Mass |

### 2. STM32 ➔ ESP32-C3 Gateway
| Chân STM32 | Chân ESP32-C3 | Chức năng |
| :--- | :--- | :--- |
| **PA9 (USART1_TX)** | **GPIO 4 (UART1_RX)** | STM32 gửi gói tin JSON sang ESP32 |
| **PA10 (USART1_RX)** | **GPIO 5 (UART1_TX)** | Dự phòng cho chiều lệnh ngược (Downlink) |
| **GND** | **GND** | **Bắt buộc nối chung Mass** |

---

## 📂 Cấu trúc thư mục

```
ESP32-IoT-Gateway/
├── wifiesp32/                  # Mã nguồn ESP32-C3 IoT Gateway (PlatformIO + ESP-IDF)
│   ├── main/
│   │   ├── app_config.h        # Cấu hình tập trung Wi-Fi, MQTT Broker, chân GPIO
│   │   ├── wifi_app.c / .h     # Module Wi-Fi Station & tự động kết nối lại
│   │   ├── mqtt_app.c / .h     # Module MQTT Client (Pub/Sub)
│   │   ├── uart_app.c / .h     # Task FreeRTOS gom dòng byte UART theo ký tự '\n'
│   │   └── main.c              # Khởi tạo NVS, UART, Wi-Fi, MQTT & Heartbeat
│   ├── components/mqtt/        # Thư viện MQTT Component nội bộ (Build Offline 100%)
│   ├── web_dashboard/
│   │   └── index.html          # Web quản trị thời gian thực (HTML5 + Tailwind + Chart.js)
│   └── platformio.ini          # Cấu hình nạp firmware ESP32-C3 Native USB CDC
│
├── stm32_sensor_node/          # Mã nguồn STM32F103 Node cảm biến (PlatformIO + STM32Cube)
│   ├── Core/
│   │   ├── Src/
│   │   │   ├── main.c          # Vòng lặp lấy mẫu ADC, tính Volt và gửi UART
│   │   │   ├── adc.c           # Cấu hình bộ ADC1 12-bit
│   │   │   ├── gpio.c          # Cấu hình GPIO và LED chỉ báo PC13
│   │   │   ├── usart.c         # Cấu hình USART1 115200 8N1
│   │   │   └── stm32f1xx_hal_msp.c # Cấu hình SWD mở liên tục cho ST-Link
│   │   └── Inc/
│   └── platformio.ini          # Cấu hình biên dịch & nạp qua ST-Link
│
├── docs/                       # Tài liệu kỹ thuật
│   ├── Bao_Cao_Kien_Truc_Mang_IoT_STM32_ESP32.docx # Báo cáo chuyên sâu định dạng Word
│   └── bao_cao_kien_truc_mang_iot.md              # Báo cáo kỹ thuật định dạng Markdown
│
└── README.md                   # Hướng dẫn chi tiết dự án
```

---

## 🚀 Hướng dẫn nạp code & chạy thử nghiệm

### 1. Chuẩn bị ESP32-C3
1. Mở file `wifiesp32/main/app_config.h`, điền tên và mật khẩu Wi-Fi của bạn:
   ```c
   #define WIFI_SSID           "TEN_WIFI"
   #define WIFI_PASS           "MAT_KHAU"
   ```
2. Cắm cáp Type-C vào ESP32-C3.
3. Mở thư mục `wifiesp32` trên VS Code với PlatformIO ➔ Bấm nút **Upload (`➔`)**.

### 2. Chuẩn bị STM32 Blue Pill
1. Cắm mạch nạp ST-Link vào máy tính và nối 4 dây SWD (`GND`, `CLK`, `DIO`, `3.3V`) vào STM32.
2. Mở thư mục `stm32_sensor_node` trên VS Code với PlatformIO ➔ Bấm nút **Upload (`➔`)**.

### 3. Xem dữ liệu trên Web Dashboard
1. Mở trực tiếp file `wifiesp32/web_dashboard/index.html` bằng Google Chrome hoặc Microsoft Edge.
2. Khi xoay biến trở, các thẻ hiển thị **Điện áp (Volt)**, **Tỷ lệ xoay (%)** và **Đồ thị thời gian thực** sẽ tự động nhảy số tức thì!

---

## 📄 Bản quyền & Tác giả
- Tác giả: **v2tAcodin**
- License: MIT License
