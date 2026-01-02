import time
import paho.mqtt.client as paho
from paho import mqtt
import json

# ==================== CẤU HÌNH ====================
MQTT_BROKER = "afe100349ba44464b15f0bfb86846d85.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "lethanhtra"
MQTT_PASSWORD = "Thanhtra2004"
MQTT_TOPIC_WEATHER = "station/weather/alert"  # Topic gửi cảnh báo thời tiết

# ==================== CALLBACKS ====================
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Kết nối thành công!")
    else:
        print(f"❌ Kết nối thất bại: {rc}")

def on_publish(client, userdata, mid, properties=None):
    print(f"   ✓ Message ID {mid} đã gửi")

# ==================== TẠO CLIENT ====================
client = paho.Client(client_id="WeatherStation", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect
client.on_publish = on_publish

client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

# ==================== KẾT NỐI ====================
print("=" * 60)
print("🌊 TRẠM THỜI TIẾT - GỬI CẢNH BÁO")
print("=" * 60)
print(f"📡 Broker: {MQTT_BROKER}")
print(f"📌 Topic: {MQTT_TOPIC_WEATHER}")
print("=" * 60)

try:
    print("\n🔄 Đang kết nối...")
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start()
    time.sleep(2)
    
    # ==================== CÁC LOẠI CẢNH BÁO ====================
    weather_alerts = [
        {
            "station_id": "STATION_DN_01",
            "alert_type": "TYPHOON",
            "severity": "HIGH",
            "message": "Bão cấp 10 đang tiến vào khu vực, tốc độ gió 100km/h. Yêu cầu tất cả thuyền vào bờ ngay lập tức!",
            "area_lat": 16.0544,
            "area_lon": 108.2022,
            "radius_km": 80
        },
        {
            "station_id": "STATION_DN_01",
            "alert_type": "HEAVY_WAVE",
            "severity": "MEDIUM",
            "message": "Sóng cao 3-4m, gió mạnh cấp 7. Thuyền nhỏ nên tìm nơi trú ẩn.",
            "area_lat": 16.0344,
            "area_lon": 108.1822,
            "radius_km": 50
        },
        {
            "station_id": "STATION_DN_02",
            "alert_type": "STRONG_WIND",
            "severity": "MEDIUM",
            "message": "Gió giật mạnh cấp 8-9, khả năng mưa lớn. Cảnh báo đi biển.",
            "area_lat": 16.0744,
            "area_lon": 108.2222,
            "radius_km": 60
        },
        {
            "station_id": "STATION_DN_01",
            "alert_type": "FOG",
            "severity": "LOW",
            "message": "Sương mù dày đặc, tầm nhìn dưới 200m. Giảm tốc độ và bật đèn.",
            "area_lat": 16.0644,
            "area_lon": 108.2422,
            "radius_km": 30
        },
        {
            "station_id": "STATION_DN_03",
            "alert_type": "THUNDERSTORM",
            "severity": "HIGH",
            "message": "Dông lốc mạnh kèm sét, mưa to. Tất cả thuyền tránh xa vùng này!",
            "area_lat": 16.0444,
            "area_lon": 108.1622,
            "radius_km": 40
        }
    ]
    
    print("\n📤 Bắt đầu gửi cảnh báo thời tiết...\n")
    
    for i, alert in enumerate(weather_alerts, 1):
        message = json.dumps(alert)
        
        severity_icon = "🔴" if alert['severity'] == 'HIGH' else "🟡" if alert['severity'] == 'MEDIUM' else "🟢"
        
        print(f"{i}. {severity_icon} Gửi cảnh báo: {alert['alert_type']}")
        print(f"   📍 Vùng ảnh hưởng: ({alert['area_lat']}, {alert['area_lon']})")
        print(f"   ⭕ Bán kính: {alert['radius_km']}km")
        print(f"   📝 {alert['message'][:60]}...")
        
        client.publish(MQTT_TOPIC_WEATHER, message, qos=1)
        
        time.sleep(2)
    
    time.sleep(3)
    
    print("\n" + "=" * 60)
    print("✅ ĐÃ GỬI XONG TẤT CẢ CẢNH BÁO!")
    print("=" * 60)
    print("👉 Kiểm tra:")
    print("   - Backend console: Xem log nhận cảnh báo")
    print("   - Web: http://localhost:5000")
    print("   - Thuyền trong vùng sẽ nhận broadcast")
    print("=" * 60)
    
except KeyboardInterrupt:
    print("\n⏹️  Đã dừng")
except Exception as e:
    print(f"\n❌ Lỗi: {e}")
    import traceback
    traceback.print_exc()
finally:
    client.loop_stop()
    client.disconnect()
    print("\n🔌 Đã ngắt kết nối\n")