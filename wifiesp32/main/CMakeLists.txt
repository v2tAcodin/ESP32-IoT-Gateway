idf_component_register(SRCS "main.c"
                            "wifi_app.c"
                            "mqtt_app.c"
                            "uart_app.c"
                       INCLUDE_DIRS "."
                       REQUIRES nvs_flash esp_wifi esp_event driver esp_driver_uart mqtt)
