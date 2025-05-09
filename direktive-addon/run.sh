#!/bin/sh

echo "CONSUMER RUN.SH: Script started. Attempting to write to /tmp/consumer.log" > /tmp/consumer.log
echo "CONSUMER RUN.SH: Testing write to /tmp/consumer.log" >> /tmp/consumer.log 2>&1
ls -l /usr/local/bin/consumer_script.py >> /tmp/consumer.log 2>&1
which python3 >> /tmp/consumer.log 2>&1
echo "CONSUMER RUN.SH: About to exec python script. Previous output should be in /tmp/consumer.log" >> /tmp/consumer.log 2>&1

echo "CONSUMER RUN.SH: Executing python script (output to /tmp/consumer.log via redirection on exec line)..."

# Appending to the log file now, as we've already written to it.
exec python3 /usr/local/bin/consumer_script.py >> /tmp/consumer.log 2>&1