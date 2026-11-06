#pragma once

#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Khởi tạo module Wi-Fi ở chế độ Station (STA)
 * Kết nối vào router được cấu hình trong app_config.h
 */
esp_err_t wifi_app_init(void);

/**
 * @brief Chờ cho đến khi Wi-Fi kết nối thành công và nhận được địa chỉ IP
 * @param timeout_ms Thời gian chờ tối đa (ms)
 * @return true nếu đã có IP, false nếu quá thời gian chờ (timeout)
 */
bool wifi_app_wait_for_connected(uint32_t timeout_ms);

/**
 * @brief Kiểm tra trạng thái kết nối Wi-Fi hiện tại
 */
bool wifi_app_is_connected(void);

#ifdef __cplusplus
}
#endif

