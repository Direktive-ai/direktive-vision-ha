FROM ghcr.io/blakeblackshear/frigate:0.13.2

COPY consumer_script/consumer.py /usr/local/bin/consumer_script.py
COPY consumer_script/requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt \
    && chmod +x /usr/local/bin/consumer_script.py \
    && python3 -m py_compile /usr/local/bin/consumer_script.py

COPY cpu_model.tflite /cpu_model.tflite
COPY labelmap.txt /labelmap.txt
COPY setup-config.sh /setup-config.sh
RUN chmod +x /setup-config.sh

# Overwrite Frigate's s6 run script to include our setup-config.sh
RUN echo "#!/bin/sh\n# Execute our setup script first\n/setup-config.sh\n# Now execute the original Frigate startup command\ncd /opt/frigate && exec python3.9 -u -m frigate" > /etc/s6-overlay/s6-rc.d/frigate/run \
    && chmod +x /etc/s6-overlay/s6-rc.d/frigate/run

# Set up s6 service for the consumer script
RUN mkdir -p /etc/s6-overlay/s6-rc.d/consumer
RUN mkdir -p /etc/s6-overlay/s6-rc.d/consumer/dependencies.d
RUN mkdir -p /etc/s6-overlay/s6-rc.d/user/contents.d

COPY run.sh /etc/s6-overlay/s6-rc.d/consumer/run
RUN chmod +x /etc/s6-overlay/s6-rc.d/consumer/run
RUN echo "longrun" > /etc/s6-overlay/s6-rc.d/consumer/type

RUN echo "#!/usr/bin/execlineb -P\nforeground { echo Consumer service is starting... }\ntrue" > /etc/s6-overlay/s6-rc.d/consumer/up
RUN chmod +x /etc/s6-overlay/s6-rc.d/consumer/up

# Register the consumer service with s6-rc
RUN touch /etc/s6-overlay/s6-rc.d/user/contents.d/consumer
RUN mkdir -p /config

ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/lib \
    MQTT_HOST=core-mosquitto \
    MQTT_PORT=1883 \
    MQTT_USER="" \
    MQTT_PASSWORD="" \
    CAMERA_RTSP_URL="rtsp://example.com/stream" \
    FFMPEG_LOGLEVEL=verbose

ENTRYPOINT ["/init"]