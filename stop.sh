#!/bin/bash
# stop.sh — Stop ONLY the services started by start.sh (uses .pids file)
# IMPORTANT: Only kills PIDs recorded in .pids — never uses pkill/killall
# which could accidentally kill other processes (e.g. the SDLC backend server).

echo "Stopping GembaONE Platform services..."
if [ -f .pids ]; then
    while IFS= read -r pid; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null && echo "  Stopped PID $pid" || echo "  PID $pid already stopped"
        fi
    done < .pids
    rm -f .pids
    echo "All services stopped"
else
    echo "No .pids file found — services may not be running or were stopped already"
fi
