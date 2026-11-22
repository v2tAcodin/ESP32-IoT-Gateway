"""
========================================================================================
TOOL TEST GIẢ LẬP GỬI GÓI TIN CẢM BIẾN LƯỢNG MƯA LÊN CLOUD BROKER
========================================================================================
Dùng để kiểm thử Web Dashboard và tool logger_to_excel.py ngay cả khi chưa cắm STM32/ESP32!
"""

import time
import math
import random
import json
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "my_iot_project/stm32_sensor_data"

print(f"[*] Đang kết nối tới MQTT Broker: {BROKER}:{PORT}")
try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"sim_sensor_{int(time.time())}")
except AttributeError:
    client = mqtt.Client(client_id=f"sim_sensor_{int(time.time())}")

client.connect(BROKER, PORT, 60)
client.loop_start()
print(f"[*] Đang bắt đầu phát dữ liệu mô phỏng lên topic: '{TOPIC}'...")
print("[*] Nhấn Ctrl + C để dừng lại.\n")

step = 0
try:
    while True:
        # Mô phỏng mực nước dao động dạng sin từ 30cm đến 180cm
        base_level = 80.0 + math.sin(step * 0.1) * 50.0 + random.uniform(-2.0, 2.0)
        base_level = max(0.0, min(500.0, base_level))

        # Tính toán điện áp tương ứng: 0.10V (0cm) -> 3.3V (500cm)
        volt = 0.10 + (base_level / 500.0) * (3.3 - 0.10)
        press = base_level / 1019.72
        percent = (base_level / 500.0) * 100.0
        raw_adc = int((volt / 3.3) * 4095)

        payload = {
            "level": round(base_level, 1),
            "volt": round(volt, 2),
            "percent": round(percent, 1),
            "press": round(press, 3),
            "raw": raw_adc,
            "is_simulated": True
        }

        payload_json = json.dumps(payload)
        client.publish(TOPIC, payload_json)
        print(f" -> [GỬI THÀNH CÔNG] {payload_json}")

        step += 1
        time.sleep(1.0) # Gửi mỗi 1 giây

except KeyboardInterrupt:
    print("\n[*] Đã dừng gửi.")
    client.loop_stop()
    client.disconnect()
