# Validation results

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

A subsequent October 5 screenshot verifies fresh target root-filesystem samples (all checked 52s earlier): space used **32.6297% / 4.84 GB**, available **9.99 GB**, total **15.64 GB**, free inodes **90.5097%**, read-only flag **0**. These are reported filesystem metrics, not the virtual disk capacity. [Screenshot](evidence/2026-10-05-target-root-filesystem.png).

**Pending:** custom dashboard and reusable configuration exports.

## Target HTTP endpoint — 2026-10-05

Operator output confirms target Nginx package `1.24.0-2ubuntu7.18` and an active service. A request from the monitoring server to `http://192.168.77.20/health.txt` returned HTTP 200 and the marker `NOC-LAB-HTTP-OK`. The Zabbix web scenario `HTTP health` was subsequently verified with six normal web items, failed step `0`, response code `200` and a response-time sample of **1.44 ms**. Its configured interval is 30 seconds, with one attempt and a 5-second step timeout; these are not measured detection timings. The HTTP trigger was verified enabled and OK before testing. During a target-only Nginx stop, the failed-step value changed to `1`; after restart it returned to `0` with a fresh HTTP 200 response. Command completion timestamps were **16:23:07 UTC** (stop) and **16:24:24 UTC** (start), 77 seconds apart. Event history confirms **RESOLVED**, with problem at **16:23:31 UTC** and recovery at **16:24:31 UTC**: approximately **24 seconds to detect** and **7 seconds to recognize recovery**, measured from command completion. Recorded problem duration was 60 seconds. This is one trial, not a latency guarantee. See the [test evidence and limits](evidence/2026-10-05-http-fault.txt).

## Target VM outage — 2026-10-05

Operator screenshots confirm a graceful target shutdown request at **16:40:42 UTC**. The HTTP problem appeared at **16:41:04 UTC** (22s later), and the passive-agent availability problem at **16:44:26 UTC** (3m44s later). The enabled agent trigger uses `max(/linux-target/zabbix[host,agent,available],{$AGENT.TIMEOUT})=0`; the effective macro was verified as `3m`.

The operator recorded **16:44:40 UTC** immediately before the intended VM start action. HTTP automatically resolved at **16:45:31 UTC** (51s after that reference); agent availability automatically resolved at **16:46:26 UTC** (1m46s). Event durations were 4m27s and 2m respectively. A post-boot SSH check returned `active` for both Nginx and Agent 2. A separate recent-restart warning remained visible at that point; subsequent CPU-test screenshots confirm it resolved at 16:55:30 UTC.

This is one completed trial. Recovery measurements include boot and monitoring delays, plus any gap between the host timestamp and the start click. The timestamp is not proof of exact VM power-on time; cross-machine clock accuracy was not independently measured. Agent unavailability alone does not distinguish VM shutdown from an agent or network failure. See [evidence](evidence/2026-10-05-vm-outage.txt) and [runbook](../runbooks/MON-02-vm-outage.md).

## Bounded CPU load — 2026-10-05

Operator output confirms `nproc=1` and a single `yes` process bounded by `timeout --kill-after=5s 8m`, inside the target. Latest data and its graph show **100% CPU**. The enabled Warning trigger was `min(/linux-target/system.cpu.util,5m)>{$CPU.UTIL.CRIT}`, with effective threshold 90 and a dependency on the load-average trigger.

The pre-load reference was **16:50:45 UTC**; the CPU problem appeared at **16:57:24 UTC**, **6m39s later**. The operator recorded the post-load timestamp **16:59:02 UTC** and timeout exit code **124**. Automatic recovery occurred at **16:59:24 UTC**, **22s after that timestamp**, with a recorded event duration of 2m. Separate interactive commands introduce gaps around the actual load start/end: the reference timestamps are 8m17s apart, while the configured timeout was 8m. These differences are approximate reference-to-event timings, not exact process-to-event latencies.

The fault/recovery trial passed. A subsequent Latest data screenshot confirms CPU **0.2338%**, checked 5s earlier. The [recovery graph](evidence/2026-10-05-cpu-recovery-graph.png) shows the 100% plateau returning to baseline (graph last value 0.1838%, a separate sample). No repeated load test is required. See [evidence](evidence/2026-10-05-cpu-load.txt) and [runbook](../runbooks/MON-03-cpu-load.md).

## Historical cloud-image baseline — 2026-09-27

The earlier automated build used different allocations, UEFI and kernel `6.8.0-142-generic`. It passed its own cloud-init, SSH, bidirectional ICMP, DNS/time and QEMU guest-agent checks. Those guests were subsequently replaced by the manual build above.

[Historical observations](evidence/2026-09-27-guest-baseline.txt) are retained as dated evidence, not current-state claims. Private workstation details, credentials and session logs remain outside Git.
