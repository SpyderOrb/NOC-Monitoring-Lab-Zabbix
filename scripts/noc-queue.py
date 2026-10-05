#!/usr/bin/env python3
"""Small in-memory job queue for learning application monitoring on Linux."""

import argparse
from collections import deque
import fcntl
import json
from pathlib import Path
import signal
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--duration", type=int, default=0,
                        help="Stop after this many seconds; 0 runs until interrupted")
    args = parser.parse_args()
    if args.duration < 0:
        parser.error("duration must be nonnegative")
    args.state_dir.mkdir(parents=True, exist_ok=True)
    # Prevent two instances from publishing to the same directory.
    lock = (args.state_dir / "queue.lock").open("a")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.exit(1, "Another queue instance is using this state directory.\n")

    stopping = False

    def stop(_signum, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    queue = deque()
    capacity = 100
    produced = processed = rejected = 0
    started = time.monotonic()
    next_produce = started + 2
    next_work = started + 1
    next_publish = started
    last_worker_seen = 0
    print(f"Queue started; telemetry: {args.state_dir / 'metrics.json'}", flush=True)
    while not stopping:
        now = time.monotonic()
        if args.duration and now - started >= args.duration:
            break
        paused = (args.state_dir / "pause-worker").exists()
        if now >= next_produce:
            next_produce = now + 2
            if len(queue) < capacity:
                produced += 1
                queue.append(produced)
            else:
                rejected += 1
        if now >= next_work:
            next_work = now + 1
            if not paused:
                last_worker_seen = int(time.time())
                if queue:
                    queue.popleft()
                    processed += 1
        if now >= next_publish:
            next_publish = now + 1
            metrics = {
                "schema_version": 1,
                "updated_at": int(time.time()),
                "queue_depth": len(queue),
                "queue_capacity": capacity,
                "produced_total": produced,
                "processed_total": processed,
                "rejected_total": rejected,
                "worker_paused": int(paused),
                "worker_last_seen": last_worker_seen,
            }
            # Atomic replacement keeps readers from seeing half-written JSON.
            temporary = args.state_dir / "metrics.json.tmp"
            temporary.write_text(json.dumps(metrics) + "\n", encoding="utf-8")
            temporary.replace(args.state_dir / "metrics.json")
        time.sleep(0.1)
    print("Queue stopped; final telemetry remains for inspection.", flush=True)
    lock.close()


if __name__ == "__main__":
    main()
