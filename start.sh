#!/bin/bash

LOG_FILE="script.log"

function auto() {
    echo "Starting script..."
    python3 Script.py >> "$LOG_FILE" 2>&1 &
    PID=$!
    echo "Script running with PID: $PID"
}

function stop() {
    if [ ! -z "$PID" ] && ps -p $PID > /dev/null; then
        echo "Stopping script with PID: $PID"
        kill -9 $PID
        wait $PID 2>/dev/null
    else
        echo "No running process found to stop."
    fi
}

# Loop utama
while true; do
    echo "Monitoring log for 'Delay 6 minutes'..."
    auto

    # Pantau log
    while true; do
        if grep -q "Delay 6 minutes" "$LOG_FILE"; then
            echo "Log detected: 'Delay 6 minutes'. Restarting process..."
            stop
            break
        fi
        sleep 1 # Hindari penggunaan CPU tinggi
    done
done
