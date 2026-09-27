# Validation results

## Ubuntu guests — 2026-09-27

Both guests were created from the authenticated Ubuntu release image build `20260926`. Five acceptance groups passed; [recorded observations](evidence/2026-09-27-guest-baseline.txt) include exact versions, times and baseline memory/disk readings.

| Check | Observation |
|---|---|
| Provenance and boot | Canonical manifest signature and image SHA256 verified. Both guests booted Ubuntu 24.04.5 LTS, kernel `6.8.0-142-generic`, through UEFI. Cloud-init completed with no errors; no failed systemd units. |
| SSH and identity | Key login worked for `noc`; password and keyboard-interactive authentication disabled, root password locked. Machine IDs and SSH host keys differ between guests. |
| Addressing and peer connectivity | DHCP assigned `.10` to the server and `.20` to the target; both use gateway `192.168.77.1`. Three ICMP requests succeeded in each direction with zero packet loss. |
| DNS, repositories and time | Both resolved `archive.ubuntu.com` and completed `apt-get update` with `APT::Update::Error-Mode=any`. NTP synchronized on both guests. |
| Host integration and budget | Guest agents answered through libvirt. Allocations matched 2 vCPU / 4 GiB / 24 GiB and 1 vCPU / 1 GiB / 12 GiB. Guest autostart disabled. |

Not yet tested: Zabbix server/agent, HTTP service, dashboard, fault/recovery scenarios, or guest restart persistence. Guest agent refers to QEMU guest agent, not the Zabbix agent. The baseline is an idle guest observation, not a load or capacity test.

## Earlier infrastructure check — 2026-09-22

Before creating the guests, KVM access, a temporary paused VM lifecycle, the lab network/DNS and the storage pool were checked. Those checks did not boot a guest OS. The guest results above are the more useful baseline for continuing the project.

The network XML also passed schema validation. Local credentials, VM images and workspace notes are excluded from Git.
