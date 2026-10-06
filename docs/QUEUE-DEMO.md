# Application queue demonstration

Verified scope: the guest service runs with Python 3.12.3 and publishes readable JSON. Agent 2 collects the raw master item every 10 seconds; four dependent items expose depth, worker last seen, telemetry updated at and worker heartbeat age. Worker-stall, backlog and stale-file detection/recovery passed guest trials. A transient worker alert during publisher restart led to a derived-age correction, followed by successful restart and worker-pause regression checks. The template export passed offline checks; fresh-instance import is untested and deferred.

`scripts/noc-queue.py` uses the Python standard library on Linux. One process simulates a producer (one job every two seconds) and worker (one job per second). Jobs are integer IDs in an in-memory deque, not external business tasks. Maximum queue depth is100; excess arrivals increment a rejection counter. Restart resets the queue and counters. There is no unbounded job file or per-job log.

Run with `--state-dir DIRECTORY`; optional `--duration SECONDS` stops a preliminary run automatically. Without a duration, SIGINT/SIGTERM stops the process. An exclusive file lock prevents concurrent instances using the same directory. The state directory must be dedicated to this demo.

Telemetry is replaced atomically once per second in `metrics.json`. Fields include queue_depth, queue_capacity, produced_total, processed_total, rejected_total, worker_paused, worker_last_seen and updated_at. Timestamps are Unix seconds. Worker heartbeat advances even when the queue is empty; before its first tick it is0.

A file named `pause-worker` in the state directory pauses simulated processing while production and telemetry continue. Removing that flag resumes processing. This permits distinguishing an application worker stall from an unavailable agent or stale telemetry publisher. Stopping the whole script leaves the last JSON file in place, so monitoring must separately detect an old updated_at value; repeated reads alone do not prove freshness.

Local smoke checks covered normal processing, duplicate-instance rejection, growing backlog and frozen worker heartbeat during pause, resumed draining, and bounded process exit. These are script tests, not Zabbix integration or guest fault results. Guest service deployment and master-item collection are operator-confirmed; worker-stall and backlog detection/recovery are operator-confirmed in one guest trial.

## Persistent guest deployment

The supplied `configs/systemd/noc-queue.service` runs as a dedicated unprivileged `noc-queue` account. Install the script root-owned under `/opt/noc-queue/noc-queue.py` and the unit under `/etc/systemd/system/noc-queue.service`. Create a system user/group named noc-queue with no login or home directory before starting. StateDirectory creates `/var/lib/noc-queue` owned by that account; mode0755 and umask0022 allow the Zabbix agent to read the non-secret JSON. ProtectSystem=strict and ProtectHome=yes limit writes to the service state directory. A failed process restarts after5s; normal administrative stop is not restarted.

After validating the unit, reload systemd and enable/start noc-queue. Verify active state, boot enablement and JSON readability as the zabbix user. Production use would require a separate design; this remains an in-memory educational simulator. No real business jobs are persisted.

## Verified Zabbix collection

Create a template named `NOC Queue by Zabbix agent` in `Templates/Applications`. Add a passive Zabbix agent item named `Queue: Raw metrics`, key `vfs.file.contents[/var/lib/noc-queue/metrics.json]`, information type Text, update interval10s and history1d. Link the template to linux-target alongside Linux by Zabbix agent. No custom agent parameter is required.

Operator-provided History shows five samples at10-second intervals, with produced_total and processed_total advancing together from225 to245, queue_depth0, rejected_total0 and worker_paused0. Both updated_at and worker_last_seen advance with every sample. This verifies collection and healthy operation, not queue alerting. The [custom template export](../configs/zabbix/noc-queue-template.yaml) has been captured and inspected; fresh-instance import remains untested.

Dependent items use Numeric (unsigned), history1d and trends0, with the raw item as master. JSONPath extracts `$.queue_depth` (key `noc.queue.depth`), `$.worker_last_seen` (`noc.queue.worker.last_seen`) and `$.updated_at` (`noc.queue.updated_at`). Both timestamp items use units `unixtime`. Latest data confirms depth0, all four queue items checked8s earlier, and both timestamps advancing by10s.

## Telemetry freshness trigger

