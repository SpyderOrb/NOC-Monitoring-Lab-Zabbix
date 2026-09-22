# Lab design and build steps

Status: virtualization host prepared and checked on 2026-09-22; the two Linux guests and Zabbix deployment are pending. See [validation](VALIDATION.md).

## Initial topology

```text
Host browser -> Zabbix server VM -> Linux target VM
                                   agent + HTTP service
```

The implemented libvirt network `noc-lab` uses bridge `virbr-noc`, gateway `192.168.77.1/24` and IPv4 NAT. The subnet did not overlap the host routes at setup. Its DNS domain is `noc.test`; DHCP reservations are in [the reusable network definition](../configs/libvirt/noc-lab.xml). Guest outbound connectivity will be tested after guest creation. NAT permits guest-initiated access to the LAN as well as the internet; this is not a network for hostile workloads.

## Host preparation

The host has an Intel i5-1145G7 (4 cores / 8 threads), approximately 15 GiB usable RAM and hardware KVM support. Before installation, approximately 10 GiB RAM and 113 GiB disk were available. KVM was already enabled; no firmware change was needed.

Installed from the configured CachyOS/Arch repositories:

| Package | Installed version |
|---|---|
| qemu-desktop | 11.1.1-2 |
| libvirt | 1:12.7.0-1.1 |
| virt-manager / virt-install | 5.1.0-4 |
| dnsmasq | 2.93-1.1 (already installed) |
| edk2-ovmf | 202608-1 |

QEMU/KVM runs the guests; libvirt manages their lifecycle, network and storage; virt-manager provides a graphical view. Management uses `qemu:///system` with local polkit authentication. The packaged `libvirtd.service` and its local sockets are enabled. No libvirt TCP management listener was enabled. The network driver uses its default nftables backend.

The existing UFW firewall remains active. Four lab-specific IPv4 rules permit DHCP, DNS and outbound forwarding through the current uplink `wlan0`. If the uplink changes, review the forwarding rule before expecting guest internet access. Host Wi-Fi addressing and the default route were preserved.

Commands used on the inspected host (run from the repository root; inspect existing routes, firewall rules, networks and pools before reuse):

```sh
sudo pacman -S --needed qemu-desktop libvirt virt-manager virt-install dnsmasq edk2-ovmf
sudo systemctl enable --now libvirtd.service
sudo ufw allow in on virbr-noc proto udp from any to 0.0.0.0/0 port 67 comment 'NOC lab DHCP'
sudo ufw allow in on virbr-noc proto udp from 192.168.77.0/24 to 192.168.77.1 port 53 comment 'NOC lab DNS UDP'
sudo ufw allow in on virbr-noc proto tcp from 192.168.77.0/24 to 192.168.77.1 port 53 comment 'NOC lab DNS TCP'
sudo ufw route allow in on virbr-noc out on wlan0 from 192.168.77.0/24 to any comment 'NOC lab outbound'
sudo virsh -c qemu:///system net-define configs/libvirt/noc-lab.xml
sudo virsh -c qemu:///system net-start noc-lab
sudo virsh -c qemu:///system net-autostart noc-lab
sudo install -d -m 0755 /var/lib/libvirt/images/noc-lab
sudo virsh -c qemu:///system pool-define-as noc-lab dir --target /var/lib/libvirt/images/noc-lab
sudo virsh -c qemu:///system pool-start noc-lab
sudo virsh -c qemu:///system pool-autostart noc-lab
```

The package transaction used existing synchronized package databases; it did not run a standalone database refresh or a system upgrade. On an outdated rolling-release host, complete its normal system update before installing packages.

Inspect with `virsh -c qemu:///system --readonly net-list --all` and `virsh -c qemu:///system --readonly pool-list --all`. Open virt-manager with the system QEMU/KVM connection; management may request administrator authentication. The dedicated pool is empty. Its autostart activates the storage directory, not the guests.

## Planned guests

