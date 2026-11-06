#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Khởi tạo phần cứng UART và tạo FreeRTOS Task lắng nghe dữ liệu từ STM32
 */
esp_err_t uart_app_init(void);

#ifdef __cplusplus
}
#endif

