# Validation results

## Results at a glance

The results below come from manual lab tests, recorded terminal output and Zabbix screenshots. Timings are approximate delays from the action timestamps in individual trials, not guaranteed response times.

| Test | Observed result | Detection / recovery |
|---|---|---|
| Nginx stopped | HTTP problem cleared after restart | About 24 s / 7 s |
| Target VM shut down | HTTP and agent problems cleared after boot | HTTP: 22 s / 51 s; agent: 3m 44s / 1m 46s; recovery measured from a pre-start reference |
| HTTP 200, wrong content | Required-text check failed, then cleared after correct content was restored | Exact action-to-event delays not established |
| CPU load | 100% CPU observed; warning cleared after the load ended | About 6m 39s / 22 s from recorded references |
| Worker paused for 150 s | Worker recovered first; backlog cleared after draining | Worker: 32 s / 2 s; backlog: 72 s / 152 s |
| Publisher stopped — corrected retest | Old JSON timestamp detected; recovery without an extra worker warning visible | About 62 s / 2 s |
| Worker paused for 45 s — corrected retest | Real worker stall still detected after the restart correction | About 36 s / 1 s |

The dashboard and offline configuration-export checks are also verified. Fresh-instance import, the queue `nodata()` branch and backlog-dependency suppression during a parent fault have not been tested. The original restart warning and the subsequent correction are documented below.

