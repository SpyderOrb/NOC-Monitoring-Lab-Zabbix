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

**Still pending for this build:** independent DNS checks, target time synchronization, QEMU guest-agent verification, and full physical-host reboot behavior. Successful repository access is narrower evidence than an exhaustive network test. Historical results below do not establish these checks for the new guests.

## Server self-monitoring — 2026-10-04

Operator-provided terminal output confirms Zabbix server/frontend/Agent 2 packages `1:7.0.31-1+ubuntu24.04`, PostgreSQL cluster `16/main` online, and enabled/running Zabbix server. Nginx configuration validation passed; Nginx and PHP 8.3 FPM were active. The frontend was reached on port 8080 and administrator login succeeded. Server time synchronization was also confirmed.

A Latest data screenshot shows CPU utilization **2.8777%** (last check 55 seconds earlier), available memory **3.1 GB** (16 seconds), and root-filesystem data (42 seconds), including **93.4309% free inodes**. These are observed samples, not performance benchmarks. The view reports 117 normal items and 11 unsupported items; startup logs identify disabled optional-process checks, and the complete unsupported list has not been reviewed.

## Initial target collection — 2026-10-04

Operator output confirms target Agent 2 version 7.0.31, enabled/running with successful configuration validation, agent hostname `linux-target`, and a TCP listener on port 10050. A Latest data screenshot filtered to `linux-target` shows 68 items and fresh CPU values: idle **99.8567%** (26 seconds earlier) and iowait **0.05574%** (22 seconds). This verifies initial remote collection, not just a listening service. Available memory was also verified at **1.61 GB / 83.7653%**, checked 25/24 seconds earlier. The latest captured state shows 67 normal items and one unsupported item: interface speed rejects a negative value (`-1000000`). Its raw source value has not yet been verified. Disk and interface discovery tags were present but their sampled values were not shown.

**Pending:** target unsupported-item diagnosis and filesystem-value validation, HTTP service monitoring, custom dashboard, fault/recovery exercises and detection timings.

## Historical cloud-image baseline — 2026-09-27

The earlier automated build used different allocations, UEFI and kernel `6.8.0-142-generic`. It passed its own cloud-init, SSH, bidirectional ICMP, DNS/time and QEMU guest-agent checks. Those guests were subsequently replaced by the manual build above.

[Historical observations](evidence/2026-09-27-guest-baseline.txt) are retained as dated evidence, not current-state claims. Private workstation details, credentials and session logs remain outside Git.
