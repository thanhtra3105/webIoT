from unittest import case
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import paho.mqtt.client as paho
from paho import mqtt
import json
import threading
from datetime import datetime
import time

app = Flask(__name__)
CORS(app)

# ==================== CẤU HÌNH HIVEMQ ====================
MQTT_BROKER = "afe100349ba44464b15f0bfb86846d85.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "lethanhtra"
MQTT_PASSWORD = "Thanhtra2004"
MQTT_TOPIC_BOATS = "boat/rescue/data"
MQTT_TOPIC_WEATHER = "station/weather/alert"
MQTT_TOPIC_BROADCAST = "boat/rescue/broadcast"

NORMAL = 0
FLIP = 1
FIRE = 2
SOS = 3

# Lưu trữ dữ liệu
boats_data = {}
alerts_history = []
weather_alerts = []
mqtt_connected = False

# ==================== MQTT CALLBACKS ====================
def on_connect(client, userdata, flags, rc, properties=None):
    global mqtt_connected
    print("=" * 60)
    if rc == 0:
        print("✅ CONNACK received - Kết nối HiveMQ thành công!")
        mqtt_connected = True
        client.subscribe(MQTT_TOPIC_BOATS, qos=1)
        client.subscribe(MQTT_TOPIC_WEATHER, qos=1)
        print(f"📡 Đã subscribe topic thuyền: {MQTT_TOPIC_BOATS}")
        print(f"🌊 Đã subscribe topic thời tiết: {MQTT_TOPIC_WEATHER}")
    else:
        mqtt_connected = False
        print(f"❌ Kết nối thất bại với code: {rc}")
    print("=" * 60)

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print(f"✅ Subscribed successfully - mid: {mid}, QoS: {granted_qos}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        topic = msg.topic
        
        if topic == MQTT_TOPIC_BOATS:
            handle_boat_message(payload)
        elif topic == MQTT_TOPIC_WEATHER:
            handle_weather_alert(payload, client)
            
    except Exception as e:
        print(f"❌ Lỗi xử lý message: {e}")

def handle_boat_message(payload):
    try:
        print(f"\n📨 Nhận dữ liệu thuyền: {payload}")
        data = json.loads(payload)
        
        boat_id = data.get('uid', 'UNKNOWN')
        sos_code = data.get('sos_type', -1)
        if sos_code == 0:
            sos_type = 'NORMAL'
        elif sos_code == 1:
            sos_type = 'FLIP'
        elif sos_code == 2:
            sos_type = 'FIRE'
        else:
            sos_type = 'SOS'
        lat = float(data.get('lat', 0))
        lon = float(data.get('lon', 0))
        timestamp = data.get('timestamp', '')
        
        boats_data[boat_id] = {
            'uid': boat_id,
            'sos_type': sos_type,
            'lat': lat,
            'lon': lon,
            'timestamp': timestamp,
            'status': 'EMERGENCY' if sos_type != 'NORMAL' else 'NORMAL'
        }
        
        if sos_type != 'NORMAL':
            alerts_history.insert(0, {
                'uid': boat_id,
                'sos_type': sos_type,
                'lat': lat,
                'lon': lon,
                'timestamp': timestamp,
                'type': 'BOAT'
            })
            if len(alerts_history) > 100:
                alerts_history.pop()
        
    except Exception as e:
        print(f"❌ Lỗi xử lý thuyền: {e}")

def handle_weather_alert(payload, client):
    """Xử lý cảnh báo thời tiết và broadcast tới thuyền"""
    try:
        print(f"\n🌊 Nhận cảnh báo thời tiết: {payload}")
        data = json.loads(payload)
        
        # Xử lý station_id hoặc uid
        station_id = data.get('station_id', data.get('uid', 'ADMIN_WEB'))
        if isinstance(station_id, int):
            if station_id == 0:
                station_id = 'ADMIN_WEB'
            else:
                station_id = f"STATION_{station_id:02X}"
        
        # Xử lý weather_type hoặc alert_type
        weather_type = data.get('weather_type', data.get('alert_type'))
        if isinstance(weather_type, int):
            type_map = {10: 'STORM', 11: 'HIGH_WAVES', 12: 'TSUNAMI', 13: 'FOG'}
            alert_type = type_map.get(weather_type, 'UNKNOWN')
        else:
            alert_type = weather_type or 'UNKNOWN'
        
        # Xử lý level hoặc severity
        level = data.get('level', data.get('severity'))
        if isinstance(level, int):
            severity_map = {1: 'LOW', 2: 'MEDIUM', 3: 'HIGH'}
            severity = severity_map.get(level, 'MEDIUM')
        else:
            severity = level or 'MEDIUM'
        
        # Xử lý message
        message = data.get('message', f'Cảnh báo {alert_type}')
        
        area_lat = float(data.get('area_lat', 16.0))
        area_lon = float(data.get('area_lon', 108.0))
        radius_km = float(data.get('radius_km', 50))
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Tạo ID duy nhất cho cảnh báo
        alert_id = f"{station_id}_{int(time.time() * 1000)}"
        
        # Lưu cảnh báo
        weather_alert = {
            'id': alert_id,
            'station_id': station_id,
            'alert_type': alert_type,
            'severity': severity,
            'message': message,
            'area_lat': area_lat,
            'area_lon': area_lon,
            'radius_km': radius_km,
            'timestamp': timestamp
        }
        
        # Thêm vào danh sách hiển thị
        weather_alerts.insert(0, weather_alert)
        if len(weather_alerts) > 50:
            weather_alerts.pop()
        
        # Thêm vào lịch sử
        alerts_history.insert(0, {
            'uid': station_id,
            'lat': area_lat,
            'lon': area_lon,
            'alert': alert_type,
            'timestamp': timestamp,
            'type': 'WEATHER',
            'severity': severity,
            'message': message
        })
        
        # Tìm thuyền trong vùng nguy hiểm
        affected_boats = find_boats_in_area(area_lat, area_lon, radius_km)
        
        if affected_boats:
            broadcast_message = {
                'type': 'WEATHER_ALERT',
                'alert_type': alert_type,
                'severity': severity,
                'message': message,
                'affected_boats': affected_boats,
                'area_lat': area_lat,
                'area_lon': area_lon,
                'radius_km': radius_km,
                'timestamp': timestamp
            }
            client.publish(MQTT_TOPIC_BROADCAST, json.dumps(broadcast_message), qos=1)
            print(f"📢 Đã broadcast tới {len(affected_boats)} thuyền: {affected_boats}")
        else:
            print(f"ℹ️  Không có thuyền nào trong vùng ảnh hưởng")
        
    except Exception as e:
        print(f"❌ Lỗi xử lý thời tiết: {e}")

def find_boats_in_area(center_lat, center_lon, radius_km):
    affected = []
    for boat_id, boat in boats_data.items():
        lat_diff = abs(boat['lat'] - center_lat) * 111
        lon_diff = abs(boat['lon'] - center_lon) * 111 * 0.9
        distance = (lat_diff**2 + lon_diff**2)**0.5
        
        if distance <= radius_km:
            affected.append(boat_id)
    return affected

def on_disconnect(client, userdata, rc, properties=None):
    global mqtt_connected
    mqtt_connected = False
    if rc != 0:
        print(f"⚠️  Ngắt kết nối không mong muốn - code: {rc}")

# ==================== MQTT CLIENT ====================
mqtt_client = paho.Client(client_id="BoatRescueServer", userdata=None, protocol=paho.MQTTv5)
mqtt_client.on_connect = on_connect
mqtt_client.on_subscribe = on_subscribe
mqtt_client.on_message = on_message
mqtt_client.on_disconnect = on_disconnect
mqtt_client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

def start_mqtt():
    try:
        print(f"\n🔄 Đang kết nối MQTT...")
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        mqtt_client.loop_forever()
    except Exception as e:
        print(f"❌ Lỗi kết nối MQTT: {e}")

# ==================== API ENDPOINTS ====================

@app.route('/')
def index():
    try:
        return send_from_directory('.', 'index.html')
    except:
        return "<h1>Error path</h1>"

@app.route('/api/boats')
def get_boats():
    return jsonify({'success': True, 'data': list(boats_data.values())})

@app.route('/api/weather')
def get_weather_alerts():
    return jsonify({'success': True, 'data': weather_alerts})

@app.route('/api/stats')
def get_stats():
    total_boats = len(boats_data)
    emergency_boats = sum(1 for b in boats_data.values() if b['status'] == 'EMERGENCY')
    return jsonify({
        'success': True,
        'data': {
            'total_boats': total_boats,
            'emergency_boats': emergency_boats,
            'normal_boats': total_boats - emergency_boats,
            'weather_alerts': len(weather_alerts)
        }
    })

# --- API MỚI: NHẬP CẢNH BÁO TỪ WEB ---
@app.route('/api/publish/weather', methods=['POST'])
def publish_manual_weather():
    try:
        data = request.json
        print(f"🌍 Web gửi cảnh báo: {data}")

        # Chuyển đổi severity sang level
        severity = data.get('severity', 'MEDIUM')
        level_map = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}
        level = level_map.get(severity, 2)
        
        # Chuyển đổi alert_type sang weather_type
        alert_type = data.get('alert_type')
        type_map = {'STORM': 10, 'HIGH_WAVES': 11, 'TSUNAMI': 12, 'FOG': 13}
        weather_type = type_map.get(alert_type, 10)
        
        payload = {
            'uid': 0,  # Web admin
            'weather_type': weather_type,
            'level': level,
            'message': data.get('message', 'Cảnh báo thủ công'),
            'area_lat': float(data.get('area_lat')),
            'area_lon': float(data.get('area_lon')),
            'radius_km': float(data.get('radius_km', 20))
        }

        # Publish lên MQTT để hệ thống tự xử lý (vẽ map, broadcast thuyền)
        mqtt_client.publish(MQTT_TOPIC_WEATHER, json.dumps(payload), qos=1)
        print(f"✅ Đã publish cảnh báo lên MQTT: {payload}")

        return jsonify({'success': True, 'message': 'Đã gửi cảnh báo'})
    except Exception as e:
        print(f"❌ Lỗi publish weather: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# API MỚI: XÓA CẢNH BÁO
@app.route('/api/weather/<alert_id>', methods=['DELETE'])
def delete_weather(alert_id):
    global weather_alerts
    original_len = len(weather_alerts)
    weather_alerts = [alert for alert in weather_alerts if alert.get('id') != alert_id]
    
    if len(weather_alerts) < original_len:
        print(f"🗑️ Đã xóa cảnh báo ID: {alert_id}")
        return jsonify({'success': True, 'message': 'Deleted'})
    else:
        return jsonify({'success': False, 'message': 'Not found'}), 404

# ==================== CHẠY SERVER ====================
if __name__ == '__main__':
    mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
    mqtt_thread.start()
    time.sleep(2)
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True, use_reloader=False)