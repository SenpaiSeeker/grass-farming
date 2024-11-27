function auto() {
    python3 grass_freeproxy.py &
    GRASS_PID=$!
    echo "grass_freeproxy.py running with PID: $GRASS_PID"
}

function stop_grass() {
    if [ ! -z "$GRASS_PID" ]; then
        echo "Stopping grass_freeproxy.py with PID: $GRASS_PID"
        kill -9 $GRASS_PID
    else
        echo "No grass_freeproxy.py process found to stop."
    fi
}

while true; do
    echo "Starting auto process..."
    auto
    RANDOM_SLEEP=$((RANDOM % 60 * 10))
    sleep $RANDOM_SLEEP
    stop_grass
done
