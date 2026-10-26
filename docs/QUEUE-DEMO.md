# Application queue demonstration

This demo adds application checks to the host monitoring. A producer adds jobs and a worker processes them. Pausing the worker lets the queue grow while telemetry keeps updating; stopping the entire service leaves a readable but outdated metrics file.

Worker, backlog and stale-file alerts all produced problem and recovery events in the recorded tests. A restart warning led to a change in the worker-age calculation and two follow-up tests. Those results use the [October 6 export](../configs/zabbix/recorded/noc-queue-template-2026-10-06.yaml). The current source also contains an [offline-tested startup fix](#startup-fix-and-upgrade-order), which has not been deployed or tested in Zabbix.

`scripts/noc-queue.py` uses the Python standard library on Linux. One process simulates a producer (one job every two seconds) and worker (one job per second). Jobs are integer IDs in an in-memory deque, not external business tasks. Maximum queue depth is 100; excess arrivals increment a rejection counter. Restart resets the queue and counters. There is no unbounded job file or per-job log.

Run with `--state-dir DIRECTORY`; optional `--duration SECONDS` stops a preliminary run automatically. Without a duration, SIGINT/SIGTERM stops the process. An exclusive file lock prevents concurrent instances using the same directory. The state directory must be dedicated to this demo.

Telemetry is replaced atomically once per second in `metrics.json`. Fields include queue_depth, queue_capacity, produced_total, processed_total, rejected_total, worker_paused, worker_last_seen, updated_at and started_at. Timestamps are Unix seconds. The new `started_at` field is fixed for each process lifetime and changes on restart; it is an additive field in schema version 1. Worker heartbeat advances even when the queue is empty; before its first tick it is 0.

A file named `pause-worker` in the state directory pauses simulated processing while production and telemetry continue. Removing that flag resumes processing. This permits distinguishing an application worker stall from an unavailable agent or stale telemetry publisher. Stopping the whole script leaves the last JSON file in place, so monitoring must separately detect an old updated_at value; repeated reads alone do not prove freshness.

Local smoke checks covered normal processing, duplicate-instance rejection, growing backlog and frozen worker heartbeat during pause, resumed draining, and bounded process exit. These are script tests, not Zabbix integration or guest fault results. Guest service deployment and master-item collection are operator-confirmed; worker-stall and backlog detection/recovery are operator-confirmed in one guest trial.

## Persistent guest deployment

The supplied `configs/systemd/noc-queue.service` runs as a dedicated unprivileged `noc-queue` account. Install the script root-owned under `/opt/noc-queue/noc-queue.py` and the unit under `/etc/systemd/system/noc-queue.service`. Create a system user/group named noc-queue with no login or home directory before starting. StateDirectory creates `/var/lib/noc-queue` owned by that account; mode 0755 and umask 0022 allow the Zabbix agent to read the non-secret JSON. ProtectSystem=strict and ProtectHome=yes limit writes to the service state directory. A failed process restarts after 5 s; normal administrative stop is not restarted.

After validating the unit, reload systemd and enable/start noc-queue. Verify active state, boot enablement and JSON readability as the zabbix user. Production use would require a separate design; this remains an in-memory educational simulator. No real business jobs are persisted.

For a fresh target, first copy [noc-queue.py](../scripts/noc-queue.py) and [noc-queue.service](../configs/systemd/noc-queue.service) into `~/lab-install/` inside **linux-target**. Agent 2 must already be installed so the `zabbix` account exists. Run the following there, one command at a time, stopping on errors. Create the service account only if it does not already exist; inspect an existing account before reusing it.

```bash
hostname
sudo useradd --system --user-group --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin noc-queue
sudo install -d -o root -g root -m 0755 /opt/noc-queue
sudo install -o root -g root -m 0644 ~/lab-install/noc-queue.py /opt/noc-queue/noc-queue.py
sudo install -o root -g root -m 0644 ~/lab-install/noc-queue.service /etc/systemd/system/noc-queue.service
sudo systemd-analyze verify /etc/systemd/system/noc-queue.service
sudo systemctl daemon-reload
sudo systemctl enable --now noc-queue
systemctl is-active noc-queue
systemctl is-enabled noc-queue
sudo -u zabbix cat /var/lib/noc-queue/metrics.json
```

Expect hostname `linux-target`, then `active`, `enabled` and readable JSON. Compare two JSON samples a few seconds apart: both timestamps should advance and `processed_total` should increase. A sample taken immediately at startup can have heartbeat 0; wait for the first worker tick before testing. Installing these files on the monitoring server would not deploy the target service.

## Verified Zabbix collection

Create a template named `NOC Queue by Zabbix agent` in `Templates/Applications`. Add a passive Zabbix agent item named `Queue: Raw metrics`, key `vfs.file.contents[/var/lib/noc-queue/metrics.json]`, information type Text, update interval 10 s and history 1 d. Link the template to linux-target alongside Linux by Zabbix agent. No custom agent parameter is required.

The current template has five items:

| Item | Key | Source |
|---|---|---|
| Raw metrics | `vfs.file.contents[/var/lib/noc-queue/metrics.json]` | Passive agent; reads the JSON file every 10s |
| Queue depth | `noc.queue.depth` | JSONPath `$.queue_depth` |
| Worker last seen | `noc.queue.worker.last_seen` | JSONPath `$.worker_last_seen`; Unix timestamp |
| Telemetry updated at | `noc.queue.updated_at` | JSONPath `$.updated_at`; Unix timestamp |
| Worker heartbeat age | `noc.queue.worker.age` | JavaScript: age of the last heartbeat, or process startup before the first heartbeat, from one JSON sample |

All four dependent items use the raw item as their master, Numeric (unsigned), one day of history and no trends. In the recorded October 6 version, age returns 0 before the first heartbeat. The revised source uses elapsed time since `started_at` until a real heartbeat arrives. Recorded guest samples show fresh JSON, advancing timestamps and a healthy worker age of 0 after recovery; they do not validate the newer startup behavior.

**Recorded-version limit:** if `pause-worker` already exists at startup, the October 6 preprocessing keeps worker age at 0 indefinitely. That version cannot detect the initial worker pause. The source fix below addresses this case; no guest update is claimed. Begin the existing MON-05 trial from an advancing, nonzero heartbeat.

## Startup fix and upgrade order

The revised simulator publishes its process start time without inventing a worker heartbeat. [Preprocessing](../configs/zabbix/queue-worker-age.js) uses `updated_at - started_at` while `worker_last_seen` is zero, then `updated_at - worker_last_seen` once the worker runs. Both values come from the same JSON sample. A pause present at startup can now produce age greater than the existing 30-second threshold; a normal restart begins at age zero. Wall-clock rollback remains clamped to zero, so synchronized guest/server clocks are still required.

Missing, negative, fractional or nonnumeric timestamps produce a preprocessing error. In particular, an older sample with heartbeat zero and no `started_at` cannot silently appear healthy. Older samples with a valid nonzero heartbeat remain readable. Zabbix supports errors raised from its [JavaScript preprocessing function body](https://www.zabbix.com/documentation/7.0/en/manual/config/items/preprocessing/javascript).

The following upgrade sequence is proposed and **has not been performed in the lab**:

1. Preserve the installed script and export the current queue template. On the target, install the revised simulator and restart its service in a planned test window; restart clears this demo's in-memory jobs and counters. Confirm fresh JSON contains `started_at`. The old template tolerates the extra field.
2. In the queue template's `Queue: Worker heartbeat age` item, replace only the JavaScript preprocessing body with the supplied source. The revised YAML is an alternative for a separate import test; it retains the original template/item UUIDs and would update the existing template, not create an independent copy. Keep unrelated settings and triggers unchanged.
3. Verify normal startup, a worker paused before its first heartbeat, pause/recovery after normal work, and publisher restart. Capture fresh samples and actual Zabbix problem/recovery events before claiming integration success or replacing the recorded export. Remove the pause flag and restore healthy processing at the end of each trial.

For rollback, restore the prior preprocessing first. Its old zero-heartbeat behavior works with the extra JSON field. Restore the saved simulator too if needed; restarting it again resets the in-memory queue. This rollback also restores the documented initial-pause limitation.

## Offline regression checks

On Linux, run `python3 -m unittest discover -s tests -v` from the repository root with Python 3.9+ and Node.js installed. No additional Python or npm packages are needed. The same command runs in [GitHub Actions](../.github/workflows/check-queue.yml).

The [tests](../tests/test_queue.py) exercise the actual simulator loop with a controlled clock for normal startup, initial pause/recovery, a later pause and healthy/paused restarts. They execute the preprocessing against the generated samples, reject invalid timestamps, preserve the recorded export and check source/template equality. One real subprocess check covers duplicate-instance rejection, graceful shutdown and lock release. Temporary state stays outside the lab; no guest services are contacted. Node checks the function's logic, not Zabbix's Duktape integration, trigger scheduling or import schema.

## Alert conditions

The template trigger `Queue: Telemetry is stale or missing` (Average) is inherited, enabled and OK on linux-target, with no visible Info error. Its expression is `now()-last(/NOC Queue by Zabbix agent/noc.queue.updated_at)>60 or nodata(/NOC Queue by Zabbix agent/noc.queue.updated_at,1m)=1`. It checks file timestamp age separately from absence of dependent samples. The publisher-stop trial verified its stale-file age branch, with approximate detection 68 s and recovery 8 s. The no-data branch remains untested.

The Warning trigger `Queue: Worker heartbeat stalled` is also inherited, enabled and OK with no visible Info error. Current expression: `last(/NOC Queue by Zabbix agent/noc.queue.worker.age)>30 and now()-last(/NOC Queue by Zabbix agent/noc.queue.updated_at)<=30`. This replaced the original comparison against worker_last_seen after restart noise was observed. It assesses stalled processing only while the telemetry timestamp is fresh. Loss of telemetry can clear this condition without proving worker recovery; the separate freshness alert then owns the loss of visibility. The worker pause/recovery trial passed on October 6.

The Warning trigger `Queue: Backlog is high` is inherited, enabled and OK. Problem expression: `min(/NOC Queue by Zabbix agent/noc.queue.depth,1m)>10`; OK event generation uses recovery expression `last(/NOC Queue by Zabbix agent/noc.queue.depth)<3`. These separate thresholds provide hysteresis. Backlog fault/recovery passed on October 6; the saved dependency on Queue: Telemetry is stale or missing is verified, but suppression during a parent fault has not been tested.

## Worker pause and recovery — October 6, 2026

A 150-second guest-only worker pause left production and JSON publishing active. Worker stall opened 32 s after the pause reference; backlog opened 72 s after it. Removing the flag restored worker heartbeat, resolving that event 2 s after the resume reference. Backlog resolved 152 s after resume, once accumulated jobs drained; a subsequent fresh sample showed depth 0. These are approximate single-trial observations. [UTC evidence and limits](evidence/2026-10-06-queue-worker.txt) · [Resolved events](evidence/2026-10-06-queue-resolved.png) · [Drained queue](evidence/2026-10-06-queue-drained.png) · [Repeatable runbook](../runbooks/MON-05-queue-worker.md).

## Publisher stop — October 6, 2026

The service was administratively stopped for 120 s. Its final JSON remained readable through Agent 2. The telemetry alert opened 13:36:58 UTC and automatically resolved 13:37:58 after restart. Fresh advancing timestamps and depth 0 confirm final healthy state. A transient worker alert also opened and resolved at 13:37:58 (displayed duration 0); this is a known restart-noise issue, not a clean worker-alert acceptance. [Evidence and limits](evidence/2026-10-06-queue-telemetry.txt) · [Events including transient warning](evidence/2026-10-06-queue-telemetry-resolved.png).

Correction verified in the recorded regressions: a dependent `noc.queue.worker.age` item uses the JavaScript preserved in the [October 6 export](../configs/zabbix/recorded/noc-queue-template-2026-10-06.yaml) on the raw JSON. This computes timestamp difference from one sample, with 0 during the initial pre-heartbeat tick. The inherited worker trigger references this derived age and was verified enabled/OK without a visible error. One publisher-restart regression passed after this change: detection 62 s, recovery 2 s and no new worker warning visible. A 45-second positive worker-pause check passed: detection 36 s, recovery 1 s and worker age 0 after resume.

The corrected publisher-stop regression used stop/start references 13:45:06/13:47:06 UTC. Telemetry event 13:46:08→13:47:08 automatically resolved; final depth 0, worker age 0 and advancing timestamps confirm recovery. [Regression event](evidence/2026-10-06-queue-telemetry-retest.png). Absence of a new worker warning is verified for this one run, not every scheduling possibility.

The corrected worker trigger also detected a real 45-second pause (references 13:49:32→13:50:17 UTC). Its event 13:50:08→13:50:18 automatically resolved. Subsequent fresh telemetry showed worker age 0 and depth 12 decreasing by 5 per sample; the final drained sample for this short regression was not supplied. [Positive regression event](evidence/2026-10-06-queue-worker-retest.png).

[Repeatable publisher-stop runbook](../runbooks/MON-06-queue-telemetry.md).
