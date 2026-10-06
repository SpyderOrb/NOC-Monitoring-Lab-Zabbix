# MON-05 — Paused worker and accumulated backlog

Scope: disposable linux-target guest running the [queue simulator](../docs/QUEUE-DEMO.md), with five supported queue items and three enabled triggers in normal state. Do not run on the physical host or monitoring server. Verify guest hostname before starting.

On linux-target, pause the simulated worker for150s while leaving production and telemetry running:

```bash
sudo -u noc-queue bash -c '
set -e
trap "rm -f /var/lib/noc-queue/pause-worker" EXIT
touch /var/lib/noc-queue/pause-worker
date -u "+WORKER paused: %Y-%m-%d %H:%M:%S UTC"
sleep 150
rm -f /var/lib/noc-queue/pause-worker
date -u "+WORKER resumed: %Y-%m-%d %H:%M:%S UTC"
'
```

In Latest data, expect growing depth, a frozen worker timestamp and advancing telemetry timestamp. In Problems, capture Worker heartbeat stalled followed by Backlog is high. Telemetry freshness should remain healthy. After automatic resume, expect heartbeat recovery first, then backlog recovery after approximately another150s of draining. Verify both events automatically RESOLVED, depth0–2 and advancing timestamps; do not manually close events.

EXIT cleanup also attempts flag removal after errors or Ctrl+C; it cannot run after SIGKILL. If needed, remove only this demo flag on linux-target: `sudo -u noc-queue rm -f /var/lib/noc-queue/pause-worker`. Do not stop the service or fabricate JSON values for this trial. The queue is capped at100; counters and jobs are in-memory and reset on service restart.

The October6 trial passed:150s pause, worker detection32s and recovery2s relative to action references; backlog detection72s and recovery152s. Delays are single-trial approximations, not guaranteed bounds. Maximum depth and rejection count were not captured. [Evidence](../docs/evidence/2026-10-06-queue-worker.txt).

After switching the worker trigger to single-JSON derived age, a45-second positive regression passed (36s detection,1s recovery; fresh workerage0 afterward). The unchanged backlog threshold was already verified by the150-second trial. [Regression event](../docs/evidence/2026-10-06-queue-worker-retest.png).
