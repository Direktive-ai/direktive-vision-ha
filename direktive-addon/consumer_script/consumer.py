import paho.mqtt.client as mqtt
import json
import os
import time
import subprocess

print("Direktive Vision: Python interpreter started execution.", flush=True)

# Helper function to get config using jq
def get_config_value(key, default_value):
    try:
        default_jq = json.dumps(default_value)
        jq_query = f'.{key} // {default_jq}'
        result = subprocess.run(['jq', '-r', jq_query, '/data/options.json'], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"[CONFIG_LOADER] WARN: Could not read '{key}' using jq ({e}). Using default: {default_value}", flush=True)
        return default_value
    except Exception as e:
        print(f"[CONFIG_LOADER] WARN: Unexpected error reading '{key}' using jq ({e}). Using default: {default_value}", flush=True)
        return default_value

print("Direktive Vision: get_config_value function defined.", flush=True)

MQTT_HOST_RAW = get_config_value('mqtt_host', 'core-mosquitto')
print(f"Direktive Vision: MQTT_HOST_RAW = '{MQTT_HOST_RAW}'", flush=True)
MQTT_HOST = MQTT_HOST_RAW

MQTT_PORT_RAW = get_config_value('mqtt_port', 1883)
print(f"Direktive Vision: MQTT_PORT_RAW = '{MQTT_PORT_RAW}' (type: {type(MQTT_PORT_RAW)})", flush=True)
try:
    MQTT_PORT = int(MQTT_PORT_RAW)
    print(f"Direktive Vision: MQTT_PORT (int) = {MQTT_PORT}", flush=True)
except ValueError as e:
    print(f"[CONFIG_LOADER] ERROR: Failed to convert MQTT_PORT_RAW '{MQTT_PORT_RAW}' to int. Error: {e}. Using default 1883.", flush=True)
    MQTT_PORT = 1883

MQTT_USER_RAW = get_config_value('mqtt_user', '')
print(f"Direktive Vision: MQTT_USER_RAW = '{MQTT_USER_RAW}'", flush=True)
MQTT_USER = MQTT_USER_RAW

MQTT_PASSWORD_RAW = get_config_value('mqtt_password', '')

print(f"Direktive Vision: MQTT_PASSWORD_RAW has been retrieved (value not logged).", flush=True)
MQTT_PASSWORD = MQTT_PASSWORD_RAW


FRIGATE_EVENTS_TOPIC = "frigate/events" 
print(f"Direktive Vision: FRIGATE_EVENTS_TOPIC = '{FRIGATE_EVENTS_TOPIC}'", flush=True)

_addon_name_from_env = os.environ.get('ADDON_SLUG')
print(f"Direktive Vision: ADDON_SLUG from env = '{_addon_name_from_env}'", flush=True)

ADDON_NAME_RAW = get_config_value('ADDON_SLUG', 'my_vision_ai_fallback_jq')
print(f"Direktive Vision: ADDON_SLUG from get_config_value = '{ADDON_NAME_RAW}'", flush=True)

if _addon_name_from_env and _addon_name_from_env != 'null':
    ADDON_NAME = _addon_name_from_env
elif ADDON_NAME_RAW and ADDON_NAME_RAW != 'null':
    ADDON_NAME = ADDON_NAME_RAW
else:
    ADDON_NAME = 'my_vision_ai_ultimate_fallback'
print(f"Direktive Vision: Final ADDON_NAME = '{ADDON_NAME}'", flush=True)

def on_connect(client, userdata, flags, reason_code, properties=None):
    connect_msg_prefix = f"[{ADDON_NAME}] [on_connect]"
    if reason_code == mqtt.CONNACK_ACCEPTED:
        log_msg = f"{connect_msg_prefix} Consumer connected to MQTT Broker at {MQTT_HOST}:{MQTT_PORT}! Subscribing to {FRIGATE_EVENTS_TOPIC}"
        print(log_msg, flush=True)
        try:
            client.subscribe(FRIGATE_EVENTS_TOPIC)
            subscribe_msg = f"{connect_msg_prefix} Subscribed to {FRIGATE_EVENTS_TOPIC} successfully."
            print(subscribe_msg, flush=True)
        except Exception as e_sub:
            subscribe_err_msg = f"{connect_msg_prefix} Error during subscribe: {e_sub}"
            print(subscribe_err_msg, flush=True)
    else:
        log_msg = f"{connect_msg_prefix} Failed to connect to MQTT, return code {reason_code}"
        print(log_msg, flush=True)

def on_disconnect(client, userdata, disconnect_flags, reason_code, properties=None):
    log_msg = f"[{ADDON_NAME}] [on_disconnect] Disconnected from MQTT Broker with result code {reason_code}."
    print(log_msg, flush=True)

