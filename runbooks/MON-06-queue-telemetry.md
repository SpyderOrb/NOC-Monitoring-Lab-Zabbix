# MON-06 — Stopped queue telemetry publisher

Scope: disposable `linux-target` guest with the [queue service and current template](../docs/QUEUE-DEMO.md). Begin with fresh queue metrics and all three queue triggers OK. Verify the guest hostname; run this only on the target.

Stop the service for 120 seconds, retaining its last JSON file, then restart it:

```bash
sudo bash -c '
set -e
trap "systemctl start noc-queue" EXIT
systemctl stop noc-queue
date -u "+QUEUE stopped: %Y-%m-%d %H:%M:%S UTC"
sleep 120
systemctl start noc-queue
date -u "+QUEUE started: %Y-%m-%d %H:%M:%S UTC"
trap - EXIT
'
systemctl is-active noc-queue
```

While stopped, Agent 2 can still read the old JSON. Latest data checks may stay recent, but the telemetry timestamp must stop advancing. Expect **Queue: Telemetry is stale or missing** to enter PROBLEM. This exercises the timestamp-age branch, not `nodata()`.

After restart, verify `active`, advancing telemetry/worker timestamps, worker age near 0, and automatic telemetry recovery. The corrected worker-age trigger should avoid the extra startup warning seen with the original expression. Restart resets this simulator's jobs and counters; depth 0 after restart is not evidence that pre-stop jobs were processed.

The EXIT trap attempts to restart the service after errors or Ctrl+C; it cannot run after SIGKILL. If interrupted, check service state and, if needed, run `sudo systemctl start noc-queue` on the target.

The corrected October 6 trial detected stale telemetry approximately 62s after the stop reference and recognized recovery 2s after the restart reference. No new worker warning was visible in that run. These are single-trial observations, not timing guarantees. The initial trial's transient warning is retained in the [evidence](../docs/evidence/2026-10-06-queue-telemetry.txt); the [regression screenshot](../docs/evidence/2026-10-06-queue-telemetry-retest.png) records the corrected result.