The template trigger `Queue: Telemetry is stale or missing` (Average) is inherited, enabled and OK on linux-target, with no visible Info error. Its expression is `now()-last(/NOC Queue by Zabbix agent/noc.queue.updated_at)>60 or nodata(/NOC Queue by Zabbix agent/noc.queue.updated_at,1m)=1`. It checks file timestamp age separately from absence of dependent samples. The publisher-stop trial verified its stale-file age branch, with approximate detection68s and recovery8s. The no-data branch remains untested.

The Warning trigger `Queue: Worker heartbeat stalled` is also inherited, enabled and OK with no visible Info error. Current expression: `last(/NOC Queue by Zabbix agent/noc.queue.worker.age)>30 and now()-last(/NOC Queue by Zabbix agent/noc.queue.updated_at)<=30`. This replaced the original comparison against worker_last_seen after restart noise was observed. It assesses stalled processing only while the telemetry timestamp is fresh. Loss of telemetry can clear this condition without proving worker recovery; the separate freshness alert then owns the loss of visibility. The worker pause/recovery trial passed on October 6.

The Warning trigger `Queue: Backlog is high` is inherited, enabled and OK. Problem expression: `min(/NOC Queue by Zabbix agent/noc.queue.depth,1m)>10`; OK event generation uses recovery expression `last(/NOC Queue by Zabbix agent/noc.queue.depth)<3`. These separate thresholds provide hysteresis. Backlog fault/recovery passed on October 6; the saved dependency on Queue: Telemetry is stale or missing is verified, but suppression during a parent fault has not been tested.

## Worker pause and recovery — October 6, 2026

A150-second guest-only worker pause left production and JSON publishing active. Worker stall opened32s after the pause reference; backlog opened72s after it. Removing the flag restored worker heartbeat, resolving that event2s after the resume reference. Backlog resolved152s after resume, once accumulated jobs drained; a subsequent fresh sample showed depth0. These are approximate single-trial observations. [UTC evidence and limits](evidence/2026-10-06-queue-worker.txt) · [Resolved events](evidence/2026-10-06-queue-resolved.png) · [Drained queue](evidence/2026-10-06-queue-drained.png) · [Repeatable runbook](../runbooks/MON-05-queue-worker.md).

## Publisher stop — October 6, 2026

The service was administratively stopped for120s. Its final JSON remained readable through Agent2. The telemetry alert opened13:36:58UTC and automatically resolved13:37:58 after restart. Fresh advancing timestamps and depth0 confirm final healthy state. A transient worker alert also opened and resolved at13:37:58 (displayed duration0); this is a known restart-noise issue, not a clean worker-alert acceptance. [Evidence and limits](evidence/2026-10-06-queue-telemetry.txt) · [Events including transient warning](evidence/2026-10-06-queue-telemetry-resolved.png).

Correction verified in the recorded regressions: a dependent `noc.queue.worker.age` item uses [JavaScript preprocessing](../configs/zabbix/queue-worker-age.js) on the raw JSON. This computes timestamp difference from one sample, with 0 during the initial pre-heartbeat tick. The inherited worker trigger references this derived age and was verified enabled/OK without a visible error. One publisher-restart regression passed after this change: detection 62s, recovery 2s and no new worker warning visible. A 45-second positive worker-pause check passed: detection 36s, recovery 1s and worker age 0 after resume.

The corrected publisher-stop regression used stop/start references13:45:06/13:47:06UTC. Telemetry event13:46:08→13:47:08 automatically resolved; final depth0,worker age0 and advancing timestamps confirm recovery. [Regression event](evidence/2026-10-06-queue-telemetry-retest.png). Absence of a new worker warning is verified for this one run, not every scheduling possibility.

The corrected worker trigger also detected a real45-second pause (references13:49:32→13:50:17UTC). Its event13:50:08→13:50:18 automatically resolved. Subsequent fresh telemetry showed worker age0 and depth12 decreasing by5 per sample; the final drained sample for this short regression was not supplied. [Positive regression event](evidence/2026-10-06-queue-worker-retest.png).

[Repeatable publisher-stop runbook](../runbooks/MON-06-queue-telemetry.md).
