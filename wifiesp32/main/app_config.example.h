#pragma once

#include "driver/uart.h"

/*
 * ==============================================================================
 * CẤU HÌNH MẪU HỆ THỐNG ESP32-C3 CLOUD GATEWAY
 * ==============================================================================
 * Hướng dẫn: Sao chép tệp này thành "app_config.h" và điền SSID/Password Wi-Fi
 * thực tế của bạn. Tệp "app_config.h" đã được đưa vào .gitignore để không bị
 * đẩy công khai lên GitHub.
 */

// 1. CẤU HÌNH WI-FI (Băng tần 2.4 GHz)
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASS "YOUR_WIFI_PASSWORD"
// Chế độ Auto-Reconnect vô hạn: Tự động kết nối lại liên tục khi mất sóng Wi-Fi/Hotspot

// 2. CẤU HÌNH MQTT CLOUD BROKER
#define MQTT_BROKER_URI "mqtt://broker.hivemq.com:1883"
#define MQTT_TOPIC_DATA "my_iot_project/stm32_sensor_data"

// 3. CẤU HÌNH GIAO TIẾP UART VỚI STM32
#define STM32_UART_PORT UART_NUM_1
#define STM32_UART_BAUD 115200

// Chân GPIO trên ESP32-C3:
// - GPIO 4 (RX) nối PA9 (TX) của STM32
// - GPIO 5 (TX) nối PA10 (RX) của STM32
#define STM32_UART_RX_PIN (4)
#define STM32_UART_TX_PIN (5)

// Kích thước bộ đệm nhận UART (byte)
#define UART_BUF_SIZE (1024)
