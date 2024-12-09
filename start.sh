function auto() {
    python3 auto_proxy.py local_proxies.txt
    sleep 5
    python3 grass_proxy.py &
    PID=$!
    echo "running with PID: $PID"
}

function stop() {
    if [ ! -z "$PID" ]; then
        echo "Stopping with PID: $PID"
        kill -9 $PID
        clear
    else
        echo "No process found to stop."
    fi
}

while true; do
    echo "Starting auto process..."
    auto
    sleep $((RANDOM % 360 * 10 * 24))
    stop
done
