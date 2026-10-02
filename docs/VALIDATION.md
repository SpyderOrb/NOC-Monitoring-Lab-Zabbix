# Validation results

## Manual Ubuntu baseline — 2026-10-02

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

**Still pending for this build:** bidirectional inter-guest ping, independent DNS/time synchronization checks, QEMU guest-agent verification, and full physical-host reboot behavior. Successful repository access is narrower evidence than an exhaustive network test. Historical results below do not establish these checks for the new guests.

**Monitoring is not implemented:** Zabbix server/agent, HTTP service, dashboard, fault/recovery exercises and detection timings remain planned. This is a guest baseline, not a monitoring demonstration or load test.

## Historical cloud-image baseline — 2026-09-27

The earlier automated build used different allocations, UEFI and kernel `6.8.0-142-generic`. It passed its own cloud-init, SSH, bidirectional ICMP, DNS/time and QEMU guest-agent checks. Those guests were subsequently replaced by the manual build above.

[Historical observations](evidence/2026-09-27-guest-baseline.txt) are retained as dated evidence, not current-state claims. Private workstation details, credentials and session logs remain outside Git.
