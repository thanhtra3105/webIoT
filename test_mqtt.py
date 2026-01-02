

import time
import paho.mqtt.client as paho
from paho import mqtt

MQTT_BORKER = "afe100349ba44464b15f0bfb86846d85.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "lethanhtra"
MQTT_PASSWORD = "Thanhtra2004"

# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)

# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, properties=None):
    print("mid: " + str(mid))

# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect

# enable TLS for secure connection
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
# set username and password
client.username_pw_set("lethanhtra", "Thanhtra2004")
# connect to HiveMQ Cloud on port 8883 (default for MQTT)
client.connect("afe100349ba44464b15f0bfb86846d85.s1.eu.hivemq.cloud", 8883)

# setting callbacks, use separate functions like above for better visibility
client.on_subscribe = on_subscribe
client.on_message = on_message
client.on_publish = on_publish

client.subscribe("encyclopedia/#", qos=1)

client.publish("encyclopedia/temperature", payload="hot", qos=1)


client.loop_forever()

