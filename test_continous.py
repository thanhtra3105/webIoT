import time
import paho.mqtt.client as paho
from paho import mqtt
import json
import random

# ==================== CẤU HÌNH ====================
MQTT_BROKER = "afe100349ba44464b15f0bfb86846d85.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "lethanhtra"
MQTT_PASSWORD = "Thanhtra2004"
MQTT_TOPIC = "boat/rescue/data"

# ==================== CALLBACKS ====================
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Kết nối thành công!")
    else:
        print(f"❌ Kết nối thất bại: {rc}")

def on_publish(client, userdata, mid, properties=None):
    pass  # Không in log để giữ console gọn

# ==================== TẠO CLIENT ====================
client = paho.Client(client_id="ContinuousBoatSender", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect
client.on_publish = on_publish

client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

# ==================== DỮ LIỆU THUYỀN ====================
boats = {
    "DN-001": {"lat": 16.0544, "lon": 108.2022, "alert": "NO_ALERT"},
    "DN-002": {"lat": 16.0744, "lon": 108.2222, "alert": "NO_ALERT"},
    "DN-003": {"lat": 16.0344, "lon": 108.1822, "alert": "NO_ALERT"},
    "DN-004": {"lat": 16.0644, "lon": 108.2422, "alert": "NO_ALERT"},
    "DN-005": {"lat": 16.0444, "lon": 108.1622, "alert": "NO_ALERT"},
}

# Danh sách cảnh báo có thể xảy ra
alert_types = ["SOS", "LOW_BATTERY", "ENGINE_FAILURE", "MAN_OVERBOARD", "WATER_LEAK"]

# ==================== KẾT NỐI VÀ GỬI ====================
print("=" * 60)
print("🚢 GIÁM SÁT THUYỀN REAL-TIME")
print("=" * 60)
print(f"📡 Broker: {MQTT_BROKER}")
print(f"📌 Topic: {MQTT_TOPIC}")
print(f"⏱️  Chu kỳ: 3 giây/lần")
print("=" * 60)
print("⚠️  Nhấn Ctrl+C để dừng\n")

try:
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start()
    time.sleep(2)
    
    iteration = 0
    
    while True:
        iteration += 1
        print(f"\n{'='*60}")
        print(f"📡 Vòng {iteration} - {time.strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        for boat_id, data in boats.items():
            # Di chuyển ngẫu nhiên (giả lập GPS)
            data["lat"] += random.uniform(-0.002, 0.002)
            data["lon"] += random.uniform(-0.002, 0.002)
            
            # Giới hạn trong vùng Đà Nẵng
            data["lat"] = max(16.0, min(16.15, data["lat"]))
            data["lon"] = max(108.1, min(108.3, data["lon"]))
            
            # 15% khả năng có cảnh báo
            if random.random() < 0.15:
                data["alert"] = random.choice(alert_types)
                status_icon = "🚨"
            else:
                data["alert"] = "NO_ALERT"
                status_icon = "✅"
            
            # Tạo message
            message = {
                "UID": boat_id,
                "lat": round(data["lat"], 6),
                "lon": round(data["lon"], 6),
                "alert": data["alert"]
            }
            
            # Gửi
            client.publish(MQTT_TOPIC, json.dumps(message), qos=1)
            
            # In log
            print(f"{status_icon} {boat_id}: ({message['lat']:.4f}, {message['lon']:.4f}) - {message['alert']}")
        
        print(f"\n⏳ Đợi 3 giây...")
        time.sleep(3)
        
except KeyboardInterrupt:
    print("\n\n" + "=" * 60)
    print("⏹️  ĐÃ DỪNG!")
    print("=" * 60)
    print(f"📊 Tổng số vòng đã chạy: {iteration}")
    print(f"📤 Tổng số message đã gửi: {iteration * len(boats)}")
    
except Exception as e:
    print(f"\n❌ Lỗi: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    client.loop_stop()
    client.disconnect()
    print("\n🔌 Đã ngắt kết nối\n")