| Guest | vCPU | RAM | Maximum qcow2 disk | Reserved IPv4 | NIC MAC |
|---|---:|---:|---:|---|---|
| zabbix-server | 2 | 4 GiB | 24 GiB | 192.168.77.10 | 52:54:00:77:00:10 |
| linux-target | 1 | 1 GiB | 12 GiB | 192.168.77.20 | 52:54:00:77:00:20 |

This is a starting budget for a two-host lab, not a vendor sizing recommendation. Recheck resources before creating guests and measure pressure after deployment. Sparse disks grow as data is written; snapshots also consume host disk. Leave guest autostart disabled initially.

Selected guest release family: Ubuntu Server 24.04 LTS, with Zabbix 7.0 LTS packages planned. Both are supported release families as checked on 2026-09-22; neither is installed. Use an official amd64 cloud image, verify its checksum against an authenticated upstream manifest, and record its exact build and installed package versions. Use distinct SSH host keys and keep cloud-init credentials local. UEFI firmware is installed for guest creation.

## Build stages

1. Prepare virtualization and create the two guests. Select a supported guest OS and Zabbix release from current upstream documentation. Set a memory/disk budget and verify guest reachability.
2. Install Zabbix and connect the target agent. Acceptance: a recent target metric is visible and its origin/time can be explained.
3. Add host availability, HTTP and CPU monitoring, a small dashboard, deliberate thresholds and local problem/recovery events. Check that normal operation is healthy.
4. Reproduce the three faults below, restore normal operation and export the reusable configuration. Add concise validation results and runbooks.

## Exercises

| ID | Controlled fault | Expected observation | Recovery |
|---|---|---|---|
| MON-01 | Stop the target's HTTP service | HTTP problem while the target remains reachable | Start service; HTTP succeeds and the event recovers |
| MON-02 | Shut down the target VM | Host-unavailable problem; assess dependent alert suppression | Start guest; monitoring resumes and the event recovers |
| MON-03 | Generate bounded CPU load inside the target VM | Sustained-load problem after the configured evaluation period | Stop load; CPU normalizes and the event recovers |

For each exercise record the fault time, first problem time, restoration time, recovery event time and relevant polling/evaluation intervals. These are observed lab timings, not production SLA claims. Exercise MON-03 must run with a fixed duration and within the guest's CPU allocation.

## Implementation notes

- Use agents and ordinary Linux services first. SNMP network-device monitoring can be a later extension.
- Choose thresholds from observed baseline data; test both an expected problem and normal recovery.
- Keep snapshots or a reversible rollback before fault exercises.
- Add evidence and exports only when produced. Exclude secrets from reusable exports.

## Upstream references

- [CachyOS QEMU and VMM setup](https://wiki.cachyos.org/virtualization/qemu_and_vmm_setup/) — distribution setup context; this lab uses the installed nftables backend with scoped UFW rules.
- [libvirt daemons](https://libvirt.org/daemons.html) and [network format](https://libvirt.org/formatnetwork.html).
- [Ubuntu 24.04 release notes](https://documentation.ubuntu.com/release-notes/24.04/) and [official cloud images](https://cloud-images.ubuntu.com/noble/current/).
- [Zabbix release lifecycle](https://www.zabbix.com/life_cycle_and_release_policy) and [7.0 packages for Ubuntu 24.04](https://www.zabbix.com/download?zabbix=7.0&os_distribution=ubuntu&os_version=24.04&components=server_frontend_agent&db=pgsql&ws=nginx).
- [Zabbix requirements](https://www.zabbix.com/documentation/current/en/manual/installation/requirements)
- [Zabbix appliance](https://www.zabbix.com/documentation/current/en/manual/appliance)
- [Linux monitoring](https://www.zabbix.com/documentation/current/en/manual/guides/monitor_linux)
- [Web monitoring](https://www.zabbix.com/documentation/current/en/manual/web_monitoring)
