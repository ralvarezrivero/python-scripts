import paho.mqtt.client as mqtt
import time
import socket

# Override DNS resolution in Python
def custom_getaddrinfo(host, port, family=0, socktype=0, proto=0, flags=0):
    if host == "stage-app.analytics.t-mobile.com":
        print(f"Resolving {host} to 23.50.53.209 (Python override)")
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('23.50.53.209', port))]
    else:
        # Use normal DNS for other hosts
        return orig_getaddrinfo(host, port, family, socktype, proto, flags)

# Backup original function and replace
orig_getaddrinfo = socket.getaddrinfo
socket.getaddrinfo = custom_getaddrinfo

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    print(f"Connection flags: {flags}")
    if rc == 0:
        print("SUCCESS! Publishing test message...")
        client.publish("test/topic", "Hello from Python MQTT client!")
        print("Message sent!")
    else:
        print(f"Connection failed with code {rc}")

def on_publish(client, userdata, mid):
    print(f"Message {mid} published successfully!")

def on_disconnect(client, userdata, rc):
    print(f"Disconnected with result code {rc}")

def on_log(client, userdata, level, buf):
    print(f"LOG: {buf}")

# Create client with debugging
client = mqtt.Client()
client.on_connect = on_connect
client.on_publish = on_publish
client.on_disconnect = on_disconnect
client.on_log = on_log

# Enable debugging
client.enable_logger()

# Configure for WebSocket
client.ws_set_options(path="/mqtt")

print("Connecting to WebSocket MQTT broker...")
print("Target: stage-app.analytics.t-mobile.com:443/mqtt")
print("Will resolve to: 23.50.53.209")

try:
    client.connect("stage-app.analytics.t-mobile.com", 443, keepalive=60)
    client.loop_start()
    
    print("Waiting for connection...")
    time.sleep(15)
    
    print("Disconnecting...")
    client.disconnect()
    client.loop_stop()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Restore original function
socket.getaddrinfo = orig_getaddrinfo