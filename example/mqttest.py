import paho.mqtt.client as mqtt
import time

def on_connect(client, userdata, flags, rc, properties=None):
    client.subscribe("HFWM/8731/frequency/1")
    if rc == 0:
        print(f"[MQTT] Connected")
    else:
        print(f"[MQTT] Connect failed with code {rc}")

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(payload)

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message
client.connect("fys-s-dep-bkr01.fysad.fys.kuleuven.be", 1883)
client.loop_start() # Run in a background thread
for _ in range(10):
    time.sleep(0.5)