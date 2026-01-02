import time
import paho.mqtt.client as paho
from paho import mqtt
import json

# ==================== CẤU HÌNH ====================
MQTT_BROKER = "afe100349ba44464b15f0bfb86846d85.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "lethanhtra"
MQTT_PASSWORD = "Thanhtra2004"
MQTT_TOPIC = "boat/rescue/data"  # Topic gửi dữ liệu thuyền

# ==================== CALLBACKS ====================
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ CONNACK received - Kết nối thành công!")
    else:
        print(f"❌ Kết nối thất bại với code: {rc}")

def on_publish(client, userdata, mid, properties=None):
    print(f"   ✓ Message ID {mid} đã gửi thành công")

# ==================== TẠO CLIENT ====================
client = paho.Client(client_id="TestBoatPublisher", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect
client.on_publish = on_publish

# Enable TLS
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
# Set username và password
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

# ==================== KẾT NỐI ====================
print("=" * 60)
print("🧪 TEST GỬI DỮ LIỆU THUYỀN LÊN HIVEMQ")
print("=" * 60)
print(f"📡 Broker: {MQTT_BROKER}:{MQTT_PORT}")
print(f"👤 Username: {MQTT_USERNAME}")
print(f"📌 Topic: {MQTT_TOPIC}")
print("=" * 60)

try:
    print("\n🔄 Đang kết nối...")
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start()
    time.sleep(2)  # Đợi kết nối
    
    # ==================== DỮ LIỆU THUYỀN ====================
    test_boats = [
        {
            "UID": "DN-001",
            "lat": 16.0544,
            "lon": 108.2022,
            "alert": "NO_ALERT"
        },
        {
            "UID": "DN-002", 
            "lat": 16.0744,
            "lon": 108.2222,
            "alert": "SOS"
        },
        {
            "UID": "DN-003",
            "lat": 16.0344,
            "lon": 108.1822,
            "alert": "LOW_BATTERY"
        },
        {
            "UID": "DN-004",
            "lat": 16.0644,
            "lon": 108.2422,
            "alert": "ENGINE_FAILURE"
        },
        {
            "UID": "DN-005",
            "lat": 16.0444,
            "lon": 108.1622,
            "alert": "NO_ALERT"
        },
        {
            "UID": "DN-006",
            "lat": 16.0700,
            "lon": 108.2300,
            "alert": "MAN_OVERBOARD"
        }
    ]
    
    print("\n📤 Bắt đầu gửi dữ liệu...\n")
    
    for i, boat in enumerate(test_boats, 1):
        message = json.dumps(boat)
        
        result = client.publish(MQTT_TOPIC, payload=message, qos=1)
        
        status = "🚨 KHẨN CẤP" if boat['alert'] != 'NO_ALERT' else "✅ Bình thường"
        print(f"{i}. Gửi: {boat['UID']} - {status}")
        print(f"   📍 Vị trí: ({boat['lat']}, {boat['lon']})")
        print(f"   🚨 Cảnh báo: {boat['alert']}")
        
        time.sleep(1.5)  # Đợi giữa các lần gửi
    
    print("\n⏳ Đợi tin nhắn được gửi...")
    time.sleep(3)
    
    print("\n" + "=" * 60)
    print("✅ ĐÃ GỬI XONG TẤT CẢ DỮ LIỆU!")
    print("=" * 60)
    print("👉 Kiểm tra:")
    print("   - Backend console: Xem log nhận dữ liệu")
    print("   - Web: http://localhost:5000")
    print("   - API Stats: http://localhost:5000/api/stats")
    print("   - MQTT Status: http://localhost:5000/api/mqtt/status")
    print("=" * 60)
    
except KeyboardInterrupt:
    print("\n⏹️  Đã dừng bởi người dùng")
except Exception as e:
    print(f"\n❌ Lỗi: {e}")
    import traceback
    traceback.print_exc()
finally:
    client.loop_stop()
    client.disconnect()
    print("\n🔌 Đã ngắt kết nối\n")