def on_message(client, userdata, msg):
    message_prefix = f"[{ADDON_NAME}] [on_message]"
    try:
        payload_str = msg.payload.decode('utf-8')
        print(f"{message_prefix} Received event on {msg.topic}", flush=True)
        event_data = json.loads(payload_str)
        
        event_type = event_data.get('type')
        after_data = event_data.get('after', {})
        label = after_data.get('label')
        camera = after_data.get('camera')
        score = after_data.get('score')
        event_id = after_data.get('id')

        # Filter for 'new' events or 'update' events if you need ongoing status
        if event_type in ['new', 'update']:
            log_msg = f"{message_prefix} Detected '{label}' on camera '{camera}' (ID: {event_id}, Score: {score:.2f})"
            print(log_msg, flush=True)

            if label == "person_fallen" and score > 0.7:
                critical_msg = f"{message_prefix} CRITICAL: Person fallen detected on {camera}!"
                print(critical_msg, flush=True)
            
            elif label == "baby_sleeping" and score > 0.6:
                info_msg = f"{message_prefix} INFO: Baby sleeping detected on {camera}."
                print(info_msg, flush=True)

    except json.JSONDecodeError:
        err_msg = f"{message_prefix} Received non-JSON message on {msg.topic}: {msg.payload.decode('utf-8', errors='ignore')}"
        print(err_msg, flush=True)
    except Exception as e:
        err_msg = f"{message_prefix} Error processing message: {e}"
        print(err_msg, flush=True)

def main():
    print(f"[{ADDON_NAME}] main() called.", flush=True)
    client_id = f"{ADDON_NAME}-consumer-{os.getpid()}"
    print(f"[{ADDON_NAME}] Client ID generated: {client_id}", flush=True)

    print(f"[{ADDON_NAME}] Attempting to create mqtt.Client...", flush=True)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id, protocol=mqtt.MQTTv5)
    print(f"[{ADDON_NAME}] mqtt.Client created successfully.", flush=True)
    
    if MQTT_USER and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        print(f"[{ADDON_NAME}] username_pw_set completed.", flush=True)
    else:
        print(f"[{ADDON_NAME}] MQTT_USER ('{MQTT_USER}') or MQTT_PASSWORD (is_set: {bool(MQTT_PASSWORD)}) is not set. Skipping username_pw_set.", flush=True)
    
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    print(f"[{ADDON_NAME}] Consumer attempting to connect to MQTT broker: {MQTT_HOST}:{MQTT_PORT}", flush=True)
    
    try:
        print(f"[{ADDON_NAME}] >>> Calling client.connect('{MQTT_HOST}', {MQTT_PORT}, keepalive=60)...", flush=True)
        client.connect(MQTT_HOST, MQTT_PORT, 60) # The 60 is keepalive
        print(f"[{ADDON_NAME}] <<< client.connect() returned without immediate error. Connection process initiated.", flush=True)
        
        print(f"[{ADDON_NAME}] >>> Calling client.loop_forever()... This is a blocking call.", flush=True)
        client.loop_forever() 
        print(f"[{ADDON_NAME}] <<< client.loop_forever() exited cleanly.", flush=True)

    except ConnectionRefusedError as e:
        print(f"[{ADDON_NAME}] MQTT ConnectionRefusedError during connect/loop: {e}. Script will exit.", flush=True)
    except TimeoutError as e:
        print(f"[{ADDON_NAME}] MQTT TimeoutError during connect/loop: {e}. Script will exit.", flush=True)
    except OSError as e:
         print(f"[{ADDON_NAME}] MQTT OSError (e.g., host not found) during connect/loop: {e}. Script will exit.", flush=True)
    except KeyboardInterrupt:
        print(f"[{ADDON_NAME}] KeyboardInterrupt received. Attempting graceful shutdown...", flush=True)
    except Exception as e:
        print(f"[{ADDON_NAME}] UNHANDLED EXCEPTION in connect/loop_forever: {type(e).__name__} - {e}. Script will exit.", flush=True)
        import traceback
        traceback.print_exc()
    finally:
        print(f"[{ADDON_NAME}] main() function's try/except/finally block is ending. Attempting to clean up MQTT client.", flush=True)
        try:
            print(f"[{ADDON_NAME}] Attempting client.disconnect()...", flush=True)
            client.disconnect()
            print(f"[{ADDON_NAME}] client.disconnect() called.", flush=True)
        except Exception as e_disc:
            print(f"[{ADDON_NAME}] Error during client.disconnect(): {e_disc}", flush=True)
        try:
            print(f"[{ADDON_NAME}] Attempting client.loop_stop()...", flush=True)
            client.loop_stop()
            print(f"[{ADDON_NAME}] client.loop_stop() called.", flush=True)
        except Exception as e_stop:
            print(f"[{ADDON_NAME}] Error during client.loop_stop(): {e_stop}", flush=True)
        print(f"[{ADDON_NAME}] MQTT client cleanup attempted. Script will now terminate.", flush=True)

if __name__ == '__main__':
    print(f"[{ADDON_NAME}] Starting MQTT Consumer Script...", flush=True)
    main() 