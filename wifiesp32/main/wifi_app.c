#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"

#include "app_config.h"
#include "wifi_app.h"

static const char *TAG = "WIFI_APP";

// Sử dụng EventGroup của FreeRTOS để đồng bộ hóa trạng thái kết nối
static EventGroupHandle_t s_wifi_event_group;
#define WIFI_CONNECTED_BIT BIT0
#define WIFI_FAIL_BIT      BIT1

static int s_retry_num = 0;

/*
 * TẠI SAO LẠI CÓ HÀM NÀY?
 * ESP-IDF hoạt động theo cơ chế hướng sự kiện (Event-driven).
 * Khi Wi-Fi bắt đầu, ngắt kết nối hoặc nhận được IP từ Router, hệ điều hành sẽ
 * tự động kích hoạt callback này.
 */
static void wifi_event_handler(void* arg, esp_event_base_t event_base,
                                int32_t event_id, void* event_data)
{
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        ESP_LOGI(TAG, "Wi-Fi khoi dong, bat dau ket noi toi: %s...", WIFI_SSID);
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        if (s_retry_num < WIFI_MAX_RETRY) {
            esp_wifi_connect();
            s_retry_num++;
            ESP_LOGW(TAG, "Mat ket noi Wi-Fi, dang thu lai lan %d/%d...", s_retry_num, WIFI_MAX_RETRY);
        } else {
            xEventGroupSetBits(s_wifi_event_group, WIFI_FAIL_BIT);
            ESP_LOGE(TAG, "Ket noi Wi-Fi that bai sau nhieu lan thu!");
        }
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(TAG, "===> DA KET NOI WI-FI THANH CONG! IP: " IPSTR, IP2STR(&event->ip_info.ip));
        s_retry_num = 0;
        xEventGroupSetBits(s_wifi_event_group, WIFI_CONNECTED_BIT);
    }
}

esp_err_t wifi_app_init(void)
{
    s_wifi_event_group = xEventGroupCreate();

    // Khởi tạo stack mạng TCP/IP của hệ thống
    ESP_ERROR_CHECK(esp_netif_init());

    // Tạo vòng lặp sự kiện mặc định (Event Loop) của hệ thống
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    // Tạo interface card mạng ảo cho chế độ Station (thiết bị con kết nối router)
    esp_netif_create_default_wifi_sta();

    // Khởi tạo driver Wi-Fi với cấu hình mặc định
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    // Đăng ký nhận sự kiện Wi-Fi và sự kiện cấp phát IP
    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT,
                                                        ESP_EVENT_ANY_ID,
                                                        &wifi_event_handler,
                                                        NULL,
                                                        NULL));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT,
                                                        IP_EVENT_STA_GOT_IP,
                                                        &wifi_event_handler,
                                                        NULL,
                                                        NULL));

    // Cấu hình SSID và mật khẩu
    wifi_config_t wifi_config = {
        .sta = {
            .ssid = WIFI_SSID,
            .password = WIFI_PASS,
            .threshold.authmode = WIFI_AUTH_WPA2_PSK,
        },
    };

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG, "Module Wi-Fi da khoi tao thanh cong.");
    return ESP_OK;
}

bool wifi_app_wait_for_connected(uint32_t timeout_ms)
{
    TickType_t ticks = (timeout_ms == portMAX_DELAY) ? portMAX_DELAY : pdMS_TO_TICKS(timeout_ms);
    EventBits_t bits = xEventGroupWaitBits(s_wifi_event_group,
                                           WIFI_CONNECTED_BIT | WIFI_FAIL_BIT,
                                           pdFALSE,
                                           pdFALSE,
                                           ticks);

    return (bits & WIFI_CONNECTED_BIT) != 0;
}

bool wifi_app_is_connected(void)
{
    if (s_wifi_event_group == NULL) {
        return false;
    }
    EventBits_t bits = xEventGroupGetBits(s_wifi_event_group);
    return (bits & WIFI_CONNECTED_BIT) != 0;
}

