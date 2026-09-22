# Validation results

## Virtualization host — 2026-09-22

Directly observed on CachyOS, kernel `7.2.4-1-cachyos`, with the package versions in [LAB.md](LAB.md). Five acceptance checks passed:

| Check | Observation |
|---|---|
| KVM access | `/dev/kvm` opened successfully; KVM API returned version 12. |
| VM lifecycle | Through `qemu:///system`, libvirt created a transient KVM domain with 1 vCPU and 128 MiB RAM in the paused state, then stopped it. Its UUID was absent afterward. It had no disk or NIC; no operating system was booted. |
| Lab network | `noc-lab` active with autostart, NAT, gateway `.1`, and DHCP reservations `.10` / `.20`. IPv4 forwarding enabled; NAT rules and all four scoped UFW rules present. DNS at `192.168.77.1` answered a query for `example.org`. |
| Storage | The `noc-lab` directory pool was active with autostart and contained zero volumes. |
| Host integration | The default route matched the pre-change snapshot. `libvirtd.service` was enabled. No TCP listener existed on libvirt management ports 16509 or 16514. |

Additional static checks: the network XML passed `virt-xml-validate`; local coordination, credentials and image paths are excluded from Git.

Limits: no full guest OS boot, DHCP lease acquisition, guest-to-guest reachability, guest internet access, GUI interaction or reboot persistence test has been performed. Autostart settings were inspected, not verified by rebooting the host. DNS was tested from the host. No Zabbix metrics, dashboard, alert timings or fault/recovery results exist yet. MON-01, MON-02 and MON-03 remain planned.