The October 7 repository review added [monitoring setup instructions](MONITORING.md) and explicit queue installation commands without changing the guests or exported templates. A local simulator/preprocessing check reproduced the [initially paused worker detection gap](QUEUE-DEMO.md#verified-zabbix-collection); this adds a known limit, not a new Zabbix fault/recovery result.

## Manual Ubuntu baseline — 2026-10-02–03

Both guests were installed manually through virt-manager using the verified Ubuntu Server ISO. The checks below are based on operator-provided console/SSH output; local SSH configuration was also inspected. See the [concise evidence record](evidence/2026-10-02-manual-baseline.txt).

| Check | Observed result |
|---|---|
| Installation media | ISO SHA256 matched the manifest; its signature verified against the official Ubuntu CD-image key. |
| Guest installation | Both guests booted Ubuntu 24.04.5 LTS, kernel `6.8.0-146-generic`. Separate disks, BIOS boot, ext4 root partitions without LVM. |
| Resources | Server: 2 vCPU / 4 GiB / 25 GiB. Target: 1 vCPU / 2 GiB / 16 GiB. Disk capacities are virtual, not measured physical usage. |
| Address persistence | Reservations present in live and persistent libvirt network XML. Following guest restarts, server used `192.168.77.10/24`, target `.20/24`, both with gateway `.1`. |
| Host-to-guest SSH | Password bootstrap and subsequent explicit key-only login tests returned the expected hostname and user on both guests. Project-local aliases were tested. Password authentication remains enabled. |
| Repository access and updates | Both guests successfully refreshed APT indexes and completed package upgrades. Post-update SSH sessions were established after instructed restarts. |
| Post-update health | Both showed zero failed systemd units and no findings from `sudo dpkg --audit`. Reserved addresses remained present. |
| Inter-guest reachability — October 3 | Three ICMP requests succeeded in each direction, with zero packet loss. This checks IP reachability, not application ports. |

**Still pending for this build:** independent DNS checks, QEMU guest-agent verification, and full physical-host reboot behavior. Successful repository access is narrower evidence than an exhaustive network test. Historical results below do not establish these checks for the new guests.

## Server self-monitoring — 2026-10-04

Operator-provided terminal output confirms Zabbix server/frontend/Agent 2 packages `1:7.0.31-1+ubuntu24.04`, PostgreSQL cluster `16/main` online, and enabled/running Zabbix server. Nginx configuration validation passed; Nginx and PHP 8.3 FPM were active. The frontend was reached on port 8080 and administrator login succeeded. Server time synchronization was also confirmed.

A Latest data screenshot shows CPU utilization **2.8777%** (last check 55 seconds earlier), available memory **3.1 GB** (16 seconds), and root-filesystem data (42 seconds), including **93.4309% free inodes**. These are observed samples, not performance benchmarks. The view reports 117 normal items and 11 unsupported items; startup logs identify disabled optional-process checks, and the complete unsupported list has not been reviewed.

## Initial target collection — 2026-10-04

Operator output confirms target Agent 2 version 7.0.31, enabled/running with successful configuration validation, agent hostname `linux-target`, and a TCP listener on port 10050. A Latest data screenshot filtered to `linux-target` shows 68 items and fresh CPU values: idle **99.8567%** (26 seconds earlier) and iowait **0.05574%** (22 seconds). This verifies initial remote collection, not just a listening service. Available memory was also verified at **1.61 GB / 83.7653%**, checked 25/24 seconds earlier. The latest captured state shows 67 normal items and one unsupported item: interface speed rejects a negative value (`-1000000`). The guest sysfs speed source was confirmed as `-1`; nominal link speed is unavailable on this virtual interface. The operator reports disabling only that speed item. Speed-based utilization checks are therefore outside the verified scope. Disk and interface discovery tags were present but their sampled values were not shown.

A subsequent October 5 screenshot verifies fresh target root-filesystem samples (all checked 52 s earlier): space used **32.6297% / 4.84 GB**, available **9.99 GB**, total **15.64 GB**, free inodes **90.5097%**, read-only flag **0**. These are reported filesystem metrics, not the virtual disk capacity. [Screenshot](evidence/2026-10-05-target-root-filesystem.png).

**Export status:** target host YAML captured and inspected; Linux and custom queue template exports are captured and inspected; the host export is refreshed with both links; fresh-instance import is untested and deferred.

## Target HTTP endpoint — 2026-10-05

Operator output confirms target Nginx package `1.24.0-2ubuntu7.18` and an active service. A request from the monitoring server to `http://192.168.77.20/health.txt` returned HTTP 200 and the marker `NOC-LAB-HTTP-OK`. The Zabbix web scenario `HTTP health` was subsequently verified with six normal web items, failed step `0`, response code `200` and a response-time sample of **1.44 ms**. Its configured interval is 30 seconds, with one attempt and a 5-second step timeout; these are not measured detection timings. The HTTP trigger was verified enabled and OK before testing. During a target-only Nginx stop, the failed-step value changed to `1`; after restart it returned to `0` with a fresh HTTP 200 response. Command completion timestamps were **16:23:07 UTC** (stop) and **16:24:24 UTC** (start), 77 seconds apart. Event history confirms **RESOLVED**, with problem at **16:23:31 UTC** and recovery at **16:24:31 UTC**: approximately **24 seconds to detect** and **7 seconds to recognize recovery**, measured from command completion. Recorded problem duration was 60 seconds. This is one trial, not a latency guarantee. See the [test evidence and limits](evidence/2026-10-05-http-fault.txt).

## Target VM outage — 2026-10-05

Operator screenshots confirm a graceful target shutdown request at **16:40:42 UTC**. The HTTP problem appeared at **16:41:04 UTC** (22 s later), and the passive-agent availability problem at **16:44:26 UTC** (3m 44s later). The enabled agent trigger uses `max(/linux-target/zabbix[host,agent,available],{$AGENT.TIMEOUT})=0`; the effective macro was verified as `3m`.

The operator recorded **16:44:40 UTC** immediately before the intended VM start action. HTTP automatically resolved at **16:45:31 UTC** (51 s after that reference); agent availability automatically resolved at **16:46:26 UTC** (1m 46s). Event durations were 4m 27s and 2 m respectively. A post-boot SSH check returned `active` for both Nginx and Agent 2. A separate recent-restart warning remained visible at that point; subsequent CPU-test screenshots confirm it resolved at 16:55:30 UTC.

This is one completed trial. Recovery measurements include boot and monitoring delays, plus any gap between the host timestamp and the start click. The timestamp is not proof of exact VM power-on time; cross-machine clock accuracy was not independently measured. Agent unavailability alone does not distinguish VM shutdown from an agent or network failure. See [evidence](evidence/2026-10-05-vm-outage.txt) and [runbook](../runbooks/MON-02-vm-outage.md).

## Bounded CPU load — 2026-10-05

Operator output confirms `nproc=1` and a single `yes` process bounded by `timeout --kill-after=5s 8m`, inside the target. Latest data and its graph show **100% CPU**. The enabled Warning trigger was `min(/linux-target/system.cpu.util,5m)>{$CPU.UTIL.CRIT}`, with effective threshold 90 and a dependency on the load-average trigger.

The pre-load reference was **16:50:45 UTC**; the CPU problem appeared at **16:57:24 UTC**, **6m 39s later**. The operator recorded the post-load timestamp **16:59:02 UTC** and timeout exit code **124**. Automatic recovery occurred at **16:59:24 UTC**, **22 s after that timestamp**, with a recorded event duration of 2 m. Separate interactive commands introduce gaps around the actual load start/end: the reference timestamps are 8m 17s apart, while the configured timeout was 8 m. These differences are approximate reference-to-event timings, not exact process-to-event latencies.

The fault/recovery trial passed. A subsequent Latest data screenshot confirms CPU **0.2338%**, checked 5 s earlier. The [recovery graph](evidence/2026-10-05-cpu-recovery-graph.png) shows the 100% plateau returning to baseline (graph last value 0.1838%, a separate sample). No repeated load test is required. See [evidence](evidence/2026-10-05-cpu-load.txt) and [runbook](../runbooks/MON-03-cpu-load.md).

## HTTP content mismatch — 2026-10-05

An additional trial changed the target health marker while keeping Nginx reachable. Both a server-side request and fresh Zabbix values showed HTTP 200, while the web scenario failed its required-pattern check. The HTTP event opened at 19:29:01 UTC and automatically resolved at 19:36:01 UTC after the correct marker was restored on the target, lasting 7 m. An initial restoration on the wrong guest delayed recovery. Separate post-change terminal timestamps cannot establish exact detection/recovery latency. [Evidence and limits](evidence/2026-10-05-http-content.txt) · [Resolved event](evidence/2026-10-05-http-content-resolved.png).

## Overview dashboard — 2026-10-05

Screenshots verify six widgets in `NOC Lab Overview`: target agent availability, CPU utilization, available memory percentage, root-disk used percentage, current problems for both lab hosts, and target HTTP scenario status. Visible values included available (1.00), CPU 0.22%, memory 84.28%, root disk 32.63% and HTTP Ok 1, with no current problems. The operator subsequently confirmed that data updates and the layout persists after a browser reload. This verifies the basic dashboard; global dashboard export and restoration have not been tested; the setup recipe is documented.

[Dashboard setup](DASHBOARD.md)

## Configuration export — 2026-10-05

The operator exported the target host from the frontend. The inspected YAML contains one host, the passive-agent interface, the Linux template link, the HTTP scenario and its custom trigger. The original export was inspected for scope and secrets; the [public copy](../configs/zabbix/linux-target.yaml) was subsequently refreshed on October 6 to include both template links. This is content inspection, not an import or server-schema validation. Linked template contents, global dashboard, history and the discovered speed-item exclusion are not present. [Restoration prerequisites and limits](../configs/zabbix/README.md).

## Application queue collection — 2026-10-05

The operator verified Python 3.12.3, a 30-second processing baseline, and the enabled/active noc-queue guest service. The zabbix account can read its JSON. History screenshots subsequently show five fresh Queue: Raw metrics samples 10 s apart: produced/processed counters 225→245, depth 0, rejected 0, paused 0 and advancing telemetry/worker timestamps. This confirms passive collection through the custom template. Dependent metrics and worker/backlog triggers were subsequently verified; the custom template export was subsequently captured and inspected, with import untested. [Implementation and scope](QUEUE-DEMO.md).

## Application worker pause — 2026-10-06

A 150-second worker-only pause produced growing depth and a frozen worker heartbeat while telemetry continued. Worker warning opened 13:25:48 UTC and resolved 13:27:48; backlog warning opened 13:26:28 and resolved 13:30:18. Pause/resume references 13:25:16/13:27:46 give approximate detection delays 32 s/72 s and recovery delays 2 s/152 s respectively. Final fresh sample at 13:30:28 showed depth 0 and both timestamps advancing. Both events automatically resolved in one trial. Exact maximum depth/rejection count, dependency suppression and custom-template restoration remain unverified. Stale-publisher results are recorded below. [Evidence](evidence/2026-10-06-queue-worker.txt) · [Runbook](../runbooks/MON-05-queue-worker.md).

## Stopped queue publisher — 2026-10-06

Stop/start references 13:35:50/13:37:50 UTC bound a 120-second service stop. The retained JSON stayed readable; telemetry event 13:36:58→13:37:58 automatically resolved (approximate detection 68 s, recovery 8 s). Service active, depth 0 and advancing timestamps 13:38:07 confirm recovery. However, a worker warning opened/resolved at 13:37:58 (duration 0), exposing restart noise. Its precise cause is unproven; initial heartbeat 0 and mixing separate dependent timestamp samples are plausible mechanisms. A derived age from a single JSON snapshot was subsequently deployed and the inherited worker trigger updated. A 120-second publisher-stop regression opened telemetry at 13:46:08 and resolved 13:47:08 UTC (stop/start references 13:45:06/13:47:06; approximate 62 s/2 s delays), with no new worker warning visible. Final service active, depth 0, worker age 0 and fresh timestamps 13:47:27 confirm recovery. A subsequent 45-second worker pause confirmed positive detection/recovery with the changed expression: pause/resume 13:49:32/13:50:17 UTC, event 13:50:08→13:50:18, approximate 36 s/1 s delays. After resume worker age 0 and fresh timestamps confirmed liveness; depth 12 was still decreasing. Complete drain for this short regression was not captured; the earlier full backlog trial remains valid. No-data branch and dependency suppression are untested. [Evidence](evidence/2026-10-06-queue-telemetry.txt).

## Historical cloud-image baseline — 2026-09-27

The earlier automated build used different allocations, UEFI and kernel `6.8.0-142-generic`. It passed its own cloud-init, SSH, bidirectional ICMP, DNS/time and QEMU guest-agent checks. Those guests were subsequently replaced by the manual build above.

[Historical observations](evidence/2026-09-27-guest-baseline.txt) are retained as dated evidence, not current-state claims. Private workstation details, credentials and session logs remain outside Git.

## Custom queue export — 2026-10-06

The inspected [template YAML](../configs/zabbix/noc-queue-template.yaml) contains five items, three triggers, the saved backlog dependency and corrected worker-age preprocessing/expression. Embedded JavaScript matches the reviewed source and the public copy is byte-identical to the operator export. No credentials or personal paths were found. YAML parsing and focused configuration checks subsequently passed. Zabbix server-schema validation and a fresh-instance import remain untested and deferred. [Restoration instructions](../configs/zabbix/README.md).

## Export parameter audit — 2026-10-06

Both template YAML files parse successfully. The installed Linux template is the passive variant, vendor 7.0-4, with 43 regular items and 3 discovery rules; macros `{$AGENT.TIMEOUT}=3m`, `{$CPU.UTIL.CRIT}=90` and `{$LOAD_AVG_PER_CPU.MAX.WARN}=1.5` match the tested settings. Focused checks confirmed UUID format/uniqueness per export, master references, CPU/agent expressions and queue JSONPath/JavaScript, history, units, recovery threshold and dependency. Queue export matches its public copy; the Linux public copy differs only by trimmed trailing whitespace and parses identically. The October 6 refreshed host export links both templates and retains the verified agent address and HTTP scenario/trigger. These are offline checks, not an import test.
