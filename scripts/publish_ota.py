import paho.mqtt.publish as publish
import json
import os

payload = json.dumps({
    "version":  os.environ["OTA_VERSION"],
    "url":      os.environ["OTA_URL"],
    "severity": os.environ["OTA_SEVERITY"],
    "sha":      os.environ["OTA_SHA"]
})

broker = os.environ["MQTT_BROKER"]
port   = int(os.environ["MQTT_PORT"])
topic  = os.environ["MQTT_TOPIC"]

print(f"OTA Payload : {payload}")
print(f"Broker      : {broker}:{port}")
print(f"Topic       : {topic}")

publish.single(
    topic    = topic,
    payload  = payload,
    hostname = broker,
    port     = port,
    qos      = 1,
    retain   = True
)

print("OTA published successfully.")
