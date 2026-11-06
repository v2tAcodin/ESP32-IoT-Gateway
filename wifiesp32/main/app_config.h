#pragma once

#include "driver/uart.h"

/*
 * ==============================================================================
 * CẤU HÌNH HỆ THỐNG ESP32-C3 CLOUD GATEWAY
 * ==============================================================================
 * Tách riêng file cấu hình giúp bạn dễ dàng thay đổi thông tin Wi-Fi, MQTT
 * hoặc chân kết nối mà không cần sửa sâu vào mã nguồn logic.
 */

// 1. CẤU HÌNH WI-FI
// Thay đổi thành tên và mật khẩu Wi-Fi của bạn (Lưu ý: ESP32 chỉ hỗ trợ băng
// tần 2.4GHz)
#define WIFI_SSID "Android 22.1"
#define WIFI_PASS "ngocuyenww"
#define WIFI_MAX_RETRY 10

// 2. CẤU HÌNH MQTT CLOUD BROKER
// Sử dụng HiveMQ Public Broker miễn phí, không cần đăng ký tài khoản lúc đầu
#define MQTT_BROKER_URI "mqtt://broker.hivemq.com:1883"

// Topic: Giống như một "kênh" truyền hình, ESP32 phát vào kênh này, Web sẽ mở
// kênh này để xem Hãy đổi "iot_lab_test" thành một chuỗi riêng biệt của bạn để
// tránh bị trùng với người khác trên Broker công cộng!
#define MQTT_TOPIC_DATA "my_iot_project/stm32_sensor_data"

// 3. CẤU HÌNH GIAO TIẾP UART VỚI STM32
#define STM32_UART_PORT UART_NUM_1
#define STM32_UART_BAUD 115200

// Chân GPIO trên ESP32-C3:
// - Chân RX nối vào chân TX của STM32
// - Chân TX nối vào chân RX của STM32
#define STM32_UART_RX_PIN (4)
#define STM32_UART_TX_PIN (5)

// Kích thước bộ đệm nhận UART (byte)
#define UART_BUF_SIZE (1024)
