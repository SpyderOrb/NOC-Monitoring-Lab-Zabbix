# Application queue demonstration

Status: 30-second guest baseline verified with Python 3.12.3: produced14, processed14, depth0, rejected0, worker_paused0. The guest service is active and enabled; JSON is readable as the zabbix user (9 produced/9 processed, depth0, rejected0). Passive-agent collection is verified: the Queue: Raw metrics master item receives fresh JSON every 10 seconds. Dependent metrics, triggers and guest fault/recovery trials remain pending.

`scripts/noc-queue.py` uses the Python standard library on Linux. One process simulates a producer (one job every two seconds) and worker (one job per second). Jobs are integer IDs in an in-memory deque, not external business tasks. Maximum queue depth is100; excess arrivals increment a rejection counter. Restart resets the queue and counters. There is no unbounded job file or per-job log.

Run with `--state-dir DIRECTORY`; optional `--duration SECONDS` stops a preliminary run automatically. Without a duration, SIGINT/SIGTERM stops the process. An exclusive file lock prevents concurrent instances using the same directory. The state directory must be dedicated to this demo.

Telemetry is replaced atomically once per second in `metrics.json`. Fields include queue_depth, queue_capacity, produced_total, processed_total, rejected_total, worker_paused, worker_last_seen and updated_at. Timestamps are Unix seconds. Worker heartbeat advances even when the queue is empty; before its first tick it is0.

A file named `pause-worker` in the state directory pauses simulated processing while production and telemetry continue. Removing that flag resumes processing. This permits distinguishing an application worker stall from an unavailable agent or stale telemetry publisher. Stopping the whole script leaves the last JSON file in place, so monitoring must separately detect an old updated_at value; repeated reads alone do not prove freshness.

Local smoke checks covered normal processing, duplicate-instance rejection, growing backlog and frozen worker heartbeat during pause, resumed draining, and bounded process exit. These are script tests, not Zabbix integration or guest fault results. Guest service deployment and master-item collection are operator-confirmed; queue fault detection and recovery in Zabbix have not yet been tested.

## Persistent guest deployment

The supplied `configs/systemd/noc-queue.service` runs as a dedicated unprivileged `noc-queue` account. Install the script root-owned under `/opt/noc-queue/noc-queue.py` and the unit under `/etc/systemd/system/noc-queue.service`. Create a system user/group named noc-queue with no login or home directory before starting. StateDirectory creates `/var/lib/noc-queue` owned by that account; mode0755 and umask0022 allow the Zabbix agent to read the non-secret JSON. ProtectSystem=strict and ProtectHome=yes limit writes to the service state directory. A failed process restarts after5s; normal administrative stop is not restarted.

After validating the unit, reload systemd and enable/start noc-queue. Verify active state, boot enablement and JSON readability as the zabbix user. Production use would require a separate design; this remains an in-memory educational simulator. No real business jobs are persisted.

## Verified Zabbix collection

Create a template named `NOC Queue by Zabbix agent` in `Templates/Applications`. Add a passive Zabbix agent item named `Queue: Raw metrics`, key `vfs.file.contents[/var/lib/noc-queue/metrics.json]`, information type Text, update interval10s and history1d. Link the template to linux-target alongside Linux by Zabbix agent. No custom agent parameter is required.

Operator-provided History shows five samples at10-second intervals, with produced_total and processed_total advancing together from225 to245, queue_depth0, rejected_total0 and worker_paused0. Both updated_at and worker_last_seen advance with every sample. This verifies collection and healthy operation, not queue alerting. The custom template export is still pending.
