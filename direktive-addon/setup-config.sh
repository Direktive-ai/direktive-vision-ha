#!/bin/sh

# Create config directory if it doesn't exist
mkdir -p /config

MQTT_HOST_EFFECTIVE=$(jq -r '.mqtt_host // "core-mosquitto"' /data/options.json)
MQTT_PORT_EFFECTIVE=$(jq -r '.mqtt_port // 1883' /data/options.json)
MQTT_USER_EFFECTIVE=$(jq -r '.mqtt_user // ""' /data/options.json)
MQTT_PASSWORD_EFFECTIVE=$(jq -r '.mqtt_password // ""' /data/options.json)
CAMERA_ENTITY_ID=$(jq -r '.camera_entity_id // "camera.example_camera"' /data/options.json)
API_KEY_EFFECTIVE=$(jq -r '.api_key' /data/options.json)
ENCRYPTION_KEY_EFFECTIVE=$(jq -r '.encryption_key // ""' /data/options.json)

# Debug output
echo "Starting setup-config service" > /tmp/setup-config.log
echo "Effective MQTT_HOST: $MQTT_HOST_EFFECTIVE" >> /tmp/setup-config.log
echo "Effective CAMERA_ENTITY_ID: $CAMERA_ENTITY_ID" >> /tmp/setup-config.log

# Fetch camera stream URL from Home Assistant API
echo "Fetching stream URL for $CAMERA_ENTITY_ID..." >> /tmp/setup-config.log
API_RESPONSE=$(curl -s -X GET \
    -H "Authorization: Bearer $SUPERVISOR_TOKEN" \
    -H "Content-Type: application/json" \
    "http://supervisor/core/api/states/$CAMERA_ENTITY_ID")

CAMERA_STREAM_URL=$(echo "$API_RESPONSE" | jq -r '.attributes.stream_source // ""')

if [ -z "$CAMERA_STREAM_URL" ]; then
    echo "Warning: Could not retrieve stream_source for entity $CAMERA_ENTITY_ID from HA API." >> /tmp/setup-config.log
    echo "API Response was: $API_RESPONSE" >> /tmp/setup-config.log
    echo "Falling back to using CAMERA_ENTITY_ID directly, which might be an RTSP URL or might fail." >> /tmp/setup-config.log
    CAMERA_STREAM_URL="$CAMERA_ENTITY_ID" # Fallback: use the entity_id itself, assuming it might be a URL. Or set an error URL.
else
    echo "Successfully fetched stream URL: $CAMERA_STREAM_URL" >> /tmp/setup-config.log
fi

# Generate Frigate configuration
cat > /config/config.yml <<EOF
mqtt:
  host: "$MQTT_HOST_EFFECTIVE"
  port: $MQTT_PORT_EFFECTIVE
  user: "$MQTT_USER_EFFECTIVE"
  password: "$MQTT_PASSWORD_EFFECTIVE"
  topic_prefix: frigate

# Explicitly define the stream for go2rtc
go2rtc:
  streams:
    camera1: "$CAMERA_STREAM_URL" # Use the fetched stream URL for go2rtc
  # Optional: If you want go2rtc to restream via RTSP on its default port 8554
  rtsp:
    listen: ":8554" # Ensure go2rtc's RTSP server is listening

cameras:
  camera1:
    ffmpeg:
      inputs:
        # Tell Frigate to use an HTTP-based stream from go2rtc for camera1
        - path: http://127.0.0.1:1984/api/stream.mp4?src=camera1 
          input_args: -re # Add -re for live HTTP input, may override defaults
          roles:
            - detect
            - rtmp
    detect:
      enabled: true
      width: 640
      height: 360
      fps: 5
    objects:
      track:
        - person
    record:
      enabled: false

detectors:
  cpu:
    type: cpu # Ensure detector type matches the model
    num_threads: 2

model:
  # Use a standard CPU model path
  path: /cpu_model.tflite
  width: 320 # Adjust width/height/labelmap based on the actual CPU model used
  height: 320
  labelmap_path: /labelmap.txt # Use a standard labelmap path

logger:
  default: info
  logs:
    frigate.video.camera1: debug
EOF

echo "Config file /config/config.yml generated"

# Debug output
echo "Config file contents:" >> /tmp/setup-config.log
cat /config/config.yml >> /tmp/setup-config.log
echo "Setup-config service completed" >> /tmp/setup-config.log 