#!/command/with-contenv sh
# ==============================================================================
# Initialize the addon
# ==============================================================================

# Create config directory if it doesn't exist
mkdir -p /config

# Generate Frigate configuration
cat > /config/frigate.yaml << 'EOF'
mqtt:
  host: "core-mosquitto"
  port: 1883
  user: ""
  password: ""
  topic_prefix: frigate

cameras:
  camera1:
    ffmpeg:
      inputs:
        - path: "rtsp://example.com/stream"
          input_args: -rtsp_transport tcp
          roles:
            - detect
            - rtmp
    detect:
      width: 1280
      height: 720
      fps: 5
    objects:
      track:
        - person
        - car
    motion:
      mask:
        - 0,0,1280,0,1280,720,0,720
    record:
      enabled: false
    snapshots:
      enabled: true
      timestamp: true
      bounding_box: true
      retain:
        default: 10

detectors:
  cpu:
    type: cpu
    num_threads: 2

model:
  path: /config/model_cache/model.tflite
  width: 320
  height: 320
  labelmap_path: /config/model_cache/labels.txt
EOF

python3 /usr/local/bin/consumer_script.py &

exec /init 