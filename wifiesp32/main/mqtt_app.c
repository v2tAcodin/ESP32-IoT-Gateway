#include <string.h>
#include "esp_log.h"
#include "mqtt_client.h"

#include "app_config.h"
#include "mqtt_app.h"

static const char *TAG = "MQTT_APP";

static esp_mqtt_client_handle_t s_mqtt_client = NULL;
static bool s_is_connected = false;

/*
 * TẠI SAO LẠI CẦN MQTT EVENT HANDLER?
 * MQTT duy trì một kết nối socket liên tục (Persistent connection) tới Broker.
 * Handler này giúp ta biết khi nào kết nối thành công, bị ngắt mạng, hoặc khi nhận
 * được dữ liệu phản hồi từ Cloud gửi xuống (Downlink).
 */
static void mqtt_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data)
{
    esp_mqtt_event_handle_t event = event_data;

    switch ((esp_mqtt_event_id_t)event_id) {
    case MQTT_EVENT_CONNECTED:
        s_is_connected = true;
        ESP_LOGI(TAG, "===> DA KET NOI TOI MQTT BROKER THANH CONG!");
        ESP_LOGI(TAG, "San sang truyen nhan du lieu tren topic: %s", MQTT_TOPIC_DATA);
        break;

    case MQTT_EVENT_DISCONNECTED:
        s_is_connected = false;
        ESP_LOGW(TAG, "Mat ket noi toi MQTT Broker! ESP32 se tu dong thu ket noi lai...");
        break;

    case MQTT_EVENT_PUBLISHED:
        ESP_LOGD(TAG, "Goi tin da duoc xuat ban len Cloud thanh cong (msg_id=%d)", event->msg_id);
        break;

    case MQTT_EVENT_DATA:
        // Dùng khi Cloud gửi lệnh điều khiển xuống STM32 (mục tiêu nâng cấp sau này)
        ESP_LOGI(TAG, "Nhan duoc lenh tu Cloud: Topic=%.*s, Data=%.*s",
                 event->topic_len, event->topic,
                 event->data_len, event->data);
        break;

    case MQTT_EVENT_ERROR:
        ESP_LOGE(TAG, "Loi trong qua trinh giao tiep MQTT!");
        break;

    default:
        break;
    }
}

esp_err_t mqtt_app_init(void)
{
    esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = MQTT_BROKER_URI,
    };

    s_mqtt_client = esp_mqtt_client_init(&mqtt_cfg);
    if (s_mqtt_client == NULL) {
        ESP_LOGE(TAG, "Khong the tao MQTT client handle!");
        return ESP_FAIL;
    }

    ESP_ERROR_CHECK(esp_mqtt_client_register_event(s_mqtt_client,
                                                   ESP_EVENT_ANY_ID,
                                                   mqtt_event_handler,
                                                   NULL));

    ESP_ERROR_CHECK(esp_mqtt_client_start(s_mqtt_client));
    ESP_LOGI(TAG, "Khoi dong tien trinh MQTT Client ket noi toi: %s", MQTT_BROKER_URI);
    return ESP_OK;
}

esp_err_t mqtt_app_publish(const char *topic, const char *data)
{
    if (s_mqtt_client == NULL || !s_is_connected) {
        ESP_LOGW(TAG, "Chua the gui len Cloud vi MQTT chua ket noi!");
        return ESP_ERR_INVALID_STATE;
    }

    const char *target_topic = (topic != NULL) ? topic : MQTT_TOPIC_DATA;
    int msg_id = esp_mqtt_client_publish(s_mqtt_client, target_topic, data, 0, 1, 0);

    if (msg_id < 0) {
        ESP_LOGE(TAG, "Loi khi goi publish MQTT!");
        return ESP_FAIL;
    }

    ESP_LOGI(TAG, "[MQTT PUB] -> Topic: %s | Payload: %s", target_topic, data);
    return ESP_OK;
}

bool mqtt_app_is_connected(void)
{
    return s_is_connected;
}

