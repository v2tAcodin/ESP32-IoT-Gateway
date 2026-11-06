#pragma once

#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Khởi tạo và kích hoạt MQTT Client
 */
esp_err_t mqtt_app_init(void);

/**
 * @brief Đẩy một chuỗi dữ liệu (thường là JSON) lên MQTT Topic
 * @param topic Tên topic (truyền NULL để lấy mặc định MQTT_TOPIC_DATA trong app_config.h)
 * @param data Chuỗi dữ liệu kết thúc bằng ký tự null '\0'
 * @return ESP_OK nếu gửi thành công vào hàng đợi MQTT, ngược lại trả về mã lỗi
 */
esp_err_t mqtt_app_publish(const char *topic, const char *data);

/**
 * @brief Kiểm tra xem ESP32 đã kết nối tới MQTT Broker chưa
 */
bool mqtt_app_is_connected(void);

#ifdef __cplusplus
}
#endif

