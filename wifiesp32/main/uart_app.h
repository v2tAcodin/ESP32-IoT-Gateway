#pragma once

#include <stdint.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Khởi tạo phần cứng UART và tạo FreeRTOS Task lắng nghe dữ liệu từ STM32
 */
esp_err_t uart_app_init(void);

/**
 * @brief Lấy tổng số gói tin đã nhận từ STM32 qua UART
 */
uint32_t uart_app_get_rx_count(void);

#ifdef __cplusplus
}
#endif

