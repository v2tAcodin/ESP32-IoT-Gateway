#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nvs_flash.h"
#include "esp_log.h"

#include "app_config.h"
#include "wifi_app.h"
#include "mqtt_app.h"
#include "uart_app.h"

static const char *TAG = "MAIN_APP";

void app_main(void)
{
    ESP_LOGI(TAG, "===============================================");
    ESP_LOGI(TAG, "  ESP32-C3 STM32-TO-CLOUD GATEWAY KHOI DONG");
    ESP_LOGI(TAG, "===============================================");

    /*
     * 1. KHỞI TẠO NVS (NON-VOLATILE STORAGE)
     * Tại sao phải làm bước này?
     * Driver Wi-Fi của ESP-IDF bắt buộc phải dùng bộ nhớ Flash NVS để lưu trữ
     * các thông số hiệu chuẩn vô tuyến (RF/PHY calibration) và trạng thái mạng.
     */
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    /*
     * 2. KHỞI TẠO GIAO TIẾP UART VỚI STM32
     * Chạy task đọc UART ngay từ đầu để không bỏ lỡ dữ liệu nào từ STM32,
     * cho dù lúc này Wi-Fi chưa kết nối xong.
     */
    ESP_ERROR_CHECK(uart_app_init());

    /*
     * 3. KẾT NỐI WI-FI
     * Bật module Wi-Fi Station và gửi yêu cầu kết nối tới Router
     */
    ESP_ERROR_CHECK(wifi_app_init());

    /*
     * 4. CHỜ KẾT NỐI WI-FI THÀNH CÔNG VÀ NHẬN IP
     * Khi đã có IP từ Router thì mới bắt đầu khởi động MQTT Client
     */
    ESP_LOGI(TAG, "Dang cho ket noi Wi-Fi thanh cong de khoi tao MQTT...");
    if (wifi_app_wait_for_connected(30000)) { // Chờ tối đa 30 giây
        ESP_LOGI(TAG, "Wi-Fi da san sang! Tien hanh khoi tao MQTT Client...");
        ESP_ERROR_CHECK(mqtt_app_init());
    } else {
        ESP_LOGE(TAG, "Timeout: Khong the ket noi Wi-Fi sau 30s. Vui long kiem tra lai SSID/PASS!");
    }

    /*
     * 5. VÒNG LẶP THEO DÕI HỆ THỐNG (SYSTEM HEARTBEAT)
     * In ra log định kỳ để bạn theo dõi dung lượng RAM còn lại và trạng thái kết nối.
     */
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(10000)); // Lặp lại mỗi 10 giây
        ESP_LOGI(TAG, "[HEARTBEAT] Free Heap: %lu bytes | Wi-Fi: %s | MQTT: %s",
                 esp_get_free_heap_size(),
                 wifi_app_is_connected() ? "CONNECTED" : "DISCONNECTED",
                 mqtt_app_is_connected() ? "CONNECTED" : "DISCONNECTED");
    }
}

