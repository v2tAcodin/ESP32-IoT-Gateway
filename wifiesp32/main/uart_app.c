#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/uart.h"
#include "esp_log.h"

#include "app_config.h"
#include "mqtt_app.h"
#include "uart_app.h"

static const char *TAG = "UART_APP";

/*
 * TẠI SAO LẠI CẦN TASK GOM DÒNG NÀY?
 * Dữ liệu UART được truyền dạng dòng byte liên tục (stream). Nếu đọc nguyên một
 * khối (chunk), bạn rất dễ gặp tình trạng:
 * - Nửa gói tin trước đến trong lần đọc 1
 * - Nửa gói tin sau đến trong lần đọc 2
 * Task này sẽ gom từng byte vào buffer cho đến khi bắt gặp ký tự xuống dòng '\n',
 * đảm bảo gói tin (JSON) luôn nguyên vẹn 100% trước khi đẩy lên Cloud!
 */
static void uart_rx_task(void *pvParameters)
{
    uint8_t byte_in;
    char line_buf[UART_BUF_SIZE];
    int line_idx = 0;

    ESP_LOGI(TAG, "Task lang nghe UART tu STM32 da khoi chay (RX=GPIO%d, TX=GPIO%d, Baud=%d)",
             STM32_UART_RX_PIN, STM32_UART_TX_PIN, STM32_UART_BAUD);

    while (1) {
        // Đọc từng byte từ bộ đệm UART, chờ tối đa 10ms để nhường CPU nếu không có dữ liệu
        int len = uart_read_bytes(STM32_UART_PORT, &byte_in, 1, pdMS_TO_TICKS(10));
        if (len > 0) {
            // Khi gặp ký tự kết thúc dòng '\n'
            if (byte_in == '\n') {
                line_buf[line_idx] = '\0'; // Thêm ký tự kết thúc chuỗi C

                // Cắt bỏ ký tự '\r' nếu có (trong trường hợp STM32 gửi "\r\n")
                if (line_idx > 0 && line_buf[line_idx - 1] == '\r') {
                    line_buf[line_idx - 1] = '\0';
                }

                // Kiểm tra chuỗi không rỗng
                if (strlen(line_buf) > 0) {
                    ESP_LOGI(TAG, "[UART RX] Nhan tu STM32: %s", line_buf);

                    // Đẩy dữ liệu lên Cloud qua MQTT
                    esp_err_t err = mqtt_app_publish(NULL, line_buf);
                    if (err != ESP_OK) {
                        ESP_LOGW(TAG, "Chua the day goi tin len Cloud: %s", esp_err_to_name(err));
                    }
                }

                // Reset con trỏ đệm để sẵn sàng cho gói tin tiếp theo
                line_idx = 0;
            } else {
                // Lưu byte vào bộ đệm tạm
                if (line_idx < (UART_BUF_SIZE - 1)) {
                    line_buf[line_idx++] = (char)byte_in;
                } else {
                    ESP_LOGW(TAG, "Canh bao: Bo dem UART day truoc khi gap ky tu '\\n'! Reset bo dem.");
                    line_idx = 0;
                }
            }
        }
    }
}

esp_err_t uart_app_init(void)
{
    uart_config_t uart_config = {
        .baud_rate = STM32_UART_BAUD,
        .data_bits = UART_DATA_8_BITS,
        .parity    = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };

    ESP_ERROR_CHECK(uart_param_config(STM32_UART_PORT, &uart_config));
    ESP_ERROR_CHECK(uart_set_pin(STM32_UART_PORT,
                                 STM32_UART_TX_PIN,
                                 STM32_UART_RX_PIN,
                                 UART_PIN_NO_CHANGE,
                                 UART_PIN_NO_CHANGE));

    // Cài đặt driver UART với bộ đệm RX nội bộ (RingBuffer 2048 bytes)
    ESP_ERROR_CHECK(uart_driver_install(STM32_UART_PORT, UART_BUF_SIZE * 2, 0, 0, NULL, 0));

    // Tạo FreeRTOS Task chạy ngầm để lắng nghe UART độc lập
    xTaskCreate(uart_rx_task, "uart_rx_task", 4096, NULL, 10, NULL);

    ESP_LOGI(TAG, "Module UART STM32 Bridge da khoi tao thanh cong.");
    return ESP_OK;
}

